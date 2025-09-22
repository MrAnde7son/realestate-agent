import os
import logging
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.conf import settings

from .models import Asset, Document
from .serializers import DocumentSerializer, DocumentUploadSerializer, DocumentListSerializer
from .storage import document_storage

try:
    from utils.tabu_parser import parse_tabu_pdf
except Exception:  # pragma: no cover - fallback when parser is unavailable
    parse_tabu_pdf = None

logger = logging.getLogger(__name__)


class DocumentUploadView(APIView):
    """Handle document uploads for assets."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, asset_id):
        """Upload a document for an asset."""
        try:
            # Get asset
            asset = get_object_or_404(Asset, id=asset_id)
            
            # Check permissions (user owns asset or is admin)
            if not (asset.created_by == request.user or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Prepare data for serializer (support legacy field names)
            data = request.data.copy()
            uploaded_file = request.FILES.get('file') or data.get('file')
            if 'document_type' not in data and 'type' in data:
                data['document_type'] = data['type']
            if not data.get('title'):
                inferred_title = getattr(uploaded_file, 'name', None) if uploaded_file else None
                data['title'] = inferred_title or 'מסמך'

            # Validate upload data
            serializer = DocumentUploadSerializer(data=data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            file = serializer.validated_data['file']
            
            # Save file
            file_info, error = document_storage.save_document(file, asset_id, file.name)
            if error:
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create document record
            document = Document.objects.create(
                asset=asset,
                user=request.user,
                title=serializer.validated_data['title'],
                description=serializer.validated_data.get('description', ''),
                document_type=serializer.validated_data['document_type'],
                document_date=serializer.validated_data.get('document_date'),
                external_id=serializer.validated_data.get('external_id', ''),
                external_url=serializer.validated_data.get('external_url', ''),
                filename=file.name,
                file_path=file_info['file_path'],
                file_size=file_info['file_size'],
                mime_type=file_info['mime_type'],
                source='user_upload'
            )

            # Parse Tabu documents and persist extracted rows
            if document.document_type == 'tabu' and parse_tabu_pdf:
                try:
                    with default_storage.open(file_info['file_path'], 'rb') as stored_file:
                        rows = parse_tabu_pdf(stored_file) or []
                    if rows:
                        document.meta = {**(document.meta or {}), 'tabu_rows': rows}
                        document.save(update_fields=['meta'])
                except Exception as parse_error:  # pragma: no cover - defensive logging
                    logger.error(
                        "Error parsing tabu document %s: %s", document.id, parse_error
                    )

            # Return document data in the structure expected by the frontend
            doc_payload = {
                'id': document.id,
                'title': document.title,
                'description': document.description,
                'type': document.document_type,
                'status': document.status,
                'filename': document.filename,
                'file_size': document.file_size,
                'date': document.document_date.isoformat() if document.document_date else None,
                'url': document.file_url,
                'source': document.source,
                'external_id': document.external_id,
                'external_url': document.external_url,
                'downloadable': document.is_downloadable,
                'uploaded_at': document.uploaded_at.isoformat() if document.uploaded_at else None,
                'uploaded_by': str(document.user) if document.user else None,
                'meta': document.meta,
            }

            return Response({'doc': doc_payload}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return Response(
                {'error': 'Upload failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentListView(APIView):
    """List documents for an asset."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, asset_id):
        """Get all documents for an asset."""
        try:
            # Get asset
            asset = get_object_or_404(Asset, id=asset_id)
            
            # Check permissions
            if not (asset.created_by == request.user or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get documents
            documents = asset.documents.all()
            serializer = DocumentListSerializer(documents, many=True)
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return Response(
                {'error': 'Failed to list documents'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AssetRightsView(APIView):
    """Return comprehensive rights data for an asset including Tabu and GIS data."""

    permission_classes = [IsAuthenticated]

    def get(self, request, asset_id):
        try:
            asset = get_object_or_404(Asset, id=asset_id)

            if not (asset.created_by == request.user or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            query = (request.query_params.get('q') or '').strip().lower()
            
            # Initialize response data
            rights_data = {
                'tabu_data': [],
                'gis_rights': [],
                'building_rights': {},
                'ownership_summary': {},
                'total_rows': 0
            }

            # 1. Get Tabu data from uploaded documents
            documents = asset.documents.filter(document_type='tabu').order_by('-uploaded_at')
            for document in documents:
                doc_rows = document.meta.get('tabu_rows') if document.meta else []
                if not isinstance(doc_rows, list):
                    continue

                for idx, row in enumerate(doc_rows):
                    field = str(row.get('field', '') or '')
                    value = str(row.get('value', '') or '')
                    
                    row_data = {
                        'id': f"tabu_{document.id}-{idx}",
                        'document_id': document.id,
                        'document_title': document.title,
                        'document_url': document.file_url,
                        'uploaded_at': document.uploaded_at.isoformat() if document.uploaded_at else None,
                        'source': 'tabu_upload',
                        'field': field,
                        'value': value,
                        'type': 'tabu'
                    }
                    
                    # Filter by query if provided
                    if not query or query in field.lower() or query in value.lower():
                        rights_data['tabu_data'].append(row_data)

            # 2. Get GIS rights data from asset metadata
            gis_rights = asset.get_property_value('gis_data.land_use_rights', [])
            if gis_rights:
                for idx, right in enumerate(gis_rights):
                    if isinstance(right, dict):
                        right_data = {
                            'id': f"gis_rights_{idx}",
                            'source': 'gis',
                            'type': 'land_use',
                            'land_use': right.get('land_use', ''),
                            'plan_name': right.get('plan_name', ''),
                            'plan_number': right.get('plan_number', ''),
                            'status': right.get('status', ''),
                            'area': right.get('area', ''),
                            'description': f"שימוש קרקע: {right.get('land_use', '')}",
                            'raw_data': right
                        }
                        
                        # Filter by query if provided
                        if not query or any(query in str(v).lower() for v in right_data.values() if v):
                            rights_data['gis_rights'].append(right_data)

            # 3. Get building rights information
            if asset.meta:
                building_rights = {
                    'main_rights_sqm': asset.meta.get('mainRightsSqm'),
                    'service_rights_sqm': asset.meta.get('serviceRightsSqm'),
                    'remaining_rights_sqm': asset.meta.get('remainingRightsSqm'),
                    'zoning': asset.meta.get('zoning'),
                    'program': asset.meta.get('program'),
                    'rights_usage_pct': asset.meta.get('rightsUsagePct')
                }
                rights_data['building_rights'] = building_rights

            # 4. Parse ownership information from Tabu data
            ownership_info = self._parse_ownership_from_tabu(rights_data['tabu_data'])
            rights_data['ownership_summary'] = ownership_info

            # 5. Calculate total rows
            rights_data['total_rows'] = len(rights_data['tabu_data']) + len(rights_data['gis_rights'])

            return Response(rights_data)

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Error fetching rights for asset {asset_id}: {exc}")
            return Response(
                {'error': 'Failed to fetch rights data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _parse_ownership_from_tabu(self, tabu_data):
        """Parse ownership information from Tabu data."""
        ownership = {
            'owners': [],
            'total_ownership_percentage': 0,
            'parcel_info': {}
        }
        
        current_owner = None
        ownership_percentage = 0
        
        for row in tabu_data:
            field = row.get('field', '').lower()
            value = row.get('value', '')
            
            # Look for owner information
            if 'בעלים' in field or 'owner' in field:
                if current_owner and ownership_percentage > 0:
                    ownership['owners'].append({
                        'name': current_owner,
                        'percentage': ownership_percentage
                    })
                current_owner = value
                ownership_percentage = 0
            
            # Look for ownership percentage
            elif '%' in value or 'אחוז' in field:
                try:
                    # Extract percentage from value
                    import re
                    percentage_match = re.search(r'(\d+(?:\.\d+)?)', value)
                    if percentage_match:
                        ownership_percentage = float(percentage_match.group(1))
                except (ValueError, AttributeError):
                    pass
            
            # Look for parcel information
            elif 'גוש' in field:
                ownership['parcel_info']['block'] = value
            elif 'חלקה' in field:
                ownership['parcel_info']['parcel'] = value
            elif 'תת חלקה' in field:
                ownership['parcel_info']['subparcel'] = value
        
        # Add the last owner if exists
        if current_owner and ownership_percentage > 0:
            ownership['owners'].append({
                'name': current_owner,
                'percentage': ownership_percentage
            })
        
        # Calculate total ownership percentage
        ownership['total_ownership_percentage'] = sum(owner['percentage'] for owner in ownership['owners'])
        
        return ownership


class DocumentDetailView(APIView):
    """Handle individual document operations."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, asset_id, document_id):
        """Get document details."""
        try:
            # Get document
            document = get_object_or_404(Document, id=document_id, asset_id=asset_id)
            
            # Check permissions
            if not (document.asset.created_by == request.user or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = DocumentSerializer(document)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return Response(
                {'error': 'Failed to get document'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, asset_id, document_id):
        """Update document metadata."""
        try:
            # Get document
            document = get_object_or_404(Document, id=document_id, asset_id=asset_id)
            
            # Check permissions
            if not (document.asset.created_by == request.user or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Update document
            serializer = DocumentSerializer(document, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return Response(
                {'error': 'Failed to update document'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, asset_id, document_id):
        """Delete document."""
        try:
            # Get document
            document = get_object_or_404(Document, id=document_id, asset_id=asset_id)
            
            # Check permissions
            if not (document.asset.created_by == request.user or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Delete file
            document.delete_file()
            
            # Delete document record
            document.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return Response(
                {'error': 'Failed to delete document'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentDownloadView(View):
    """Handle document downloads."""
    
    def get(self, request, asset_id, document_id):
        """Download a document file."""
        try:
            # Get document
            document = get_object_or_404(Document, id=document_id, asset_id=asset_id)
            
            # Check permissions
            if not request.user.is_authenticated:
                return HttpResponse('Authentication required', status=401)
            
            if not (document.asset.created_by == request.user or request.user.is_staff):
                return HttpResponse('Permission denied', status=403)
            
            # Check if file exists
            if not document.is_downloadable:
                raise Http404("File not found")
            
            # Get file content
            try:
                with default_storage.open(document.file_path, 'rb') as file:
                    response = HttpResponse(file.read(), content_type=document.mime_type)
                    response['Content-Disposition'] = f'attachment; filename="{document.filename}"'
                    return response
            except Exception as e:
                logger.error(f"Error reading file {document.file_path}: {e}")
                raise Http404("File not found")
                
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            return HttpResponse('Download failed', status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_document_from_meta(request, asset_id):
    """Create Document records from meta field documents."""
    try:
        # Get asset
        asset = get_object_or_404(Asset, id=asset_id)
        
        # Check permissions
        if not (asset.created_by == request.user or request.user.is_staff):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get documents from meta
        if not asset.meta or 'documents' not in asset.meta:
            return Response({'message': 'No documents in meta field'})
        
        created_documents = []
        documents = asset.get_property_value('documents', [])
        for doc_data in documents:
            # Skip if already exists as Document record
            if Document.objects.filter(
                asset=asset, 
                external_id=doc_data.get('id')
            ).exists():
                continue
            
            # Create Document record
            document = Document.objects.create(
                asset=asset,
                user=request.user,
                title=doc_data.get('title', 'Untitled Document'),
                description=doc_data.get('description', ''),
                document_type=doc_data.get('type', 'other'),
                status=doc_data.get('status', 'pending'),
                external_id=doc_data.get('id'),
                external_url=doc_data.get('url'),
                source=doc_data.get('source', 'meta_migration'),
                document_date=doc_data.get('date'),
                filename=doc_data.get('filename', 'unknown'),
                file_path='',  # No file for meta documents
                file_size=0,
                mime_type='application/octet-stream'
            )
            
            created_documents.append(DocumentSerializer(document).data)
        
        return Response({
            'message': f'Created {len(created_documents)} documents',
            'documents': created_documents
        })
        
    except Exception as e:
        logger.error(f"Error creating documents from meta: {e}")
        return Response(
            {'error': 'Failed to create documents'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
