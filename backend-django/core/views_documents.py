import logging
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views import View
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView

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

    permission_classes = [AllowAny]  # Changed from [IsAuthenticated] to allow public access

    def get(self, request, asset_id):
        try:
            asset = get_object_or_404(Asset, id=asset_id)


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
                        # Extract meaningful data from raw GIS data
                        raw_data = right.get('raw_data', {})
                        land_use = raw_data.get('t_yeud_karka', '') or right.get('land_use', '')
                        main_purpose = raw_data.get('t_yeud_rashi', '') or right.get('plan_name', '')
                        area = raw_data.get('ms_shetach', '') or right.get('area', '')
                        block = raw_data.get('ms_gush', '') or ''
                        parcel = raw_data.get('ms_migrash', '') or ''
                        
                        # Create multiple rows for different GIS data points
                        gis_rows = []
                        
                        if land_use:
                            gis_rows.append({
                                'id': f"gis_rights_{idx}_land_use",
                                'source': 'gis',
                                'field': 'שימוש קרקע',
                                'value': land_use,
                                'type': 'land_use'
                            })
                        
                        if main_purpose:
                            gis_rows.append({
                                'id': f"gis_rights_{idx}_purpose",
                                'source': 'gis',
                                'field': 'יעוד ראשי',
                                'value': main_purpose,
                                'type': 'land_use'
                            })
                        
                        if area:
                            gis_rows.append({
                                'id': f"gis_rights_{idx}_area",
                                'source': 'gis',
                                'field': 'שטח (מ״ר)',
                                'value': str(area),
                                'type': 'land_use'
                            })
                        
                        if block:
                            gis_rows.append({
                                'id': f"gis_rights_{idx}_block",
                                'source': 'gis',
                                'field': 'גוש',
                                'value': str(block),
                                'type': 'land_use'
                            })
                        
                        if parcel:
                            gis_rows.append({
                                'id': f"gis_rights_{idx}_parcel",
                                'source': 'gis',
                                'field': 'חלקה',
                                'value': str(parcel),
                                'type': 'land_use'
                            })
                        
                        # Add all GIS rows that match the query
                        for row in gis_rows:
                            if not query or query in row['field'].lower() or query in row['value'].lower():
                                rights_data['gis_rights'].append(row)

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

            # 4. Get detailed privilege page data
            privilege_data = asset.get_property_value('privilege_page_data')
            if privilege_data:
                detailed_rights = self._process_privilege_page_data(privilege_data)
                rights_data['detailed_rights'] = detailed_rights

            # 5. Parse ownership information from Tabu data
            ownership_info = self._parse_ownership_from_tabu(rights_data['tabu_data'])
            rights_data['ownership_summary'] = ownership_info

            # 6. Calculate total rows
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
            
            # Look for ownership percentage - handle fractions like "1/2"
            elif '%' in value or 'אחוז' in field or '/' in value:
                try:
                    import re
                    # Handle fractions like "1/2" = 50%
                    if '/' in value:
                        fraction_match = re.search(r'(\d+)/(\d+)', value)
                        if fraction_match:
                            numerator = float(fraction_match.group(1))
                            denominator = float(fraction_match.group(2))
                            ownership_percentage = (numerator / denominator) * 100
                    else:
                        # Handle regular percentages
                        percentage_match = re.search(r'(\d+(?:\.\d+)?)', value)
                        if percentage_match:
                            ownership_percentage = float(percentage_match.group(1))
                except (ValueError, AttributeError, ZeroDivisionError):
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

    def _process_privilege_page_data(self, privilege_data):
        """Process privilege page data into detailed building rights format."""
        detailed_rights = {
            'source': 'privilege_page',
            'rights_details': [],
            'building_lines': [],
            'floor_details': [],
            'percentages': {},
            'areas': {},
            'notes': []
        }
        
        if not isinstance(privilege_data, dict):
            return detailed_rights
            
        rights = privilege_data.get('rights', {})
        basic = privilege_data.get('basic', {})
        
        # Extract building lines
        building_lines = rights.get('building_lines', [])
        for line in building_lines:
            detailed_rights['building_lines'].append({
                'type': 'building_line',
                'description': line,
                'source': 'privilege_page'
            })
        
        # Extract floor details
        floor_details = rights.get('floor_details', [])
        for floor in floor_details:
            detailed_rights['floor_details'].append({
                'type': floor.get('type', ''),
                'percentage': floor.get('percentage', 0),
                'area_sqm': floor.get('area_sqm', 0),
                'source': 'privilege_page'
            })
        
        # Extract percentages
        if rights.get('percent_building'):
            detailed_rights['percentages']['building_percentage'] = rights['percent_building']
        
        # Extract areas
        areas = rights.get('areas', [])
        for area in areas:
            detailed_rights['areas'][f'area_{len(detailed_rights["areas"])}'] = area
        
        # Extract specific building rights
        specific_rights = rights.get('specific_building_rights', [])
        for right in specific_rights:
            detailed_rights['rights_details'].append({
                'type': 'specific_right',
                'description': right,
                'source': 'privilege_page'
            })
        
        # Extract notes
        notes = rights.get('notes', [])
        for note in notes:
            if isinstance(note, dict):
                detailed_rights['notes'].append({
                    'text': note.get('text', ''),
                    'type': note.get('type', 'general'),
                    'source': 'privilege_page'
                })
            else:
                detailed_rights['notes'].append({
                    'text': str(note),
                    'type': 'general',
                    'source': 'privilege_page'
                })
        
        # Extract basic information
        if basic.get('parcel_area_sqm'):
            detailed_rights['areas']['parcel_area_sqm'] = basic['parcel_area_sqm']
        
        return detailed_rights


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


class DocumentDownloadView(APIView):
    """Handle document downloads."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, asset_id, document_id):
        """Download a document file."""
        try:
            # Get document
            document = get_object_or_404(Document, id=document_id, asset_id=asset_id)
            
            # Check permissions
            if not (document.asset.created_by == request.user or request.user.is_staff):
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            # Check if file exists
            logger.info(f"Document {document_id} file_path: {document.file_path}")
            logger.info(f"Document {document_id} is_downloadable: {document.is_downloadable}")
            logger.info(f"Document {document_id} default_storage.exists: {default_storage.exists(document.file_path)}")
            
            if not document.is_downloadable:
                return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Stream file content through API
            from django.http import StreamingHttpResponse
            from django.core.files.storage import default_storage
            
            try:
                
                def file_generator():
                    with default_storage.open(document.file_path, 'rb') as file:
                        while True:
                            chunk = file.read(8192)  # 8KB chunks
                            if not chunk:
                                break
                            yield chunk
                
                response = StreamingHttpResponse(
                    file_generator(),
                    content_type=document.mime_type
                )
                response['Content-Disposition'] = f'attachment; filename="{document.filename}"'
                response['Content-Length'] = document.file_size
                return response
            except Exception as e:
                logger.error(f"Error reading file {document.file_path}: {e}")
                return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            return Response({'error': 'Download failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
