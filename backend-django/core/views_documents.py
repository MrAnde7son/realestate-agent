import logging
from django.shortcuts import get_object_or_404
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

            # 2. Get comprehensive GIS data from asset metadata (stored directly in meta)
            gis_data = asset.meta.get('gis_data', {}) if asset.meta else {}
            logger.info(f"Asset {asset_id}: GIS data from meta: {list(gis_data.keys()) if gis_data else 'empty'}")
            
            # Also get the comprehensive GIS collector data (stored directly in meta)
            gis_collector_data = asset.meta.get('gis_collector_data', {}) if asset.meta else {}
            if gis_collector_data:
                # Merge GIS collector data into gis_data for comprehensive processing
                gis_data['gis_collector_data'] = gis_collector_data
                logger.info(f"Asset {asset_id}: Found GIS collector data with {len(gis_collector_data)} keys: {list(gis_collector_data.keys())}")
            else:
                logger.info(f"Asset {asset_id}: No GIS collector data found in metadata. Available meta keys: {list(asset.meta.keys()) if asset.meta else 'no meta'}")
            
            # Process land use rights data
            gis_rights = gis_data.get('rights', [])
            if gis_rights:
                for idx, right in enumerate(gis_rights):
                    if isinstance(right, dict):
                        # Extract meaningful data from raw GIS data
                        land_use = right.get('t_yeud_karka', '')
                        main_purpose = right.get('t_yeud_rashi', '')
                        area = right.get('ms_shetach', '')
                        block = right.get('ms_gush', '')
                        parcel = right.get('ms_migrash', '')
                        
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
            
            # Process additional GIS data sources
            self._process_gis_data_sources(gis_data, rights_data, query)

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
            privilege_data_list = asset.get_property_value('privilege_page_data')
            if privilege_data_list:
                # Handle both old single dict format and new list format
                if isinstance(privilege_data_list, list):
                    # New list format - process all privilege page data
                    detailed_rights_list = []
                    for idx, privilege_data in enumerate(privilege_data_list):
                        if privilege_data:
                            detailed_rights = self._process_privilege_page_data(privilege_data)
                            detailed_rights['page_index'] = idx
                            detailed_rights_list.append(detailed_rights)
                    rights_data['detailed_rights'] = detailed_rights_list
                elif isinstance(privilege_data_list, dict):
                    # Old single dict format - maintain backward compatibility
                    detailed_rights = self._process_privilege_page_data(privilege_data_list)
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


    def _process_gis_data_sources(self, gis_data, rights_data, query):
        """Process comprehensive GIS collector data sources into rights data format."""
        
        # Process blocks data
        blocks = gis_data.get('blocks', [])
        for idx, block in enumerate(blocks):
            if isinstance(block, dict):
                block_number = block.get('ms_gush', '')
                block_area = block.get('ms_shetach', '')
                block_status = block.get('t_status_hesder', '')
                block_total_parcels = block.get('ms_mispar_chelkot', '')
                
                if block_number:
                    rights_data['gis_rights'].append({
                        'id': f"gis_blocks_{idx}_number",
                        'source': 'gis_blocks',
                        'field': 'מספר גוש',
                        'value': str(block_number),
                        'type': 'cadastral'
                    })
                if block_area:
                    rights_data['gis_rights'].append({
                        'id': f"gis_blocks_{idx}_area",
                        'source': 'gis_blocks',
                        'field': 'שטח גוש (מ״ר)',
                        'value': str(block_area),
                        'type': 'cadastral'
                    })
                if block_status:
                    rights_data['gis_rights'].append({
                        'id': f"gis_blocks_{idx}_status",
                        'source': 'gis_blocks',
                        'field': 'סטטוס גוש',
                        'value': str(block_status),
                        'type': 'cadastral'
                    })
                if block_total_parcels:
                    rights_data['gis_rights'].append({
                        'id': f"gis_blocks_{idx}_total_parcels",
                        'source': 'gis_blocks',
                        'field': 'מספר חלקות בגוש',
                        'value': str(block_total_parcels),
                        'type': 'cadastral'
                    })
        
        # Process parcels data
        parcels = gis_data.get('parcels', [])
        for idx, parcel in enumerate(parcels):
            if isinstance(parcel, dict):
                parcel_number = parcel.get('ms_chelka', '')
                parcel_area = parcel.get('ms_shetach', '')
                parcel_registered_area = parcel.get('ms_shetach_rashum', '')
                parcel_status = parcel.get('t_status_hesder', '')
                parcel_accuracy = parcel.get('k_dargat_diyuk', '')
                
                if parcel_number:
                    rights_data['gis_rights'].append({
                        'id': f"gis_parcels_{idx}_number",
                        'source': 'gis_parcels',
                        'field': 'מספר חלקה',
                        'value': str(parcel_number),
                        'type': 'cadastral'
                    })
                if parcel_area:
                    rights_data['gis_rights'].append({
                        'id': f"gis_parcels_{idx}_area",
                        'source': 'gis_parcels',
                        'field': 'שטח חלקה (מ״ר)',
                        'value': str(parcel_area),
                        'type': 'cadastral'
                    })
                if parcel_registered_area:
                    rights_data['gis_rights'].append({
                        'id': f"gis_parcels_{idx}_registered_area",
                        'source': 'gis_parcels',
                        'field': 'שטח חלקה רשום (מ״ר)',
                        'value': str(parcel_registered_area),
                        'type': 'cadastral'
                    })
                if parcel_status:
                    rights_data['gis_rights'].append({
                        'id': f"gis_parcels_{idx}_status",
                        'source': 'gis_parcels',
                        'field': 'סטטוס חלקה',
                        'value': str(parcel_status),
                        'type': 'cadastral'
                    })
                if parcel_accuracy:
                    rights_data['gis_rights'].append({
                        'id': f"gis_parcels_{idx}_accuracy",
                        'source': 'gis_parcels',
                        'field': 'דרגת דיוק חלקה',
                        'value': str(parcel_accuracy),
                        'type': 'cadastral'
                    })
        
        # Process comprehensive building permits data
        permits = gis_data.get('permits', [])
        for idx, permit in enumerate(permits):
            if isinstance(permit, dict):
                # Basic permit info
                permit_number = permit.get('permit_number', '')
                request_num = permit.get('request_num', '')
                permission_num = permit.get('permission_num', '')
                building_num = permit.get('building_num', '')
                permit_type = permit.get('permit_type', '')
                permit_date = permit.get('permit_date', '')
                
                # Permit areas and units
                housing_units = permit.get('yechidot_diyur', '')
                commercial_area = permit.get('mischar_shetach', '')
                residential_area = permit.get('megurim_shetach', '')
                residential_units = permit.get('megurim_yechidot', '')
                public_area = permit.get('mivney_tzibur_shetach', '')
                parking_area = permit.get('melonaut_shetach', '')
                parking_units = permit.get('melonaut_yechidot', '')
                total_area = permit.get('sach_shetach', '')
                
                # Permit flags and special features
                small_apartments = permit.get('dirot_ktanot', '')
                unified_housing_area = permit.get('diyur_meuchad_shetach', '')
                unified_housing_units = permit.get('diyur_meuchad_yechidot', '')
                accessible_apartments = permit.get('dirot_haskara', '')
                public_built_area = permit.get('tziburi_banuy_shetach', '')
                mavat_plan_num = permit.get('mispar_tochnit_mavat', '')
                parking_rooms_calculated = permit.get('melonaut_rooms_mechushav', '')
                full_utilization = permit.get('sw_mimush_male', '')
                subject_type = permit.get('sug_nose', '')
                process = permit.get('maslul', '')
                rights_notification = permit.get('sw_niyud_zchuyot', '')
                repartition = permit.get('sw_repartzelatzya', '')
                urban_renewal = permit.get('sw_hitchadshut_ironit', '')
                
                # Add all permit fields to rights data
                permit_fields = [
                    ('מספר היתר', permit_number),
                    ('מספר בקשה', request_num),
                    ('מספר אישור', permission_num),
                    ('מספר בניין', building_num),
                    ('סוג היתר', permit_type),
                    ('תאריך היתר', permit_date),
                    ('יחידות דיור', housing_units),
                    ('שטח מסחרי (מ״ר)', commercial_area),
                    ('שטח מגורים (מ״ר)', residential_area),
                    ('יחידות מגורים', residential_units),
                    ('שטח ציבורי (מ״ר)', public_area),
                    ('שטח חניה (מ״ר)', parking_area),
                    ('יחידות חניה', parking_units),
                    ('שטח כולל (מ״ר)', total_area),
                    ('דירות קטנות', small_apartments),
                    ('שטח דיור מאוחד (מ״ר)', unified_housing_area),
                    ('יחידות דיור מאוחד', unified_housing_units),
                    ('דירות נגישות', accessible_apartments),
                    ('שטח ציבורי בנוי (מ״ר)', public_built_area),
                    ('מספר תוכנית מבאו', mavat_plan_num),
                    ('חדרי חניה מחושבים', parking_rooms_calculated),
                    ('ניצול מלא', 'כן' if full_utilization else 'לא' if full_utilization is not None else ''),
                    ('סוג נושא', subject_type),
                    ('מסלול', process),
                    ('הודעה על זכויות', 'כן' if rights_notification else 'לא' if rights_notification is not None else ''),
                    ('חלוקה מחדש', 'כן' if repartition else 'לא' if repartition is not None else ''),
                    ('חידוש עירוני', 'כן' if urban_renewal else 'לא' if urban_renewal is not None else ''),
                ]
                
                for field_name, field_value in permit_fields:
                    if field_value and str(field_value).strip():
                        rights_data['gis_rights'].append({
                            'id': f"gis_permits_{idx}_{field_name.replace(' ', '_').replace('(', '').replace(')', '')}",
                            'source': 'gis_permits',
                            'field': field_name,
                            'value': str(field_value),
                            'type': 'permits'
                        })
        
        # Process detailed land use data
        land_use_detailed = gis_data.get('land_use_detailed', [])
        for idx, land_use in enumerate(land_use_detailed):
            if isinstance(land_use, dict):
                land_use_type = land_use.get('land_use_type', '')
                land_use_area = land_use.get('area', '')
                if land_use_type:
                    rights_data['gis_rights'].append({
                        'id': f"gis_land_use_detailed_{idx}_type",
                        'source': 'gis_land_use_detailed',
                        'field': 'סוג שימוש מפורט',
                        'value': str(land_use_type),
                        'type': 'land_use_detailed'
                    })
                if land_use_area:
                    rights_data['gis_rights'].append({
                        'id': f"gis_land_use_detailed_{idx}_area",
                        'source': 'gis_land_use_detailed',
                        'field': 'שטח שימוש מפורט (מ״ר)',
                        'value': str(land_use_area),
                        'type': 'land_use_detailed'
                    })
        
        # Process shelters data
        shelters = gis_data.get('shelters', [])
        for idx, shelter in enumerate(shelters):
            if isinstance(shelter, dict):
                shelter_type = shelter.get('shelter_type', '')
                shelter_capacity = shelter.get('capacity', '')
                if shelter_type:
                    rights_data['gis_rights'].append({
                        'id': f"gis_shelters_{idx}_type",
                        'source': 'gis_shelters',
                        'field': 'סוג מחסה',
                        'value': str(shelter_type),
                        'type': 'shelters'
                    })
                if shelter_capacity:
                    rights_data['gis_rights'].append({
                        'id': f"gis_shelters_{idx}_capacity",
                        'source': 'gis_shelters',
                        'field': 'קיבולת מחסה',
                        'value': str(shelter_capacity),
                        'type': 'shelters'
                    })
        
        # Process green areas data
        green_areas = gis_data.get('green', [])
        for idx, green in enumerate(green_areas):
            if isinstance(green, dict):
                green_type = green.get('green_type', '')
                green_area = green.get('area', '')
                if green_type:
                    rights_data['gis_rights'].append({
                        'id': f"gis_green_{idx}_type",
                        'source': 'gis_green',
                        'field': 'סוג שטח ירוק',
                        'value': str(green_type),
                        'type': 'green_areas'
                    })
                if green_area:
                    rights_data['gis_rights'].append({
                        'id': f"gis_green_{idx}_area",
                        'source': 'gis_green',
                        'field': 'שטח ירוק (מ״ר)',
                        'value': str(green_area),
                        'type': 'green_areas'
                    })
        
        # Process noise levels data
        noise_levels = gis_data.get('noise', [])
        for idx, noise in enumerate(noise_levels):
            if isinstance(noise, dict):
                noise_level = noise.get('noise_level', '')
                noise_source = noise.get('noise_source', '')
                if noise_level:
                    rights_data['gis_rights'].append({
                        'id': f"gis_noise_{idx}_level",
                        'source': 'gis_noise',
                        'field': 'רמת רעש (dB)',
                        'value': str(noise_level),
                        'type': 'noise'
                    })
                if noise_source:
                    rights_data['gis_rights'].append({
                        'id': f"gis_noise_{idx}_source",
                        'source': 'gis_noise',
                        'field': 'מקור רעש',
                        'value': str(noise_source),
                        'type': 'noise'
                    })
        
        # Process cell antennas data
        antennas = gis_data.get('antennas', [])
        for idx, antenna in enumerate(antennas):
            if isinstance(antenna, dict):
                antenna_type = antenna.get('antenna_type', '')
                antenna_status = antenna.get('status', '')
                if antenna_type:
                    rights_data['gis_rights'].append({
                        'id': f"gis_antennas_{idx}_type",
                        'source': 'gis_antennas',
                        'field': 'סוג אנטנה',
                        'value': str(antenna_type),
                        'type': 'antennas'
                    })
                if antenna_status:
                    rights_data['gis_rights'].append({
                        'id': f"gis_antennas_{idx}_status",
                        'source': 'gis_antennas',
                        'field': 'סטטוס אנטנה',
                        'value': str(antenna_status),
                        'type': 'antennas'
                    })
        
        # Process preservation data
        preservation = gis_data.get('preservation', [])
        for idx, preserve in enumerate(preservation):
            if isinstance(preserve, dict):
                preserve_type = preserve.get('preservation_type', '')
                preserve_status = preserve.get('status', '')
                if preserve_type:
                    rights_data['gis_rights'].append({
                        'id': f"gis_preservation_{idx}_type",
                        'source': 'gis_preservation',
                        'field': 'סוג שימור',
                        'value': str(preserve_type),
                        'type': 'preservation'
                    })
                if preserve_status:
                    rights_data['gis_rights'].append({
                        'id': f"gis_preservation_{idx}_status",
                        'source': 'gis_preservation',
                        'field': 'סטטוס שימור',
                        'value': str(preserve_status),
                        'type': 'preservation'
                    })
        
        # Process dangerous buildings data
        dangerous = gis_data.get('dangerous', [])
        for idx, danger in enumerate(dangerous):
            if isinstance(danger, dict):
                danger_type = danger.get('danger_type', '')
                danger_level = danger.get('danger_level', '')
                if danger_type:
                    rights_data['gis_rights'].append({
                        'id': f"gis_dangerous_{idx}_type",
                        'source': 'gis_dangerous',
                        'field': 'סוג סכנה',
                        'value': str(danger_type),
                        'type': 'dangerous'
                    })
                if danger_level:
                    rights_data['gis_rights'].append({
                        'id': f"gis_dangerous_{idx}_level",
                        'source': 'gis_dangerous',
                        'field': 'רמת סכנה',
                        'value': str(danger_level),
                        'type': 'dangerous'
                    })
        
        # Process local plans data
        local_plans = gis_data.get('local_plans', [])
        for idx, plan in enumerate(local_plans):
            if isinstance(plan, dict):
                plan_number = plan.get('plan_number', '')
                plan_name = plan.get('plan_name', '')
                plan_status = plan.get('status', '')
                if plan_number:
                    rights_data['gis_rights'].append({
                        'id': f"gis_local_plans_{idx}_number",
                        'source': 'gis_local_plans',
                        'field': 'מספר תכנית מקומית',
                        'value': str(plan_number),
                        'type': 'plans'
                    })
                if plan_name:
                    rights_data['gis_rights'].append({
                        'id': f"gis_local_plans_{idx}_name",
                        'source': 'gis_local_plans',
                        'field': 'שם תכנית מקומית',
                        'value': str(plan_name),
                        'type': 'plans'
                    })
                if plan_status:
                    rights_data['gis_rights'].append({
                        'id': f"gis_local_plans_{idx}_status",
                        'source': 'gis_local_plans',
                        'field': 'סטטוס תכנית מקומית',
                        'value': str(plan_status),
                        'type': 'plans'
                    })
        
        # Process city plans data
        city_plans = gis_data.get('city_plans', [])
        for idx, plan in enumerate(city_plans):
            if isinstance(plan, dict):
                plan_number = plan.get('plan_number', '')
                plan_name = plan.get('plan_name', '')
                plan_status = plan.get('status', '')
                if plan_number:
                    rights_data['gis_rights'].append({
                        'id': f"gis_city_plans_{idx}_number",
                        'source': 'gis_city_plans',
                        'field': 'מספר תכנית עירונית',
                        'value': str(plan_number),
                        'type': 'plans'
                    })
                if plan_name:
                    rights_data['gis_rights'].append({
                        'id': f"gis_city_plans_{idx}_name",
                        'source': 'gis_city_plans',
                        'field': 'שם תכנית עירונית',
                        'value': str(plan_name),
                        'type': 'plans'
                    })
                if plan_status:
                    rights_data['gis_rights'].append({
                        'id': f"gis_city_plans_{idx}_status",
                        'source': 'gis_city_plans',
                        'field': 'סטטוס תכנית עירונית',
                        'value': str(plan_status),
                        'type': 'plans'
                    })
        
        # Filter all GIS data by query if provided
        if query:
            rights_data['gis_rights'] = [
                row for row in rights_data['gis_rights']
                if query in row['field'].lower() or query in row['value'].lower()
            ]


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
