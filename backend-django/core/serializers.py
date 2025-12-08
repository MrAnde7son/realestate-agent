from typing import Tuple, Optional
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Asset,
    Permit,
    Plan,
    SupportTicket,
    ConsultationRequest,
    AlertRule,
    AlertEvent,
    Snapshot,
    AssetContribution,
    UserProfile,
    PlanType,
    UserPlan,
    Document,
    RealEstateTransaction,
    Listing,
    AssetDocument,
    AssetTransaction,
    AssetPermit,
    AssetPlan,
    AssetListing,
)
from .services.asset_links import (
    asset_documents_all,
    asset_transactions_all,
    asset_permits_all,
    asset_plans_all,
)
from .utils.listings import normalize_listing_from_model

User = get_user_model()


class MetaSerializerMixin(serializers.ModelSerializer):
    """Adds _meta section with field lineage information for unified metadata structure."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        meta = getattr(instance, "meta", {}) or {}
        field_meta = {}

        # Allow callers to opt out of returning attribution metadata to reduce payload size
        include_meta = True
        if hasattr(self, "context") and isinstance(self.context, dict):
            include_meta = self.context.get("include_meta", True)
        
        # Process unified metadata structure
        for key, value in meta.items():
            if isinstance(value, dict) and "value" in value:
                # This is a unified metadata entry
                actual_value = value.get("value")
                # Only override model field if metadata value is not None and not empty string
                if actual_value is not None and actual_value != "":
                    data[key] = actual_value
                
                # Extract attribution information
                source = value.get("source")
                fetched = value.get("fetched_at")
                url = value.get("url")
                
                if source and fetched:
                    field_meta[key] = {
                        "source": source,
                        "fetched_at": fetched
                    }
                    if url:
                        field_meta[key]["url"] = url
            elif not isinstance(value, dict):
                # This is a simple value (backward compatibility)
                # Only override model field if metadata value is not None and not empty string
                if value is not None and value != "":
                    data[key] = value
        
        # Add _meta section if we have attribution data
        if include_meta and field_meta:
            data["_meta"] = field_meta

        return data


class AssetSerializer(MetaSerializerMixin):
    address = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    # Override to ensure fallback population from primary listing/area when DB fields are null
    price = serializers.SerializerMethodField()
    price_per_sqm = serializers.SerializerMethodField()
    # Expose market metric fields (snake_case) directly
    price_gap_pct = serializers.FloatField(read_only=True)
    expected_price_range = serializers.CharField(read_only=True)
    model_price = serializers.IntegerField(read_only=True)
    confidence_pct = serializers.FloatField(read_only=True)
    delta_vs_area_pct = serializers.FloatField(read_only=True)
    cap_rate_pct = serializers.FloatField(read_only=True)
    competition_1km = serializers.CharField(read_only=True)
    risk_flags = serializers.JSONField(read_only=True)
    dom_percentile = serializers.IntegerField(read_only=True)
    
    # Price per square meter metrics
    avg_price_per_sqm = serializers.FloatField(read_only=True)
    min_price_per_sqm = serializers.FloatField(read_only=True)
    max_price_per_sqm = serializers.FloatField(read_only=True)
    
    # CamelCase fields for frontend compatibility
    priceGapPct = serializers.FloatField(source='price_gap_pct', read_only=True)
    modelPrice = serializers.IntegerField(source='model_price', read_only=True)
    confidencePct = serializers.FloatField(source='confidence_pct', read_only=True)
    capRatePct = serializers.FloatField(source='cap_rate_pct', read_only=True)
    avgPricePerSqm = serializers.FloatField(source='avg_price_per_sqm', read_only=True)
    minPricePerSqm = serializers.FloatField(source='min_price_per_sqm', read_only=True)
    maxPricePerSqm = serializers.FloatField(source='max_price_per_sqm', read_only=True)
    rentPrice = serializers.SerializerMethodField()
    
    # Planning and Legal Analysis fields
    rightsUsagePct = serializers.FloatField(source='rights_usage_pct', read_only=True)
    legalRestrictions = serializers.CharField(source='legal_restrictions', read_only=True)
    urbanRenewalPotential = serializers.CharField(source='urban_renewal_potential', read_only=True)
    bettermentLevy = serializers.CharField(source='betterment_levy', read_only=True)
    
    # GIS Environment fields (from meta via get_property_value)
    openSpacesNearby = serializers.SerializerMethodField()
    publicBuildings = serializers.SerializerMethodField()
    parking = serializers.SerializerMethodField()
    nearbyProjects = serializers.SerializerMethodField()
    publicTransport = serializers.SerializerMethodField()
    greenScore = serializers.SerializerMethodField()
    investmentPotential = serializers.SerializerMethodField()
    investmentPotentialScore = serializers.SerializerMethodField()
    
    # New GIS data fields
    metroStationDistanceM = serializers.SerializerMethodField()
    metroStationsCount = serializers.SerializerMethodField()
    parkingLotsCount = serializers.SerializerMethodField()
    publicParkingLotsCount = serializers.SerializerMethodField()
    schoolsCount = serializers.SerializerMethodField()
    nearestSchoolDistanceM = serializers.SerializerMethodField()
    constructionSitesCount = serializers.SerializerMethodField()
    affordableHousingProjectsCount = serializers.SerializerMethodField()
    bikePathsCount = serializers.SerializerMethodField()
    hasBikePaths = serializers.SerializerMethodField()
    soilContaminationSitesCount = serializers.SerializerMethodField()
    nearestSoilContaminationDistanceM = serializers.SerializerMethodField()
    greenAmenitiesCount = serializers.SerializerMethodField()
    playgroundsCount = serializers.SerializerMethodField()
    medicalFacilitiesCount = serializers.SerializerMethodField()
    nearestMedicalFacilityDistanceM = serializers.SerializerMethodField()
    communityFacilitiesCount = serializers.SerializerMethodField()
    dogParksCount = serializers.SerializerMethodField()
    publicGardensCount = serializers.SerializerMethodField()
    medicalCentersCount = serializers.SerializerMethodField()
    healthFundsCount = serializers.SerializerMethodField()
    pharmaciesCount = serializers.SerializerMethodField()
    tama38KeyArea = serializers.SerializerMethodField()
    tama38KeyAreasCount = serializers.SerializerMethodField()
    roadWorksCount = serializers.SerializerMethodField()
    hasActiveRoadWorks = serializers.SerializerMethodField()

    is_commercial = serializers.BooleanField(read_only=True)
    isCommercial = serializers.BooleanField(source='is_commercial', read_only=True)
    isWatched = serializers.SerializerMethodField()
    
    # Enhanced Planning Metrics
    buildingCoveragePct = serializers.FloatField(source='building_coverage_pct', read_only=True)
    heightAnalysis = serializers.JSONField(source='height_analysis', read_only=True)
    setbackAnalysis = serializers.JSONField(source='setback_analysis', read_only=True)
    primary_listing = serializers.SerializerMethodField()
    listing_type = serializers.SerializerMethodField()
    ad_type = serializers.SerializerMethodField()
    contact_name = serializers.SerializerMethodField()
    contact_phone = serializers.SerializerMethodField()
    recent_deal = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        include_meta = self.context.get("include_meta", True)
        if not include_meta:
            # Remove the raw meta blob for lightweight responses
            self.fields.pop("meta", None)

    def get_rentPrice(self, obj):
        value = getattr(obj, "rent_price", None)
        if value not in (None, ""):
            return value
        # Read from meta to populate rent price even when include_meta is False
        # (include_meta only controls whether meta blob is included in response)
        meta = getattr(obj, "meta", {}) or {}
        listing_prices = meta.get("listing_prices")
        if isinstance(listing_prices, dict):
            rent_val = listing_prices.get("rent")
            if rent_val not in (None, ""):
                return rent_val
        return None

    def get_price(self, obj):
        """Return explicit asset price or fallback to primary listing price."""
        value = getattr(obj, "price", None)
        if value not in (None, ""):
            return value
        # Try reading from meta hint first
        # Note: include_meta flag only controls whether meta blob is included in response,
        # not whether we can read from it to populate derived fields
        meta = getattr(obj, "meta", {}) or {}
        listing_prices = meta.get("listing_prices")
        if isinstance(listing_prices, dict):
            listing_val = listing_prices.get("sale") or listing_prices.get("price")
            if listing_val not in (None, ""):
                return listing_val
        # Fallback to primary listing normalized data
        primary_price = self._get_primary_value(obj, "price", "price_value", "listing_price")
        return primary_price

    def get_price_per_sqm(self, obj):
        """Return explicit asset price_per_sqm or compute from price and area/size."""
        direct_value = getattr(obj, "price_per_sqm", None)
        if direct_value not in (None, ""):
            return direct_value
        # Try primary listing's direct ppm
        primary_ppm = self._get_primary_value(obj, "price_per_sqm", "pricePerSqm")
        if primary_ppm not in (None, ""):
            return primary_ppm
        # Compute from price and area if available
        # Prefer total_area over area (consistent with enrichment pipeline)
        price_val = self.get_price(obj)
        area_val = getattr(obj, "total_area", None)
        if area_val in (None, ""):
            area_val = getattr(obj, "area", None)
        if area_val in (None, ""):
            area_val = self._get_primary_value(obj, "size", "area", "square_meters", "squareMeters")
        try:
            if price_val not in (None, "") and area_val not in (None, "", 0):
                return int(round(float(price_val) / float(area_val)))
        except Exception:  # pragma: no cover - safety
            return None
        return None

    def get_address(self, obj):
        """Get formatted address for frontend compatibility."""
        if obj.normalized_address:
            return obj.normalized_address
        else:
            # Build address from components
            parts = []
            if obj.street:
                parts.append(obj.street)
            if obj.number:
                parts.append(str(obj.number))
            if obj.building_type and obj.floor:
                parts.append(f"{obj.building_type} {obj.floor}")
            if obj.apartment:
                parts.append(f"דירה {obj.apartment}")
            if obj.city:
                parts.append(obj.city)
            return " ".join(parts) if parts else None
    
    def get_type(self, obj):
        """Get property type from building_type or fallback to Yad2 listings."""
        # First try the direct building_type field
        if obj.building_type:
            return obj.building_type
        
        # Skip meta access if include_meta is False (optimization for list views)
        if not self.context.get("include_meta", True):
            return None
        
        # Fallback: try to get property type from Yad2 listings
        yad2_listings = obj.get_property_value('yad2_listings', [])
        if yad2_listings:
            for listing in yad2_listings:
                if listing.get('property_type'):
                    return listing['property_type']
        
        # Fallback: try to get property type from meta
        property_type = obj.get_property_value('property_type')
        if property_type:
            return property_type
            
        return None
    
    def get_documents(self, obj):
        """Get documents from both Document model and meta field."""
        if not self.context.get("include_documents", True):
            return []

        documents = []

        # Get documents from Document model (legacy + M2M)
        for doc in asset_documents_all(obj):
            documents.append({
                'id': doc.id,
                'title': doc.title,
                'description': doc.description,
                'type': doc.document_type,
                'status': doc.status,
                'filename': doc.filename,
                'file_size': doc.file_size,
                'date': doc.document_date,
                'url': doc.file_url,
                'source': doc.source,
                'external_id': doc.external_id,
                'external_url': doc.external_url,
                'downloadable': doc.is_downloadable,
                'uploaded_at': doc.uploaded_at,
                'uploaded_by': str(doc.user) if doc.user else None
            })
        
        # Get documents from meta field (for backward compatibility)
        if obj.meta and 'documents' in obj.meta:
            for doc in obj.meta['documents']:
                # Only add if not already in Document model
                # Use 'id' field for meta documents since they don't have 'external_id'
                if not any(d.get('external_id') == doc.get('id') for d in documents):
                    documents.append(doc)

        return documents

    def _listing_sort_key(self, listing):
        # Primary sort: exact address match
        # Secondary sort: fetched_at timestamp
        
        # Try to get asset address from the context
        asset_address = None
        if hasattr(self, '_current_asset_address'):
            asset_address = self._current_asset_address
        elif hasattr(self.parent, 'instance') and self.parent.instance:
            normalized_addr = getattr(self.parent.instance, "normalized_address", "") or ""
            asset_address = normalized_addr.lower() if normalized_addr else None
        
        if hasattr(listing, "address"):
            listing_addr = getattr(listing, "address", "") or ""
            listing_address = listing_addr.lower() if listing_addr else ""
        else:
            listing_address = ""
        
        # Check for exact address match
        if asset_address and listing_address:
            # Exact match gets highest priority
            if asset_address == listing_address:
                return (1, 0, 0)  # Priority: exact match, full timestamp, 0 for tie-breaker
            
            # Check if street and number match (e.g., "ביריה 9")
            asset_parts = asset_address.split()
            if len(asset_parts) >= 2 and asset_parts[1].isdigit():
                street_number = f"{asset_parts[0]} {asset_parts[1]}"
                if street_number in listing_address:
                    return (0.5, 0, 0)  # Priority: partial match, no timestamp needed
        
        # No address match or no address info available - sort by fetched_at
        fetched_at = getattr(listing, "fetched_at", None)
        if not fetched_at:
            return (-1, 0, 0)  # Lower priority if no fetched_at
        try:
            timestamp = fetched_at.timestamp()
            return (0, timestamp, 0)
        except (AttributeError, OSError, OverflowError, ValueError):  # pragma: no cover - safety
            return (-1, 0, 0)

    def _extract_street_and_number(self, address: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract street name and house number from an address.
        Returns (street_name, house_number) or (None, None) if not found.
        
        Tries to extract just the street name word(s) directly before the house number,
        ignoring prefixes like "מרתף/ פרטר -" or "דירה".
        
        Examples:
        - "ארלוזורוב 59, תל אביב" -> ("ארלוזורוב", "59")
        - "רוזוב 14" -> ("רוזוב", "14")
        - "מרתף/ פרטר - ארלוזורוב 156" -> ("ארלוזורוב", "156")
        - "street name" -> (None, None) if no number found
        """
        if not address or not isinstance(address, str):
            return None, None
        
        address = address.strip().lower()
        if not address:
            return None, None
        
        # Split by spaces and look for a digit (house number)
        parts = address.split()
        if len(parts) < 2:
            return None, None
        
        # Find the first numeric part (house number)
        # We need to ensure we extract complete, standalone numeric tokens
        for i in range(len(parts) - 1):
            # Check if the next part is a complete numeric token (house number)
            next_part = parts[i + 1].strip()
            # Remove common separators like commas, dashes, periods from both ends
            next_part_clean = next_part.strip(',-–—.')
            
            # Ensure it's a complete numeric token (all digits, no partial matches)
            # This ensures "2" doesn't get confused with "22" or "222"
            if next_part_clean and next_part_clean.isdigit():
                # Try to extract just the street name (the word directly before the number)
                # In cases like "מרתף/ פרטר - ארלוזורוב 156", we want "ארלוזורוב"
                # Look backwards from the number to find the street name word
                street_name = None
                street_parts = []
                for j in range(i, -1, -1):
                    candidate = parts[j].strip().rstrip('/-–—,')
                    # Skip empty strings and common separators/prefixes
                    if not candidate or candidate in ['/', '-', '–', '—', ',']:
                        continue
                    # Skip if it's a digit
                    if candidate.isdigit():
                        break
                    # If this looks like a street name (non-numeric, not too short)
                    if len(candidate) > 1:
                        street_parts.insert(0, candidate)
                        # Take up to 2 words as street name (handles "רחוב דיזנגוף" or "ארלוזורוב")
                        if len(street_parts) >= 2:
                            break
                
                if street_parts:
                    street_name = ' '.join(street_parts)
                    return street_name, next_part_clean
                
                # Fallback: use everything before the number (cleaned)
                # Only if we couldn't find a clean street name
                all_before = ' '.join(parts[:i + 1]).strip().rstrip('/-–—,')
                if all_before:
                    return all_before, next_part_clean
        
        return None, None

    def _matches_street_and_number(self, address1: str, address2: str) -> bool:
        """
        Check if two addresses have the same street name and house number.
        Only returns True if both street name and number match exactly.
        This ensures "2" doesn't match "22" or "222".
        """
        street1, num1 = self._extract_street_and_number(address1)
        street2, num2 = self._extract_street_and_number(address2)
        
        # Both must have street and number
        if not (street1 and num1 and street2 and num2):
            return False
        
        # Street names must match exactly
        if street1 != street2:
            return False
        
        # Numbers must match exactly as strings
        # This ensures "2" != "22" (different string lengths)
        if num1 != num2:
            return False
        
        # Additional safeguard: compare as integers to catch any edge cases
        # This double-checks that numeric values are truly equal
        try:
            int1, int2 = int(num1), int(num2)
            if int1 != int2:
                return False
        except (ValueError, TypeError):
            # If conversion fails, string comparison above is sufficient
            pass
        
        return True

    def _get_primary_listing_instance(self, obj):
        if hasattr(obj, "_primary_listing_instance_cache"):
            return obj._primary_listing_instance_cache

        if (
            hasattr(obj, "_prefetched_objects_cache")
            and obj._prefetched_objects_cache.get("listings_m2m") is not None
        ):
            listings = list(obj._prefetched_objects_cache["listings_m2m"])
        else:
            listings = list(obj.listings_m2m.all())

        if not listings:
            obj._primary_listing_instance_cache = None
            return None

        # Get asset address for matching - same logic as _find_best_listing
        normalized_addr = getattr(obj, "normalized_address", "") or ""
        if not normalized_addr:
            obj._primary_listing_instance_cache = None
            return None
        
        asset_address = normalized_addr.lower()
        
        # Find the best matching listing - same logic as _find_best_listing
        for listing in listings:
            listing_addr = getattr(listing, "address", "") or ""
            listing_address = listing_addr.lower() if listing_addr else ""
            
            if not listing_address:
                continue
            
            # Check for exact match with full address
            if asset_address == listing_address:
                obj._primary_listing_instance_cache = listing
                return listing
            
            # Check for exact street + number match (e.g., "ארלוזורוב 59")
            if self._matches_street_and_number(asset_address, listing_address):
                obj._primary_listing_instance_cache = listing
                return listing
        
        # No match found - return None (same as _find_best_listing)
        obj._primary_listing_instance_cache = None
        return None

    def _get_primary_listing_data(self, obj):
        if hasattr(obj, "_primary_listing_data_cache"):
            return obj._primary_listing_data_cache

        listing = self._get_primary_listing_instance(obj)
        if not listing:
            obj._primary_listing_data_cache = None
            return None

        data = normalize_listing_from_model(listing)
        
        # Enhance with fields from asset.meta if available (from enrichment pipeline)
        # These fields were extracted during enrichment and stored in primary_listing_source
        if obj.meta and isinstance(obj.meta, dict):
            primary_listing_source = obj.meta.get('primary_listing_source', {})
            if isinstance(primary_listing_source, dict):
                # List of high-priority fields to merge from enrichment pipeline
                # Only merge if not already set in normalized data
                enrichment_fields = [
                    'priceDropped', 'previousPrice', 'shelter', 'accessibility',
                    'buildingClass', 'generalCondition', 'investmentYield', 'approximateRent',
                    'commuteTime', 'publishedDays', 'datePosted',
                    'tagBestSchool', 'tagSafety', 'tagFamilyFriendly', 'tagLightRail',
                    'tagParkAccess', 'tagQuietStreet', 'tagCommute', 'exclusive'
                ]
                for field in enrichment_fields:
                    if field in primary_listing_source and data.get(field) is None:
                        data[field] = primary_listing_source[field]
        
        obj._primary_listing_data_cache = data
        return data

    def get_primary_listing(self, obj):
        return self._get_primary_listing_data(obj)

    def _get_primary_value(self, obj, *keys):
        data = self._get_primary_listing_data(obj)
        if not data:
            return None
        for key in keys:
            value = data.get(key)
            if value not in (None, ""):
                return value
        return None

    def get_listing_type(self, obj):
        return self._get_primary_value(obj, "listing_type", "listingType")

    def get_ad_type(self, obj):
        return self._get_primary_value(obj, "ad_type", "adType")

    def get_contact_name(self, obj):
        direct = self._get_primary_value(obj, "contact_name", "contactName")
        if direct:
            return direct
        info = self._get_primary_value(obj, "contact_info", "contactInfo") or {}
        return (info or {}).get("name") if isinstance(info, dict) else None

    def get_contact_phone(self, obj):
        direct = self._get_primary_value(obj, "contact_phone", "contactPhone")
        if direct:
            return direct
        info = self._get_primary_value(obj, "contact_info", "contactInfo") or {}
        if isinstance(info, dict):
            return info.get("phone") or info.get("brokerPhone")
        return None

    def get_recent_deal(self, obj):
        value = self._get_primary_value(obj, "recent_deal", "recentDeal")
        return bool(value) if value is not None else None

    def get_video_url(self, obj):
        return self._get_primary_value(obj, "video_url", "video", "videoUrl")

    def get_photos(self, obj):
        data = self._get_primary_listing_data(obj)
        if not data:
            return []
        photos = data.get("photos") or data.get("images") or []
        return photos or []

    def get_isWatched(self, obj):
        annotated_value = getattr(obj, "is_watched", None)
        if annotated_value is not None:
            return bool(annotated_value)

        request = self.context.get("request") if isinstance(self.context, dict) else None
        user = getattr(request, "user", None) if request else None
        if not user or not getattr(user, "is_authenticated", False):
            return False

        return obj.watchlist_entries.filter(user=user).exists()
    
    # GIS Environment field getters
    def _get_property(self, obj, key):
        """Helper to get property value from meta or direct field."""
        return obj.get_property_value(key)
    
    def get_openSpacesNearby(self, obj):
        return self._get_property(obj, 'openSpacesNearby')
    
    def get_publicBuildings(self, obj):
        return self._get_property(obj, 'publicBuildings')
    
    def get_parking(self, obj):
        return self._get_property(obj, 'parking')
    
    def get_nearbyProjects(self, obj):
        return self._get_property(obj, 'nearbyProjects')
    
    def get_publicTransport(self, obj):
        return self._get_property(obj, 'publicTransport')
    
    def get_greenScore(self, obj):
        return self._get_property(obj, 'greenScore')
    
    def get_investmentPotential(self, obj):
        return self._get_property(obj, 'investmentPotential')
    
    def get_investmentPotentialScore(self, obj):
        return self._get_property(obj, 'investmentPotentialScore')
    
    def get_metroStationDistanceM(self, obj):
        return self._get_property(obj, 'metroStationDistanceM')
    
    def get_metroStationsCount(self, obj):
        return self._get_property(obj, 'metroStationsCount')
    
    def get_parkingLotsCount(self, obj):
        return self._get_property(obj, 'parkingLotsCount')
    
    def get_publicParkingLotsCount(self, obj):
        return self._get_property(obj, 'publicParkingLotsCount')
    
    def get_schoolsCount(self, obj):
        return self._get_property(obj, 'schoolsCount')
    
    def get_nearestSchoolDistanceM(self, obj):
        return self._get_property(obj, 'nearestSchoolDistanceM')
    
    def get_constructionSitesCount(self, obj):
        return self._get_property(obj, 'constructionSitesCount')
    
    def get_affordableHousingProjectsCount(self, obj):
        return self._get_property(obj, 'affordableHousingProjectsCount')
    
    def get_bikePathsCount(self, obj):
        return self._get_property(obj, 'bikePathsCount')
    
    def get_hasBikePaths(self, obj):
        return self._get_property(obj, 'hasBikePaths')
    
    def get_soilContaminationSitesCount(self, obj):
        return self._get_property(obj, 'soilContaminationSitesCount')
    
    def get_nearestSoilContaminationDistanceM(self, obj):
        return self._get_property(obj, 'nearestSoilContaminationDistanceM')
    
    def get_greenAmenitiesCount(self, obj):
        return self._get_property(obj, 'greenAmenitiesCount')
    
    def get_playgroundsCount(self, obj):
        return self._get_property(obj, 'playgroundsCount')
    
    def get_medicalFacilitiesCount(self, obj):
        return self._get_property(obj, 'medicalFacilitiesCount')
    
    def get_nearestMedicalFacilityDistanceM(self, obj):
        return self._get_property(obj, 'nearestMedicalFacilityDistanceM')
    
    def get_communityFacilitiesCount(self, obj):
        return self._get_property(obj, 'communityFacilitiesCount')
    
    def get_dogParksCount(self, obj):
        return self._get_property(obj, 'dogParksCount')
    
    def get_publicGardensCount(self, obj):
        return self._get_property(obj, 'publicGardensCount')
    
    def get_medicalCentersCount(self, obj):
        return self._get_property(obj, 'medicalCentersCount')
    
    def get_healthFundsCount(self, obj):
        return self._get_property(obj, 'healthFundsCount')
    
    def get_pharmaciesCount(self, obj):
        return self._get_property(obj, 'pharmaciesCount')
    
    def get_tama38KeyArea(self, obj):
        return self._get_property(obj, 'tama38KeyArea')
    
    def get_tama38KeyAreasCount(self, obj):
        return self._get_property(obj, 'tama38KeyAreasCount')
    
    def get_roadWorksCount(self, obj):
        return self._get_property(obj, 'roadWorksCount')
    
    def get_hasActiveRoadWorks(self, obj):
        return self._get_property(obj, 'hasActiveRoadWorks')
    
    class Meta:
        model = Asset
        fields = [
            'id', 'scope_type', 'city', 'neighborhood', 'street', 'number',
            'block', 'parcel', 'subparcel', 'lat', 'lon', 'normalized_address', 'address', 'status',
            'building_type', 'type', 'floor', 'apartment', 'total_floors', 'rooms', 'bedrooms', 'bathrooms',
            'area', 'total_area', 'balcony_area', 'parking_spaces', 'storage_room',
            'elevator', 'air_conditioning', 'furnished', 'renovated', 'year_built',
            'last_renovation', 'price', 'price_per_sqm', 'rent_estimate',
            'rent_price', 'rentPrice',
            'price_gap_pct','expected_price_range','model_price','confidence_pct','delta_vs_area_pct','cap_rate_pct','competition_1km','risk_flags','dom_percentile',
            'avg_price_per_sqm','min_price_per_sqm','max_price_per_sqm',
            'priceGapPct','modelPrice','confidencePct','capRatePct','avgPricePerSqm','minPricePerSqm','maxPricePerSqm',
            'rightsUsagePct','legalRestrictions','urbanRenewalPotential','bettermentLevy',
            'buildingCoveragePct','heightAnalysis','setbackAnalysis',
            'openSpacesNearby','publicBuildings','parking','nearbyProjects','publicTransport',
            'greenScore','investmentPotential','investmentPotentialScore',
            'metroStationDistanceM','metroStationsCount','parkingLotsCount','publicParkingLotsCount',
            'schoolsCount','nearestSchoolDistanceM','constructionSitesCount','affordableHousingProjectsCount',
            'bikePathsCount','hasBikePaths','soilContaminationSitesCount','nearestSoilContaminationDistanceM',
            'greenAmenitiesCount','playgroundsCount','medicalFacilitiesCount','nearestMedicalFacilityDistanceM',
            'communityFacilitiesCount','dogParksCount','publicGardensCount','medicalCentersCount','healthFundsCount','pharmaciesCount',
            'tama38KeyArea','tama38KeyAreasCount','roadWorksCount','hasActiveRoadWorks',
            'zoning', 'building_rights', 'permit_status', 'permit_date', 'is_demo',
            'is_commercial', 'isCommercial',
            'isWatched',
            'last_enriched_at', 'created_at', 'meta', 'documents',
            'primary_listing', 'listing_type', 'ad_type',
            'contact_name', 'contact_phone',
            'recent_deal', 'video_url', 'photos',
            # GIS Collector Data Fields
            'parcel_area', 'parcel_registered_area', 'parcel_status', 'parcel_accuracy',
            'block_area', 'block_registered_area', 'block_total_parcels', 'block_status', 'block_last_update',
            'total_permits', 'permit_request_num', 'permit_permission_num', 'permit_building_num',
            'permit_housing_units', 'permit_commercial_area', 'permit_residential_area', 'permit_residential_units',
            'permit_public_area', 'permit_parking_area', 'permit_parking_units', 'permit_small_apartments',
            'permit_unified_housing_area', 'permit_unified_housing_units', 'permit_accessible_apartments',
            'permit_public_built_area', 'permit_total_area', 'permit_mavat_plan_num', 'permit_parking_rooms_calculated',
            'permit_full_utilization', 'permit_subject_type', 'permit_process', 'permit_rights_notification',
            'permit_repartition', 'permit_urban_renewal', 'permit_open_request_date', 'permit_construction_start_date'
        ]


class PermitSerializer(MetaSerializerMixin):
    is_tama_38 = serializers.SerializerMethodField()
    has_construction_allowances = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()
    asset_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    assets = serializers.SerializerMethodField(read_only=True)
    request_num = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Permit
        fields = [
            'id', 'asset', 'asset_ids', 'assets', 'permit_number', 'request_num', 'description', 'status',
            # Dates
            'issued_date', 'expiry_date',
            # Files and documents
            'file_url',
            # Computed fields
            'is_tama_38', 'has_construction_allowances', 'display_title',
            # Metadata
            'raw'
        ]
        read_only_fields = ['asset']

    def get_assets(self, instance):
        assets_qs = instance.all_assets() if hasattr(instance, 'all_assets') else instance.assets.all()
        return [{'id': asset.id} for asset in assets_qs]
    
    def get_request_num(self, instance):
        """Get request_num from raw JSONField."""
        raw = getattr(instance, 'raw', {}) or {}
        return raw.get('request_num') or raw.get('meta', {}).get('request_num') if isinstance(raw.get('meta'), dict) else None

    def get_is_tama_38(self, instance):
        """Check if permit is TAMA 38 from raw JSONField."""
        raw = getattr(instance, 'raw', {}) or {}
        meta = raw.get('meta', {}) if isinstance(raw.get('meta'), dict) else {}
        return (
            raw.get('sw_tama_38') or
            raw.get('sw_tama_38_chadash') or
            raw.get('sw_tama_38_tosefet') or
            meta.get('sw_tama_38') or
            meta.get('sw_tama_38_chadash') or
            meta.get('sw_tama_38_tosefet') or
            False
        )

    def get_has_construction_allowances(self, instance):
        """Check if permit has construction allowances from raw JSONField."""
        raw = getattr(instance, 'raw', {}) or {}
        meta = raw.get('meta', {}) if isinstance(raw.get('meta'), dict) else {}
        return bool(
            raw.get('hakala_tosefet_achuz_shetach') or
            raw.get('hakala_yd_hagdala_achuz') or
            raw.get('hakala_yd_mevukash') or
            raw.get('hakala_yd_mutar') or
            meta.get('hakala_tosefet_achuz_shetach') or
            meta.get('hakala_yd_hagdala_achuz') or
            meta.get('hakala_yd_mevukash') or
            meta.get('hakala_yd_mutar')
        )

    def get_display_title(self, instance):
        """Get display title from raw JSONField or generate from permit_number."""
        raw = getattr(instance, 'raw', {}) or {}
        meta = raw.get('meta', {}) if isinstance(raw.get('meta'), dict) else {}
        return (
            raw.get('koteret') or
            meta.get('koteret') or
            raw.get('description') or
            instance.description or
            f"Permit {instance.permit_number}"
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        assets_qs = instance.all_assets() if hasattr(instance, 'all_assets') else instance.assets.all()
        data['asset_ids'] = [asset.id for asset in assets_qs]
        return data

    def _sync_assets(self, instance, asset_ids):
        current_ids = set(instance.assets.values_list('id', flat=True))
        desired_ids = set(asset_ids)
        add_ids = desired_ids - current_ids
        remove_ids = current_ids - desired_ids

        for asset_id in add_ids:
            AssetPermit.objects.get_or_create(permit=instance, asset_id=asset_id)
        if remove_ids:
            AssetPermit.objects.filter(permit=instance, asset_id__in=remove_ids).delete()

    def create(self, validated_data):
        asset_ids = validated_data.pop('asset_ids', None)
        instance = super().create(validated_data)
        if asset_ids is not None:
            self._sync_assets(instance, asset_ids)
        return instance

    def update(self, instance, validated_data):
        asset_ids = validated_data.pop('asset_ids', None)
        instance = super().update(instance, validated_data)
        if asset_ids is not None:
            self._sync_assets(instance, asset_ids)
        return instance


class PlanSerializer(MetaSerializerMixin):
    asset_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    assets = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Plan
        fields = [
            'id', 'asset', 'asset_ids', 'assets', 'plan_number', 'title', 'description', 'status',
            'effective_date', 'file_url'
        ]
        read_only_fields = ['asset']

    def get_assets(self, instance):
        assets_qs = instance.all_assets() if hasattr(instance, 'all_assets') else instance.assets.all()
        return [{'id': asset.id} for asset in assets_qs]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        assets_qs = instance.all_assets() if hasattr(instance, 'all_assets') else instance.assets.all()
        data['asset_ids'] = [asset.id for asset in assets_qs]
        return data

    def _sync_assets(self, instance, asset_ids):
        current_ids = set(instance.assets.values_list('id', flat=True))
        desired_ids = set(asset_ids)
        add_ids = desired_ids - current_ids
        remove_ids = current_ids - desired_ids

        for asset_id in add_ids:
            AssetPlan.objects.get_or_create(plan=instance, asset_id=asset_id)
        if remove_ids:
            AssetPlan.objects.filter(plan=instance, asset_id__in=remove_ids).delete()

    def create(self, validated_data):
        asset_ids = validated_data.pop('asset_ids', None)
        instance = super().create(validated_data)
        if asset_ids is not None:
            self._sync_assets(instance, asset_ids)
        return instance

    def update(self, instance, validated_data):
        asset_ids = validated_data.pop('asset_ids', None)
        instance = super().update(instance, validated_data)
        if asset_ids is not None:
            self._sync_assets(instance, asset_ids)
        return instance


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "status")


class ConsultationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationRequest
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "status")


class AlertRuleSerializer(serializers.ModelSerializer):
    """Serializer for AlertRule model."""
    
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    
    class Meta:
        model = AlertRule
        fields = [
            'id', 'user', 'scope', 'asset', 'trigger_type', 'trigger_type_display',
            'params', 'channels', 'frequency', 'frequency_display', 'scope_display',
            'active', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def validate_channels(self, value):
        """Validate that channels are valid options."""
        valid_channels = ['email', 'whatsapp']
        for channel in value:
            if channel not in valid_channels:
                raise serializers.ValidationError(f"Invalid channel: {channel}. Must be one of {valid_channels}")
        return value
    
    def validate_params(self, value):
        """Validate parameters based on trigger type."""
        trigger_type = self.initial_data.get('trigger_type')
        
        if trigger_type == 'PRICE_DROP':
            pct = value.get('pct', 3)
            if not isinstance(pct, (int, float)) or pct < 0 or pct > 100:
                raise serializers.ValidationError("Price drop percentage must be between 0 and 100")
        
        elif trigger_type == 'MARKET_TREND':
            delta_pct = value.get('delta_pct', 5)
            window_days = value.get('window_days', 30)
            radius_km = value.get('radius_km', 1.0)
            
            if not isinstance(delta_pct, (int, float)) or delta_pct < 0 or delta_pct > 100:
                raise serializers.ValidationError("Market trend delta percentage must be between 0 and 100")
            if not isinstance(window_days, int) or window_days < 7 or window_days > 180:
                raise serializers.ValidationError("Window days must be between 7 and 180")
            if not isinstance(radius_km, (int, float)) or radius_km < 0.1 or radius_km > 5:
                raise serializers.ValidationError("Radius must be between 0.1 and 5 km")
        
        elif trigger_type == 'NEW_GOV_TX':
            radius_m = value.get('radius_m', 500)
            if not isinstance(radius_m, (int, float)) or radius_m < 50 or radius_m > 2000:
                raise serializers.ValidationError("Radius must be between 50 and 2000 meters")
        
        elif trigger_type == 'LISTING_REMOVED':
            misses = value.get('misses', 2)
            if not isinstance(misses, int) or misses < 1 or misses > 10:
                raise serializers.ValidationError("Misses must be between 1 and 10")
        
        return value
    
    def validate(self, data):
        """Validate that asset is provided when scope is 'asset'."""
        if data.get('scope') == 'asset' and not data.get('asset'):
            raise serializers.ValidationError("Asset must be provided when scope is 'asset'")
        return data


class AlertEventSerializer(serializers.ModelSerializer):
    """Serializer for AlertEvent model."""
    
    alert_rule = AlertRuleSerializer(read_only=True)
    asset_address = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertEvent
        fields = [
            'id', 'alert_rule', 'asset', 'asset_address', 'occurred_at',
            'payload', 'delivered_at', 'digest_id'
        ]
        read_only_fields = ('id', 'occurred_at', 'delivered_at', 'digest_id')
    
    def get_asset_address(self, obj):
        """Get formatted asset address."""
        if obj.asset:
            return obj.asset.normalized_address or f"{obj.asset.street} {obj.asset.number}, {obj.asset.city}"
        return None


class SnapshotSerializer(serializers.ModelSerializer):
    """Serializer for Snapshot model."""
    
    class Meta:
        model = Snapshot
        fields = ['id', 'asset', 'payload', 'ppsqm', 'created_at']
        read_only_fields = ('id', 'created_at')


class AssetContributionSerializer(serializers.ModelSerializer):
    """Serializer for AssetContribution model."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    contribution_type_display = serializers.SerializerMethodField()
    
    def get_contribution_type_display(self, obj):
        """Return Hebrew translation for contribution type."""
        translations = {
            'creation': 'יצירת נכס',
            'enrichment': 'העשרת נתונים',
            'verification': 'אימות נתונים',
            'update': 'עדכון שדה',
            'source_add': 'הוספת מקור',
            'comment': 'הערה/תגובה'
        }
        return translations.get(obj.contribution_type, obj.get_contribution_type_display())
    
    class Meta:
        model = AssetContribution
        fields = [
            'id', 'asset', 'user', 'user_email', 'user_first_name', 'user_last_name',
            'contribution_type', 'contribution_type_display', 'field_name',
            'old_value', 'new_value', 'source', 'description', 'created_at'
        ]
        read_only_fields = ('id', 'created_at')


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_email', 'user_first_name', 'user_last_name',
            'assets_created', 'assets_updated', 'contributions_made',
            'data_points_added', 'sources_contributed', 'reputation_score',
            'verification_count', 'helpful_votes', 'show_attribution',
            'public_profile', 'contribution_notifications', 'created_at',
            'updated_at', 'last_contribution_at'
        ]
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class AssetWithAttributionSerializer(AssetSerializer):
    """Enhanced Asset serializer with attribution information."""
    
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    last_updated_by_email = serializers.CharField(source='last_updated_by.email', read_only=True)
    last_updated_by_name = serializers.SerializerMethodField()
    contributions = AssetContributionSerializer(many=True, read_only=True)
    contribution_count = serializers.SerializerMethodField()
    
    class Meta(AssetSerializer.Meta):
        fields = AssetSerializer.Meta.fields + [
            'created_by', 'created_by_email', 'created_by_name',
            'last_updated_by', 'last_updated_by_email', 'last_updated_by_name',
            'contributions', 'contribution_count'
        ]
    
    def get_created_by_name(self, obj):
        """Get full name of the user who created the asset."""
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.email
        return None
    
    def get_last_updated_by_name(self, obj):
        """Get full name of the user who last updated the asset."""
        if obj.last_updated_by:
            return f"{obj.last_updated_by.first_name} {obj.last_updated_by.last_name}".strip() or obj.last_updated_by.email
        return None
    
    def get_contribution_count(self, obj):
        """Get total number of contributions for this asset."""
        return obj.contributions.count()


class PlanTypeSerializer(serializers.ModelSerializer):
    """Serializer for plan types."""
    
    class Meta:
        model = PlanType
        fields = [
            'id', 'name', 'display_name', 'description', 'price', 'currency', 'billing_period',
            'asset_limit', 'report_limit', 'alert_limit', 'advanced_analytics', 'data_export',
            'api_access', 'priority_support', 'custom_reports', 'is_active'
        ]


class UserPlanSerializer(serializers.ModelSerializer):
    """Serializer for user plans."""
    plan_type = PlanTypeSerializer(read_only=True)
    is_expired = serializers.SerializerMethodField()
    remaining_assets = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPlan
        fields = [
            'id', 'plan_type', 'is_active', 'started_at', 'expires_at', 'auto_renew',
            'last_payment_at', 'next_payment_at', 'assets_used', 'reports_used', 'alerts_used',
            'is_expired', 'remaining_assets'
        ]
    
    def get_is_expired(self, obj):
        """Check if the plan has expired."""
        return obj.is_expired()
    
    def get_remaining_assets(self, obj):
        """Get remaining asset slots."""
        return obj.get_remaining_assets()


class UserPlanInfoSerializer(serializers.Serializer):
    """Serializer for comprehensive user plan information."""
    plan_name = serializers.CharField()
    display_name = serializers.CharField()
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    billing_period = serializers.CharField()
    is_active = serializers.BooleanField()
    is_expired = serializers.BooleanField()
    expires_at = serializers.DateTimeField(allow_null=True)
    limits = serializers.DictField()
    features = serializers.DictField()


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""

    file_url = serializers.ReadOnlyField()
    is_downloadable = serializers.ReadOnlyField()
    uploaded_by = serializers.StringRelatedField(source='user', read_only=True)
    asset_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    assets = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'asset', 'asset_ids', 'assets', 'user', 'title', 'description', 'document_type',
            'status', 'filename', 'file_size', 'mime_type', 'external_id',
            'external_url', 'source', 'document_date', 'uploaded_at',
            'updated_at', 'file_url', 'is_downloadable', 'uploaded_by', 'meta'
        ]
        read_only_fields = ['id', 'asset', 'user', 'uploaded_at', 'updated_at', 'file_url', 'is_downloadable']

    def _collect_assets(self, instance):
        """Collect related assets without incurring N+1 queries."""
        assets = []
        seen_ids = set()

        # Primary (legacy) FK
        if getattr(instance, "asset_id", None):
            primary_asset = getattr(instance, "asset", None)
            if primary_asset is None:
                try:
                    primary_asset = Asset.objects.get(id=instance.asset_id)
                except Asset.DoesNotExist:
                    primary_asset = None
            if primary_asset is not None:
                assets.append(primary_asset)
                seen_ids.add(primary_asset.id)

        # Many-to-many assets (prefetched when possible)
        if hasattr(instance, "_prefetched_objects_cache") and "assets" in instance._prefetched_objects_cache:
            related_assets = instance._prefetched_objects_cache["assets"]
        else:
            related_assets = instance.assets.all()

        for asset in related_assets:
            if asset.id in seen_ids:
                continue
            assets.append(asset)
            seen_ids.add(asset.id)

        return assets

    def get_assets(self, instance):
        return [
            {
                'id': asset.id,
                'address': getattr(asset, 'address', None),
                'city': getattr(asset, 'city', None),
            }
            for asset in self._collect_assets(instance)
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['asset_ids'] = [asset.id for asset in self._collect_assets(instance)]
        return data

    def _sync_assets(self, instance, asset_ids):
        current_ids = set(instance.assets.values_list('id', flat=True))
        desired_ids = set(asset_ids)
        add_ids = desired_ids - current_ids
        remove_ids = current_ids - desired_ids

        for asset_id in add_ids:
            AssetDocument.objects.get_or_create(document=instance, asset_id=asset_id)
        if remove_ids:
            AssetDocument.objects.filter(document=instance, asset_id__in=remove_ids).delete()

    def create(self, validated_data):
        asset_ids = validated_data.pop('asset_ids', None)
        instance = super().create(validated_data)
        if asset_ids is not None:
            self._sync_assets(instance, asset_ids)
        return instance

    def update(self, instance, validated_data):
        asset_ids = validated_data.pop('asset_ids', None)
        instance = super().update(instance, validated_data)
        if asset_ids is not None:
            self._sync_assets(instance, asset_ids)
        return instance


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload."""
    file = serializers.FileField()
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    document_type = serializers.ChoiceField(choices=Document.DOCUMENT_TYPE_CHOICES, default='other')
    document_date = serializers.DateField(required=False, allow_null=True)
    external_id = serializers.CharField(required=False, allow_blank=True, max_length=100)
    external_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate_file(self, value):
        """Validate uploaded file."""
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(f"File size cannot exceed {max_size / (1024*1024):.1f}MB")
        
        # Check file type
        allowed_types = [
            'application/pdf',
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(f"File type {value.content_type} is not allowed")
        
        return value


class DocumentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for document lists."""
    file_url = serializers.ReadOnlyField()
    is_downloadable = serializers.ReadOnlyField()
    uploaded_by = serializers.StringRelatedField(source='user', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'document_type', 'status', 'filename', 
            'file_size', 'document_date', 'uploaded_at', 'file_url', 
            'is_downloadable', 'uploaded_by'
        ]


class RealEstateTransactionSerializer(serializers.ModelSerializer):
    asset_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    assets = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RealEstateTransaction
        fields = [
            'id', 'asset', 'asset_ids', 'assets', 'deal_id', 'date', 'price', 'rooms',
            'area', 'floor', 'address', 'raw', 'fetched_at'
        ]
        read_only_fields = ['asset']

    def get_assets(self, instance):
        assets_qs = instance.all_assets() if hasattr(instance, 'all_assets') else instance.assets.all()
        return [{'id': asset.id} for asset in assets_qs]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        assets_qs = instance.all_assets() if hasattr(instance, 'all_assets') else instance.assets.all()
        data['asset_ids'] = [asset.id for asset in assets_qs]
        return data

    def _sync_assets(self, instance, asset_ids):
        current_ids = set(instance.assets.values_list('id', flat=True))
        desired_ids = set(asset_ids)
        add_ids = desired_ids - current_ids
        remove_ids = current_ids - desired_ids

        for asset_id in add_ids:
            AssetTransaction.objects.get_or_create(transaction=instance, asset_id=asset_id)
        if remove_ids:
            AssetTransaction.objects.filter(transaction=instance, asset_id__in=remove_ids).delete()

    def create(self, validated_data):
        asset_ids = validated_data.pop('asset_ids', None)
        instance = super().create(validated_data)
        if asset_ids is not None:
            self._sync_assets(instance, asset_ids)
        return instance

    def update(self, instance, validated_data):
        asset_ids = validated_data.pop('asset_ids', None)
        instance = super().update(instance, validated_data)
        if asset_ids is not None:
            self._sync_assets(instance, asset_ids)
        return instance


class ListingSerializer(serializers.ModelSerializer):
    asset_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    assets = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id',
            'source',
            'external_id',
            'title',
            'url',
            'raw',
            'status',
            'price',
            'rooms',
            'area',
            'address',
            'listing_type',
            'contact_name',
            'contact_phone',
            'recent_deal',
            'photos',
            'video_url',
            'fetched_at',
            'asset_ids',
            'assets',
        ]

    def get_assets(self, instance):
        assets_qs = instance.assets.all()
        return [{'id': asset.id} for asset in assets_qs]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['asset_ids'] = list(instance.assets.values_list('id', flat=True))
        return data

    def _sync_assets(self, instance, asset_ids):
        current_ids = set(instance.assets.values_list('id', flat=True))
        desired_ids = set(asset_ids)
        add_ids = desired_ids - current_ids
        remove_ids = current_ids - desired_ids

        for asset_id in add_ids:
            AssetListing.objects.get_or_create(listing=instance, asset_id=asset_id)
        if remove_ids:
            AssetListing.objects.filter(listing=instance, asset_id__in=remove_ids).delete()

    def create(self, validated_data):
        asset_ids = validated_data.pop('asset_ids', None)
        instance = super().create(validated_data)
        if asset_ids is not None:
            self._sync_assets(instance, asset_ids)
        return instance

    def update(self, instance, validated_data):
        asset_ids = validated_data.pop('asset_ids', None)
        instance = super().update(instance, validated_data)
        if asset_ids is not None:
            self._sync_assets(instance, asset_ids)
        return instance


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin user management with full CRUD operations."""
    
    full_name = serializers.SerializerMethodField()
    last_login_display = serializers.SerializerMethodField()
    created_at_display = serializers.SerializerMethodField()
    is_active_display = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'company', 'role', 'is_active', 'is_active_display',
            'is_verified', 'is_demo', 'is_staff', 'is_superuser',
            'created_at', 'created_at_display', 'updated_at', 'last_login', 'last_login_display',
            'date_joined', 'language', 'timezone', 'currency', 'date_format',
            'notify_email', 'notify_whatsapp', 'notify_urgent', 'notification_time'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        """Get user's full name."""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username or obj.email
    
    def get_last_login_display(self, obj):
        """Format last login date."""
        if obj.last_login:
            return obj.last_login.strftime('%Y-%m-%d %H:%M')
        return 'מעולם לא'
    
    def get_created_at_display(self, obj):
        """Format created date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    
    def get_is_active_display(self, obj):
        """Get active status display."""
        return 'פעיל' if obj.is_active else 'לא פעיל'
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if self.instance and self.instance.email == value:
            return value
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness."""
        if self.instance and self.instance.username == value:
            return value
        
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def create(self, validated_data):
        """Create a new user."""
        # Set a default password for new users
        password = validated_data.pop('password', 'defaultpassword123')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user instance."""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class AdminUserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users by admin."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone', 'company',
            'role', 'is_active', 'is_verified', 'is_demo', 'is_staff',
            'password', 'confirm_password', 'language', 'timezone', 'currency',
            'date_format', 'notify_email', 'notify_whatsapp', 'notify_urgent',
            'notification_time'
        ]
    
    def validate(self, data):
        """Validate password confirmation."""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': "Passwords don't match."
            })
        return data
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def create(self, validated_data):
        """Create a new user."""
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users by admin."""
    
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone', 'company',
            'role', 'is_active', 'is_verified', 'is_demo', 'is_staff',
            'password', 'language', 'timezone', 'currency', 'date_format',
            'notify_email', 'notify_whatsapp', 'notify_urgent', 'notification_time'
        ]
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False}
        }
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if self.instance and self.instance.email == value:
            return value
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness."""
        if self.instance and self.instance.username == value:
            return value
        
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def update(self, instance, validated_data):
        """Update user instance."""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance
