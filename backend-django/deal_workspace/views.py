from __future__ import annotations

from datetime import datetime, time
from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import dateparse, timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models, serializers, utils

User = get_user_model()


class DealScopedMixin:
    """Common helpers to scope querysets to deal participants."""

    def _is_admin(self) -> bool:
        return utils.user_is_admin(self.request.user)

    def _participant_deal_ids(self) -> Iterable[int]:
        if not hasattr(self, "_cached_deal_ids"):
            if not self.request.user.is_authenticated:
                self._cached_deal_ids = []
            else:
                self._cached_deal_ids = list(
                    models.PartyRole.objects.filter(
                        user=self.request.user
                    ).values_list("deal_id", flat=True)
                )
        return self._cached_deal_ids

    def _party_roles(self):
        if not hasattr(self, "_cached_roles"):
            if not self.request.user.is_authenticated:
                self._cached_roles = models.PartyRole.objects.none()
            else:
                self._cached_roles = models.PartyRole.objects.filter(
                    user=self.request.user
                )
        return self._cached_roles


class DealCreateView(APIView):
    """Create a deal for a given asset with optional invited parties."""

    def post(self, request, asset_id: int) -> Response:
        if not request.user or not request.user.is_authenticated:
            raise PermissionDenied("Authentication required")

        asset = get_object_or_404(
            models.Deal._meta.get_field("asset").remote_field.model,
            pk=asset_id,
        )
        stage = request.data.get("stage", models.Deal.Stage.DISCOVERY)
        confidentiality = request.data.get(
            "confidentiality_level", models.Deal.Confidentiality.STANDARD
        )
        parties = request.data.get("parties", [])

        with transaction.atomic():
            deal = models.Deal.objects.create(
                asset=asset,
                stage=stage,
                deal_lead=request.user,
                confidentiality_level=confidentiality,
            )

            created_roles = []
            for party in parties:
                role = party.get("role")
                side = party.get("side")
                if not role or not side:
                    raise ValidationError(
                        "Each party must include role and side"
                    )
                user_id = party.get("user_id")
                external_contact = party.get("external_contact_json", {})
                user = None
                if user_id:
                    user = get_object_or_404(User, pk=user_id)
                created_roles.append(
                    models.PartyRole.objects.create(
                        deal=deal,
                        user=user,
                        external_contact_json=external_contact,
                        role=role,
                        side=side,
                        invitation_status=(
                            models.PartyRole.InvitationStatus.ACCEPTED
                            if user_id
                            else models.PartyRole.InvitationStatus.PENDING
                        ),
                    )
                )

            # Ensure the creator has at least observer privileges on the deal
            if not any(
                role.user_id == request.user.id for role in created_roles
            ):
                models.PartyRole.objects.create(
                    deal=deal,
                    user=request.user,
                    role=models.PartyRole.Role.AGENT,
                    side=models.PartyRole.Side.NEUTRAL,
                    invitation_status=(
                        models.PartyRole.InvitationStatus.ACCEPTED
                    ),
                )

            models.AuditLog.objects.create(
                entity_type="deal",
                entity_id=str(deal.pk),
                action="created",
                by_partyrole=deal.party_roles.filter(
                    user=request.user
                ).first(),
                diff_json={
                    "stage": stage,
                    "confidentiality_level": confidentiality,
                },
                ip=request.META.get("REMOTE_ADDR"),
                ua=request.META.get("HTTP_USER_AGENT", ""),
            )

        serializer = serializers.DealSerializer(
            deal, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DealViewSet(DealScopedMixin, viewsets.ModelViewSet):
    serializer_class = serializers.DealSerializer
    queryset = models.Deal.objects.select_related(
        "asset", "deal_lead"
    ).prefetch_related("party_roles")

    def get_queryset(self):
        qs = super().get_queryset()

        if not self._is_admin():
            deal_ids = self._participant_deal_ids()
            if not deal_ids:
                return qs.none()
            qs = qs.filter(id__in=deal_ids)

        params = self.request.query_params

        stage = params.get("stage")
        if stage:
            qs = qs.filter(stage=stage)

        deal_lead = params.get("deal_lead")
        if deal_lead:
            qs = qs.filter(deal_lead_id=deal_lead)

        asset_id = params.get("asset_id")
        if asset_id:
            qs = qs.filter(asset_id=asset_id)

        updated_after = params.get("updated_after")
        if updated_after:
            parsed = dateparse.parse_datetime(updated_after)
            if not parsed:
                parsed_date = dateparse.parse_date(updated_after)
                if parsed_date:
                    parsed = timezone.make_aware(
                        datetime.combine(parsed_date, time.min)
                    )
            if parsed:
                qs = qs.filter(updated_at__gte=parsed)

        search = params.get("q")
        if search:
            qs = qs.filter(
                Q(asset__normalized_address__icontains=search)
                | Q(asset__city__icontains=search)
                | Q(asset__street__icontains=search)
                | Q(asset__neighborhood__icontains=search)
            )

        return qs.order_by("-updated_at", "-created_at")

    def perform_update(self, serializer):
        previous = serializer.instance.stage
        deal = serializer.save()
        if previous != deal.stage:
            models.AuditLog.objects.create(
                entity_type="deal",
                entity_id=str(deal.pk),
                action="stage_changed",
                by_partyrole=deal.party_roles.filter(
                    user=self.request.user
                ).first(),
                diff_json={"from": previous, "to": deal.stage},
                ip=self.request.META.get("REMOTE_ADDR"),
                ua=self.request.META.get("HTTP_USER_AGENT", ""),
            )


class NegotiationCreateView(APIView):
    def post(self, request, deal_id: int) -> Response:
        deal = get_object_or_404(models.Deal, pk=deal_id)
        if not (
            utils.user_is_admin(request.user)
            or utils.get_party_role_for_user(deal, request.user)
        ):
            raise PermissionDenied("Not a participant in this deal")

        with transaction.atomic():
            negotiation = models.Negotiation.objects.create(deal=deal)
            deal.stage = models.Deal.Stage.NEGOTIATION
            deal.save(update_fields=["stage", "updated_at"])
            models.AuditLog.objects.create(
                entity_type="negotiation",
                entity_id=str(negotiation.pk),
                action="created",
                by_partyrole=deal.party_roles.filter(
                    user=request.user
                ).first(),
                diff_json={},
                ip=request.META.get("REMOTE_ADDR"),
                ua=request.META.get("HTTP_USER_AGENT", ""),
            )

        serializer = serializers.NegotiationSerializer(
            negotiation, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NegotiationViewSet(DealScopedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.NegotiationSerializer
    queryset = models.Negotiation.objects.select_related(
        "deal", "current_offer"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if self._is_admin():
            return qs
        deal_ids = self._participant_deal_ids()
        if not deal_ids:
            return qs.none()
        return qs.filter(deal_id__in=deal_ids)


class OfferViewSet(DealScopedMixin, viewsets.ModelViewSet):
    serializer_class = serializers.OfferSerializer
    queryset = models.Offer.objects.select_related(
        "negotiation", "submitted_by", "negotiation__deal"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if self._is_admin():
            filtered = qs
        else:
            deal_ids = self._participant_deal_ids()
            if not deal_ids:
                return qs.none()
            filtered = qs.filter(negotiation__deal_id__in=deal_ids)

        negotiation_id = self.request.query_params.get("negotiation_id")
        if negotiation_id:
            filtered = filtered.filter(negotiation_id=negotiation_id)
        status_param = self.request.query_params.get("status")
        if status_param:
            filtered = filtered.filter(status=status_param)
        expires_before = self.request.query_params.get("expires_before")
        if expires_before:
            dt = dateparse.parse_datetime(expires_before)
            if dt:
                filtered = filtered.filter(expiration_at__lte=dt)
        expires_after = self.request.query_params.get("expires_after")
        if expires_after:
            dt = dateparse.parse_datetime(expires_after)
            if dt:
                filtered = filtered.filter(expiration_at__gte=dt)
        return filtered

    def _create_offer(
        self,
        serializer: serializers.OfferSerializer,
        party_role: models.PartyRole,
    ) -> models.Offer:
        data = dict(serializer.validated_data)
        negotiation = data.pop("negotiation")
        offer = models.Offer.objects.create(
            negotiation=negotiation,
            submitted_by=party_role,
            **data,
        )
        negotiation.current_offer = offer
        negotiation.save(update_fields=["current_offer", "updated_at"])
        models.AuditLog.objects.create(
            entity_type="offer",
            entity_id=str(offer.pk),
            action="created",
            by_partyrole=party_role,
            diff_json={"amount": str(offer.amount), "status": offer.status},
            ip=self.request.META.get("REMOTE_ADDR"),
            ua=self.request.META.get("HTTP_USER_AGENT", ""),
        )
        return offer

    def perform_create(self, serializer):
        negotiation = serializer.validated_data["negotiation"]
        party_role = utils.get_party_role_for_user(
            negotiation.deal, self.request.user
        )
        if not party_role and not self._is_admin():
            raise PermissionDenied("You are not part of this negotiation")
        if negotiation.status != models.Negotiation.Status.OPEN:
            raise ValidationError("Negotiation is not open")
        offer = self._create_offer(serializer, party_role)
        serializer.instance = offer

    @action(detail=True, methods=["post"])
    def counter(self, request, pk=None):
        offer = self.get_object()
        negotiation = offer.negotiation
        party_role = utils.get_party_role_for_user(
            negotiation.deal, request.user
        )
        if not party_role and not self._is_admin():
            raise PermissionDenied("You are not part of this negotiation")
        if party_role.side == offer.submitted_by.side:
            raise PermissionDenied(
                "Counter offer must come from the opposite side"
            )

        data = request.data.copy()
        data["negotiation"] = negotiation.pk
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            locked = models.Offer.objects.select_for_update().get(pk=offer.pk)
            if locked.status != models.Offer.Status.ACTIVE:
                raise ValidationError("Only active offers can be countered")
            locked.status = models.Offer.Status.COUNTERED
            locked.save(update_fields=["status", "updated_at"])
            new_offer = self._create_offer(serializer, party_role)

        output = self.get_serializer(new_offer)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def _require_counterparty(
        self, offer: models.Offer, user
    ) -> models.PartyRole:
        party_role = utils.get_party_role_for_user(
            offer.negotiation.deal, user
        )
        if not party_role and not utils.user_is_admin(user):
            raise PermissionDenied("You are not part of this negotiation")
        if party_role and party_role.side == offer.submitted_by.side:
            raise PermissionDenied("Action requires counterparty")
        return party_role

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        with transaction.atomic():
            offer = (
                models.Offer.objects.select_for_update()
                .select_related(
                    "negotiation", "negotiation__deal", "submitted_by"
                )
                .get(pk=pk)
            )
            if offer.status != models.Offer.Status.ACTIVE:
                raise ValidationError("Only active offers can be accepted")
            if offer.is_expired():
                offer.status = models.Offer.Status.EXPIRED
                offer.save(update_fields=["status", "updated_at"])
                raise ValidationError("Offer has expired")
            self._require_counterparty(offer, request.user)
            offer.status = models.Offer.Status.ACCEPTED
            offer.save(update_fields=["status", "updated_at"])
            negotiation = offer.negotiation
            negotiation.status = models.Negotiation.Status.CLOSED
            negotiation.current_offer = offer
            negotiation.save(
                update_fields=["status", "current_offer", "updated_at"]
            )
            deal = negotiation.deal
            deal.stage = models.Deal.Stage.LEGAL
            deal.save(update_fields=["stage", "updated_at"])
            models.AuditLog.objects.create(
                entity_type="offer",
                entity_id=str(offer.pk),
                action="accepted",
                by_partyrole=deal.party_roles.filter(
                    user=request.user
                ).first(),
                diff_json={},
                ip=request.META.get("REMOTE_ADDR"),
                ua=request.META.get("HTTP_USER_AGENT", ""),
            )
        serializer = self.get_serializer(offer)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        with transaction.atomic():
            offer = (
                models.Offer.objects.select_for_update()
                .select_related(
                    "negotiation", "negotiation__deal", "submitted_by"
                )
                .get(pk=pk)
            )
            if offer.status != models.Offer.Status.ACTIVE:
                raise ValidationError("Only active offers can be rejected")
            self._require_counterparty(offer, request.user)
            offer.status = models.Offer.Status.REJECTED
            offer.save(update_fields=["status", "updated_at"])
            models.AuditLog.objects.create(
                entity_type="offer",
                entity_id=str(offer.pk),
                action="rejected",
                by_partyrole=offer.negotiation.deal.party_roles.filter(
                    user=request.user
                ).first(),
                diff_json={},
                ip=request.META.get("REMOTE_ADDR"),
                ua=request.META.get("HTTP_USER_AGENT", ""),
            )
        serializer = self.get_serializer(offer)
        return Response(serializer.data)


class DocumentViewSet(DealScopedMixin, viewsets.ModelViewSet):
    serializer_class = serializers.DocumentSerializer
    queryset = models.Document.objects.select_related(
        "deal", "asset", "uploader_partyrole"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if self._is_admin():
            filtered = qs
        else:
            user = self.request.user
            if not user.is_authenticated:
                return qs.none()
            buyer_deals = (
                self._party_roles()
                .filter(side=models.PartyRole.Side.BUYER)
                .values_list("deal_id", flat=True)
            )
            seller_deals = (
                self._party_roles()
                .filter(side=models.PartyRole.Side.SELLER)
                .values_list("deal_id", flat=True)
            )
            neutral_deals = (
                self._party_roles()
                .filter(side=models.PartyRole.Side.NEUTRAL)
                .values_list("deal_id", flat=True)
            )
            filtered = qs.filter(
                Q(visibility_scope=models.Document.Visibility.PUBLIC_LINK)
                | Q(uploader_partyrole__user=user)
                | Q(
                    deal_id__in=buyer_deals,
                    visibility_scope__in=[
                        models.Document.Visibility.DEAL,
                        models.Document.Visibility.BUYER_SIDE,
                    ],
                )
                | Q(
                    deal_id__in=seller_deals,
                    visibility_scope__in=[
                        models.Document.Visibility.DEAL,
                        models.Document.Visibility.SELLER_SIDE,
                    ],
                )
                | Q(
                    deal_id__in=neutral_deals,
                    visibility_scope=models.Document.Visibility.DEAL,
                )
            )
        deal_id = self.request.query_params.get("deal_id")
        if deal_id:
            filtered = filtered.filter(deal_id=deal_id)
        kind = self.request.query_params.get("kind")
        if kind:
            filtered = filtered.filter(kind=kind)
        status_param = self.request.query_params.get("status")
        if status_param:
            filtered = filtered.filter(status=status_param)
        return filtered.distinct()

    def perform_create(self, serializer):
        deal = serializer.validated_data.get("deal")
        party_role = None
        if deal:
            party_role = utils.get_party_role_for_user(deal, self.request.user)
            if not party_role and not self._is_admin():
                raise PermissionDenied("You cannot upload to this deal")
        document = serializer.save(
            uploader_partyrole=party_role,
            status=models.Document.Status.PROCESSING,
        )
        models.AuditLog.objects.create(
            entity_type="document",
            entity_id=str(document.pk),
            action="uploaded",
            by_partyrole=party_role,
            diff_json={
                "kind": document.kind,
                "visibility": document.visibility_scope,
            },
            ip=self.request.META.get("REMOTE_ADDR"),
            ua=self.request.META.get("HTTP_USER_AGENT", ""),
        )

    @action(detail=True, methods=["post"])
    def extract(self, request, pk=None):
        document = self.get_object()
        document.status = models.Document.Status.READY
        document.extracted_json = request.data or {}
        document.save(update_fields=["status", "extracted_json", "updated_at"])
        models.AuditLog.objects.create(
            entity_type="document",
            entity_id=str(document.pk),
            action="extracted",
            by_partyrole=document.uploader_partyrole,
            diff_json=document.extracted_json,
            ip=request.META.get("REMOTE_ADDR"),
            ua=request.META.get("HTTP_USER_AGENT", ""),
        )
        serializer = self.get_serializer(document)
        return Response(serializer.data)


class LegalCaseViewSet(DealScopedMixin, viewsets.ModelViewSet):
    serializer_class = serializers.LegalCaseSerializer
    queryset = models.LegalCase.objects.select_related(
        "deal", "responsible_partyrole"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if self._is_admin():
            filtered = qs
        else:
            deal_ids = self._participant_deal_ids()
            if not deal_ids:
                return qs.none()
            filtered = qs.filter(deal_id__in=deal_ids)
        return filtered


class TaskViewSet(DealScopedMixin, viewsets.ModelViewSet):
    serializer_class = serializers.TaskSerializer
    queryset = models.Task.objects.select_related(
        "deal", "legalcase", "assignee_partyrole"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if self._is_admin():
            filtered = qs
        else:
            deal_ids = self._participant_deal_ids()
            if not deal_ids:
                return qs.none()
            filtered = qs.filter(
                Q(deal_id__in=deal_ids) | Q(legalcase__deal_id__in=deal_ids)
            )
        deal_id = self.request.query_params.get("deal_id")
        if deal_id:
            filtered = filtered.filter(
                Q(deal_id=deal_id) | Q(legalcase__deal_id=deal_id)
            )
        status_param = self.request.query_params.get("status")
        if status_param:
            filtered = filtered.filter(status=status_param)
        return filtered.distinct()


class AppraisalViewSet(DealScopedMixin, viewsets.ModelViewSet):
    serializer_class = serializers.AppraisalSerializer
    queryset = models.Appraisal.objects.select_related("asset", "deal")

    def get_queryset(self):
        qs = super().get_queryset()
        if self._is_admin():
            filtered = qs
        else:
            user = self.request.user
            if not user.is_authenticated:
                return qs.none()
            asset_ids = models.Deal.objects.filter(
                id__in=self._participant_deal_ids()
            ).values_list("asset_id", flat=True)
            filtered = qs.filter(
                Q(deal_id__in=self._participant_deal_ids())
                | Q(asset_id__in=asset_ids)
            )
        asset_id = self.request.query_params.get("asset_id")
        if asset_id:
            filtered = filtered.filter(asset_id=asset_id)
        return filtered


class PlanSetViewSet(DealScopedMixin, viewsets.ModelViewSet):
    serializer_class = serializers.PlanSetSerializer
    queryset = models.PlanSet.objects.select_related(
        "asset", "architect_partyrole"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if self._is_admin():
            filtered = qs
        else:
            asset_ids = models.Deal.objects.filter(
                id__in=self._participant_deal_ids()
            ).values_list("asset_id", flat=True)
            filtered = qs.filter(asset_id__in=asset_ids)
        asset_id = self.request.query_params.get("asset_id")
        if asset_id:
            filtered = filtered.filter(asset_id=asset_id)
        return filtered


class MortgageApplicationViewSet(DealScopedMixin, viewsets.ModelViewSet):
    serializer_class = serializers.MortgageApplicationSerializer
    queryset = models.MortgageApplication.objects.select_related(
        "deal", "applicant_partyrole"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if self._is_admin():
            filtered = qs
        else:
            deal_ids = self._participant_deal_ids()
            if not deal_ids:
                return qs.none()
            filtered = qs.filter(deal_id__in=deal_ids)
        deal_id = self.request.query_params.get("deal_id")
        if deal_id:
            filtered = filtered.filter(deal_id=deal_id)
        return filtered

    def perform_create(self, serializer):
        deal = serializer.validated_data["deal"]
        party_role = serializer.validated_data["applicant_partyrole"]
        if party_role.deal_id != deal.id:
            raise ValidationError("Applicant must belong to deal")
        if party_role.user != self.request.user and not self._is_admin():
            raise PermissionDenied(
                "Only the applicant can create their mortgage application"
            )
        serializer.save()


class MortgageOfferViewSet(DealScopedMixin, viewsets.ModelViewSet):
    serializer_class = serializers.MortgageOfferSerializer
    queryset = models.MortgageOffer.objects.select_related(
        "mortgageapplication", "mortgageapplication__deal"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if self._is_admin():
            filtered = qs
        else:
            deal_ids = self._participant_deal_ids()
            if not deal_ids:
                return qs.none()
            filtered = qs.filter(mortgageapplication__deal_id__in=deal_ids)
        mortgageapplication_id = self.request.query_params.get(
            "mortgageapplication_id"
        )
        if mortgageapplication_id:
            filtered = filtered.filter(
                mortgageapplication_id=mortgageapplication_id
            )
        return filtered

    def perform_create(self, serializer):
        application = serializer.validated_data["mortgageapplication"]
        party_role = utils.get_party_role_for_user(
            application.deal, self.request.user
        )
        if not party_role and not self._is_admin():
            raise PermissionDenied("You cannot add offers to this application")
        serializer.save()


class AuditLogViewSet(
    DealScopedMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = serializers.AuditLogSerializer
    queryset = models.AuditLog.objects.select_related(
        "by_partyrole", "by_partyrole__deal"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        if self._is_admin():
            return qs
        deal_ids = self._participant_deal_ids()
        if not deal_ids:
            return qs.none()
        return qs.filter(by_partyrole__deal_id__in=deal_ids)
