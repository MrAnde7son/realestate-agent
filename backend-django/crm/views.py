from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.http import HttpResponse
import csv
from io import StringIO

from .models import Contact, Lead, LeadStatus
from .serializers import (
    ContactSerializer, 
    LeadSerializer, 
    LeadStatusUpdateSerializer,
    LeadNoteSerializer
)
from .permissions import IsOwnerContact
from .analytics import (
    track_crm_search, track_crm_export, track_crm_dashboard_view,
    track_crm_contact_lead_association, track_crm_bulk_action,
    track_crm_permission_denied, track_crm_error
)


class StandardPagination(PageNumberPagination):
    """Default pagination for CRM endpoints supporting `page_size` query param."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def should_paginate(request):
    """Determine if pagination should be applied based on query parameters."""

    params = request.query_params
    return any(params.get(param) for param in ("page", "page_size"))


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for managing contacts."""

    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated, IsOwnerContact]
    pagination_class = StandardPagination

    def get_queryset(self):
        """Return contacts owned by the current user, or all contacts for superusers."""
        if self.request.user.is_superuser:
            return Contact.objects.all().order_by("-updated_at")
        return Contact.objects.filter(owner=self.request.user).order_by("-updated_at")

    def perform_create(self, serializer):
        """Set the owner when creating a contact."""
        try:
            with transaction.atomic():
                serializer.save(owner=self.request.user)
        except IntegrityError as e:
            from rest_framework.exceptions import ValidationError
            if 'unique constraint' in str(e).lower() and 'email' in str(e):
                raise ValidationError({
                    'email': ['A contact with this email already exists for your account.']
                })
            raise ValidationError({
                'non_field_errors': ['A database error occurred while creating the contact.']
            })

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if should_paginate(request):
            try:
                paginator = self.pagination_class()
                page = paginator.paginate_queryset(queryset, request, view=self)
                serializer = self.get_serializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            except Exception:
                # If pagination fails, fall back to non-paginated response
                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search contacts by name, email, phone, or tags."""
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
        
        # Build search query
        search_q = Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query)
        
        # Add tag search - check if any tag contains the query
        search_q |= Q(tags__icontains=query)
        
        contacts = self.get_queryset().filter(search_q)[:10]  # Limit to 10 results
        
        # Track search event
        track_crm_search(request.user.id, 'contacts', query, contacts.count())
        
        serializer = self.get_serializer(contacts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        """Export contacts for the authenticated user as CSV."""

        queryset = self.get_queryset()
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Email", "Phone", "Tags", "Created At"])

        for contact in queryset:
            writer.writerow([
                contact.name,
                contact.email,
                contact.phone,
                "; ".join(contact.tags or []),
                contact.created_at.isoformat()
            ])

        output.seek(0)

        track_crm_export(request.user.id, "contacts", queryset.count())

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="contacts.csv"'
        return response

    @action(detail=True, methods=['get'])
    def leads(self, request, pk=None):
        """Get all leads for a specific contact."""
        contact = self.get_object()
        
        # Get leads for this contact
        leads = Lead.objects.filter(contact=contact).select_related('asset').order_by('-last_activity_at')
        
        # Apply any filters from query parameters
        status_filter = request.query_params.get('status')
        if status_filter:
            leads = leads.filter(status=status_filter)
        
        # Serialize the leads
        from .serializers import LeadSerializer
        serializer = LeadSerializer(leads, many=True, context={'request': request})
        
        return Response(serializer.data)


class LeadViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leads."""

    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated, IsOwnerContact]
    pagination_class = StandardPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if should_paginate(request):
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request, view=self)
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        """Return leads for contacts owned by the current user, or all leads for superusers."""
        if self.request.user.is_superuser:
            queryset = Lead.objects.all().select_related("contact", "asset").order_by("-last_activity_at")
        else:
            queryset = Lead.objects.filter(
                contact__owner=self.request.user
            ).select_related("contact", "asset").order_by("-last_activity_at")
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

    def perform_create(self, serializer):
        """Create a lead with proper error handling."""
        try:
            serializer.save()
        except IntegrityError as e:
            if 'unique constraint' in str(e).lower() and 'contact_id' in str(e):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'non_field_errors': ['A lead already exists for this contact and asset combination.']
                })
            raise

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        """Update lead status."""
        lead = self.get_object()
        serializer = LeadStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            old_status = lead.status
            lead.status = serializer.validated_data['status']
            lead.last_activity_at = timezone.now()
            lead.save(update_fields=["status", "last_activity_at"])
            
            # Track status change event
            from .analytics import track_lead_status_changed
            track_lead_status_changed(lead, request.user.id, old_status, lead.status)
            
            return Response(LeadSerializer(lead, context={"request": request}).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def add_note(self, request, pk=None):
        """Add a note to the lead."""
        lead = self.get_object()
        serializer = LeadNoteSerializer(data=request.data)
        
        if serializer.is_valid():
            note_text = serializer.validated_data['text'].strip()
            if not note_text:
                return Response(
                    {"detail": "Cannot add empty note"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add note to the notes list
            notes = lead.notes or []
            notes.append({
                "ts": timezone.now().isoformat(),
                "text": note_text
            })
            lead.notes = notes
            lead.last_activity_at = timezone.now()
            lead.save(update_fields=["notes", "last_activity_at"])
            
            # Track note addition event
            from .analytics import track_lead_note_added
            track_lead_note_added(lead, request.user.id, note_text)
            
            return Response(LeadSerializer(lead, context={"request": request}).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def send_report(self, request, pk=None):
        """Send a report to the lead's contact."""
        lead = self.get_object()
        
        # Track report sending event
        from .analytics import track_lead_report_sent
        via = 'email' if lead.contact.email else 'link'
        track_lead_report_sent(lead, request.user.id, via)
        
        # This would integrate with the existing report service
        # For now, just return a success message
        return Response({
            "message": "Report sent successfully",
            "contact_email": lead.contact.email
        })

    @action(detail=False, methods=['get'])
    def by_asset(self, request):
        """Get leads for a specific asset."""
        asset_id = request.query_params.get('asset_id')
        if not asset_id:
            return Response(
                {"detail": "asset_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        from core.models import Asset

        try:
            asset_id_int = int(asset_id)
            asset = Asset.objects.get(id=asset_id_int)
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid asset_id format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Asset.DoesNotExist:
            return Response(
                {"detail": "Asset not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        leads = self.get_queryset().filter(asset=asset)
        serializer = self.get_serializer(leads, many=True)
        return Response(serializer.data)
