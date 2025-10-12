import logging
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.utils import timezone
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
    from utils.parse_tabu import TabuParser
except Exception:  # pragma: no cover - fallback when parser is unavailable
    TabuParser = None

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
            if document.document_type == 'tabu' and TabuParser:
                try:
                    with default_storage.open(file_info['file_path'], 'rb') as stored_file:
                        parser = TabuParser(stored_file)
                        rows = parser.parse() or []
                    if rows:
                        document.meta = {**(document.meta or {}), 'tabu_rows': rows}
                        document.save(update_fields=['meta'])
                        
                        # Update asset ownership fields from Tabu data
                        _update_asset_from_tabu(asset, rows)
                        
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
                'building_rights': {},
                'ownership_summary': {},
                'total_rows': 0
            }

            # 1. Get Tabu data from uploaded documents (use most recent document only to avoid duplicates)
            documents = asset.documents.filter(document_type='tabu').order_by('-uploaded_at')
            if documents.exists():
                # Use only the most recent Tabu document to avoid duplicates
                document = documents.first()
                doc_rows = document.meta.get('tabu_rows') if document.meta else []
                if isinstance(doc_rows, list):
                    # Deduplicate rows by field+value combination
                    seen_rows = set()
                    for idx, row in enumerate(doc_rows):
                        field = str(row.get('field', '') or '')
                        value = str(row.get('value', '') or '')
                        
                        # Create a unique key for deduplication
                        row_key = f"{field}:{value}"
                        if row_key not in seen_rows:
                            seen_rows.add(row_key)
                            
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
            
            # Process land use rights data - DISABLED (legacy data)
            # All GIS data processing has been removed as it's redundant with other tabs
            
            # Process additional GIS data sources - DISABLED (legacy data)
            # self._process_gis_data_sources(gis_data, rights_data, query)

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

            # 4. Calculate building rights and privileges
            try:
                calculated_rights = self._calculate_building_rights(asset)
                rights_data['calculated_rights'] = calculated_rights
            except Exception as e:
                logger.error(f"Error calculating building rights for asset {asset.id}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                rights_data['calculated_rights'] = {
                    'error': f'Failed to calculate building rights: {str(e)}',
                    'source': 'error'
                }

            # 5. Get detailed privilege page data
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
            # Calculate total rows
            rights_data['total_rows'] = len(rights_data['tabu_data'])

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
        
        # Debug: log the tabu data structure
        logger.debug(f"Tabu data for parsing: {tabu_data}")
        
        # First pass: collect all ownership-related data
        ownership_shares = []
        owner_names = []
        
        for row in tabu_data:
            field = row.get('field', '').lower()
            value = row.get('value', '')
            
            # Collect ownership shares - only from the specific field
            if 'החלק בנכס' in field:
                ownership_shares.append(value)
                logger.debug(f"Found ownership share: {field} = {value}")
            
            # Collect owner names
            elif 'בעלים' in field or 'owner' in field:
                owner_names.append(value)
                logger.debug(f"Found owner: {field} = {value}")
            
            # Collect parcel information
            elif 'גוש' in field:
                ownership['parcel_info']['block'] = value
            elif 'חלקה' in field:
                ownership['parcel_info']['parcel'] = value
            elif 'תת חלקה' in field:
                ownership['parcel_info']['subparcel'] = value
            
            # Collect area information with clearer naming
            elif 'שטח כולל' in field or 'total area' in field:
                ownership['parcel_info']['total_area'] = value
            elif 'שטח נטו' in field or 'net area' in field:
                ownership['parcel_info']['subparcel_area'] = value  # Clearer than 'net_area'
            elif 'שטח בנוי' in field or 'built area' in field:
                ownership['parcel_info']['built_area'] = value
            elif 'שטח' in field and 'כולל' not in field and 'נטו' not in field and 'בנוי' not in field:
                # Generic area field
                ownership['parcel_info']['area'] = value
        
        logger.debug(f"Collected ownership shares: {ownership_shares}")
        logger.debug(f"Collected owner names: {owner_names}")
        
        # Second pass: match owners with their shares
        for i, owner_name in enumerate(owner_names):
            # Try to find corresponding ownership share
            ownership_percentage = 0
            
            # If we have a corresponding share
            if i < len(ownership_shares):
                share_value = ownership_shares[i]
                try:
                    import re
                    # Handle fractions like "1/2" = 50%
                    if '/' in share_value:
                        fraction_match = re.search(r'(\d+)/(\d+)', share_value)
                        if fraction_match:
                            numerator = float(fraction_match.group(1))
                            denominator = float(fraction_match.group(2))
                            ownership_percentage = (numerator / denominator) * 100
                            logger.debug(f"Parsed fraction {share_value} as {ownership_percentage}%")
                    # Handle "בשלמות" (full ownership) = 100%
                    elif 'בשלמות' in share_value:
                        ownership_percentage = 100.0
                        logger.debug(f"Parsed full ownership as 100%")
                    else:
                        # Handle regular percentages
                        percentage_match = re.search(r'(\d+(?:\.\d+)?)', share_value)
                        if percentage_match:
                            ownership_percentage = float(percentage_match.group(1))
                            logger.debug(f"Parsed percentage {share_value} as {ownership_percentage}%")
                except (ValueError, AttributeError, ZeroDivisionError):
                    logger.debug(f"Failed to parse ownership share: {share_value}")
                    pass
            
            # Add owner with their percentage
            if ownership_percentage > 0:
                ownership['owners'].append({
                    'name': owner_name,
                    'percentage': ownership_percentage
                })
                logger.debug(f"Added owner: {owner_name} with {ownership_percentage}%")
        
        # Calculate total ownership percentage
        ownership['total_ownership_percentage'] = sum(owner['percentage'] for owner in ownership['owners'])
        
        logger.debug(f"Final ownership data: {ownership}")
        return ownership

    def _calculate_building_rights(self, asset):
        """Calculate comprehensive building rights and privileges from all available data sources."""
        calculated_rights = {
            'source': 'calculated',
            'parcel_info': {},
            'building_privileges': {},
            'current_usage': {},
            'remaining_rights': {},
            'privilege_page_details': {},
            'summary': {}
        }
        
        # Get basic parcel information
        meta = asset.meta or {}
        
        # Parcel area information
        parcel_area = meta.get('parcelArea', {}).get('value') if isinstance(meta.get('parcelArea'), dict) else meta.get('parcelArea')
        parcel_registered_area = meta.get('parcelRegisteredArea', {}).get('value') if isinstance(meta.get('parcelRegisteredArea'), dict) else meta.get('parcelRegisteredArea')
        
        calculated_rights['parcel_info'] = {
            'parcel_area_sqm': parcel_area,
            'parcel_registered_area_sqm': parcel_registered_area,
            'area_source': meta.get('parcelArea', {}).get('source', 'GIS') if isinstance(meta.get('parcelArea'), dict) else 'GIS'
        }
        
        # Get privilege page data for detailed calculations
        privilege_data_list = meta.get('privilege_page_data')
        logger.debug(f"Privilege data type: {type(privilege_data_list)}")
        if privilege_data_list:
            # Use the privilege page data directly
            privilege_data = privilege_data_list
            logger.debug(f"Privilege data keys: {list(privilege_data.keys()) if isinstance(privilege_data, dict) else 'Not a dict'}")
            
            if isinstance(privilege_data, dict) and ('rights' in privilege_data or 'rights_details' in privilege_data):
                rights = privilege_data.get('rights') or privilege_data.get('rights_details', {})
                logger.debug(f"Rights type: {type(rights)}, keys: {list(rights.keys()) if isinstance(rights, dict) else 'Not a dict'}")
                
                # Extract building privileges from privilege page
                min_values = rights.get('minimum_values', [])
                max_values = rights.get('maximum_values', [])
                floor_percentages = rights.get('floor_percentages_detailed', [])
                building_lines = rights.get('building_lines_detailed', [])
                auxiliary_area = rights.get('auxiliary_building_area', 0)
                parking_req = rights.get('parking_requirements', [])
                
                # Calculate total building privilege (use maximum values as they represent allowed building)
                total_building_privilege = 0
                if max_values:
                    # Sum up all maximum values for total building rights
                    total_building_privilege = sum([float(mv.get('value', 0)) for mv in max_values if mv.get('value')])
                
                # Calculate floor-specific privileges
                floor_privileges = {}
                
                # First pass: Calculate absolute floor areas (percentages of total building privilege)
                absolute_floors = {}
                for fp in floor_percentages:
                    floor_type = fp.get('floor', fp.get('type', ''))
                    percentage = float(fp.get('percentage', 0))
                    if floor_type and percentage > 0:
                        # Check if this is a standard/typical floor (usually the base for relative calculations)
                        is_standard_floor = floor_type in ['טיפוסית', 'ראשונה'] or 'טיפוסית' in fp.get('raw_text', '')
                        
                        floor_area = (total_building_privilege * percentage / 100) if total_building_privilege > 0 else 0
                        absolute_floors[floor_type] = {
                            'percentage': percentage,
                            'area_sqm': floor_area,
                            'raw_text': fp.get('raw_text', ''),
                            'is_standard': is_standard_floor
                        }
                
                # Second pass: Calculate relative floors (percentages of base floors)
                for fp in floor_percentages:
                    floor_type = fp.get('floor', fp.get('type', ''))
                    percentage = float(fp.get('percentage', 0))
                    raw_text = fp.get('raw_text', '')
                    
                    if floor_type and percentage > 0:
                        # Check if this floor is relative to another floor (e.g., "75% מקומה טיפוסית")
                        is_relative = False
                        base_floor_type = None
                        
                        # Look for patterns like "75% מקומה טיפוסית" or "75% of standard floor"
                        if 'מקומה' in raw_text or 'of' in raw_text.lower():
                            is_relative = True
                            # Try to identify the base floor from the raw text
                            if 'טיפוסית' in raw_text:
                                base_floor_type = 'טיפוסית'
                            elif 'ראשונה' in raw_text:
                                base_floor_type = 'ראשונה'
                            else:
                                # Default to the first standard floor found
                                for floor_name, floor_data in absolute_floors.items():
                                    if floor_data.get('is_standard', False):
                                        base_floor_type = floor_name
                                        break
                        
                        if is_relative and base_floor_type and base_floor_type in absolute_floors:
                            # Calculate as percentage of the base floor
                            base_area = absolute_floors[base_floor_type]['area_sqm']
                            floor_area = base_area * (percentage / 100)
                            floor_privileges[floor_type] = {
                                'percentage': percentage,
                                'area_sqm': floor_area,
                                'raw_text': raw_text,
                                'is_relative': True,
                                'base_floor': base_floor_type
                            }
                        else:
                            # Use absolute calculation
                            floor_privileges[floor_type] = absolute_floors[floor_type]
                
                # Calculate building line requirements
                building_line_requirements = []
                for bl in building_lines:
                    line_type = bl.get('line', bl.get('type', ''))
                    distance = float(bl.get('distance', bl.get('distance_meters', 0)))
                    if line_type and distance > 0:
                        building_line_requirements.append({
                            'type': line_type,
                            'distance_meters': distance,
                            'raw_text': bl.get('raw_text', '')
                        })
                
                # Calculate parking requirements
                parking_requirements = []
                if isinstance(parking_req, str):
                    # Handle string parking requirements
                    parking_requirements.append({
                        'area_sqm': 0,  # Can't extract numeric value from string
                        'raw_text': parking_req
                    })
                elif isinstance(parking_req, list):
                    for pr in parking_req:
                        if isinstance(pr, dict):
                            parking_value = pr.get('value', 0)
                            if parking_value > 0:
                                parking_requirements.append({
                                    'area_sqm': parking_value,
                                    'raw_text': pr.get('raw_text', '')
                                })
                        elif isinstance(pr, str):
                            parking_requirements.append({
                                'area_sqm': 0,
                                'raw_text': pr
                            })
                
                calculated_rights['building_privileges'] = {
                    'total_building_privilege_sqm': total_building_privilege,
                    'floor_privileges': floor_privileges,
                    'building_line_requirements': building_line_requirements,
                    'auxiliary_building_area_sqm': float(auxiliary_area) if auxiliary_area else 0,
                    'parking_requirements': parking_requirements,
                    'minimum_values': [float(mv.get('value', 0)) for mv in min_values],
                    'maximum_values': [float(mv.get('value', 0)) for mv in max_values]
                }
                
                calculated_rights['privilege_page_details'] = {
                    'source_file': privilege_data.get('source_file', ''),
                    'extracted_at': privilege_data.get('extracted_at', ''),
                    'basic_info': privilege_data.get('basic_info', privilege_data.get('basic', {})),
                    'alerts': privilege_data.get('alerts', []),
                    'plans_count': len(privilege_data.get('plans', {}).get('in_force', {}).get('local', [])) if privilege_data.get('plans') else 0
                }
        
        # Get current building usage from permits and other sources
        gis_data = meta.get('gis_data', {})
        permits = gis_data.get('permits', [])
        
        # Calculate current usage from permits
        total_current_area = 0
        total_housing_units = 0
        current_building_details = []
        
        for permit in permits:
            if isinstance(permit, dict):
                permit_num = permit.get('permit_number', '')
                building_num = permit.get('building_num', '')
                total_area = permit.get('sach_shetach', '')
                housing_units = permit.get('yechidot_diyur', '')
                residential_area = permit.get('megurim_shetach', '')
                commercial_area = permit.get('mischar_shetach', '')
                
                if total_area:
                    try:
                        total_current_area += float(total_area)
                    except:
                        pass
                
                if housing_units:
                    try:
                        total_housing_units += int(housing_units)
                    except:
                        pass
                
                if permit_num or building_num:
                    current_building_details.append({
                        'permit_number': permit_num,
                        'building_number': building_num,
                        'total_area_sqm': float(total_area) if total_area else 0,
                        'housing_units': int(housing_units) if housing_units else 0,
                        'residential_area_sqm': float(residential_area) if residential_area else 0,
                        'commercial_area_sqm': float(commercial_area) if commercial_area else 0
                    })
        
        # If no permits data or permits show 0 area, use asset's current area as current usage
        if total_current_area == 0 and asset.area:
            total_current_area = asset.area
        
        calculated_rights['current_usage'] = {
            'total_current_area_sqm': total_current_area,
            'total_housing_units': total_housing_units,
            'building_details': current_building_details,
            'usage_percentage': 0  # Will be calculated after building_privileges is set
        }
        
        # Calculate remaining rights
        total_privilege = calculated_rights.get('building_privileges', {}).get('total_building_privilege_sqm', 0)
        remaining_area = total_privilege - total_current_area
        remaining_percentage = (remaining_area / total_privilege * 100) if total_privilege > 0 else 0
        
        calculated_rights['remaining_rights'] = {
            'remaining_area_sqm': max(0, remaining_area),
            'remaining_percentage': max(0, remaining_percentage),
            'is_fully_utilized': remaining_area <= 0,
            'can_expand': remaining_area > 0
        }
        
        # Update usage percentage now that we have total_privilege
        calculated_rights['current_usage']['usage_percentage'] = (total_current_area / total_privilege * 100) if total_privilege > 0 else 0
        
        # Calculate additional rights percentage (אחוז זכויות נוספות)
        additional_rights_percentage = 0
        if asset.area and asset.area > 0 and remaining_area > 0:
            additional_rights_percentage = round((remaining_area / asset.area) * 100, 1)
        
        # Calculate estimated rights value (ערך משוער זכויות)
        estimated_rights_value = 0
        if asset.price_per_sqm and remaining_area > 0:
            # Use 0.7 factor as seen in the frontend calculation
            estimated_rights_value = round((asset.price_per_sqm * remaining_area * 0.7) / 1000)
        
        # Create summary
        calculated_rights['summary'] = {
            'parcel_area_sqm': parcel_area,
            'total_building_privilege_sqm': total_privilege,
            'current_usage_sqm': total_current_area,
            'remaining_rights_sqm': max(0, remaining_area),
            'additional_rights_percentage': additional_rights_percentage,
            'estimated_rights_value_k': estimated_rights_value,
            'utilization_percentage': calculated_rights['current_usage']['usage_percentage'],
            'status': 'Fully utilized' if remaining_area <= 0 else 'Can expand',
            'privilege_source': 'דף זכויות'
        }
        
        return calculated_rights

    def _process_privilege_page_data(self, privilege_data):
        """Process privilege page data into detailed building rights format."""
        detailed_rights = {
            'source': 'privilege_page',
            'rights_details': [],
            'building_lines': [],
            'floor_details': [],
            'percentages': {},
            'areas': {},
            'notes': [],
            'plans': [],
            'policy': [],
            'alerts': []
        }
        
        if not isinstance(privilege_data, dict):
            return detailed_rights
            
        rights = privilege_data.get('rights_details', privilege_data.get('rights', {}))
        basic = privilege_data.get('basic_info', privilege_data.get('basic', {}))
        plans = privilege_data.get('plans', {})
        policy = privilege_data.get('policy', [])
        alerts = privilege_data.get('alerts', [])
        
        # Extract basic information
        if basic.get('issue_date'):
            detailed_rights['rights_details'].append({
                'type': 'basic_info',
                'field': 'תאריך הפקה',
                'value': basic['issue_date'],
                'source': 'privilege_page'
            })
        
        if basic.get('address'):
            detailed_rights['rights_details'].append({
                'type': 'basic_info',
                'field': 'כתובת',
                'value': basic['address'],
                'source': 'privilege_page'
            })
        
        if basic.get('block'):
            detailed_rights['rights_details'].append({
                'type': 'basic_info',
                'field': 'גוש',
                'value': str(basic['block']),
                'source': 'privilege_page'
            })
        
        if basic.get('parcel'):
            detailed_rights['rights_details'].append({
                'type': 'basic_info',
                'field': 'חלקה',
                'value': str(basic['parcel']),
                'source': 'privilege_page'
            })
        
        if basic.get('parcel_area_sqm'):
            detailed_rights['areas']['parcel_area_sqm'] = basic['parcel_area_sqm']
            detailed_rights['rights_details'].append({
                'type': 'basic_info',
                'field': 'שטח חלקה (מ״ר)',
                'value': str(basic['parcel_area_sqm']),
                'source': 'privilege_page'
            })
        
        # Extract alerts
        for alert in alerts:
            detailed_rights['alerts'].append({
                'type': 'alert',
                'text': alert,
                'source': 'privilege_page'
            })
            detailed_rights['rights_details'].append({
                'type': 'alert',
                'field': 'התראה',
                'value': alert,
                'source': 'privilege_page'
            })
        
        # Extract plans data
        if plans:
            for category, plan_list in plans.items():
                if isinstance(plan_list, dict):
                    for subcategory, plans_in_category in plan_list.items():
                        for plan in plans_in_category:
                            plan_info = {
                                'type': 'plan',
                                'category': f"{category}_{subcategory}",
                                'plan_number': plan.get('plan_number', ''),
                                'name': plan.get('name', ''),
                                'deposit_date': plan.get('deposit_date', ''),
                                'effective_date': plan.get('effective_date', ''),
                                'urls': plan.get('urls', []),
                                'source': 'privilege_page'
                            }
                            detailed_rights['plans'].append(plan_info)
                            
                            # Add to rights_details for display
                            detailed_rights['rights_details'].append({
                                'type': 'plan',
                                'field': f'תכנית {plan.get("plan_number", "")}',
                                'value': plan.get('name', ''),
                                'plan_number': plan.get('plan_number', ''),
                                'effective_date': plan.get('effective_date', ''),
                                'urls': plan.get('urls', []),
                                'source': 'privilege_page'
                            })
        
        # Extract policy documents
        for policy_doc in policy:
            policy_info = {
                'type': 'policy',
                'policy_number': policy_doc.get('policy_number', ''),
                'name': policy_doc.get('name', ''),
                'date': policy_doc.get('date', ''),
                'source': 'privilege_page'
            }
            detailed_rights['policy'].append(policy_info)
            
            detailed_rights['rights_details'].append({
                'type': 'policy',
                'field': f'מדיניות {policy_doc.get("policy_number", "")}',
                'value': policy_doc.get('name', ''),
                'policy_number': policy_doc.get('policy_number', ''),
                'date': policy_doc.get('date', ''),
                'source': 'privilege_page'
            })
        
        # Extract building lines (both simple and detailed)
        building_lines = rights.get('building_lines', [])
        for line in building_lines:
            detailed_rights['building_lines'].append({
                'type': 'building_line',
                'description': line,
                'source': 'privilege_page'
            })
            detailed_rights['rights_details'].append({
                'type': 'building_line',
                'field': 'קו בניין',
                'value': line,
                'source': 'privilege_page'
            })
        
        # Extract detailed building lines
        building_lines_detailed = rights.get('building_lines_detailed', [])
        for line_detail in building_lines_detailed:
            detailed_rights['building_lines'].append({
                'type': 'building_line_detailed',
                'line_type': line_detail.get('type', ''),
                'distance_meters': line_detail.get('distance_meters', 0),
                'raw_text': line_detail.get('raw_text', ''),
                'source': 'privilege_page'
            })
            detailed_rights['rights_details'].append({
                'type': 'building_line_detailed',
                'field': f'קו בניין {line_detail.get("type", "")}',
                'value': f'{line_detail.get("distance_meters", 0)} מטרים',
                'raw_text': line_detail.get('raw_text', ''),
                'source': 'privilege_page'
            })
        
        # Extract floor percentages (detailed)
        floor_percentages_detailed = rights.get('floor_percentages_detailed', [])
        for floor_percent in floor_percentages_detailed:
            detailed_rights['floor_details'].append({
                'type': floor_percent.get('type', ''),
                'percentage': floor_percent.get('percentage', 0),
                'raw_text': floor_percent.get('raw_text', ''),
                'source': 'privilege_page'
            })
            detailed_rights['rights_details'].append({
                'type': 'floor_percentage',
                'field': f'אחוז קומה {floor_percent.get("type", "")}',
                'value': f'{floor_percent.get("percentage", 0)}%',
                'raw_text': floor_percent.get('raw_text', ''),
                'source': 'privilege_page'
            })
        
        # Extract minimum values
        minimum_values = rights.get('minimum_values', [])
        for min_val in minimum_values:
            detailed_rights['rights_details'].append({
                'type': 'minimum_value',
                'field': 'ערך מינימלי',
                'value': str(min_val.get('value', '')),
                'raw_text': min_val.get('raw_text', ''),
                'source': 'privilege_page'
            })
        
        # Extract maximum values
        maximum_values = rights.get('maximum_values', [])
        for max_val in maximum_values:
            detailed_rights['rights_details'].append({
                'type': 'maximum_value',
                'field': 'ערך מקסימלי',
                'value': str(max_val.get('value', '')),
                'raw_text': max_val.get('raw_text', ''),
                'source': 'privilege_page'
            })
        
        # Extract dwelling units
        if rights.get('dwelling_units'):
            detailed_rights['rights_details'].append({
                'type': 'dwelling_units',
                'field': 'יחידות דיור',
                'value': str(rights['dwelling_units']),
                'source': 'privilege_page'
            })
        
        # Extract number of floors
        if rights.get('number_of_floors'):
            detailed_rights['rights_details'].append({
                'type': 'floors',
                'field': 'מספר קומות',
                'value': str(rights['number_of_floors']),
                'source': 'privilege_page'
            })
        
        # Extract building coverage percentage
        if rights.get('building_coverage_percentage'):
            detailed_rights['percentages']['building_coverage'] = rights['building_coverage_percentage']
            detailed_rights['rights_details'].append({
                'type': 'coverage',
                'field': 'אחוז בנייה',
                'value': f"{rights['building_coverage_percentage']}%",
                'source': 'privilege_page'
            })
        
        # Extract parking requirements
        parking_requirements = rights.get('parking_requirements', [])
        for parking in parking_requirements:
            detailed_rights['rights_details'].append({
                'type': 'parking',
                'field': 'דרישות חניה',
                'value': str(parking.get('value', '')),
                'raw_text': parking.get('raw_text', ''),
                'source': 'privilege_page'
            })
        
        # Extract auxiliary building area
        if rights.get('auxiliary_building_area'):
            detailed_rights['rights_details'].append({
                'type': 'auxiliary_building',
                'field': 'שטח בניין עזר',
                'value': f"{rights['auxiliary_building_area']} מ״ר",
                'source': 'privilege_page'
            })
        
        # Extract referred plans
        referred_plans = rights.get('referred_plans', [])
        for plan_ref in referred_plans:
            detailed_rights['rights_details'].append({
                'type': 'referred_plan',
                'field': 'תכנית מופנית',
                'value': plan_ref,
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
                detailed_rights['rights_details'].append({
                    'type': 'note',
                    'field': 'הערה',
                    'value': note.get('text', ''),
                    'note_type': note.get('type', 'general'),
                    'source': 'privilege_page'
                })
            else:
                detailed_rights['notes'].append({
                    'text': str(note),
                    'type': 'general',
                    'source': 'privilege_page'
                })
                detailed_rights['rights_details'].append({
                    'type': 'note',
                    'field': 'הערה',
                    'value': str(note),
                    'note_type': 'general',
                    'source': 'privilege_page'
                })
        
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
        
        # Skip permits data - it's already shown in other tabs and not relevant for building rights
        
        # Skip detailed land use data - it's already shown in other tabs
        
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


def _update_asset_from_tabu(asset, tabu_rows):
    """Update asset ownership fields from parsed Tabu data."""
    try:
        ownership_data = AssetRightsView._parse_ownership_from_tabu(None, tabu_rows)
        
        # Update asset ownership fields if we found owner information
        if ownership_data.get('owners'):
            # Set the primary owner (first owner or owner with highest percentage)
            primary_owner = max(ownership_data['owners'], key=lambda x: x.get('percentage', 0))
            asset.owner_name = primary_owner['name']
            asset.ownership_percentage = primary_owner['percentage']
            
            # Store full ownership data in meta
            asset.meta = asset.meta or {}
            asset.meta['tabu_ownership'] = ownership_data
            
            # Update parcel information if available
            parcel_info = ownership_data.get('parcel_info', {})
            if parcel_info.get('block'):
                asset.block = parcel_info['block']
            if parcel_info.get('parcel'):
                asset.parcel = parcel_info['parcel']
            if parcel_info.get('subparcel'):
                asset.subparcel = parcel_info['subparcel']
        
        # Update area fields from Tabu data
        _update_asset_areas_from_tabu(asset, tabu_rows)
        
        asset.save()
        
        # Log ownership update if owners were found
        if ownership_data.get('owners'):
            primary_owner = max(ownership_data['owners'], key=lambda x: x.get('percentage', 0))
            logger.info(f"Updated asset {asset.id} ownership from Tabu: {primary_owner['name']} ({primary_owner['percentage']}%)")
        else:
            logger.info(f"Updated asset {asset.id} from Tabu data (no ownership info found)")
            
    except Exception as e:
        logger.error(f"Error updating asset {asset.id} from Tabu data: {e}")


def _update_asset_areas_from_tabu(asset, tabu_rows):
    """Update asset area fields from Tabu data."""
    try:
        update_fields = set()
        
        # Look for area information in Tabu data
        for row in tabu_rows:
            field = row.get('field', '').lower()
            value = row.get('value', '')
            
            # Extract numeric value from the field
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', value)
            if not numbers:
                continue
                
            area_value = float(numbers[0])
            
            # Map Tabu fields to asset fields with clearer naming
            if 'שטח כולל' in field or 'total area' in field:
                if not asset.total_area or asset.total_area != area_value:
                    asset.total_area = area_value
                    update_fields.add('total_area')
                    logger.debug(f'Updated total_area from Tabu: {area_value}')
                    
            elif 'שטח נטו' in field or 'net area' in field:
                # This represents the subparcel area (324 out of 653 total)
                if not asset.meta:
                    asset.meta = {}
                asset.meta['subparcel_area'] = {
                    'value': area_value,
                    'source': 'tabu',
                    'fetched_at': timezone.now().isoformat()
                }
                update_fields.add('meta')
                logger.debug(f'Updated subparcel_area in meta from Tabu: {area_value}')
                
                # Also update the generic area field for backward compatibility
                if not asset.area:
                    asset.area = area_value
                    update_fields.add('area')
                    logger.debug(f'Updated area field from Tabu subparcel: {area_value}')
                    
            elif 'שטח בנוי' in field or 'built area' in field:
                # Store built area in meta since there's no direct field
                if not asset.meta:
                    asset.meta = {}
                asset.meta['built_area'] = {
                    'value': area_value,
                    'source': 'tabu',
                    'fetched_at': timezone.now().isoformat()
                }
                update_fields.add('meta')
                logger.debug(f'Updated built_area in meta from Tabu: {area_value}')
                
            elif 'שטח' in field and 'כולל' not in field and 'נטו' not in field and 'בנוי' not in field:
                # Generic area field - use for total_area if not already set
                if not asset.total_area:
                    asset.total_area = area_value
                    update_fields.add('total_area')
                    logger.debug(f'Updated total_area from generic area field: {area_value}')
        
        if update_fields:
            logger.info(f"Updated asset {asset.id} area fields from Tabu: {list(update_fields)}")
            
    except Exception as e:
        logger.error(f"Error updating asset {asset.id} area fields from Tabu: {e}")


