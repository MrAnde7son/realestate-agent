from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from statistics import median
from datetime import datetime, date
from typing import Any, Dict, Iterable, List, Optional, Tuple

from django.contrib.auth import get_user_model
from django.utils import timezone
from govmap.api_client import itm_to_wgs84

from utils.helpers import _first_nonempty, _safe_get
from utils.market_utils import get_city_gross_yield
from orchestration.pipeline.listings import _normalize_listings
from orchestration.pipeline.documents import (
    Document,
    DjangoListing,
    Plan,
    _convert_unix_timestamp_to_date,
    _collect_field_updates,
    _ensure_transaction_link,
    _ensure_listing_link,
    _upsert_document,
    _upsert_plan,
    _upsert_permit,
    _extract_permit_date,
    _parse_document_date,
    _normalize_identifier,
)
from orchestration.planning_legal_analyzer import (
    calculate_planning_legal_analysis,
    apply_planning_legal_analysis_to_asset,
)


logger = logging.getLogger(__name__)


@dataclass
class FeatureVector:
    """Represents all adjustment factors for the valuation model."""

    comps_factor: float = 0.0
    size_factor: float = 0.0
    age_factor: float = 0.0
    potential_factor: float = 0.0
    new_build_factor: float = 0.0
    attachments_factor: float = 0.0
    finish_level_factor: float = 0.0
    elevator_factor: float = 0.0
    proximity_factor: float = 0.0
    noise_factor: float = 0.0
    floor_factor: float = 0.0

    @property
    def total_adjustment(self) -> float:
        return sum(
            (
                self.comps_factor,
                self.size_factor,
                self.age_factor,
                self.potential_factor,
                self.new_build_factor,
                self.attachments_factor,
                self.finish_level_factor,
                self.elevator_factor,
                self.proximity_factor,
                self.noise_factor,
                self.floor_factor,
            )
        )

    def to_dict(self) -> Dict[str, float]:
        data = asdict(self)
        data['total'] = self.total_adjustment
        return data


def _safe_numeric(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _safe_bool(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else False


def _normalize_listing_type_value(value: Any) -> Optional[str]:
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            return normalized.lower()
    return None


def _extract_listing_type(listing_data: Any) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(listing_data, dict):
        return None, None

    listing_type_value = listing_data.get('listing_type') or listing_data.get('listingType')
    normalized = _normalize_listing_type_value(listing_type_value)
    if normalized:
        return listing_type_value, normalized

    meta = listing_data.get('meta')
    if isinstance(meta, dict):
        for key in ('listing_type', 'listingType'):
            candidate = meta.get(key)
            normalized = _normalize_listing_type_value(candidate)
            if normalized:
                return candidate, normalized

        raw_meta = meta.get('raw')
        if isinstance(raw_meta, dict):
            candidate = raw_meta.get('listingType')
            normalized = _normalize_listing_type_value(candidate)
            if normalized:
                return candidate, normalized

    return None, None


def _parse_iso_date(date_value: Any) -> Optional[date]:
    if isinstance(date_value, date):
        return date_value
    if isinstance(date_value, datetime):
        return date_value.date()
    if isinstance(date_value, str):
        try:
            return datetime.fromisoformat(date_value).date()
        except ValueError:
            return None
    return None


def _compute_recency_weight(deal_date: Any) -> float:
    parsed = _parse_iso_date(deal_date)
    if not parsed:
        return 1.0

    days_diff = (date.today() - parsed).days
    # Fade weight linearly over a 24 month window (≈730 days)
    recency_weight = max(0.2, 1 - (days_diff / 730))
    return recency_weight


def _compute_ppm_weight(entry: Dict[str, Any]) -> float:
    base_weight = 1.0
    if entry.get('source') == 'nadlan':
        base_weight += 0.5  # Transactions are more reliable than listings

    recency_weight = _compute_recency_weight(entry.get('deal_date'))
    return base_weight * recency_weight


def _get_listing_area_for_ppm(listing: Dict[str, Any]) -> Optional[float]:
    """Return the best available area for PPM calculation.

    Prefers total/gross area fields when present to ensure PPM is based on the
    property's full size, falling back to net/built area if necessary.
    """

    if not isinstance(listing, dict):
        return None

    meta = listing.get('meta') if isinstance(listing.get('meta'), dict) else {}

    total_area_value = _safe_numeric(
        _first_nonempty(
            listing.get('total_size'),
            listing.get('total_area'),
            _safe_get(meta, 'total_size'),
            _safe_get(meta, 'totalSqm'),
            _safe_get(meta, 'total_area'),
        )
    )
    if total_area_value and total_area_value > 0:
        return total_area_value

    net_area_value = _safe_numeric(
        _first_nonempty(
            listing.get('area'),
            listing.get('size'),
            _safe_get(meta, 'area'),
            _safe_get(meta, 'size'),
        )
    )
    if net_area_value and net_area_value > 0:
        return net_area_value

    return None


def _calculate_base_ppm_and_value(ppm_data: List[Dict[str, Any]], asset_total_area: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    if not ppm_data:
        return None, None

    ppm_values = [d['ppm'] for d in ppm_data]
    weights = [_compute_ppm_weight(d) for d in ppm_data]
    weighted_sum = sum(ppm * weight for ppm, weight in zip(ppm_values, weights))
    weight_total = sum(weights) or 1
    weighted_ppm = weighted_sum / weight_total

    base_value = None
    if asset_total_area and asset_total_area > 0:
        comparable_prices = [d['ppm'] * asset_total_area for d in ppm_data]
        base_value = median(comparable_prices)

    return weighted_ppm, base_value


def _size_adjustment(area: Optional[float]) -> float:
    area_value = _safe_numeric(area)
    if not area_value or area_value <= 0:
        return 0.0
    if 40 <= area_value < 70:
        return 0.06
    if 70 <= area_value <= 100:
        return 0.0
    if 100 < area_value < 150:
        return -0.04
    if area_value >= 150:
        return -0.08
    return 0.0


def _age_adjustment(year_built: Optional[int]) -> float:
    year_value = _safe_numeric(year_built)
    if not year_value:
        return 0.0
    age = date.today().year - int(year_value)
    if age <= 5:
        return 0.12
    if age <= 20:
        return 0.06
    if age <= 40:
        return 0.0
    if age <= 60:
        return -0.05
    return -0.1


def _potential_adjustment(asset: Any) -> float:
    potential = None
    raw_potential = getattr(asset, 'urban_renewal_potential', None)
    if isinstance(raw_potential, str):
        potential = raw_potential.lower()
    elif isinstance(getattr(asset, 'meta', None), dict):
        potential = str(asset.meta.get('planning_potential', '')).lower()

    if _safe_bool(getattr(asset, 'permit_urban_renewal', False)):
        potential = potential or 'high'

    if potential in ('high', 'גבוה', 'tama38', 'pinui_binui'):
        return 0.15
    if potential in ('medium', 'בינוני', 'mid'):
        return 0.08
    if potential in ('negative', 'low', 'שלילי'):
        return -0.08
    return 0.0


def _new_build_adjustment(asset: Any) -> float:
    year_built = _safe_numeric(getattr(asset, 'year_built', None))
    if year_built and (date.today().year - year_built) <= 5:
        return 0.18

    meta = getattr(asset, 'meta', {}) or {}
    if isinstance(meta, dict):
        if meta.get('new_project'):
            return 0.2
        if meta.get('tama38_completed'):
            return 0.12
    return 0.0


def _attachments_adjustment(asset: Any) -> float:
    adjustment = 0.0
    parking_spaces = _safe_numeric(getattr(asset, 'parking_spaces', None)) or 0
    if parking_spaces >= 1:
        adjustment += 0.1
        if parking_spaces > 1:
            adjustment += 0.02

    if _safe_bool(getattr(asset, 'storage_room', False)):
        adjustment += 0.02

    balcony_area = _safe_numeric(getattr(asset, 'balcony_area', None))
    if balcony_area and balcony_area > 0:
        adjustment += 0.05
        if balcony_area >= 20:
            adjustment += 0.02
        elif balcony_area >= 10:
            adjustment += 0.01

    meta = getattr(asset, 'meta', {}) or {}
    if isinstance(meta, dict):
        garden_area = _safe_numeric(meta.get('garden_area')) or 0
        roof_space = _safe_numeric(meta.get('roof_space')) or 0
        if garden_area and garden_area > 0:
            adjustment += 0.1
        if roof_space and roof_space > 0:
            adjustment += 0.07

    return adjustment


def _finish_level_adjustment(asset: Any) -> float:
    meta = getattr(asset, 'meta', {}) or {}
    finish_level = str(meta.get('finish_level', '')).lower()
    renovation_state = str(meta.get('renovation_state', '')).lower()

    if _safe_bool(getattr(asset, 'renovated', False)) or finish_level in ('high', 'premium'):
        return 0.15
    if renovation_state in ('poor', 'needs_renovation'):
        return -0.15
    return 0.0


def _elevator_adjustment(asset: Any) -> float:
    floor = _safe_numeric(getattr(asset, 'floor', None))
    has_elevator = _safe_bool(getattr(asset, 'elevator', False))
    if has_elevator:
        return 0.06
    if floor is not None and floor >= 3:
        return -0.1
    return 0.0


def _proximity_adjustment(asset: Any) -> float:
    meta = getattr(asset, 'meta', {}) or {}
    adjustment = 0.0

    transit_distance = _safe_numeric(meta.get('distance_to_transit_m'))
    if isinstance(transit_distance, (int, float)):
        if transit_distance < 300:
            adjustment += 0.07
        elif transit_distance < 600:
            adjustment += 0.05

    beach_distance = _safe_numeric(meta.get('distance_to_beach_m'))
    if isinstance(beach_distance, (int, float)) and beach_distance < 600:
        adjustment += 0.12

    return adjustment


def _noise_adjustment(asset: Any) -> float:
    meta = getattr(asset, 'meta', {}) or {}
    nuisance_index = _safe_numeric(meta.get('nuisance_index'))
    if isinstance(nuisance_index, (int, float)):
        return -min(0.12, max(0.0, nuisance_index))

    road_distance = _safe_numeric(meta.get('distance_to_main_road_m'))
    if isinstance(road_distance, (int, float)) and road_distance < 80:
        return -0.08
    return 0.0


def _floor_adjustment(asset: Any) -> float:
    floor = _safe_numeric(getattr(asset, 'floor', None))
    meta = getattr(asset, 'meta', {}) or {}
    garden_area = _safe_numeric(meta.get('garden_area')) or 0

    if floor is None:
        return 0.0
    if floor == 0:
        return 0.1 if garden_area else -0.07
    if floor == 1:
        return -0.02
    if 3 <= floor <= 7:
        return 0.04
    if floor > 7:
        return 0.1
    return 0.0


def _build_feature_vector(asset: Any) -> FeatureVector:
    size = _safe_numeric(getattr(asset, 'total_area', None)) or _safe_numeric(getattr(asset, 'area', None))
    return FeatureVector(
        size_factor=_size_adjustment(size),
        age_factor=_age_adjustment(getattr(asset, 'year_built', None)),
        potential_factor=_potential_adjustment(asset),
        new_build_factor=_new_build_adjustment(asset),
        attachments_factor=_attachments_adjustment(asset),
        finish_level_factor=_finish_level_adjustment(asset),
        elevator_factor=_elevator_adjustment(asset),
        proximity_factor=_proximity_adjustment(asset),
        noise_factor=_noise_adjustment(asset),
        floor_factor=_floor_adjustment(asset),
    )


def update_asset_with_collected_data(asset_id: int, block: str, parcel: str, govmap_autocomplete_data: Dict[str, Any], govmap_data: Dict[str, Any], gis_data: Dict[str, Any], gov_data: Dict[str, Any], plans: List[Dict[str, Any]], mavat_plans: List[Dict[str, Any]], handasa_archive: List[Dict[str, Any]], listings: Iterable[Any], x_itm: Optional[float] = None, y_itm: Optional[float] = None, lon_wgs84: Optional[float] = None, lat_wgs84: Optional[float] = None, subparcel: Optional[str] = None) -> None:
    """Update the Asset with collected enrichment data.

    Improvements:
    - Granular phase logging (use env ASSET_UPDATE_DEBUG=1 to raise on first failure)
    - Smaller try blocks: a failure in one enrichment source no longer hides stack traces
    - Structured debug logs with timing per phase
    """
    # Defensive: ensure all dicts/lists are not None
    govmap_autocomplete_data = govmap_autocomplete_data or {}
    govmap_data = govmap_data or {}
    gis_data = gis_data or {}
    gov_data = gov_data or {}
    plans = plans or []
    mavat_plans = mavat_plans or []
    handasa_archive = handasa_archive or []
    listings = listings or []

    # Lazy Django setup (kept inside function so unit tests without Django still work)
    with asset_update_phase("django_setup", asset_id):
        import os as _os
        import sys as _sys
        backend_path = _os.path.join(_os.path.dirname(__file__), "..", "backend-django")
        if backend_path not in _sys.path:
            _sys.path.insert(0, backend_path)
        import django  # type: ignore
        from django.conf import settings as _settings  # type: ignore
        if not _settings.configured:
            _os.environ.setdefault("DJANGO_SETTINGS_MODULE", "broker_backend.settings")
            django.setup()
        from core.models import Asset  # type: ignore

    # Load asset
    try:
        asset = Asset.objects.get(id=asset_id)
    except Exception as e:  # noqa: BLE001
        logger.exception("[ASSET_UPDATE] Failed to load Asset id=%s: %s", asset_id, e)
        return

    # Basic identifiers & coordinates -------------------------------------------------
    with asset_update_phase("basic_fields", asset_id):
        if block:
            asset.block = block
        if parcel:
            asset.parcel = parcel
        if subparcel:
            asset.subparcel = subparcel
        
        # Helper function to check if coordinates are valid (within Israel bounds)
        def is_valid_israel_coords(lat, lon):
            """Check if coordinates are within Israel bounds."""
            if lat is None or lon is None:
                return False
            # Israel bounds: lat 29-34.8, lon 33-36.5
            return 29 <= lat <= 34.8 and 33 <= lon <= 36.5
        
        # Check if current coordinates are invalid (None or out of bounds)
        current_coords_valid = is_valid_israel_coords(asset.lat, asset.lon)
        
        # Prefer GovMap coordinates from parcel addresses (most accurate)
        # Check if GovMap provided addresses with coordinates (from get_parcel_addresses)
        govmap_addresses = govmap_data.get('addresses', [])
        if govmap_addresses:
            # Use coordinates from the first matching address (most specific)
            first_addr = govmap_addresses[0]
            addr_x = first_addr.get('x')
            addr_y = first_addr.get('y')
            if addr_x is not None and addr_y is not None:
                try:
                    addr_lon, addr_lat = itm_to_wgs84(addr_x, addr_y)
                    # Always update if current coords are invalid, otherwise only if None
                    if not current_coords_valid or asset.lat is None or asset.lon is None:
                        asset.lat = addr_lat
                        asset.lon = addr_lon
                        logger.debug("Asset %s coordinates set from GovMap parcel addresses WGS84 (lat=%.8f lon=%.8f)", asset_id, addr_lat, addr_lon)
                except Exception as e:
                    logger.warning("Failed to convert GovMap parcel address coordinates for asset %s: %s", asset_id, e)
        
        # Fallback: Use provided WGS84 coordinates (from data pipeline conversion)
        if (not current_coords_valid or asset.lat is None or asset.lon is None) and lon_wgs84 is not None and lat_wgs84 is not None:
            if is_valid_israel_coords(lat_wgs84, lon_wgs84):
                asset.lat = lat_wgs84
                asset.lon = lon_wgs84
                logger.debug("Asset %s coordinates set from GovMap WGS84 (lat=%.8f lon=%.8f)", asset_id, lat_wgs84, lon_wgs84)
        elif (not current_coords_valid or asset.lat is None or asset.lon is None) and gis_data.get('x') and gis_data.get('y'):
            try:
                lon_wgs84_gis, lat_wgs84_gis = itm_to_wgs84(gis_data.get('x'), gis_data.get('y'))
                asset.lat = lat_wgs84_gis
                asset.lon = lon_wgs84_gis
                logger.debug("Asset %s coordinates converted from GIS ITM -> WGS84", asset_id)
            except Exception:
                logger.exception("Failed to convert GIS coordinates for asset %s; storing raw ITM", asset_id)
                asset.lat = gis_data.get('x')
                asset.lon = gis_data.get('y')
        # Update street/city from GovMap addresses first (broader coverage)
        if govmap_data.get('addresses') and not getattr(asset, 'street', None):
            addresses = govmap_data.get('addresses', [])
            if addresses:
                # Use the first address found
                first_address = addresses[0]
                asset.street = first_address.get('street', '')
                asset.number = first_address.get('house_number')
                asset.city = first_address.get('city', '')
                logger.info(f"Updated asset {asset_id} with street from GovMap: {asset.street}, number: {asset.number}, city: {asset.city}")
        
        # Fallback: Update city from GovMap data directly if available and asset doesn't have city
        if govmap_data.get('city') and not getattr(asset, 'city', None):
            asset.city = govmap_data.get('city', '')
            logger.info(f"Updated asset {asset_id} with city from GovMap data: {asset.city}")
        
        # Update street/city from GIS addresses if found and asset doesn't have them (Tel Aviv specific)
        if gis_data.get('addresses') and not getattr(asset, 'street', None):
            addresses = gis_data.get('addresses', [])
            if addresses:
                # Use the first address found
                first_address = addresses[0]
                asset.street = first_address.get('street', '')
                asset.number = first_address.get('house_number')
                asset.city = first_address.get('city', '')
                logger.info(f"Updated asset {asset_id} with street from GIS: {asset.street}, number: {asset.number}, city: {asset.city}")
        
        # Fallback: Update city from GIS data directly if available and asset doesn't have city
        if gis_data.get('city') and not getattr(asset, 'city', None):
            asset.city = gis_data.get('city', '')
            logger.info(f"Updated asset {asset_id} with city from GIS data: {asset.city}")
        
        # Also update the normalized_address field if GovMap provided a detailed address
        if govmap_data.get('address') and govmap_data.get('address') != f"גוש {block} חלקה {parcel}":
            # Only update if it's not the generic block/parcel format
            asset.normalized_address = govmap_data.get('address')
            logger.info(f"Updated asset {asset_id} normalized_address field from GovMap: {asset.normalized_address}")
        
        if getattr(asset, 'street', None) and getattr(asset, 'number', None):
            asset.normalized_address = f"{asset.street} {asset.number}" + (f" דירה {asset.apartment}" if getattr(asset, 'apartment', None) else '') + (f" {asset.city}" if getattr(asset, 'city', None) else '')
        if not asset.meta:
            asset.meta = {}

    # Check if city is Tel Aviv (GIS and Handasa only support Tel Aviv)
    city = getattr(asset, 'city', '') or ''
    is_tel_aviv = 'תל אביב' in city

    # GIS processing ------------------------------------------------------------------
    with asset_update_phase("process_gis", asset_id):
        if not is_tel_aviv:
            logger.info(f"Asset {asset_id}: Skipping GIS processing (not Tel Aviv)")
        else:
            logger.info(f"Asset {asset_id}: GIS processing - gis_data exists: {bool(gis_data)}, keys: {list(gis_data.keys()) if gis_data else 'None'}")
            if gis_data:
                asset.meta['gis_data'] = {
                    'permits': gis_data.get('permits', []),
                    'rights': gis_data.get('rights', []),
                    'shelters': gis_data.get('shelters', []),
                    'green_areas': gis_data.get('green', []),
                    'noise_levels': gis_data.get('noise', []),
                    'cell_antennas': gis_data.get('antennas', []),
                    'blocks': gis_data.get('blocks', []),
                    'parcels': gis_data.get('parcels', []),
                    'coordinates': {'x': gis_data.get('x'), 'y': gis_data.get('y')},
                }
            else:
                logger.info(f"Asset {asset_id}: No GIS data available for processing")
            if handasa_archive:
                asset.meta['handasa_archive'] = handasa_archive
            existing_privilege_data = asset.meta.get('privilege_page_data')

            try:
                from gis.gis_client import TelAvivGS  # type: ignore

                def _extract_coord(data, key):
                    if isinstance(data, dict):
                        if data.get(key) is not None:
                            return data.get(key)
                        coords = data.get('coordinates')
                        if isinstance(coords, dict):
                            return coords.get(key)
                    return None

                x = (
                    _extract_coord(gis_data, 'x')
                    or _extract_coord(asset.meta.get('gis_data'), 'x')
                    or _extract_coord(govmap_data, 'x')
                )
                y = (
                    _extract_coord(gis_data, 'y')
                    or _extract_coord(asset.meta.get('gis_data'), 'y')
                    or _extract_coord(govmap_data, 'y')
                )

                if x is not None and y is not None:
                    gis_client = TelAvivGS()
                    privilege_data = gis_client.get_building_privilege_page(x, y, save_dir="privilege_pages")
                    if privilege_data and isinstance(privilege_data, dict):
                        parsed_items = []
                        pdf_entries = privilege_data.get('pdf_data') or []
                        for pdf_item in pdf_entries:
                            if isinstance(pdf_item, dict) and pdf_item.get('data'):
                                parsed_items.append(pdf_item['data'])
                        if parsed_items:
                            asset.meta['privilege_page_data'] = parsed_items
                            asset.meta['privilege_page_refreshed_at'] = datetime.utcnow().isoformat()
                        elif existing_privilege_data is not None:
                            # Keep previously stored privilege data if refresh yielded nothing
                            asset.meta['privilege_page_data'] = existing_privilege_data
            except Exception:
                logger.debug("Privilege page acquisition failed for asset %s", asset_id, exc_info=True)
            
            # Always process GIS data (even if empty) to store gis_collector_data
            _process_gis_data(asset, gis_data)

    # GovMap autocomplete --------------------------------------------------------------
    with asset_update_phase("process_govmap_autocomplete", asset_id):
        if govmap_autocomplete_data:
            asset.meta['govmap_autocomplete_data'] = {
                'autocomplete_result': govmap_autocomplete_data,
                'coordinates': {
                    'x_itm': x_itm,
                    'y_itm': y_itm,
                    'lon_wgs84': lon_wgs84,
                    'lat_wgs84': lat_wgs84,
                },
            }
            _process_govmap_autocomplete_data(asset, govmap_autocomplete_data)

    # GovMap parcel -------------------------------------------------------------------
    with asset_update_phase("process_govmap_parcel", asset_id):
        if govmap_data:
            asset.meta['govmap_data'] = {
                'parcel': govmap_data.get('api_data', {}).get('parcel', {}),
                'nearby_layers': govmap_data.get('nearby', {}),
                'coordinates': {'x': govmap_data.get('x'), 'y': govmap_data.get('y')},
                'api_data': govmap_data.get('api_data', {}),
            }
            _process_govmap_data(asset, govmap_data)

    # Government data -----------------------------------------------------------------
    with asset_update_phase("process_government", asset_id):
        if gov_data:
            asset.meta['government_data'] = {
                'decisive_appraisals': gov_data.get('decisive', []),
                'transaction_history': gov_data.get('transactions', []),
            }
            _process_government_data(asset, gov_data)
            
            # Extract neighborhood from transaction data
            _extract_neighborhood_from_transactions(asset, gov_data.get('transactions', []))

    # RAMI plans ----------------------------------------------------------------------
    with asset_update_phase("process_rami", asset_id):
        if plans:
            asset.meta['rami_plans'] = plans
            _process_rami_plans(asset, plans)

    # Mavat plans ---------------------------------------------------------------------
    with asset_update_phase("process_mavat", asset_id):
        if mavat_plans:
            asset.meta['mavat_plans'] = mavat_plans
            _process_mavat_plans(asset, mavat_plans)

    # Yad2 and Madlan listings ---------------------------------------------------------
    normalized_listings = []
    with asset_update_phase("normalize_listings", asset_id):
        normalized_listings = _normalize_listings(listings or [])
        if listings and not normalized_listings:
            logger.debug("All listings dropped while normalizing listing data for asset %s", asset_id)
        if normalized_listings:
            # Store all listings (both Yad2 and Madlan) in meta
            asset.meta['yad2_listings'] = normalized_listings  # Keep key for backward compatibility
            
            # Populate asset fields from listings (Yad2 preferred, Madlan as fallback)
            _populate_asset_fields_from_listings(asset, normalized_listings)
            
            prices = [listing.get('price') for listing in normalized_listings if listing.get('price')]
            areas = [listing.get('area') for listing in normalized_listings if listing.get('area')]
            market_data = asset.meta.setdefault('market_data', {})
            if prices:
                market_data.update({
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'avg_price': sum(prices) / len(prices),
                    'price_count': len(prices),
                })
            if areas:
                market_data.update({
                    'min_area': min(areas),
                    'max_area': max(areas),
                    'avg_area': sum(areas) / len(areas),
                    'area_count': len(areas),
                })
            if not market_data:
                asset.meta.pop('market_data', None)

    # Building rights calculation (after Yad2 to ensure area data is available)
    with asset_update_phase("calculate_building_rights", asset_id):
        if is_tel_aviv:
            _calculate_building_rights(asset, gis_data)
        else:
            logger.info(f"Asset {asset_id}: Skipping building rights calculation (not Tel Aviv)")
            _calculate_building_rights(asset, {})

    # Timestamp -----------------------------------------------------------------------
    with asset_update_phase("timestamp_and_save", asset_id):
        asset.meta['last_enrichment'] = timezone.now().isoformat()
        asset.save()

    # Django records ------------------------------------------------------------------
    with asset_update_phase("create_django_records", asset_id):
        _create_django_records_from_collected_data(
            asset,
            govmap_autocomplete_data,
            govmap_data,
            gis_data,
            gov_data,
            plans,
            mavat_plans,
            normalized_listings,
        )

    # Documents & plans ---------------------------------------------------------------
    with asset_update_phase("create_documents_and_plans", asset_id):
        # Skip handasa for non-Tel Aviv cities (only supported for Tel Aviv)
        handasa_to_process = handasa_archive if is_tel_aviv else []
        if not is_tel_aviv and handasa_archive:
            logger.info(f"Asset {asset_id}: Skipping Handasa processing (not Tel Aviv)")
        _create_documents_and_plans(asset, gis_data if is_tel_aviv else {}, gov_data, plans, mavat_plans, handasa_to_process)

    # Market metrics ------------------------------------------------------------------
    with asset_update_phase("calculate_market_metrics", asset_id):
        _calculate_market_metrics(asset, normalized_listings, gov_data)

    # Planning and Legal Analysis -----------------------------------------------------
    with asset_update_phase("calculate_planning_legal_analysis", asset_id):
        if is_tel_aviv:
            _calculate_planning_legal_analysis(asset, gis_data, gov_data)
        else:
            logger.info(f"Asset {asset_id}: Skipping planning and legal analysis (not Tel Aviv)")
            _calculate_planning_legal_analysis(asset, {}, gov_data)

    logger.info("Updated asset %s with block=%s, parcel=%s, subparcel=%s", asset_id, block, parcel, subparcel)


def create_asset_snapshot(asset_id: int, results: List[Any]) -> None:
    """Create a snapshot of asset data for alert evaluation."""
    try:
        import os
        import sys
        
        # Add Django backend to path
        backend_path = os.path.join(os.path.dirname(__file__), "..", "backend-django")
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        import django
        if not django.conf.settings.configured:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "broker_backend.settings")
            django.setup()
        
        from core.models import Asset, Snapshot
        
        asset = Asset.objects.get(id=asset_id)
        
        # Extract relevant data from results
        payload = {
            'price': asset.price,
            'price_per_sqm': asset.price_per_sqm,
            'area': asset.area,
            'rooms': asset.rooms,
            'permit_status': asset.permit_status,
            'permit_date': asset.permit_date.isoformat() if asset.permit_date else None,
            'documents': [],  # This would be populated from source records
            'gov_transactions': [],  # This would be populated from gov data
            'listing_id': None,  # This would be populated from Yad2 data
        }
        
        # Add data from results
        for result in results:
            if isinstance(result, dict):
                source = result.get('source')
                if source in ('yad2', 'madlan'):
                    # Extract listing data from Yad2 or Madlan
                    listing_data = result.get('data', {})
                    if hasattr(listing_data, 'listing_id'):
                        payload['listing_id'] = listing_data.listing_id
                    elif isinstance(listing_data, dict) and listing_data.get('listing_id'):
                        payload['listing_id'] = listing_data.get('listing_id')
                elif result.get('source') == 'transactions':
                    # Extract transaction data
                    payload['gov_transactions'] = result.get('data', [])
                elif result.get('source') == 'gis':
                    # Extract GIS data
                    gis_data = result.get('data', {})
                    if gis_data:
                        payload.update({
                            'blocks': gis_data.get('blocks', []),
                            'parcels': gis_data.get('parcels', []),
                            'permits': gis_data.get('permits', []),
                            'rights': gis_data.get('rights', []),
                            'shelters': gis_data.get('shelters', []),
                            'green': gis_data.get('green', []),
                            'noise': gis_data.get('noise', []),
                            'antennas': gis_data.get('antennas', []),
                            'block': gis_data.get('block', ''),
                            'parcel': gis_data.get('parcel', ''),
                            'x': gis_data.get('x'),
                            'y': gis_data.get('y')
                        })
                elif result.get('source') == 'gov_rami':
                    # Extract RAMI plans data
                    payload['rami_plans'] = result.get('data', [])
                elif result.get('source') == 'mavat':
                    # Extract Mavat plans data
                    payload['mavat_plans'] = result.get('data', [])
            elif hasattr(result, 'listing_id'):
                # Direct Yad2 listing object
                payload['listing_id'] = result.listing_id
                if hasattr(result, 'price'):
                    payload['price'] = result.price
                if hasattr(result, 'rooms'):
                    payload['rooms'] = result.rooms
                if hasattr(result, 'size'):
                    payload['area'] = result.size
        
        # Create snapshot
        Snapshot.objects.create(
            asset=asset,
            payload=payload,
            ppsqm=asset.price_per_sqm
        )
        
        logger.info("Created snapshot for asset %s", asset_id)
        
    except Exception as e:
        logger.error("Failed to create snapshot for asset %s: %s", asset_id, e)


def _process_gis_data(asset, gis_data):
    """Process GIS data and store using unified metadata structure."""
    logger.info(f"Asset {asset.id}: _process_gis_data called with gis_data keys: {list(gis_data.keys()) if gis_data else 'None/empty'}")
    
    # Store the complete GIS collector data in metadata
    asset.meta['gis_collector_data'] = gis_data
    logger.info(f"Asset {asset.id}: Stored gis_collector_data in metadata")
    
    # Extract parcel information (NOT total area - that's the building's area, not land area)
    if gis_data.get('parcels'):
        parcels = gis_data.get('parcels', [])
        if parcels:
            # Extract parcel information
            parcel_data = parcels[0]
            asset.set_property('parcelArea', parcel_data.get('ms_shetach'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('parcelRegisteredArea', parcel_data.get('ms_shetach_rashum'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('parcelStatus', parcel_data.get('t_status_hesder'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('parcelAccuracy', parcel_data.get('k_dargat_diyuk'), source='GIS', url='https://www.govmap.gov.il/')
            
            # Map to direct model fields
            asset.parcel_area = parcel_data.get('ms_shetach')
            asset.parcel_registered_area = parcel_data.get('ms_shetach_rashum')
            asset.parcel_status = parcel_data.get('t_status_hesder')
            asset.parcel_accuracy = parcel_data.get('k_dargat_diyuk')
    
    # Process blocks data
    if gis_data.get('blocks'):
        blocks = gis_data.get('blocks', [])
        if blocks:
            block_data = blocks[0]
            asset.set_property('blockArea', block_data.get('ms_shetach'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('blockRegisteredArea', block_data.get('ms_shetach_rashum'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('blockTotalParcels', block_data.get('ms_mispar_chelkot'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('blockStatus', block_data.get('t_status_hesder'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('blockLastUpdate', block_data.get('tr_idkun_acharon'), source='GIS', url='https://www.govmap.gov.il/')
            
            # Map to direct model fields
            asset.block_area = block_data.get('ms_shetach')
            asset.block_registered_area = block_data.get('ms_shetach_rashum')
            asset.block_total_parcels = block_data.get('ms_mispar_chelkot')
            asset.block_status = block_data.get('t_status_hesder')
            asset.block_last_update = block_data.get('tr_idkun_acharon')
    
    # Process addresses data (using existing fields)
    if gis_data.get('addresses'):
        addresses = gis_data.get('addresses', [])
        if addresses:
            address_data = addresses[0]
            asset.set_property('street', address_data.get('street'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('number', address_data.get('house_number'), source='GIS', url='https://www.govmap.gov.il/')
            # Convert ITM coordinates to WGS84 for lat/lon
            if address_data.get('x') and address_data.get('y'):
                try:
                    from govmap.api_client import itm_to_wgs84
                    lon_wgs84, lat_wgs84 = itm_to_wgs84(address_data.get('x'), address_data.get('y'))
                    asset.set_property('lat', lat_wgs84, source='GIS', url='https://www.govmap.gov.il/')
                    asset.set_property('lon', lon_wgs84, source='GIS', url='https://www.govmap.gov.il/')
                except Exception as e:
                    logger.debug(f"Failed to convert ITM coordinates: {e}")
    
    # Store summary coordinates if available
    if gis_data.get('x') and gis_data.get('y'):
        asset.set_property('gisCoordinates', {'x': gis_data.get('x'), 'y': gis_data.get('y')}, source='GIS', url='https://www.govmap.gov.il/')
    
    if gis_data.get('city'):
        asset.set_property('city', gis_data.get('city'), source='GIS', url='https://www.govmap.gov.il/')
    
    # Noise levels
    if gis_data.get('noise'):
        noise_levels = gis_data.get('noise', [])
        if noise_levels:
            max_noise = max([n.get('isov3', 0) for n in noise_levels if isinstance(n, dict)])
            asset.set_property('noiseLevel', max_noise, source='GIS', url='https://www.govmap.gov.il/')
    
    # Land use rights and zoning
    if gis_data.get('rights'):
        rights = gis_data.get('rights', [])
        if rights:
            main_rights = rights[0]
            # Map the correct field names from GIS rights data
            land_use_designation = main_rights.get('t_yeud_karka', '')  # ייעוד קרקע
            main_designation = main_rights.get('t_yeud_rashi', '')      # ייעוד ראשי
            asset.set_property('zoning', land_use_designation, source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('program', main_designation, source='GIS', url='https://www.govmap.gov.il/')

    # Building permits - Enhanced processing for GIS collector data
    if gis_data.get('permits'):
        permits = gis_data.get('permits', [])
        if permits:
            # Store all permits data
            asset.set_property('totalPermits', len(permits), source='GIS', url='https://www.govmap.gov.il/')
            asset.total_permits = len(permits)
            
            # Process the most recent permit
            recent_permit = permits[0] if permits else {}
            
            # Extract comprehensive permit information
            asset.set_property('permitRequestNum', recent_permit.get('request_num'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitPermissionNum', recent_permit.get('permission_num'), source='GIS', url='https://www.govmap.gov.il/')
            
            # Map to direct model fields
            asset.permit_request_num = recent_permit.get('request_num')
            asset.permit_permission_num = recent_permit.get('permission_num')
            asset.set_property('permitBuildingNum', recent_permit.get('building_num'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitHousingUnits', recent_permit.get('yechidot_diyur'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitCommercialArea', recent_permit.get('mischar_shetach'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitResidentialArea', recent_permit.get('megurim_shetach'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitResidentialUnits', recent_permit.get('megurim_yechidot'), source='GIS', url='https://www.govmap.gov.il/')
            
            # Map to direct model fields
            asset.permit_building_num = recent_permit.get('building_num')
            asset.permit_housing_units = recent_permit.get('yechidot_diyur')
            asset.permit_commercial_area = recent_permit.get('mischar_shetach')
            asset.permit_residential_area = recent_permit.get('megurim_shetach')
            asset.permit_residential_units = recent_permit.get('megurim_yechidot')
            asset.set_property('permitPublicArea', recent_permit.get('mivney_tzibur_shetach'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitParkingArea', recent_permit.get('melonaut_shetach'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitParkingUnits', recent_permit.get('melonaut_yechidot'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitSmallApartments', recent_permit.get('dirot_ktanot'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitUnifiedHousingArea', recent_permit.get('diyur_meuchad_shetach'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitUnifiedHousingUnits', recent_permit.get('diyur_meuchad_yechidot'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitAccessibleApartments', recent_permit.get('dirot_haskara'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitPublicBuiltArea', recent_permit.get('tziburi_banuy_shetach'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitTotalArea', recent_permit.get('sach_shetach'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitMavatPlanNum', recent_permit.get('mispar_tochnit_mavat'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitParkingRoomsCalculated', recent_permit.get('melonaut_rooms_mechushav'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitFullUtilization', recent_permit.get('sw_mimush_male'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitSubjectType', recent_permit.get('sug_nose'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitProcess', recent_permit.get('maslul'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitRightsNotification', recent_permit.get('sw_niyud_zchuyot'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitRepartition', recent_permit.get('sw_repartzelatzya'), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('permitUrbanRenewal', recent_permit.get('sw_hitchadshut_ironit'), source='GIS', url='https://www.govmap.gov.il/')
            
            # Handle dates
            if recent_permit.get('permission_date'):
                try:
                    permit_date = datetime.fromtimestamp(recent_permit['permission_date'] / 1000)
                    asset.set_property('permitDate', permit_date.date().isoformat(), source='GIS', url='https://www.govmap.gov.il/')
                except Exception as e:
                    logger.debug(f"Failed to parse permit date: {e}")
            
            if recent_permit.get('open_request'):
                try:
                    open_request_date = datetime.fromtimestamp(recent_permit['open_request'] / 1000)
                    asset.set_property('permitOpenRequestDate', open_request_date.date().isoformat(), source='GIS', url='https://www.govmap.gov.il/')
                except Exception as e:
                    logger.debug(f"Failed to parse open request date: {e}")
            
            if recent_permit.get('tr_hathalat_bniya'):
                try:
                    construction_start_date = datetime.fromtimestamp(recent_permit['tr_hathalat_bniya'] / 1000)
                    asset.set_property('permitConstructionStartDate', construction_start_date.date().isoformat(), source='GIS', url='https://www.govmap.gov.il/')
                except Exception as e:
                    logger.debug(f"Failed to parse construction start date: {e}")
            
            # Store permit status
            asset.set_property('permitStatus', recent_permit.get('building_stage', ''), source='GIS', url='https://www.govmap.gov.il/')
            
            # Create documents from permits
            _create_documents_from_permits(asset, permits)

    # Green areas
    if gis_data.get('green'):
        green_areas = gis_data.get('green', [])
        asset.set_property('greenWithin300m', len(green_areas) > 0, source='GIS', url='https://www.govmap.gov.il/')

    # Shelters
    if gis_data.get('shelters'):
        shelters = gis_data.get('shelters', [])
        if shelters and len(shelters) > 0:
            distance_values = [s.get('distance') for s in shelters if isinstance(s, dict) and s.get('distance') is not None]
            if distance_values:
                min_distance = min(distance_values)
                asset.set_property('shelterDistanceM', min_distance, source='GIS', url='https://www.govmap.gov.il/')
    
    # Cell antennas
    if gis_data.get('antennas'):
        antennas = gis_data.get('antennas', [])
        if antennas and len(antennas) > 0:
            distance_values = [a.get('distance') for a in antennas if isinstance(a, dict) and a.get('distance') is not None]
            if distance_values:
                min_distance = min(distance_values)
                asset.set_property('antennaDistanceM', min_distance, source='GIS', url='https://www.govmap.gov.il/')
    
    # Environmental fields
    asset.set_property('publicTransport', 'קרוב לתחבורה ציבורית', source='GIS (calculated)', url='https://www.govmap.gov.il/')
    
    # Get greenWithin300m value for conditional logic
    green_within_300m = asset.get_property_value('greenWithin300m')
    green_amenities_count = asset.get_property_value('greenAmenitiesCount') or 0
    bike_paths_count = asset.get_property_value('bikePathsCount') or 0
    
    # Enhanced green indicators calculation
    green_indicators = []
    if green_within_300m:
        green_indicators.append('פארקים ושטחים פתוחים')
    if green_amenities_count > 0:
        green_indicators.append(f'מתקני נופש ירוקים ({green_amenities_count})')
    if bike_paths_count > 0:
        green_indicators.append(f'שבילי אופניים ({bike_paths_count})')
    
    if green_indicators:
        asset.set_property('openSpacesNearby', ', '.join(green_indicators), source='GIS (calculated)', url='https://www.govmap.gov.il/')
        asset.set_property('greenScore', 'גבוה' if len(green_indicators) >= 2 else 'בינוני', source='GIS (calculated)', url='https://www.govmap.gov.il/')
    else:
        asset.set_property('openSpacesNearby', 'אין שטחים פתוחים קרובים', source='GIS (calculated)', url='https://www.govmap.gov.il/')
        asset.set_property('greenScore', 'נמוך', source='GIS (calculated)', url='https://www.govmap.gov.il/')
    
    # Calculate public buildings based on available infrastructure
    public_buildings_text = _calculate_public_buildings(gis_data, asset)
    asset.set_property('publicBuildings', public_buildings_text, source='GIS (calculated)', url='https://www.govmap.gov.il/')
    
    # Calculate parking availability based on permits and land use
    parking_text = _calculate_parking_availability(gis_data, asset)
    asset.set_property('parking', parking_text, source='GIS (calculated)', url='https://www.govmap.gov.il/')
    
    # Calculate nearby projects based on recent permits and plans
    nearby_projects_text = _calculate_nearby_projects(gis_data, asset)
    asset.set_property('nearbyProjects', nearby_projects_text, source='GIS (calculated)', url='https://www.govmap.gov.il/')
    
    # Additional planning fields - will be calculated in _process_rami_plans
    # These are set as defaults here, but will be overridden if RAMI data is available
    asset.set_property('additionalPlanRights', 'אין זכויות נוספות', source='GIS (calculated)', url='https://www.govmap.gov.il/')
    asset.set_property('publicObligations', 'אין חובות ציבוריות', source='GIS (calculated)', url='https://www.govmap.gov.il/')
    
    # Permit quarter (extract from permit data)
    if gis_data.get('permits'):
        permits = gis_data.get('permits', [])
        if permits:
            recent_permit = permits[0] if permits else {}
            if recent_permit.get('permission_date'):
                try:
                    permit_date = datetime.fromtimestamp(recent_permit['permission_date'] / 1000)
                    quarter = f"Q{(permit_date.month - 1) // 3 + 1}/{permit_date.year}"
                    asset.set_property('lastPermitQ', quarter, source='GIS', url='https://www.govmap.gov.il/')
                except Exception as e:
                    logger.debug(f"Failed to parse permit date: {e}")
                    pass
    
    # Metro stations - Major value driver
    if gis_data.get('metro_stations'):
        metro_stations = gis_data.get('metro_stations', [])
        if metro_stations and len(metro_stations) > 0:
            distances = [s.get('distance') for s in metro_stations if isinstance(s, dict) and s.get('distance')]
            if distances:
                min_distance = min(distances)
                asset.set_property('metroStationDistanceM', min_distance, source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('metroStationsCount', len(metro_stations), source='GIS', url='https://www.govmap.gov.il/')
    
    # Parking lots
    parking_lots = gis_data.get('parking_lots')
    if parking_lots:
        asset.set_property('parkingLotsCount', len(parking_lots), source='GIS', url='https://www.govmap.gov.il/')
        public_parking = [p for p in parking_lots if isinstance(p, dict) and p.get('type') == 'public']
        if public_parking:
            asset.set_property('publicParkingLotsCount', len(public_parking), source='GIS', url='https://www.govmap.gov.il/')
    
    # Schools and kindergartens
    schools = gis_data.get('schools')
    if schools:
        asset.set_property('schoolsCount', len(schools), source='GIS', url='https://www.govmap.gov.il/')
        distances = [s.get('distance') for s in schools if isinstance(s, dict) and s.get('distance')]
        if distances:
            min_distance = min(distances)
            asset.set_property('nearestSchoolDistanceM', min_distance, source='GIS', url='https://www.govmap.gov.il/')
    
    # Construction sites - indicates redevelopment intensity
    if gis_data.get('construction_sites'):
        construction_sites = gis_data.get('construction_sites', [])
        if construction_sites:
            asset.set_property('constructionSitesCount', len(construction_sites), source='GIS', url='https://www.govmap.gov.il/')
    
    # Affordable housing projects - indicates supply pressure
    if gis_data.get('affordable_housing'):
        affordable_housing = gis_data.get('affordable_housing', [])
        if affordable_housing:
            asset.set_property('affordableHousingProjectsCount', len(affordable_housing), source='GIS', url='https://www.govmap.gov.il/')
    
    # Bike paths - walkability indicator
    bike_paths = gis_data.get('bike_paths')
    if bike_paths:
        asset.set_property('bikePathsCount', len(bike_paths), source='GIS', url='https://www.govmap.gov.il/')
        asset.set_property('hasBikePaths', True, source='GIS', url='https://www.govmap.gov.il/')
    
    # Soil contamination - risk factor
    if gis_data.get('soil_contamination'):
        soil_contamination = gis_data.get('soil_contamination', [])
        if soil_contamination and len(soil_contamination) > 0:
            asset.set_property('soilContaminationSitesCount', len(soil_contamination), source='GIS', url='https://www.govmap.gov.il/')
            distances = [s.get('distance') for s in soil_contamination if isinstance(s, dict) and s.get('distance')]
            if distances:
                min_distance = min(distances)
                asset.set_property('nearestSoilContaminationDistanceM', min_distance, source='GIS', url='https://www.govmap.gov.il/')
    
    # Green amenities (playgrounds, dog parks, public gardens)
    if gis_data.get('green_amenities'):
        green_amenities = gis_data.get('green_amenities', [])
        if green_amenities:
            asset.set_property('greenAmenitiesCount', len(green_amenities), source='GIS', url='https://www.govmap.gov.il/')
            playgrounds = [g for g in green_amenities if isinstance(g, dict) and 'playground' in str(g.get('type', '')).lower()]
            asset.set_property('playgroundsCount', len(playgrounds), source='GIS', url='https://www.govmap.gov.il/')
    
    # Medical facilities
    medical_facilities = gis_data.get('medical_facilities')
    if medical_facilities:
        asset.set_property('medicalFacilitiesCount', len(medical_facilities), source='GIS', url='https://www.govmap.gov.il/')
        distances = [m.get('distance') for m in medical_facilities if isinstance(m, dict) and m.get('distance')]
        if distances:
            min_distance = min(distances)
            asset.set_property('nearestMedicalFacilityDistanceM', min_distance, source='GIS', url='https://www.govmap.gov.il/')
    
    # Community facilities
    community_facilities = gis_data.get('community_facilities')
    if community_facilities:
        asset.set_property('communityFacilitiesCount', len(community_facilities), source='GIS', url='https://www.govmap.gov.il/')
    
    # Dog parks
    dog_parks = gis_data.get('dog_parks')
    if dog_parks:
        asset.set_property('dogParksCount', len(dog_parks), source='GIS', url='https://www.govmap.gov.il/')
    
    # Public gardens
    public_gardens = gis_data.get('public_gardens')
    if public_gardens:
        asset.set_property('publicGardensCount', len(public_gardens), source='GIS', url='https://www.govmap.gov.il/')
    
    # Playgrounds (separate from green_amenities for more granular data)
    playgrounds = gis_data.get('playgrounds')
    if playgrounds:
        asset.set_property('playgroundsCount', len(playgrounds), source='GIS', url='https://www.govmap.gov.il/')
        # Also update if it was already set from green_amenities (use the larger value)
        existing_playgrounds = asset.get_property_value('playgroundsCount') or 0
        if len(playgrounds) > existing_playgrounds:
            asset.set_property('playgroundsCount', len(playgrounds), source='GIS', url='https://www.govmap.gov.il/')
    
    # Medical centers (separate from medical_facilities)
    medical_centers = gis_data.get('medical_centers')
    if medical_centers:
        asset.set_property('medicalCentersCount', len(medical_centers), source='GIS', url='https://www.govmap.gov.il/')
        distances = [m.get('distance') for m in medical_centers if isinstance(m, dict) and m.get('distance')]
        if distances:
            min_distance = min(distances)
            existing_distance = asset.get_property_value('nearestMedicalFacilityDistanceM')
            if existing_distance is None or min_distance < existing_distance:
                asset.set_property('nearestMedicalFacilityDistanceM', min_distance, source='GIS', url='https://www.govmap.gov.il/')
    
    # Health funds
    health_funds = gis_data.get('health_funds')
    if health_funds:
        asset.set_property('healthFundsCount', len(health_funds), source='GIS', url='https://www.govmap.gov.il/')
        distances = [h.get('distance') for h in health_funds if isinstance(h, dict) and h.get('distance')]
        if distances:
            min_distance = min(distances)
            existing_distance = asset.get_property_value('nearestMedicalFacilityDistanceM')
            if existing_distance is None or min_distance < existing_distance:
                asset.set_property('nearestMedicalFacilityDistanceM', min_distance, source='GIS', url='https://www.govmap.gov.il/')
    
    # Pharmacies
    pharmacies = gis_data.get('pharmacies')
    if pharmacies:
        asset.set_property('pharmaciesCount', len(pharmacies), source='GIS', url='https://www.govmap.gov.il/')
        distances = [p.get('distance') for p in pharmacies if isinstance(p, dict) and p.get('distance')]
        if distances:
            min_distance = min(distances)
            existing_distance = asset.get_property_value('nearestMedicalFacilityDistanceM')
            if existing_distance is None or min_distance < existing_distance:
                asset.set_property('nearestMedicalFacilityDistanceM', min_distance, source='GIS', url='https://www.govmap.gov.il/')
    
    # TAMA 38 key areas - potential for redevelopment
    tama38_areas = gis_data.get('tama38_key_areas')
    if tama38_areas:
        asset.set_property('tama38KeyArea', True, source='GIS', url='https://www.govmap.gov.il/')
        asset.set_property('tama38KeyAreasCount', len(tama38_areas), source='GIS', url='https://www.govmap.gov.il/')
    
    # Road works - disruption indicator
    road_works = gis_data.get('road_works')
    if road_works:
        asset.set_property('roadWorksCount', len(road_works), source='GIS', url='https://www.govmap.gov.il/')
        asset.set_property('hasActiveRoadWorks', True, source='GIS', url='https://www.govmap.gov.il/')
    
    # Risk flags - use get_property_value for unified access
    risk_flags = []
    noise_level = asset.get_property_value('noiseLevel') or 0
    if noise_level > 3:
        risk_flags.append('רעש גבוה')
    if not green_within_300m:
        risk_flags.append('אין שטחים פתוחים קרובים')
    shelter_distance = asset.get_property_value('shelterDistanceM')
    if shelter_distance and shelter_distance > 200:
        risk_flags.append('מרחק גדול ממקלט')
    antenna_distance = asset.get_property_value('antennaDistanceM')
    if antenna_distance and antenna_distance < 50:
        risk_flags.append('קרוב מדי לאנטנה')
    
    # Add new risk factors
    soil_contamination_count = asset.get_property_value('soilContaminationSitesCount') or 0
    if soil_contamination_count and soil_contamination_count > 0:
        nearest_contamination = asset.get_property_value('nearestSoilContaminationDistanceM')
        if nearest_contamination and nearest_contamination < 100:
            risk_flags.append('קרוב לאתר זיהום קרקע')
    
    road_works_count = asset.get_property_value('roadWorksCount') or 0
    if road_works_count and road_works_count > 0:
        risk_flags.append('עבודות כביש פעילות')
    
    asset.set_property('riskFlags', risk_flags, source='GIS (calculated)', url='https://www.govmap.gov.il/')
    
    # Calculate potential assessment indicators
    potential_indicators = []
    metro_distance = asset.get_property_value('metroStationDistanceM')
    if metro_distance and metro_distance <= 1000:
        if metro_distance <= 300:
            potential_indicators.append('קרוב מאוד לתחנת מטרו (פרימיום גבוה)')
        elif metro_distance <= 500:
            potential_indicators.append('קרוב לתחנת מטרו (פרימיום בינוני)')
        else:
            potential_indicators.append('בטווח של תחנת מטרו')
    
    schools_count = asset.get_property_value('schoolsCount') or 0
    if schools_count and schools_count > 0:
        nearest_school = asset.get_property_value('nearestSchoolDistanceM')
        if nearest_school and nearest_school <= 300:
            potential_indicators.append(f'קרוב לבתי ספר ({schools_count} בתי ספר וגנים)')
    
    tama38_key_area = asset.get_property_value('tama38KeyArea')
    if tama38_key_area:
        potential_indicators.append('באזור תמ״א 38 - פוטנציאל התחדשות עירונית')
    
    affordable_housing_count = asset.get_property_value('affordableHousingProjectsCount') or 0
    if affordable_housing_count and affordable_housing_count > 0:
        potential_indicators.append(f'פרויקטי דיור מועדף באזור ({affordable_housing_count}) - שינוי דמוגרפי צפוי')
    
    if potential_indicators:
        asset.set_property('investmentPotential', '; '.join(potential_indicators), source='GIS (calculated)', url='https://www.govmap.gov.il/')
        # Calculate potential score
        potential_score = 'גבוה'
        if len(potential_indicators) == 1:
            potential_score = 'בינוני'
        asset.set_property('investmentPotentialScore', potential_score, source='GIS (calculated)', url='https://www.govmap.gov.il/')
    else:
        asset.set_property('investmentPotential', 'אין אינדיקטורים מיוחדים לפוטנציאל', source='GIS (calculated)', url='https://www.govmap.gov.il/')
        asset.set_property('investmentPotentialScore', 'נמוך', source='GIS (calculated)', url='https://www.govmap.gov.il/')


def _calculate_building_rights(asset, gis_data):
    """
    Calculate building rights with area data from Yad2.
    
    This runs after Yad2 processing to ensure we have the most up-to-date
    area information for accurate rights calculations.
    """
    try:
        # Only calculate if we have rights data
        if not gis_data.get('rights'):
            return
        
        rights = gis_data.get('rights', [])
        if not rights:
            return
        
        # Use area from Yad2 (or existing data if Yad2 didn't have area)
        area_for_calculation = asset.total_area or asset.area
        
        # Try to get real building rights data
        remaining_rights_sqm = None
        source = 'GIS (calculated)'
        
        # Check if we have privilege page data
        privilege_data_list = asset.get_property_value('privilege_page_data')
        if privilege_data_list:
            # Handle both old single dict format and new list format
            if isinstance(privilege_data_list, list):
                # New list format - try each privilege page data
                for privilege_data in privilege_data_list:
                    if privilege_data:
                        try:
                            from gis.rights_calculator import get_remaining_rights_sqm
                            remaining_rights_sqm = get_remaining_rights_sqm(
                                privilege_data, 
                                area_for_calculation
                            )
                            if remaining_rights_sqm:
                                source = 'GIS (privilege page)'
                                break  # Use the first successful calculation
                        except Exception as e:
                            logger.debug(f"Failed to calculate rights from privilege page: {e}")
                            continue
            elif isinstance(privilege_data_list, dict):
                # Old single dict format - maintain backward compatibility
                try:
                    from gis.rights_calculator import get_remaining_rights_sqm
                    remaining_rights_sqm = get_remaining_rights_sqm(
                        privilege_data_list, 
                        area_for_calculation
                    )
                    if remaining_rights_sqm:
                        source = 'GIS (privilege page)'
                except Exception as e:
                    logger.debug(f"Failed to calculate rights from privilege page: {e}")
        
        asset.set_property('remainingRightsSqm', remaining_rights_sqm, source=source, url='https://www.govmap.gov.il/')
        asset.set_property('mainRightsSqm', int(area_for_calculation), source='GIS (calculated)', url='https://www.govmap.gov.il/')
        # Only calculate service rights if remaining_rights_sqm is not None
        service_rights_sqm = int(remaining_rights_sqm * 0.1) if remaining_rights_sqm is not None else None
        asset.set_property('serviceRightsSqm', service_rights_sqm, source='GIS (calculated)', url='https://www.govmap.gov.il/')
        
    except Exception as e:
        logger.debug(f"Failed to calculate building rights: {e}")


def _process_government_data(asset, gov_data):
    """Process government data using unified metadata structure."""
    # Transaction data
    if gov_data.get('transactions'):
        transactions = gov_data.get('transactions', [])
        asset.set_property('competition1km', len(transactions), source='Nadlan', url='https://nadlan.gov.il/')
    
    # Decisive appraisals
    if gov_data.get('decisive'):
        decisive = gov_data.get('decisive', [])
        if decisive:
            latest_appraisal = decisive[0] if decisive else {}
            asset.set_property('appraisalValue', latest_appraisal.get('appraised_value'), source='מנהל התכנון', url='https://www.gov.il/')
            asset.set_property('appraisalDate', latest_appraisal.get('appraisal_date'), source='מנהל התכנון', url='https://www.gov.il/')
            
            # Create documents from appraisals
            _create_documents_from_appraisals(asset, decisive)


def _extract_neighborhood_from_transactions(asset, transactions):
    """Extract neighborhood information from transaction data and update asset.
    """
    if not transactions or asset.neighborhood:
        # Only update if asset doesn't already have neighborhood info
        return
    
    filtered_transactions = _filter_transactions_by_asset_location(asset, transactions)
    
    if not filtered_transactions:
        logger.debug(f"No matching transactions found for asset {asset.id} location, skipping neighborhood extraction")
        return
        
    neighborhood_counts = {}
    
    for transaction in filtered_transactions:
        if isinstance(transaction, dict):
            neighborhood = transaction.get('neighborhood')
            if neighborhood and isinstance(neighborhood, str) and neighborhood.strip():
                neighborhood_counts[neighborhood] = neighborhood_counts.get(neighborhood, 0) + 1
    
    if neighborhood_counts:
        # Use the most common neighborhood from matching transactions
        most_common_neighborhood = max(neighborhood_counts.items(), key=lambda x: x[1])[0]
        asset.neighborhood = most_common_neighborhood
        logger.info(f"Updated asset {asset.id} neighborhood from {len(filtered_transactions)} matching transactions: {most_common_neighborhood}")
        
        # Store neighborhood source information
        asset.set_property('neighborhoodSource', 'Nadlan Transactions', source='Nadlan', url='https://nadlan.gov.il/')
        asset.set_property('neighborhoodConfidence', len(neighborhood_counts), source='Nadlan', url='https://nadlan.gov.il/')


def _filter_transactions_by_asset_location(asset, transactions):
    """Filter transactions to only include those matching the asset's block/parcel.
    
    Only uses block + parcel matching, which is the most reliable location identifier.
    Street and city matching are too unreliable and can lead to incorrect neighborhood
    assignments from nearby areas.
    
    Returns filtered list of transactions that match the asset's block/parcel.
    Returns empty list if asset doesn't have block/parcel info.
    """
    if not transactions:
        return []
    
    # Normalize asset location fields
    asset_block = str(asset.block or '').strip().lower()
    asset_parcel = str(asset.parcel or '').strip().lower()
    
    # Only proceed if asset has both block and parcel (required for reliable matching)
    if not asset_block or not asset_parcel:
        logger.debug(f"Asset {asset.id} missing block/parcel info, skipping neighborhood extraction from transactions")
        return []
    
    filtered = []
    
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        
        # Get transaction location fields (handle both Nadlan and GovMap field names)
        tx_block = str(_safe_get(tx, 'parcel_block') or _safe_get(tx, 'gush_num') or _safe_get(tx, 'block') or '').strip().lower()
        tx_parcel = str(_safe_get(tx, 'parcel_parcel') or _safe_get(tx, 'parcel_num') or _safe_get(tx, 'parcel') or '').strip().lower()
        
        # Only match on exact block + parcel (most reliable)
        if tx_block and tx_parcel:
            if asset_block == tx_block and asset_parcel == tx_parcel:
                filtered.append(tx)
    
    return filtered


def _process_rami_plans(asset, plans):
    """Process RAMI plans using unified metadata structure."""
    if plans:
        # Look for active plans
        active_plans = [p for p in plans if p.get('status') and 'פעיל' in p.get('status', '')]
        if active_plans:
            latest_plan = active_plans[0]
            asset.set_property('planStatus', latest_plan.get('status', ''), source='RAMI', url='https://rami.gov.il/')
            asset.set_property('planActive', True, source='RAMI', url='https://rami.gov.il/')
        else:
            asset.set_property('planActive', False, source='RAMI', url='https://rami.gov.il/')

        # Calculate additional plan rights and public obligations based on RAMI plans
        additional_rights_text = _calculate_additional_plan_rights(plans, asset)
        asset.set_property('additionalPlanRights', additional_rights_text, source='RAMI (calculated)', url='https://rami.gov.il/')
        
        # Get permits data for public obligations calculation
        gis_data = asset.meta.get('gis_data', {})
        permits = gis_data.get('permits', [])
        public_obligations_text = _calculate_public_obligations(plans, permits)
        asset.set_property('publicObligations', public_obligations_text, source='RAMI (calculated)', url='https://rami.gov.il/')

        # Create documents from RAMI plans
        _create_documents_from_rami_plans(asset, plans)


def _process_mavat_plans(asset, mavat_plans):
    """Process Mavat plans using unified metadata structure."""
    if mavat_plans:
        asset.set_property('mavatPlanCount', len(mavat_plans), source='Mavat', url='https://mavat.gov.il/')
        if mavat_plans:
            latest_plan = mavat_plans[0]
            asset.set_property('mavatPlanStatus', latest_plan.get('status', ''), source='Mavat', url='https://mavat.gov.il/')


def _process_govmap_autocomplete_data(asset, govmap_autocomplete_data):
    """Process GovMap autocomplete data using unified metadata structure."""
    try:
        res = govmap_autocomplete_data.get("res", {})
        
        # Extract address information from different categories
        for category in ["BUILDING", "STREET", "NEIGHBORHOOD", "POI_MID_POINT", "SETTLEMENT"]:
            items = res.get(category, [])
            if items:
                # Use the first item from the highest priority category
                first_item = items[0]
                if first_item.get("Value"):
                    asset.set_property(f'govmap_{category.lower()}_name', first_item.get("Value"), source='GovMap Autocomplete', url='https://www.govmap.gov.il/')
                if first_item.get("Text"):
                    asset.set_property(f'govmap_{category.lower()}_text', first_item.get("Text"), source='GovMap Autocomplete', url='https://www.govmap.gov.il/')
                break  # Use only the first matching category
        
        # Set primary address source
        asset.set_property('addressSource', 'GovMap Autocomplete', source='GovMap', url='https://www.govmap.gov.il/')
        
    except Exception as e:
        logger.warning(f"Failed to process GovMap autocomplete data: {e}")


def _process_govmap_data(asset, govmap_data):
    """Process GovMap parcel data using unified metadata structure."""
    # Process parcel data from api_data
    if govmap_data.get('api_data', {}).get('parcel'):
        parcel = govmap_data.get('api_data', {}).get('parcel', {})
        # Extract parcel information
        if parcel.get('gush'):
            asset.set_property('govmapGush', parcel.get('gush'), source='GovMap', url='https://www.govmap.gov.il/')
        if parcel.get('helka'):
            asset.set_property('govmapHelka', parcel.get('helka'), source='GovMap', url='https://www.govmap.gov.il/')
        if parcel.get('land_use'):
            asset.set_property('govmapLandUse', parcel.get('land_use'), source='GovMap', url='https://www.govmap.gov.il/')

    # Check if city is Tel Aviv (GIS is supported for Tel Aviv, so skip GovMap entities)
    city = getattr(asset, 'city', '') or ''
    is_tel_aviv = 'תל אביב' in city
    
    # Process nearby layers data (entities_by_point results)
    # Only for cities outside Tel Aviv (where GIS is not supported)
    if govmap_data.get('nearby') and not is_tel_aviv:
        nearby = govmap_data.get('nearby', {})
        
        # Map GovMap layer keys to GIS field names (same fields as GIS uses)
        layer_to_gis_field_map = {
            'schools': 'schoolsCount',
            'kindergartens': 'schoolsCount',  # Kindergartens are included in schools
            'metro_stations': 'metroStationsCount',
            'parking_lots': 'parkingLotsCount',
            'bus_stations': 'publicTransport',  # Special handling - sets string value
            'train_stations': 'publicTransport',  # Special handling - sets string value
            'urban_parks': 'publicGardensCount',
            'nature_parks': 'greenAmenitiesCount',
            'shelters': 'shelterDistanceM',  # Distance-based field (calculated from coordinates)
            'urban_renewal': 'tama38KeyArea',  # Maps to TAMA 38 key areas (special handling)
            'sports_facilities': None,  # No direct GIS equivalent
            'restaurants': None,  # No direct GIS equivalent
        }
        
        # Track public transport indicators
        public_transport_indicators = []
        
        for layer_key, layer_data in nearby.items():
            if isinstance(layer_data, dict):
                # New format: layer_data contains 'entities' list
                entities = layer_data.get('entities', [])
                count = layer_data.get('count', len(entities))
                
                if count > 0:
                    # Map to GIS field name if available
                    gis_field_name = layer_to_gis_field_map.get(layer_key)
                    
                    if gis_field_name:
                        # Special handling for publicTransport (string field, not count)
                        if gis_field_name == 'publicTransport':
                            # Collect public transport indicators
                            if layer_key == 'bus_stations':
                                public_transport_indicators.append(f'תחנות אוטובוס ({count})')
                            elif layer_key == 'train_stations':
                                public_transport_indicators.append(f'תחנות רכבת ({count})')
                        elif gis_field_name == 'shelterDistanceM':
                            # Shelters only set distance, not count (like GIS)
                            # Distance will be calculated below
                            pass
                        elif gis_field_name == 'tama38KeyArea':
                            # Urban renewal maps to TAMA 38 key areas (like GIS)
                            asset.set_property('tama38KeyArea', True, source='GovMap', url='https://www.govmap.gov.il/')
                            asset.set_property('tama38KeyAreasCount', count, source='GovMap', url='https://www.govmap.gov.il/')
                        else:
                            # Use the same field name as GIS (will update/supplement GIS data)
                            asset.set_property(gis_field_name, count, source='GovMap', url='https://www.govmap.gov.il/')
                        
                        # Calculate distances if we have entity centroids and asset coordinates
                        # This applies to shelters, metro_stations, schools, etc.
                        if entities and hasattr(asset, 'lat') and hasattr(asset, 'lon') and asset.lat and asset.lon:
                            try:
                                from govmap.api_client import itm_to_wgs84
                                from math import radians, cos, sin, asin, sqrt
                                
                                # Calculate distances for relevant layers
                                distances = []
                                for entity in entities:
                                    centroid = entity.get('centroid')
                                    if centroid and len(centroid) == 2:
                                        # Convert ITM to WGS84
                                        entity_lon, entity_lat = itm_to_wgs84(centroid[0], centroid[1])
                                        
                                        # Calculate distance using Haversine formula
                                        def haversine_distance(lat1, lon1, lat2, lon2):
                                            """Calculate distance between two points in meters."""
                                            R = 6371000  # Earth radius in meters
                                            dlat = radians(lat2 - lat1)
                                            dlon = radians(lon2 - lon1)
                                            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                                            c = 2 * asin(sqrt(a))
                                            return R * c
                                        
                                        distance = haversine_distance(asset.lat, asset.lon, entity_lat, entity_lon)
                                        distances.append(distance)
                                
                                if distances:
                                    min_distance = min(distances)
                                    
                                    # Set distance fields for relevant layers
                                    if layer_key == 'metro_stations':
                                        asset.set_property('metroStationDistanceM', min_distance, source='GovMap', url='https://www.govmap.gov.il/')
                                    elif layer_key == 'schools':
                                        asset.set_property('nearestSchoolDistanceM', min_distance, source='GovMap', url='https://www.govmap.gov.il/')
                                    elif layer_key == 'kindergartens':
                                        # Update nearest school distance if kindergartens are closer
                                        existing_distance = asset.get_property_value('nearestSchoolDistanceM') or float('inf')
                                        if min_distance < existing_distance:
                                            asset.set_property('nearestSchoolDistanceM', min_distance, source='GovMap', url='https://www.govmap.gov.il/')
                                    elif layer_key == 'shelters':
                                        # Set shelter distance (GIS uses shelterDistanceM)
                                        asset.set_property('shelterDistanceM', min_distance, source='GovMap', url='https://www.govmap.gov.il/')
                            except Exception as e:
                                logger.debug(f"Failed to calculate distances for {layer_key}: {e}")
                    else:
                        # For layers without GIS equivalents, store with GovMap prefix
                        asset.set_property(f'govmap_{layer_key}_count', count, source='GovMap', url='https://www.govmap.gov.il/')
            elif isinstance(layer_data, list):
                # Legacy format: direct list of features
                if layer_data:
                    gis_field_name = layer_to_gis_field_map.get(layer_key)
                    if gis_field_name:
                        # Special handling for publicTransport (string field, not count)
                        if gis_field_name == 'publicTransport':
                            if layer_key == 'bus_stations':
                                public_transport_indicators.append(f'תחנות אוטובוס ({len(layer_data)})')
                            elif layer_key == 'train_stations':
                                public_transport_indicators.append(f'תחנות רכבת ({len(layer_data)})')
                        elif gis_field_name == 'tama38KeyArea':
                            # Urban renewal maps to TAMA 38 key areas (like GIS)
                            asset.set_property('tama38KeyArea', True, source='GovMap', url='https://www.govmap.gov.il/')
                            asset.set_property('tama38KeyAreasCount', len(layer_data), source='GovMap', url='https://www.govmap.gov.il/')
                        else:
                            asset.set_property(gis_field_name, len(layer_data), source='GovMap', url='https://www.govmap.gov.il/')
                    else:
                        asset.set_property(f'govmap_{layer_key}_count', len(layer_data), source='GovMap', url='https://www.govmap.gov.il/')
        
        # Set publicTransport field if we found bus or train stations
        if public_transport_indicators:
            public_transport_text = ', '.join(public_transport_indicators)
            asset.set_property('publicTransport', public_transport_text, source='GovMap', url='https://www.govmap.gov.il/')
        elif not asset.get_property_value('publicTransport'):
            # If no public transport found and GIS didn't set it, set default
            asset.set_property('publicTransport', 'קרוב לתחבורה ציבורית', source='GovMap', url='https://www.govmap.gov.il/')


def _create_django_records_from_collected_data(asset, govmap_autocomplete_data, govmap_data, gis_data, gov_data, plans, mavat_plans, listings):
    """Create Django model records (SourceRecord, RealEstateTransaction) from collected data.

    Handles potential IntegrityError when UNIQUE(source, external_id) already exists for another asset by
    safely retrieving the existing record and skipping creation instead of failing the whole enrichment.
    """
    from core.models import RealEstateTransaction, SourceRecord
    from django.db import IntegrityError

    def _detect_listing_source(listing_data: Dict[str, Any]) -> str:
        """Detect listing source (yad2 or madlan) from listing data."""
        if not isinstance(listing_data, dict):
            return 'yad2'  # default
        
        url = listing_data.get('url', '')
        if isinstance(url, str):
            lower_url = url.lower()
            if 'michrazimsite' in lower_url or 'michrazim' in lower_url:
                return 'michrazim'
            if 'madlan.co.il' in lower_url:
                return 'madlan'
            if 'yad2.co.il' in lower_url:
                return 'yad2'
        
        # Check meta for source
        meta = listing_data.get('meta', {}) or {}
        if isinstance(meta, dict):
            source = meta.get('source')
            if source in ('yad2', 'madlan', 'michrazim'):
                return source
        
        # Check top-level source if provided
        if listing_data.get('source') in ('yad2', 'madlan', 'michrazim'):
            return listing_data.get('source')
        
        return 'yad2'  # default fallback

    def _safe_source_record_create(source: str, external_id: str, defaults: dict):
        """Create a SourceRecord guarding against UNIQUE(source, external_id) conflicts.

        If a record with the same (source, external_id) exists for another asset, we log and skip.
        """
        if not external_id:
            return None
        try:
            obj, created = SourceRecord.objects.get_or_create(
                source=source,  # use only the unique fields in the lookup
                external_id=str(external_id),
                defaults={**defaults, 'asset': asset},
            )
            # If the record exists but belongs to a different asset, do not reassociate (one-to-one style ownership)
            if not created and obj.asset_id != asset.id:
                logger.debug(
                    "SourceRecord (%s,%s) already linked to asset %s; skipping for asset %s",
                    source, external_id, obj.asset_id, asset.id,
                )
            return obj
        except IntegrityError:
            # Rare race condition: object created concurrently after the initial existence check
            existing = SourceRecord.objects.filter(source=source, external_id=str(external_id)).first()
            if existing:
                if existing.asset_id != asset.id:
                    logger.debug(
                        "(race) SourceRecord (%s,%s) already linked to asset %s; skipping for asset %s",
                        source, external_id, existing.asset_id, asset.id,
                    )
                return existing
            logger.warning(
                "IntegrityError creating SourceRecord (%s,%s) for asset %s; record not created",
                source, external_id, asset.id,
            )
            return None

    normalized_listings = _normalize_listings(listings or [])

    # Create SourceRecord for Yad2 and Madlan listings
    if listings and not normalized_listings:
        logger.debug("All listings dropped while normalizing listings for Django source records on asset %s", asset.id)

    if normalized_listings:
        for listing in normalized_listings:
            listing_id = listing.get('listing_id')
            if listing_id:
                # Detect source from listing data
                listing_source = _detect_listing_source(listing)
                
                _safe_source_record_create(
                    source=listing_source,
                    external_id=str(listing_id),
                    defaults={
                        'title': listing.get('title', ''),
                        'url': listing.get('url', ''),
                        'raw': listing,
                    },
                )

                if DjangoListing is not None:
                    listing_meta = listing.get('meta') or {}
                    recent_deal_candidates = (
                        listing.get('recent_deal'),
                        listing.get('recentDeal'),
                        listing_meta.get('recent_deal'),
                        listing_meta.get('recentDeal'),
                    )
                    recent_deal_value = next(
                        (value for value in recent_deal_candidates if value is not None),
                        None,
                    )
                    # Extract ad_type from multiple possible locations
                    ad_type_value = (
                        listing.get('ad_type') or 
                        listing.get('adType') or
                        listing_meta.get('ad_type') or
                        listing_meta.get('adType') or
                        (listing_meta.get('raw') or {}).get('adType') if isinstance(listing_meta.get('raw'), dict) else None
                    )
                    
                    # Fallback: infer ad_type from other fields if missing
                    if not ad_type_value:
                        contact_info = listing.get('contact_info') or listing.get('contactInfo') or {}
                        features = listing.get('features') or {}
                        has_agency = (
                            bool(contact_info.get('agent')) or
                            bool(features.get('agency')) or
                            bool(listing_meta.get('customer', {}).get('agencyName') if isinstance(listing_meta.get('customer'), dict) else None)
                        )
                        if has_agency:
                            ad_type_value = 'broker'
                    
                    listing_defaults = {
                        'title': listing.get('title'),
                        'url': listing.get('url'),
                        'raw': listing,
                        'status': listing.get('status') or listing_meta.get('status') or 'active',
                        'price': listing.get('price'),
                        'rooms': listing.get('rooms'),
                        'area': listing.get('area'),
                        'address': listing.get('address'),
                        'recent_deal': bool(recent_deal_value) if recent_deal_value is not None else False,
                        # Persist commonly used fields for UI/filters
                        'listing_type': listing.get('listing_type') or listing.get('listingType'),
                        'ad_type': ad_type_value,
                        'contact_name': listing.get('contact_name') or listing.get('contactName') or ((listing.get('contact_info') or {}).get('name') if isinstance(listing.get('contact_info'), dict) else None),
                        'contact_phone': (listing.get('contact_phone') or listing.get('contactPhone') or ((listing.get('contact_info') or {}).get('phone') if isinstance(listing.get('contact_info'), dict) else None) or ((listing.get('contact_info') or {}).get('brokerPhone') if isinstance(listing.get('contact_info'), dict) else None)),
                        'photos': listing.get('photos') or listing.get('images') or [],
                        'video_url': listing.get('video_url') or listing.get('videoUrl') or listing.get('video'),
                    }
                    try:
                        listing_obj, created_listing = DjangoListing.objects.get_or_create(
                            source=listing_source,
                            external_id=str(listing_id),
                            defaults=listing_defaults,
                        )
                        if not created_listing:
                            updates = _collect_field_updates(listing_obj, listing_defaults)
                            if updates:
                                listing_obj.save(update_fields=list(dict.fromkeys(updates)))
                        _ensure_listing_link(listing_obj, asset)
                    except Exception as exc:  # pragma: no cover - best effort logging
                        logger.warning(
                            "Failed to synchronize listing %s for asset %s: %s",
                            listing_id,
                            getattr(asset, 'id', None),
                            exc,
                        )

    # Create SourceRecord for RAMI plans
    if plans:
        for plan in plans:
            plan_number = plan.get('planNumber') or plan.get('plan_number', '')
            if plan_number:
                _safe_source_record_create(
                    source='rami_plan',
                    external_id=str(plan_number),
                    defaults={
                        'title': plan.get('title', f'תכנית רמ״י {plan_number}'),
                        'url': plan.get('url', ''),
                        'raw': plan,
                    },
                )

    # Create SourceRecord for decisive appraisals
    if gov_data and gov_data.get('decisive'):
        for appraisal in gov_data.get('decisive', []):
            appraisal_id = appraisal.get('id')
            if appraisal_id:
                _safe_source_record_create(
                    source='appraisal_decisive',
                    external_id=str(appraisal_id),
                    defaults={
                        'title': appraisal.get('title') or f"שומה החלטית {appraisal_id}",
                        'raw': appraisal,
                    },
                )

    # Create SourceRecord for Mavat plans
    if mavat_plans:
        for plan in mavat_plans:
            plan_id = plan.get('plan_id') or plan.get('id', '')
            if plan_id:
                _safe_source_record_create(
                    source='tabu',  # Using 'tabu' as closest match for Mavat
                    external_id=str(plan_id),
                    defaults={
                        'title': plan.get('title', f'תכנית מבת {plan_id}'),
                        'url': plan.get('url', ''),
                        'raw': plan,
                    },
                )

    # Create SourceRecord for GIS data
    if gis_data:
        if gis_data.get('permits'):
            _safe_source_record_create(
                source='gis_permit',
                external_id=f"permits_{asset.id}",  # keep asset-specific external id
                defaults={
                    'title': 'היתרי בנייה',
                    'raw': gis_data,
                },
            )

        if gis_data.get('rights'):
            _safe_source_record_create(
                source='gis_rights',
                external_id=f"rights_{asset.id}",
                defaults={
                    'title': 'זכויות בנייה',
                    'raw': gis_data,
                },
            )

    # Create RealEstateTransaction records from government data
    if gov_data and gov_data.get('transactions'):
        for transaction in gov_data.get('transactions', []):
            # Generate a unique deal_id from address + date + price if not present
            deal_id = transaction.get('deal_id')
            if not deal_id:
                # Try to extract objectid from raw data (GovMap deals have this)
                raw_data = transaction.get('raw', {})
                if isinstance(raw_data, dict):
                    objectid = raw_data.get('objectid') or raw_data.get('objectId') or raw_data.get('object_id')
                    if objectid:
                        deal_id = f"govmap_{objectid}"
                
                # If still no deal_id, create from address + date + price
                if not deal_id:
                    address = transaction.get('address', '')
                    deal_date = transaction.get('deal_date', '')
                    deal_amount = transaction.get('deal_amount', '')
                    # Truncate deal_id to max 100 chars (database limit)
                    deal_id = f"{address}_{deal_date}_{deal_amount}".replace(' ', '_')[:100]
            
            # Parse deal_date to proper date format
            # Handle both Nadlan format (DD/MM/YYYY) and GovMap format (YYYY-MM-DD or YYYY-MM)
            parsed_date = None
            if transaction.get('deal_date'):
                try:
                    from datetime import datetime
                    deal_date_str = transaction.get('deal_date')
                    # Try Nadlan format first (DD/MM/YYYY)
                    try:
                        parsed_date = datetime.strptime(deal_date_str, "%d/%m/%Y")
                    except ValueError:
                        # Try GovMap format (YYYY-MM-DD)
                        try:
                            parsed_date = datetime.strptime(deal_date_str, "%Y-%m-%d")
                        except ValueError:
                            # Try GovMap format (YYYY-MM) - use first day of month
                            try:
                                parsed_date = datetime.strptime(deal_date_str, "%Y-%m")
                            except ValueError:
                                pass
                    # Make datetime timezone-aware if it was successfully parsed
                    if parsed_date and timezone.is_naive(parsed_date):
                        parsed_date = timezone.make_aware(parsed_date)
                except (ValueError, TypeError):
                    pass
            
            # Parse rooms to integer
            rooms = transaction.get('rooms')
            if rooms:
                try:
                    # Extract number from rooms string (e.g., "3" from "3 חדרים")
                    rooms_match = re.search(r'\d+', str(rooms))
                    rooms = int(rooms_match.group()) if rooms_match else None
                except (ValueError, AttributeError):
                    rooms = None
            
            # Parse floor to integer
            floor = transaction.get('floor')
            if floor:
                try:
                    # Extract number from floor string (e.g., "2" from "שניה")
                    floor_map = {'ראשונה': 1, 'שניה': 2, 'שלישית': 3, 'רביעית': 4, 'חמישית': 5}
                    if floor in floor_map:
                        floor = floor_map[floor]
                    else:
                        floor_match = re.search(r'\d+', str(floor))
                        floor = int(floor_match.group()) if floor_match else None
                except (ValueError, AttributeError):
                    floor = None
            
            transaction_defaults = {
                'asset': asset,
                'date': parsed_date,
                'price': transaction.get('deal_amount'),
                'rooms': rooms,
                'area': transaction.get('area'),
                'floor': floor,
                'address': transaction.get('address'),
                'raw': transaction,
            }

            # Ensure deal_id is not empty (database constraint)
            if not deal_id or not str(deal_id).strip():
                # Generate a fallback deal_id using transaction hash if all else fails
                transaction_str = json.dumps(transaction, sort_keys=True, default=str)
                deal_id = f"fallback_{hashlib.md5(transaction_str.encode()).hexdigest()[:16]}"
            
            transaction_obj = None
            created_transaction = False
            try:
                transaction_obj, created_transaction = RealEstateTransaction.objects.get_or_create(
                    deal_id=str(deal_id)[:100],  # Ensure it fits in database field
                    defaults=transaction_defaults,
                )
            except IntegrityError:
                transaction_obj = RealEstateTransaction.objects.filter(deal_id=str(deal_id)[:100]).first()
            except Exception as e:
                logger.warning(f"Failed to create transaction with deal_id {deal_id[:50]}...: {e}")
                continue

            if transaction_obj:
                updates = []
                if not created_transaction:
                    updates.extend(
                        _collect_field_updates(
                            transaction_obj,
                            {k: v for k, v in transaction_defaults.items() if k != 'asset'},
                        )
                    )
                    if getattr(transaction_obj, 'asset_id', None) is None:
                        transaction_obj.asset = asset
                        updates.append('asset')
                    if updates:
                        transaction_obj.save(update_fields=list(dict.fromkeys(updates)))
                _ensure_transaction_link(transaction_obj, asset)

def _populate_asset_fields_from_listings(asset, normalized_listings):
    """Populate asset fields from Yad2 and Madlan listings data.
    
    This function extracts the most relevant listing data to populate
    the asset's own fields (price, area, price_per_sqm, etc.) rather than
    just storing market analysis data.
    
    Priority: Yad2 listings are preferred, with Madlan as fallback.
    """
    if not normalized_listings:
        return
    
    def _is_yad2_listing(listing_data):
        """Check if a listing is from Yad2 based on URL or meta."""
        if not isinstance(listing_data, dict):
            return False
        
        url = listing_data.get('url', '')
        if isinstance(url, str) and 'yad2.co.il' in url.lower():
            return True
        
        # Check meta for source
        meta = listing_data.get('meta', {})
        if isinstance(meta, dict):
            source = meta.get('source')
            if source == 'yad2':
                return True
        
        return False
    
    def _is_madlan_listing(listing_data):
        """Check if a listing is from Madlan based on URL or meta."""
        if not isinstance(listing_data, dict):
            return False
        
        url = listing_data.get('url', '')
        if isinstance(url, str) and 'madlan.co.il' in url.lower():
            return True
        
        # Check meta for source
        meta = listing_data.get('meta', {})
        if isinstance(meta, dict):
            source = meta.get('source')
            if source == 'madlan':
                return True
        
        return False
    
    # Separate listings by source
    yad2_listings = [listing for listing in normalized_listings if _is_yad2_listing(listing)]
    madlan_listings = [listing for listing in normalized_listings if _is_madlan_listing(listing)]
    
    # Log separation for debugging
    if yad2_listings or madlan_listings:
        logger.debug(
            '[ASSET_FIELDS] Separated listings: %d Yad2, %d Madlan for asset %s',
            len(yad2_listings),
            len(madlan_listings),
            asset.id
        )
    
    def _extract_listing_neighborhood(listing_data):
        """Extract neighborhood text from a normalized listing dictionary.
        
        Handles both Yad2 and Madlan listing structures:
        - Yad2: meta["neighborhood"]
        - Madlan: meta["address_details"]["neighbourhood"] or meta["madlan_raw"]["addressDetails"]["neighbourhood"]
        """
        if not isinstance(listing_data, dict):
            return None

        candidate = listing_data.get('neighborhood')
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

        meta = listing_data.get('meta')
        if isinstance(meta, dict):
            # Yad2: direct neighborhood in meta
            candidate = meta.get('neighborhood')
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()

            # Madlan: address_details.neighbourhood (British spelling)
            address_details = meta.get('address_details')
            if isinstance(address_details, dict):
                candidate = address_details.get('neighbourhood')  # Note: British spelling
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()

            # Madlan: madlan_raw.addressDetails.neighbourhood
            madlan_raw = meta.get('madlan_raw')
            if isinstance(madlan_raw, dict):
                address_details_raw = madlan_raw.get('addressDetails')
                if isinstance(address_details_raw, dict):
                    candidate = address_details_raw.get('neighbourhood')  # Note: British spelling
                    if isinstance(candidate, str) and candidate.strip():
                        return candidate.strip()

            address_meta = meta.get('address') or meta.get('address_components')
            if isinstance(address_meta, dict):
                candidate = address_meta.get('neighborhood')
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()

            raw_meta = meta.get('raw')
            if isinstance(raw_meta, dict):
                raw_neighborhood = raw_meta.get('neighborhood')
                if isinstance(raw_neighborhood, dict):
                    candidate = raw_neighborhood.get('text') or raw_neighborhood.get('name')
                    if isinstance(candidate, str) and candidate.strip():
                        return candidate.strip()
                elif isinstance(raw_neighborhood, str) and raw_neighborhood.strip():
                    return raw_neighborhood.strip()

                address = raw_meta.get('address')
                if isinstance(address, dict):
                    raw_neighborhood = address.get('neighborhood')
                    if isinstance(raw_neighborhood, dict):
                        candidate = raw_neighborhood.get('text') or raw_neighborhood.get('name')
                        if isinstance(candidate, str) and candidate.strip():
                            return candidate.strip()
                    elif isinstance(raw_neighborhood, str) and raw_neighborhood.strip():
                        return raw_neighborhood.strip()

        return None

    def _is_listing_commercial(listing_data):
        if not isinstance(listing_data, dict):
            return False

        # Check explicit is_commercial flag (preferred)
        is_commercial = listing_data.get('is_commercial') or listing_data.get('isCommercial')
        if is_commercial is not None:
            return bool(is_commercial)
        _, normalized_listing_type = _extract_listing_type(listing_data)
        if normalized_listing_type == 'commercial':
            return True

        return listing_data.get('ad_type', '') == 'commercial'

    def _extract_street_and_number(address: str) -> Tuple[Optional[str], Optional[str]]:
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
    
    def _matches_street_and_number(address1: str, address2: str) -> bool:
        """
        Check if two addresses have the same street name and house number.
        Only returns True if both street name and number match exactly.
        This ensures "2" doesn't match "22" or "222".
        """
        street1, num1 = _extract_street_and_number(address1)
        street2, num2 = _extract_street_and_number(address2)
        
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

    # Find the best listing to use as the primary source
    # Priority: Yad2 listings first, then Madlan as fallback
    # Within each source: exact address match > exact street+number match
    best_listing = None
    listing_source = None

    update_fields = set()

    def _find_best_listing(listings_to_search, source_name):
        """Find the best matching listing from a list of listings."""
        if not asset.normalized_address or not listings_to_search:
            return None
        
        asset_address = asset.normalized_address.lower()
        
        for listing in listings_to_search:
            listing_address = listing.get('address', '').lower()
            
            # Check for exact match with full address
            if asset_address == listing_address:
                logger.debug(
                    '[ASSET_FIELDS] Found exact address match in %s listings for asset %s',
                    source_name,
                    asset.id
                )
                return listing
            
            # Check for exact street + number match (e.g., "ארלוזורוב 59")
            if _matches_street_and_number(asset_address, listing_address):
                logger.debug(
                    '[ASSET_FIELDS] Found street+number match in %s listings for asset %s',
                    source_name,
                    asset.id
                )
                return listing
        
        return None
    
    # Try Yad2 listings first
    best_listing = _find_best_listing(yad2_listings, 'Yad2')
    if best_listing:
        listing_source = 'yad2'
    else:
        # Fallback to Madlan listings
        best_listing = _find_best_listing(madlan_listings, 'Madlan')
        if best_listing:
            listing_source = 'madlan'
            logger.info(
                '[ASSET_FIELDS] Using Madlan listing as fallback for asset %s (no Yad2 match found)',
                asset.id
            )
        else:
            # Final fallback: check all normalized listings if no source-specific match
            best_listing = _find_best_listing(normalized_listings, 'all')
            if best_listing:
                listing_source = 'unknown'
                logger.info(
                    '[ASSET_FIELDS] Using unclassified listing for asset %s (no Yad2/Madlan match found)',
                    asset.id
                )
    
    # Update is_commercial based on primary listing only
    if best_listing:
        is_commercial_listing = _is_listing_commercial(best_listing)
        asset.is_commercial = is_commercial_listing
        update_fields.add('is_commercial')
    
    if not best_listing:
        if update_fields:
            asset.save(update_fields=list(update_fields))
            logger.info('[ASSET_FIELDS] Updated asset %s fields: %s', asset.id, list(update_fields))
        return

    # Populate asset fields from the best listing
    asset_block = str(asset.block or '').strip().lower()
    asset_parcel = str(asset.parcel or '').strip().lower()
    
    should_extract_neighborhood = True
    
    # If asset has block/parcel, verify listing also matches (if listing has this info)
    if asset_block and asset_parcel:
        listing_block = str(_safe_get(best_listing, 'parcel_block') or _safe_get(best_listing.get('meta', {}), 'parcel_block') or _safe_get(best_listing.get('meta', {}), 'block') or '').strip().lower()
        listing_parcel = str(_safe_get(best_listing, 'parcel_parcel') or _safe_get(best_listing.get('meta', {}), 'parcel_parcel') or _safe_get(best_listing.get('meta', {}), 'parcel') or '').strip().lower()
        
        # If listing has block/parcel info, verify it matches
        if listing_block and listing_parcel:
            if asset_block != listing_block or asset_parcel != listing_parcel:
                # Listing doesn't match block/parcel - skip to avoid incorrect assignment
                should_extract_neighborhood = False
                logger.debug('[ASSET_FIELDS] Listing address matches but block/parcel differs, skipping neighborhood extraction')
            else:
                logger.debug('[ASSET_FIELDS] Listing matches asset block/parcel and address, extracting neighborhood')
        else:
            # Listing doesn't have block/parcel (typical for Yad2/Madlan), but address matches exactly
            logger.debug('[ASSET_FIELDS] Listing matches exact address (no block/parcel in listing), extracting neighborhood')
    
    if should_extract_neighborhood:
        listing_neighborhood = _extract_listing_neighborhood(best_listing)
        if listing_neighborhood and not asset.neighborhood:
            asset.neighborhood = listing_neighborhood
            update_fields.add('neighborhood')
            logger.debug('[ASSET_FIELDS] Set neighborhood from listing: %s', asset.neighborhood)
    
    listing_type_value, listing_type_normalized = _extract_listing_type(best_listing)

    listing_price = best_listing.get('price')
    if listing_price is not None:
        if asset.meta is None:
            asset.meta = {}

        listing_prices_meta = asset.meta.get('listing_prices')
        if not isinstance(listing_prices_meta, dict):
            listing_prices_meta = {}
            asset.meta['listing_prices'] = listing_prices_meta

        if listing_type_normalized == 'rent':
            if listing_prices_meta.get('rent') != listing_price:
                listing_prices_meta['rent'] = listing_price
            if hasattr(asset, 'rent_price') and not getattr(asset, 'rent_price', None):
                asset.rent_price = listing_price
                update_fields.add('rent_price')
                logger.debug('[ASSET_FIELDS] Set rent_price from listing: %s', asset.rent_price)
        else:
            if not asset.price:
                asset.price = listing_price
                update_fields.add('price')
                logger.debug('[ASSET_FIELDS] Set price from listing: %s', asset.price)
            if listing_prices_meta.get('sale') != listing_price:
                listing_prices_meta['sale'] = listing_price
    
    # Area fields: size represents built area (net), total_size represents lot area (gross)
    listing_net_area = _first_nonempty(
        best_listing.get('size'),
        best_listing.get('area'),
        _safe_get(best_listing.get('meta'), 'size'),
        _safe_get(best_listing.get('meta'), 'area'),
        _safe_get(best_listing.get('meta'), 'netSqm'),
    )
    if listing_net_area and not asset.area:
        # Track source and URL for area data (also sets the asset.area field)
        source_name = 'Yad2' if listing_source == 'yad2' else 'Madlan'
        default_url = 'https://www.yad2.co.il/' if listing_source == 'yad2' else 'https://www.madlan.co.il/'
        asset.set_property('area', listing_net_area, source=source_name, url=best_listing.get('url', default_url))
        update_fields.add('area')
        update_fields.add('meta')
        logger.debug('[ASSET_FIELDS] Set area from listing size: %s', asset.area)

    listing_total_area = _first_nonempty(
        best_listing.get('total_size'),
        _safe_get(best_listing.get('meta'), 'total_size'),
        _safe_get(best_listing.get('meta'), 'totalSqm'),
    )
    if listing_total_area and not asset.total_area:
        # Track source and URL for total_area data (also sets the asset.total_area field)
        source_name = 'Yad2' if listing_source == 'yad2' else 'Madlan'
        default_url = 'https://www.yad2.co.il/' if listing_source == 'yad2' else 'https://www.madlan.co.il/'
        asset.set_property('total_area', listing_total_area, source=source_name, url=best_listing.get('url', default_url))
        update_fields.add('total_area')
        update_fields.add('meta')
        logger.debug('[ASSET_FIELDS] Set total_area from listing total_size: %s', asset.total_area)

    # Calculate price_per_sqm if we have both price and area
    if asset.price and (asset.total_area or asset.area):
        area_to_use = asset.total_area or asset.area
        if area_to_use > 0:
            asset.price_per_sqm = int(asset.price / area_to_use)
            update_fields.add('price_per_sqm')
            logger.debug('[ASSET_FIELDS] Calculated price_per_sqm: %s', asset.price_per_sqm)
    
    # Additional fields from listing
    if best_listing.get('rooms') and not asset.rooms:
        asset.rooms = best_listing['rooms']
        update_fields.add('rooms')
    
    if best_listing.get('bedrooms') and not asset.bedrooms:
        asset.bedrooms = best_listing['bedrooms']
        update_fields.add('bedrooms')
    
    # Building type - only use if available from listing
    if not asset.building_type:
        listing_property_type = best_listing.get('property_type')
        if listing_property_type:
            asset.building_type = listing_property_type
            update_fields.add('building_type')
            logger.debug('[ASSET_FIELDS] Set building_type from listing: %s', asset.building_type)
    
    if best_listing.get('floor') and not asset.floor:
        floor_value = best_listing['floor']
        # Parse Hebrew floor descriptions to numbers
        if isinstance(floor_value, str):
            floor_str = floor_value.lower()
            if 'קרקע' in floor_str or 'ground' in floor_str:
                asset.floor = 0
            elif 'מרתף' in floor_str or 'basement' in floor_str:
                asset.floor = -1
            else:
                # Try to extract number from string
                numbers = re.findall(r'\d+', floor_str)
                if numbers:
                    asset.floor = int(numbers[0])
                else:
                    asset.floor = None
        else:
            asset.floor = floor_value
        update_fields.add('floor')
    
    # Contact and listing fields from best listing
    # Contact name
    if not getattr(asset, 'contact_name', None):
        contact_name = (
            best_listing.get('contact_name')
            or best_listing.get('contactName')
            or ((best_listing.get('contact_info') or {}).get('name') if isinstance(best_listing.get('contact_info'), dict) else None)
        )
        if contact_name:
            try:
                # Asset model may not have contact_name; guard with hasattr
                if hasattr(asset, 'contact_name'):
                    asset.contact_name = contact_name
                    update_fields.add('contact_name')
            except Exception:
                pass

    # Contact phone
    if not getattr(asset, 'contact_phone', None):
        contact_phone = (
            best_listing.get('contact_phone')
            or best_listing.get('contactPhone')
            or ((best_listing.get('contact_info') or {}).get('phone') if isinstance(best_listing.get('contact_info'), dict) else None)
            or ((best_listing.get('contact_info') or {}).get('brokerPhone') if isinstance(best_listing.get('contact_info'), dict) else None)
        )
        if contact_phone:
            try:
                if hasattr(asset, 'contact_phone'):
                    asset.contact_phone = contact_phone
                    update_fields.add('contact_phone')
            except Exception:
                pass

    # Listing type and ad type for downstream filters
    listing_type = listing_type_value or best_listing.get('listing_type') or best_listing.get('listingType')
    ad_type = best_listing.get('ad_type') or best_listing.get('adType')
    if listing_type and hasattr(asset, 'listing_type') and not getattr(asset, 'listing_type', None):
        asset.listing_type = listing_type
        update_fields.add('listing_type')
    if ad_type and hasattr(asset, 'ad_type') and not getattr(asset, 'ad_type', None):
        asset.ad_type = ad_type
        update_fields.add('ad_type')

    # Extract all high-priority fields from best listing (same fields as frontend expects)
    # These fields are already normalized in best_listing, but we extract them for primary_listing_source
    
    # Price-related fields
    price_dropped = best_listing.get('priceDropped') or best_listing.get('price_dropped')
    previous_price = best_listing.get('previousPrice') or best_listing.get('previous_price')
    
    # Property features
    shelter = best_listing.get('shelter')
    accessibility = best_listing.get('accessibility')
    
    # Property condition and class
    building_class = best_listing.get('buildingClass') or best_listing.get('building_class')
    general_condition = best_listing.get('generalCondition') or best_listing.get('general_condition')
    
    # Investment data
    investment_yield = best_listing.get('investmentYield') or best_listing.get('investment_yield')
    approximate_rent = best_listing.get('approximateRent') or best_listing.get('approximate_rent')
    commute_time = best_listing.get('commuteTime') or best_listing.get('commute_time')
    
    # Date fields
    published_days = best_listing.get('publishedDays') or best_listing.get('published_days')
    date_posted = best_listing.get('datePosted') or best_listing.get('date_posted')
    
    # Tags
    tag_best_school = best_listing.get('tagBestSchool') or best_listing.get('tag_best_school')
    tag_safety = best_listing.get('tagSafety') or best_listing.get('tag_safety')
    tag_family_friendly = best_listing.get('tagFamilyFriendly') or best_listing.get('tag_family_friendly')
    tag_light_rail = best_listing.get('tagLightRail') or best_listing.get('tag_light_rail')
    tag_park_access = best_listing.get('tagParkAccess') or best_listing.get('tag_park_access')
    tag_quiet_street = best_listing.get('tagQuietStreet') or best_listing.get('tag_quiet_street')
    tag_commute = best_listing.get('tagCommute') or best_listing.get('tag_commute')
    
    # Extract exclusivity from best listing
    # First check if already normalized in the listing
    exclusive = best_listing.get('exclusive')
    if exclusive is None:
        # Fallback: extract from raw data (same logic as backend normalization)
        listing_meta = best_listing.get('meta', {})
        if isinstance(listing_meta, dict):
            # Check Madlan exclusivity
            poc = listing_meta.get('poc', {})
            if isinstance(poc, dict):
                exclusivity = poc.get('exclusivity', {})
                if isinstance(exclusivity, dict):
                    madlan_exclusive = exclusivity.get('exclusive')
                    if madlan_exclusive is not None:
                        exclusive = bool(madlan_exclusive)
            
            # Check Yad2 exclusivity (preferred over Madlan)
            raw_data = best_listing.get('raw') or listing_meta.get('raw', {})
            if isinstance(raw_data, dict):
                in_property = raw_data.get('inProperty', {})
                if isinstance(in_property, dict):
                    yad2_exclusive = in_property.get('isAssetExclusive')
                    if yad2_exclusive is not None:
                        exclusive = bool(yad2_exclusive)

    # Store source information in meta
    if asset.meta is None:
        asset.meta = {}

    populated_fields = set(update_fields)
    populated_fields.add('meta')

    # Use the determined source (yad2 or madlan), default to yad2 for backward compatibility
    final_source = listing_source or 'yad2'
    
    primary_listing_source = {
        'source': final_source,
        'listing_id': best_listing.get('listing_id'),
        'address': best_listing.get('address'),
        'url': best_listing.get('url'),
        'listing_type': listing_type,
        'populated_fields': list(populated_fields),
    }
    if listing_price is not None:
        if listing_type_normalized == 'rent':
            primary_listing_source['rent_price'] = listing_price
        else:
            primary_listing_source['price'] = listing_price
    
    # Store all high-priority fields from listing in primary_listing_source
    # These will be used by the serializer to enhance the normalized listing data
    if price_dropped is not None:
        primary_listing_source['priceDropped'] = bool(price_dropped) if isinstance(price_dropped, bool) else price_dropped
    if previous_price is not None:
        primary_listing_source['previousPrice'] = previous_price
    if shelter is not None:
        primary_listing_source['shelter'] = bool(shelter) if isinstance(shelter, bool) else shelter
    if accessibility is not None:
        primary_listing_source['accessibility'] = bool(accessibility) if isinstance(accessibility, bool) else accessibility
    if building_class is not None:
        primary_listing_source['buildingClass'] = building_class
    if general_condition is not None:
        primary_listing_source['generalCondition'] = general_condition
    if investment_yield is not None:
        primary_listing_source['investmentYield'] = investment_yield
    if approximate_rent is not None:
        primary_listing_source['approximateRent'] = approximate_rent
    if commute_time is not None:
        primary_listing_source['commuteTime'] = commute_time
    if published_days is not None:
        primary_listing_source['publishedDays'] = published_days
    if date_posted is not None:
        primary_listing_source['datePosted'] = date_posted
    if tag_best_school is not None:
        primary_listing_source['tagBestSchool'] = bool(tag_best_school) if isinstance(tag_best_school, bool) else tag_best_school
    if tag_safety is not None:
        primary_listing_source['tagSafety'] = bool(tag_safety) if isinstance(tag_safety, bool) else tag_safety
    if tag_family_friendly is not None:
        primary_listing_source['tagFamilyFriendly'] = bool(tag_family_friendly) if isinstance(tag_family_friendly, bool) else tag_family_friendly
    if tag_light_rail is not None:
        primary_listing_source['tagLightRail'] = bool(tag_light_rail) if isinstance(tag_light_rail, bool) else tag_light_rail
    if tag_park_access is not None:
        primary_listing_source['tagParkAccess'] = bool(tag_park_access) if isinstance(tag_park_access, bool) else tag_park_access
    if tag_quiet_street is not None:
        primary_listing_source['tagQuietStreet'] = bool(tag_quiet_street) if isinstance(tag_quiet_street, bool) else tag_quiet_street
    if tag_commute is not None:
        primary_listing_source['tagCommute'] = bool(tag_commute) if isinstance(tag_commute, bool) else tag_commute
    if exclusive is not None:
        primary_listing_source['exclusive'] = bool(exclusive)
        logger.debug('[ASSET_FIELDS] Set exclusive from listing: %s', exclusive)

    asset.meta['primary_listing_source'] = primary_listing_source
    update_fields.add('meta')
    
    if update_fields:
        asset.save(update_fields=list(update_fields))
        logger.info('[ASSET_FIELDS] Updated asset %s fields: %s', asset.id, list(update_fields))


def _is_transaction_commercial(transaction: Dict[str, Any]) -> Optional[bool]:
    """Check if a transaction is commercial based on asset_type field.
    
    Args:
        transaction: Transaction dictionary with asset_type field
        
    Returns:
        True if transaction is explicitly commercial,
        False if transaction is explicitly residential, default
    """
    if not isinstance(transaction, dict):
        return None
    
    asset_type = transaction.get('asset_type') or transaction.get('assetType')
    if not asset_type or not isinstance(asset_type, str):
        return None
    
    asset_type_lower = asset_type.strip().lower()
    
    # Common residential types in Hebrew
    residential_types = ['דירה', 'בית', 'וילה', 'קוטג', 'נטהאוז', 'דופלקס', 'טריפלקס', 'חד משפחתי' ,'דו משפחתי', 'מרתף', 'גג']
    
    # If asset_type is explicitly residential, return False
    if asset_type_lower in residential_types:
        return False
    
    # Common commercial indicators
    commercial_indicators = ['משרד', 'חנות', 'מסחרי', 'מסחר', 'משרדים', 'מחסן', 'בית מסחר', 'קומת מסחר']
    
    # Check if asset_type contains commercial indicators
    for indicator in commercial_indicators:
        if indicator in asset_type_lower:
            return True

    # By default, non-commercial
    return False


def _is_listing_commercial(listing_data: Dict[str, Any]) -> bool:
    """Check if a listing is commercial.
    
    Args:
        listing_data: Listing dictionary
        
    Returns:
        True if listing is commercial, False otherwise
    """
    if not isinstance(listing_data, dict):
        return False

    _, normalized_listing_type = _extract_listing_type(listing_data)
    if normalized_listing_type == 'commercial':
        return True

    return listing_data.get('ad_type', '') == 'commercial' or listing_data.get('adType', '') == 'commercial'


def _calculate_market_metrics(asset, listings, gov_data):
    """Calculate and persist market metrics.

    - Computes metrics from Yad2 listings and Nadlan transactions (prices, areas)
    - Calculates price per square meter (PPM) from both sources
    - Derives model price as PPM × asset total area
    - Derives confidence, competition, rent estimate, cap rate, DOM percentile
    - Generates risk flags heuristically
    - Stores camelCase metrics in asset.meta['market_metrics'] for backward compatibility
    - Maps a subset to snake_case Asset fields
    
    Note: Only compares commercial assets with commercial assets, and non-commercial with non-commercial.
    """
    try:
        listing_dicts = _normalize_listings(listings or []) if listings else []
        metrics: Dict[str, Any] = {}

        # --- Extract transaction data from gov_data ---
        transactions = []
        if gov_data and 'transactions' in gov_data:
            transactions = gov_data['transactions'] or []

        # Get asset's commercial status (default to False if None)
        asset_is_commercial = bool(getattr(asset, 'is_commercial', False))

        # --- Calculate Price Per Square Meter (PPM) from both sources ---
        ppm_data = []
        
        # From Yad2 and Madlan listings
        if listing_dicts:
            for listing in listing_dicts:
                price = listing.get('price')
                area = _get_listing_area_for_ppm(listing)
                if price and area and area > 0:
                    _, normalized_listing_type = _extract_listing_type(listing)
                    if normalized_listing_type == 'rent':
                        continue
                    
                    # Filter by commercial status: only include listings that match asset's commercial status
                    listing_is_commercial = _is_listing_commercial(listing)
                    if listing_is_commercial != asset_is_commercial:
                        continue
                    
                    # Filter out outliers: area < 10 sqm or unrealistic price per sqm
                    # This prevents data errors from skewing the model price
                    if area < 10:
                        continue  # Skip very small areas (likely data errors, parking spaces, or storage units)
                    
                    ppm = price / area
                    
                    # Filter out unrealistic PPM values (outside 1K-500K range)
                    # This prevents outliers from skewing the average PPM calculation
                    if ppm < 1000 or ppm > 500000:
                        continue  # Skip unrealistic price per sqm values
                    
                    # Determine source from URL or meta
                    url = listing.get('url', '')
                    source = 'yad2'  # default
                    if isinstance(url, str):
                        if 'madlan.co.il' in url.lower():
                            source = 'madlan'
                        elif 'yad2.co.il' in url.lower():
                            source = 'yad2'
                    
                    # Check meta for source
                    meta = listing.get('meta', {})
                    if isinstance(meta, dict):
                        meta_source = meta.get('source')
                        if meta_source in ('yad2', 'madlan'):
                            source = meta_source
                    
                    ppm_data.append({
                        'ppm': ppm,
                        'price': price,
                        'area': area,
                        'source': source,
                        'address': listing.get('address', ''),
                        'rooms': listing.get('rooms'),
                        'floor': listing.get('floor')
                    })

        # From Nadlan transactions
        if transactions:
            for transaction in transactions:
                price = transaction.get('deal_amount') or transaction.get('price')
                area = transaction.get('area')
                if price and area and area > 0:
                    # Filter by commercial status: only include transactions that match asset's commercial status
                    transaction_is_commercial = _is_transaction_commercial(transaction)
                    # Only include transactions that match asset's commercial status
                    if transaction_is_commercial != asset_is_commercial:
                        continue
                    
                    # Filter out outliers: area < 10 sqm or unrealistic price per sqm
                    # This prevents data errors (like 1 sqm transactions) from skewing the model price
                    if area < 10:
                        continue  # Skip very small areas (likely data errors, parking spaces, or storage units)
                    
                    ppm = price / area
                    
                    # Filter out unrealistic PPM values (outside 1K-500K range)
                    # This prevents outliers from skewing the average PPM calculation
                    if ppm < 1000 or ppm > 500000:
                        continue  # Skip unrealistic price per sqm values
                    
                    ppm_data.append({
                        'ppm': ppm,
                        'price': price,
                        'area': area,
                        'source': 'nadlan',
                        'address': transaction.get('address', ''),
                        'rooms': transaction.get('rooms'),
                        'floor': transaction.get('floor'),
                        'deal_date': transaction.get('deal_date')
                    })

        # --- Calculate market metrics based on PPM ---
        if ppm_data:
            ppm_values = [d['ppm'] for d in ppm_data]
            prices = [d['price'] for d in ppm_data]
            areas = [d['area'] for d in ppm_data]

            asset_total_area = _safe_numeric(getattr(asset, 'total_area', None)) or _safe_numeric(getattr(asset, 'area', None))
            base_ppm, base_value = _calculate_base_ppm_and_value(ppm_data, asset_total_area)

            feature_vector = _build_feature_vector(asset)
            adjustment_multiplier = 1 + feature_vector.total_adjustment

            # Calculate model price as BaseValue × (1 + Σ adjustments)
            if base_ppm is not None:
                if base_value is None and asset_total_area and asset_total_area > 0:
                    base_value = base_ppm * asset_total_area

                if base_value is None:
                    # Fallback to median comparable price if no area
                    base_value = median(prices)

                adjusted_model_price = int(base_value * adjustment_multiplier)
                metrics['baseModelPrice'] = int(base_value)
                metrics['modelPrice'] = adjusted_model_price
                metrics['adjustments'] = {
                    'multiplier': adjustment_multiplier,
                    'totalPct': round(feature_vector.total_adjustment * 100, 2),
                    'featureVector': feature_vector.to_dict(),
                }

                if asset_total_area and asset_total_area > 0:
                    adjusted_ppm = base_ppm * adjustment_multiplier
                    metrics['adjustedPricePerSqm'] = round(adjusted_ppm, 2)

                # Calculate price gap if asset has a price
                price_value = _safe_numeric(getattr(asset, 'price', None))
                if price_value and adjusted_model_price > 0:
                    metrics['priceGapPct'] = round(((price_value - adjusted_model_price) / adjusted_model_price) * 100, 2)

            # Store PPM statistics
            if base_ppm is not None:
                metrics['avgPricePerSqm'] = round(base_ppm, 2)
            metrics['minPricePerSqm'] = round(min(ppm_values), 2)
            metrics['maxPricePerSqm'] = round(max(ppm_values), 2)
            metrics['expectedPriceRange'] = f"{min(prices):,} - {max(prices):,}"

            # Enhanced confidence calculation
            # Weight transactions higher than listings (transactions are actual sales)
            transaction_count = len([d for d in ppm_data if d['source'] == 'nadlan'])
            yad2_listing_count = len([d for d in ppm_data if d['source'] == 'yad2'])
            madlan_listing_count = len([d for d in ppm_data if d['source'] == 'madlan'])
            listing_count = yad2_listing_count + madlan_listing_count

            # Base confidence: 15% per transaction, 10% per listing, max 100%
            confidence = min(100, (transaction_count * 15) + (listing_count * 10))
            metrics['confidencePct'] = confidence

            # Store source breakdown
            metrics['ppmSources'] = {
                'transactions': transaction_count,
                'yad2_listings': yad2_listing_count,
                'madlan_listings': madlan_listing_count,
                'listings': listing_count,
                'total': len(ppm_data)
            }

            # Area comparison
            asset_area_value = _safe_numeric(getattr(asset, 'area', None))
            if areas and asset_area_value:
                avg_area = sum(areas) / len(areas)
                if avg_area > 0:
                    metrics['deltaVsAreaPct'] = round(((asset_area_value - avg_area) / avg_area) * 100, 2)

            # Competition heuristic based on total comparable data
            n = len(ppm_data)
            if n > 10:
                metrics['competition1km'] = 'גבוהה'
            elif n > 5:
                metrics['competition1km'] = 'בינונית'
            else:
                metrics['competition1km'] = 'נמוכה'

            # DOM percentile heuristic (coarse)
            metrics['domPercentile'] = min(90, n * 10)
        else:
            # No comps -> low confidence baseline
            metrics['confidencePct'] = 0
            metrics['ppmSources'] = {'transactions': 0, 'listings': 0, 'total': 0}

        # --- Rent & Cap Rate ---
        if asset.price:  # need price for rent estimation
            # Calculate rent based on city-specific gross yield
            gross_yield_pct = get_city_gross_yield(asset.city, asset.neighborhood)
            # Gross Yield = Annual Rent / Property Price
            # Therefore: Annual Rent = Property Price × Gross Yield %
            annual_rent = asset.price * (gross_yield_pct / 100)
            monthly_rent = annual_rent / 12
            metrics['rentEstimate'] = int(monthly_rent)
            # Cap rate is the same as gross yield in this calculation
            metrics['capRatePct'] = round(gross_yield_pct, 2)

        # --- Risk Flags ---
        risk_flags = []
        if abs(metrics.get('priceGapPct', 0)) > 20:
            risk_flags.append('פער מחיר גבוה')
        if abs(metrics.get('deltaVsAreaPct', 0)) > 30:
            risk_flags.append('פער שטח גבוה')
        if metrics.get('confidencePct', 0) < 40:
            risk_flags.append('ביטחון נמוך')
        metrics['riskFlags'] = risk_flags

        # --- Persist to meta (camelCase retained) ---
        if not asset.meta:
            asset.meta = {}
        asset.meta['market_metrics'] = metrics

        # --- Map camelCase to snake_case model fields ---
        field_map = {
            'priceGapPct': 'price_gap_pct',
            'expectedPriceRange': 'expected_price_range',
            'modelPrice': 'model_price',
            'confidencePct': 'confidence_pct',
            'deltaVsAreaPct': 'delta_vs_area_pct',
            'capRatePct': 'cap_rate_pct',
            'competition1km': 'competition_1km',
            'riskFlags': 'risk_flags',
            'domPercentile': 'dom_percentile',
            'rentEstimate': 'rent_estimate',
            'avgPricePerSqm': 'avg_price_per_sqm',
            'minPricePerSqm': 'min_price_per_sqm',
            'maxPricePerSqm': 'max_price_per_sqm',
        }
        update_fields = {'meta'}
        for camel, snake in field_map.items():
            if camel in metrics and hasattr(asset, snake):
                setattr(asset, snake, metrics[camel])
                update_fields.add(snake)

        asset.save(update_fields=list(update_fields))
        logger.debug('[MARKET_METRICS] asset=%s metrics=%s', asset.id, metrics)
    except Exception as e:  # pragma: no cover - defensive
        logger.error('Failed to calculate market metrics for asset %s: %s', getattr(asset, 'id', '?'), e)


def _calculate_planning_legal_analysis(asset, gis_data: Dict[str, Any], gov_data: Dict[str, Any]) -> None:
    """Calculate and persist planning and legal analysis fields.
    
    Calculates:
    - Rights usage percentage (רמת ניצול זכויות)
    - Legal restrictions (מגבלות משפטיות)
    - Urban renewal potential (פוטנציאל התחדשות)
    - Betterment levy (היטל השבחה צפוי)
    """
    try:
        # Get tabu data from gov_data if available
        tabu_data = gov_data.get('tabu_data') if gov_data else None
        
        # Calculate planning and legal analysis
        analysis = calculate_planning_legal_analysis(asset, gis_data, tabu_data)
        
        # Apply results to asset
        apply_planning_legal_analysis_to_asset(asset, analysis)
        
        # Save the asset with updated fields
        update_fields = []
        if analysis.rights_usage_pct is not None:
            update_fields.append('rights_usage_pct')
        if analysis.legal_restrictions:
            update_fields.append('legal_restrictions')
        if analysis.urban_renewal_potential:
            update_fields.append('urban_renewal_potential')
        if analysis.betterment_levy:
            update_fields.append('betterment_levy')
        if analysis.building_coverage_pct is not None:
            update_fields.append('building_coverage_pct')
        if analysis.height_analysis:
            update_fields.append('height_analysis')
        if analysis.setback_analysis:
            update_fields.append('setback_analysis')
            
        if update_fields:
            asset.save(update_fields=update_fields)
            logger.debug('[PLANNING_LEGAL] asset=%s analysis=%s', asset.id, {
                'rights_usage_pct': analysis.rights_usage_pct,
                'legal_restrictions': analysis.legal_restrictions,
                'urban_renewal_potential': analysis.urban_renewal_potential,
                'betterment_levy': analysis.betterment_levy
            })
        
    except Exception as e:  # pragma: no cover - defensive
        logger.error('Failed to calculate planning and legal analysis for asset %s: %s', getattr(asset, 'id', '?'), e)
def _create_documents_and_plans(asset, gis_data, gov_data, plans, mavat_plans, handasa_archive):
    """Create Document and Plan records from collected data."""
    try:
        User = get_user_model()
        
        # Get or create a system user for automated documents
        system_user, created = User.objects.get_or_create(
            email='system@nadlaner.com',
            defaults={
                'first_name': 'System',
                'last_name': 'User',
                'is_active': False
            }
        )

        if Document is None or Plan is None:
            logger.warning(
                "Django models unavailable; skipping document/plan creation for asset %s",
                getattr(asset, 'id', None),
            )
            return
        
        
        if gis_data and gis_data.get('permits'):
            _create_documents_from_permits(asset, gis_data.get('permits', []), source='GIS')

        if handasa_archive:
            handasa_permits = [
                doc for doc in handasa_archive if (doc.get('document_type') or '').startswith('permit')
            ]
            if handasa_permits:
                _create_documents_from_permits(asset, handasa_permits, source='Handasa')

        # Create Document records from government appraisals
        if gov_data and gov_data.get('decisive'):
            for appraisal in gov_data.get('decisive', []):
                appraisal_id = appraisal.get('id')
                if not appraisal_id:
                    continue

                parsed_date = _parse_document_date(appraisal.get('date'))
                document_payload = {
                    'title': f"שומה החלטית {appraisal_id}",
                    'description': f"שומה החלטית מספר {appraisal_id}",
                    'status': 'approved',
                    'external_url': appraisal.get('url', ''),
                    'source': 'gov',
                    'document_date': parsed_date,
                    'file_size': 0,
                    'filename': f"appraisal_decisive_{appraisal_id}.pdf",
                    'file_path': '',
                    'mime_type': 'application/pdf',
                    'meta': appraisal,
                }

                document, created_doc = _upsert_document(
                    'appraisal_decisive',
                    appraisal_id,
                    document_payload,
                    asset=asset,
                    user=system_user,
                )

        # Create Plan/Document records from GIS plans
        if gis_data:
            local_plans = gis_data.get('local_plans') or []
            city_plans = gis_data.get('city_plans') or []

            if local_plans:
                _create_documents_from_gis_plans(asset, local_plans, 'local', system_user)

            if city_plans:
                _create_documents_from_gis_plans(asset, city_plans, 'citywide', system_user)

        # Create Plan records from RAMI plans
        if plans:
            for plan in plans:
                plan_number = plan.get('planNumber') or plan.get('plan_number', '')
                if plan_number:
                    # Create Plan record
                    plan_title = (
                        plan.get('title')
                        or plan.get('plan_name')
                        or plan.get('planName')
                        or plan.get('name')
                        or f'תכנית רמ״י {plan_number}'
                    )
                    plan_payload = {
                        'title': plan_title,
                        'description': plan.get('description') or plan_title,
                        'status': plan.get('status', ''),
                        'file_url': plan.get('url', ''),
                        'raw': plan,
                    }
                    plan_obj, _ = _upsert_plan(
                        plan_number,
                        plan_payload,
                        asset=asset,
                    )
                    
                    # Also create Document record for the plan
                    document_payload = {
                        'title': plan.get('title', f'תכנית רמ״י {plan_number}'),
                        'description': f"תכנית רמ״י מספר {plan_number}",
                        'status': 'approved' if plan.get('status') == 'מאושר' else 'pending',
                        'external_url': plan.get('url', ''),
                        'source': 'RAMI',
                        'document_date': _parse_document_date(plan.get('statusDate')),
                        'file_size': 0,
                        'filename': f"rami_plan_{plan_number}.pdf",
                        'file_path': '',
                        'mime_type': 'application/pdf',
                        'meta': plan,
                    }
                    document, doc_created = _upsert_document(
                        'plan',
                        f"rami_{plan_number}",
                        document_payload,
                        asset=asset,
                        user=system_user,
                    )
        
        # Create Plan records from Mavat plans
        if mavat_plans:
            for plan in mavat_plans:
                plan_id = plan.get('plan_id') or plan.get('id', '')
                if plan_id:
                    plan_key = f"{plan_id}"
                    plan_title = (
                        plan.get('title')
                        or plan.get('plan_name')
                        or plan.get('planName')
                        or plan.get('name')
                        or f'תכנית מנהל התיכנון {plan_id}'
                    )
                    plan_payload = {
                        'title': plan_title,
                        'description': plan.get('description') or plan_title,
                        'status': plan.get('status', ''),
                        'file_url': plan.get('url', ''),
                        'raw': plan,
                    }
                    plan_obj, _ = _upsert_plan(
                        plan_key,
                        plan_payload,
                        asset=asset,
                    )
                    
                    # Also create Document record for the plan
                    document_payload = {
                        'title': plan.get('title', f'תכנית מבת {plan_id}'),
                        'description': f"תכנית מבת מספר {plan_id}",
                        'status': 'approved' if plan.get('status') == 'מאושר' else 'pending',
                        'external_url': plan.get('url', ''),
                        'source': 'Mavat',
                        'document_date': _parse_document_date(plan.get('statusDate')),
                        'file_size': 0,
                        'filename': f"{plan_id}.pdf",
                        'file_path': '',
                        'mime_type': 'application/pdf',
                        'meta': plan,
                    }
                    document, doc_created = _upsert_document(
                        'plan_local',
                        f"{plan_id}",
                        document_payload,
                        asset=asset,
                        user=system_user,
                    )
        
        
        logger.info(f"Created documents and plans for asset {asset.id}")
        
    except Exception as e:
        logger.error(f"Failed to create documents and plans for asset {asset.id}: {e}")



def _create_documents_from_gis_plans(asset, plans, scope: str, system_user):
    """Create Plan and Document entries for GIS plan datasets."""

    if not plans:
        return

    scope_key = (scope or 'local').lower()
    doc_type = 'plan_local' if scope_key == 'local' else 'plan_citywide'
    scope_label = 'מקומית' if scope_key == 'local' else 'עירונית'

    for index, plan in enumerate(plans, start=1):
        if not isinstance(plan, dict):
            continue

        plan_number_raw = _first_nonempty(
            plan.get('taba'),
            plan.get('plan_number'),
            plan.get('planNumber'),
            plan.get('number'),
            plan.get('ms_tochnit'),
            plan.get('plan_no'),
            plan.get('planNo'),
        )
        if not plan_number_raw:
            continue

        plan_number_str = str(plan_number_raw).strip()
        if not plan_number_str:
            continue

        plan_name = _first_nonempty(
            plan.get('shem_taba'),
            plan.get('plan_name'),
            plan.get('planName'),
            plan.get('name'),
            plan.get('title'),
        )

        plan_status = _first_nonempty(
            plan.get('t_status'),
            plan.get('t_status_klali'),
            plan.get('status'),
            plan.get('plan_status'),
            plan.get('status_name'),
        ) or ''

        plan_description = _first_nonempty(
            plan.get('description'),
            plan.get('remarks'),
            plan.get('note'),
        )

        if not plan_description:
            details = [
                value.strip()
                for value in (
                    plan.get('t_sivug') or '',
                    plan.get('t_hekef') or '',
                    plan.get('t_ramat_pirut') or '',
                )
                if value and str(value).strip()
            ]
            if details:
                plan_description = " | ".join(details)

        external_url = _first_nonempty(
            plan.get('url_documents'),
            plan.get('url_iplan'),
            plan.get('url'),
            plan.get('external_url'),
            plan.get('link'),
            plan.get('download_url'),
            plan.get('document_url'),
        )

        urls_field = plan.get('urls')
        if isinstance(urls_field, list) and urls_field:
            external_url = external_url or urls_field[0]
        elif isinstance(urls_field, str) and urls_field.strip():
            external_url = external_url or urls_field.strip()

        def _extract_plan_date(value):
            if value in (None, '', 0):
                return None
            if isinstance(value, (int, float)):
                return _convert_unix_timestamp_to_date(int(value))
            if isinstance(value, date):
                return value
            if isinstance(value, str):
                parsed = _parse_document_date(value)
                if parsed:
                    return parsed
                digits = ''.join(ch for ch in value if ch.isdigit())
                if digits:
                    try:
                        return _convert_unix_timestamp_to_date(int(digits))
                    except Exception:  # pragma: no cover - defensive parse
                        return None
            return None

        effective_date = _extract_plan_date(
            _first_nonempty(plan.get('tr_matan_tokef'), plan.get('effective_date'), plan.get('effectiveDate'))
        )
        deposit_date = _extract_plan_date(
            _first_nonempty(plan.get('tr_hafkada'), plan.get('deposit_date'), plan.get('depositDate'))
        )
        status_change_date = _extract_plan_date(plan.get('tr_shinuy_status'))

        plan_title = plan_name or f"תכנית {scope_label} {plan_number_str}"
        plan_description = plan_description or plan_title

        plan_payload = {
            'title': plan_title,
            'description': plan_description,
            'status': plan_status,
            'file_url': (external_url or ''),
            'raw': plan,
        }

        if effective_date:
            plan_payload['effective_date'] = effective_date

        _upsert_plan(plan_number_str, plan_payload, asset=asset)

        normalized_id = re.sub(r'[^0-9A-Za-z]+', '_', plan_number_str).strip('_') or str(index)
        filename = plan.get('shem_mismach') or f"gis_{scope_key}_{normalized_id}.pdf"
        inferred_mime = 'application/pdf'

        def _infer_mime_from_name(name: Optional[str]) -> Optional[str]:
            if not name:
                return None
            lower_name = str(name).lower()
            if lower_name.endswith('.pdf'):
                return 'application/pdf'
            if lower_name.endswith('.docx'):
                return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            if lower_name.endswith('.doc'):
                return 'application/msword'
            if lower_name.endswith('.zip'):
                return 'application/zip'
            return None

        inferred = _infer_mime_from_name(filename) or _infer_mime_from_name(external_url)
        if inferred:
            inferred_mime = inferred
        else:
            inferred_mime = 'application/octet-stream'

        doc_status = 'approved' if _is_plan_status_approved(plan_status) else 'pending'

        document_payload = {
            'title': plan_title,
            'description': f"תכנית {scope_label} מספר {plan_number_str}",
            'status': doc_status,
            'external_url': external_url or '',
            'source': 'GIS',
            'document_date': effective_date or deposit_date or status_change_date,
            'file_size': int(plan.get('ms_mismach') or 0) if str(plan.get('ms_mismach') or '').strip().isdigit() else 0,
            'filename': filename,
            'file_path': '',
            'mime_type': inferred_mime,
            'meta': plan,
        }

        _upsert_document(
            doc_type,
            plan_name,
            document_payload,
            asset=asset,
            user=system_user,
        )


def _is_plan_status_approved(status: Optional[str]) -> bool:
    """Return True if the plan status indicates an approved/effective plan."""

    if not status:
        return False

    normalized = str(status).lower()
    approved_keywords = ('מאושר', 'בתוקף', 'approved', 'תקף')
    return any(keyword in normalized for keyword in approved_keywords)


def _create_documents_from_permits(asset, permits, source: str = 'GIS'):
    """Create documents from permit datasets (GIS or Handasa)."""

    if not permits:
        return

    User = get_user_model()
    system_user, _ = User.objects.get_or_create(
        username='system',
        defaults={
            'email': 'system@nadlaner.com',
            'first_name': 'System',
            'last_name': 'Pipeline'
        }
    )

    created_count = 0
    safe_source = source or 'GIS'

    if Document is None:
        logger.warning(
            "Document model unavailable; skipping %s permit documents for asset %s",
            safe_source,
            getattr(asset, 'id', None),
        )
        return

    for index, permit in enumerate(permits, start=1):
        if not permit:
            continue

        normalized_doc = _normalize_permit_document_fields(permit, safe_source, index)
        if not normalized_doc:
            continue

        doc_type = normalized_doc.get('document_type', 'permit')
        external_id = normalized_doc.get('external_id')
        if not external_id:
            continue

        document_payload = {
            key: value
            for key, value in normalized_doc.items()
            if key not in ('document_type', 'external_id')
        }
        document, doc_created = _upsert_document(
            doc_type,
            external_id,
            document_payload,
            asset=asset,
            user=system_user,
        )

        permit_raw = permit if isinstance(permit, dict) else {}
        if not permit_raw and isinstance(document_payload.get('meta'), dict):
            permit_raw = document_payload.get('meta', {})

        issued_date = document_payload.get('document_date') or _extract_permit_date(
            permit_raw.get('permission_date')
            or permit_raw.get('issue_date')
            or permit_raw.get('issued_at')
            or permit_raw.get('license_issue_date')
        )
        expiry_date = None
        for candidate_key in (
            'expiry_date',
            'expiration_date',
            'license_exp_date',
            'license_expiration_date',
            'valid_until',
            'valid_till',
            'permit_expiration_date',
            'exp_date',
        ):
            candidate_value = permit_raw.get(candidate_key)
            parsed = _extract_permit_date(candidate_value)
            if parsed:
                expiry_date = parsed
                break

        permit_payload = {
            'description': document_payload.get('description') or document_payload.get('title', ''),
            'status': document_payload.get('status', ''),
            'issued_date': issued_date,
            'expiry_date': expiry_date,
            'file_url': document_payload.get('external_url', ''),
        }
        _upsert_permit(
            external_id,
            permit_payload,
            asset=asset,
            raw=permit_raw or {},
        )

        if doc_created:
            created_count += 1
            logger.debug(
                "Created %s permit document for asset %s (external_id=%s)",
                safe_source,
                getattr(asset, 'id', None),
                external_id,
            )
        else:
            logger.debug(
                "Updated %s permit document %s for asset %s",
                safe_source,
                getattr(document, 'id', None),
                getattr(asset, 'id', None),
            )

    logger.info(
        "Processed %d %s permits for asset %s (%d new, %d updated)",
        len(permits),
        safe_source,
        asset.id,
        created_count,
        len(permits) - created_count,
    )


def _normalize_permit_document_fields(permit: Dict[str, Any], source: str, fallback_index: int) -> Optional[Dict[str, Any]]:
    """Normalize permit payloads from different collectors for Document creation."""

    if not isinstance(permit, dict):
        return None

    source_key = source.lower()
    if source_key == 'handasa':
        meta = permit.get('meta') if isinstance(permit.get('meta'), dict) else dict(permit)
        external_id_raw = (
            permit.get('external_id')
            or permit.get('permission_num')
            or permit.get('request_num')
            or meta.get('UniqueID')
        )
        if external_id_raw:
            external_id = str(external_id_raw).strip()
            if external_id.startswith("{") and external_id.endswith("}"):
                external_id = external_id[1:-1]
        else:
            external_id = f"handasa_{fallback_index}"

        document_date = permit.get('document_date')
        if isinstance(document_date, str):
            parsed_date = _parse_document_date(document_date)
            if not parsed_date:
                try:
                    parsed_date = datetime.fromisoformat(document_date.replace('Z', '+00:00')).date()
                except Exception:  # pragma: no cover - defensive parsing
                    parsed_date = None
        else:
            parsed_date = document_date

        if not parsed_date:
            handasa_doc_date = meta.get('TlvMPEngDocDate')
            if handasa_doc_date:
                parsed_date = _extract_permit_date(handasa_doc_date)

        title = permit.get('title') or f"היתר {external_id}" if external_id else "היתר בנייה"
        description = permit.get('description') or meta.get('TlvMPEngDocumentType', '')
        status = permit.get('status', '')
        external_url = permit.get('external_url') or meta.get('Path', '')

        document_type = permit.get('document_type') or 'permit'
        document_category = permit.get('document_category')
        meta = dict(meta or {})
        meta['handasa_document_type'] = document_type
        if document_category is not None:
            meta['handasa_document_category'] = document_category

        permit_number = (
            permit.get('permission_num')
            or meta.get('TlvMPEngPermitNum')
            or meta.get('permit_number')
        )
        if permit_number:
            meta['permit_number'] = str(_normalize_identifier(permit_number))

        request_num = (
            permit.get('request_num')
            or meta.get('TlvMPEngRequestNum')
            or meta.get('TlvMPEngOnlineReqNum')
        )
        if request_num:
            meta['request_num'] = str(_normalize_identifier(request_num))

        addresses = (
            permit.get('addresses')
            or permit.get('assets', [{}])[0].get('address')
            or meta.get('addresses')
        )
        if isinstance(addresses, str) and addresses:
            meta['addresses'] = addresses.replace('_', ' ').strip()

        building_stage = (
            permit.get('building_stage')
            or meta.get('building_stage')
        )
        if building_stage:
            meta['building_stage'] = building_stage

        meta.setdefault('tochen_bakasha', description or title)

        return {
            'external_id': external_id,
            'title': title,
            'description': description,
            'status': status,
            'filename': f"{external_id}.pdf",
            'file_path': '',
            'file_size': 0,
            'mime_type': 'application/pdf',
            'external_url': external_url,
            'source': 'Handasa',
            'document_date': parsed_date,
            'meta': meta,
            'document_type': document_type,
        }

    # Default: GIS permits structure
    permission_num = permit.get('permission_num')
    request_num = permit.get('request_num')
    external_id = str(_normalize_identifier(permission_num or request_num or f"gis_{fallback_index}"))

    return {
        'external_id': external_id,
        'title': permit.get('koteret', ''),
        'description': permit.get('sug_bakasha', ''),
        'status': permit.get('building_stage', ''),
        'filename': f"{permission_num or external_id}.pdf",
        'file_path': './permits/',
        'file_size': 0,
        'mime_type': 'application/pdf',
        'external_url': permit.get('url_hadmaya', ''),
        'source': 'GIS',
        'document_date': _convert_unix_timestamp_to_date(permit.get('permission_date', 0)),
        'meta': permit,
        'document_type': 'permit',
    }
def _create_documents_from_appraisals(asset, appraisals):
    """Create documents from government appraisals data."""
    if not appraisals:
        return
    if Document is None:
        logger.warning(
            "Document model unavailable; skipping appraisal documents for asset %s",
            getattr(asset, 'id', None),
        )
        return
    
    # Get a system user or create one for automated processes
    User = get_user_model()
    system_user, _ = User.objects.get_or_create(
        username='system',
        defaults={
            'email': 'system@nadlaner.com',
            'first_name': 'System',
            'last_name': 'Pipeline'
        }
    )
    
    created_count = 0
    # Create documents for each appraisal
    for appraisal in appraisals:
        if not appraisal:
            continue
            
        # Extract appraisal information
        appraiser = appraisal.get('appraiser', 'לא זמין')
        appraised_value = appraisal.get('appraised_value', appraisal.get('value'))
        appraisal_date = appraisal.get('appraisal_date', appraisal.get('date'))
        url = appraisal.get('url', '')
        
        # Convert date from DD.MM.YYYY to YYYY-MM-DD format
        parsed_date = _parse_document_date(appraisal_date)
        
        # Validate and clean URL
        if url and not url.startswith(('http://', 'https://')):
            if url.startswith('/'):
                url = f"https://www.gov.il{url}"
            else:
                url = f"https://www.gov.il/{url}"
        
        external_id = f"appraisal_{appraisal.get('id', len(appraisals))}"
        document_payload = {
            'title': f"שומה מכריעה - {appraiser}",
            'description': f"שומה מכריעה על ידי {appraiser}",
            'status': 'approved',
            'external_url': url,
            'source': 'gov',
            'document_date': parsed_date,
            'file_size': 0,
            'filename': f"appraisal_{appraisal.get('id', 'unknown')}.pdf",
            'file_path': '',
            'mime_type': 'application/pdf',
            'meta': {
                'appraiser': appraiser,
                'appraised_value': appraised_value,
                'downloadable': bool(url and url.startswith(('http://', 'https://'))),
            },
        }
        document, doc_created = _upsert_document(
            'appraisal',
            external_id,
            document_payload,
            asset=asset,
            user=system_user,
        )
        if doc_created:
            created_count += 1
    
    logger.info(f"Created {created_count} appraisal documents for asset {asset.id}")


def _create_documents_from_rami_plans(asset, plans):
    """Create documents from RAMI plans data (robust to missing/None sub-keys)."""
    if not plans:
        return
    if Document is None:
        logger.warning(
            "Document model unavailable; skipping RAMI documents for asset %s",
            getattr(asset, 'id', None),
        )
        return

    # Get a system user or create one for automated processes
    User = get_user_model()
    system_user, _ = User.objects.get_or_create(
        username='system',
        defaults={
            'email': 'system@nadlaner.com',
            'first_name': 'System',
            'last_name': 'Pipeline'
        }
    )

    if Document is None:
        logger.warning(
            "Document model unavailable; skipping RAMI plan documents for asset %s",
            getattr(asset, 'id', None),
        )
        return

    created = 0
    for plan in plans or []:
        if not isinstance(plan, dict):
            continue

        plan_number = _first_nonempty(
            plan.get('planNumber'),
            plan.get('plan_number'),
            plan.get('number'),
        )
        plan_name = _first_nonempty(
            plan.get('title'),
            plan.get('plan_name'),
            plan.get('name'),
        )
        status = plan.get('status', '')

        # documentsSet can be {}, None, or missing entirely — handle all
        raw = plan.get('raw') or {}
        documents_set = raw.get('documentsSet') or {}

        # child entries can be dicts or None — guard each before reading 'path'
        map_entry     = _safe_get(documents_set, 'map')
        takanon_entry = _safe_get(documents_set, 'takanon')
        mmg_entry     = _safe_get(documents_set, 'mmg')

        url = _first_nonempty(
            _safe_get(map_entry, 'path'),
            _safe_get(takanon_entry, 'path'),
            _safe_get(mmg_entry, 'path'),
            plan.get('url'),  # last resort if provided on the plan itself
        ) or ''

        # Normalize RAMI relative URLs
        if url and not url.startswith(('http://', 'https://')):
            if url.startswith('/'):
                url = f"https://rami.gov.il{url}"
            else:
                url = f"https://rami.gov.il/{url}"

        # Create Document record
        # Parse document date properly
        parsed_date = _parse_document_date(plan.get('statusDate', plan.get('date', '')))
        
        external_id = f"rami_plan_{plan_number}" if plan_number else f"rami_plan_{created + 1}"
        document_payload = {
            'title': f"תכנית רמ״י - {plan_name}" if plan_name else (f"תכנית רמ״י {plan_number}" if plan_number else "תכנית רמ״י"),
            'description': f"תכנית רמ״י {plan_number}" if plan_number else "תכנית רמ״י",
            'status': 'approved' if status == 'מאושר' else 'pending',
            'external_url': url,
            'source': 'RAMI',
            'document_date': parsed_date,
            'file_size': 0,
            'filename': f"rami_plan_{plan_number}.pdf" if plan_number else f"rami_plan_{created + 1}.pdf",
            'file_path': '',
            'mime_type': 'application/pdf',
            'meta': {
                'plan_number': plan_number,
                'plan_name': plan_name,
                'downloadable': bool(url and url.startswith(('http://', 'https://'))),
            },
        }
        document, doc_created = _upsert_document(
            'plan',
            external_id,
            document_payload,
            asset=asset,
            user=system_user,
        )
        if doc_created:
            created += 1

    logger.info("Created %d RAMI plan documents for asset %s", created, asset.id)

# ---------------------------------------------------------------------------
# Dynamic field calculation helpers
# ---------------------------------------------------------------------------

def _calculate_public_buildings(gis_data: Dict[str, Any], asset) -> str:
    """Calculate public buildings text based on available infrastructure."""
    indicators = []
    
    # Check for shelters (public safety infrastructure)
    shelter_distance = asset.get_property_value('shelterDistanceM')
    if shelter_distance and shelter_distance <= 200:
        indicators.append('מקלטים קרובים')
    
    # Check for green areas (public spaces)
    green_within_300m = asset.get_property_value('greenWithin300m')
    if green_within_300m:
        indicators.append('שטחים ירוקים')
    
    # Check for schools and kindergartens (new GIS data)
    schools_count = asset.get_property_value('schoolsCount') or 0
    if schools_count > 0:
        indicators.append(f'בתי ספר וגני ילדים ({schools_count})')
    
    # Check for medical facilities (new GIS data)
    medical_count = asset.get_property_value('medicalFacilitiesCount') or 0
    if medical_count > 0:
        indicators.append(f'מתקנים רפואיים ({medical_count})')
    
    # Check for community facilities (new GIS data)
    community_count = asset.get_property_value('communityFacilitiesCount') or 0
    if community_count > 0:
        indicators.append(f'מתקני קהילה ({community_count})')
    
    # Check for public buildings in permits
    permits = gis_data.get('permits', [])
    public_building_permits = []
    for permit in permits:
        if isinstance(permit, dict):
            # Look for permits that might indicate public buildings
            building_stage = permit.get('building_stage', '').lower()
            tochen_bakasha = permit.get('tochen_bakasha', '').lower()
            if any(keyword in building_stage or keyword in tochen_bakasha 
                   for keyword in ['ציבורי', 'ממשלתי', 'עירייה', 'בית ספר', 'גן ילדים', 'מרפאה']):
                public_building_permits.append(permit)
    
    if public_building_permits:
        indicators.append(f'מבני ציבור בהקמה ({len(public_building_permits)} היתרים)')
    
    if indicators:
        return f"מבני ציבור בקרבת מקום: {', '.join(indicators)}"
    else:
        return "אין מבני ציבור קרובים"

def _calculate_parking_availability(gis_data: Dict[str, Any], asset) -> str:
    """Calculate parking availability based on permits, land use data, and parking lots."""
    parking_indicators = []
    
    # Check for parking lots (new GIS data)
    parking_lots_count = asset.get_property_value('parkingLotsCount') or 0
    public_parking_count = asset.get_property_value('publicParkingLotsCount') or 0
    if parking_lots_count > 0:
        if public_parking_count > 0:
            parking_indicators.append(f'חניונים ציבוריים ({public_parking_count})')
        if parking_lots_count > public_parking_count:
            private_count = parking_lots_count - public_parking_count
            parking_indicators.append(f'חניונים פרטיים ({private_count})')
    
    # Check permits for parking-related information
    permits = gis_data.get('permits', [])
    parking_permits = []
    for permit in permits:
        if isinstance(permit, dict):
            # Look for parking-related fields in permits
            tochen_bakasha = permit.get('tochen_bakasha', '').lower()
            hakala_tosefet_achuz_shetach = permit.get('hakala_tosefet_achuz_shetach', '')
            if any(keyword in tochen_bakasha for keyword in ['חניה', 'חניון', 'מקום חניה']):
                parking_permits.append(permit)
            elif hakala_tosefet_achuz_shetach and float(hakala_tosefet_achuz_shetach or 0) > 0:
                parking_permits.append(permit)
    
    if parking_permits:
        parking_indicators.append(f'היתרי חניה ({len(parking_permits)} היתרים)')
    
    # Check land use rights for parking obligations
    rights = gis_data.get('rights', [])
    if rights:
        for right in rights:
            if isinstance(right, dict):
                land_use = right.get('land_use', '').lower()
                if 'חניה' in land_use or 'חניון' in land_use:
                    parking_indicators.append('זכויות חניה בקרקע')
                    break
    
    # Check privilege page data for parking rights
    privilege_data_list = asset.get_property_value('privilege_page_data')
    if privilege_data_list:
        # Handle both old single dict format and new list format
        if isinstance(privilege_data_list, list):
            # New list format - check all privilege page data
            for privilege_data in privilege_data_list:
                if privilege_data and isinstance(privilege_data, dict):
                    parking_percentages = privilege_data.get('parking_percentages', [])
                    if parking_percentages:
                        parking_indicators.append('זכויות חניה בתוכנית')
                        break  # Found parking rights, no need to check others
        elif isinstance(privilege_data_list, dict):
            # Old single dict format - maintain backward compatibility
            parking_percentages = privilege_data_list.get('parking_percentages', [])
            if parking_percentages:
                parking_indicators.append('זכויות חניה בתוכנית')
    
    if parking_indicators:
        return f"חניה זמינה: {', '.join(parking_indicators)}"
    else:
        return "אין מידע על חניה"

def _calculate_nearby_projects(gis_data: Dict[str, Any], asset) -> str:
    """Calculate nearby projects based on recent permits, construction sites, affordable housing, and TAMA 38 areas."""
    from datetime import datetime, timedelta
    
    projects = []
    
    # Check for recent building permits (last 3 years)
    permits = gis_data.get('permits', [])
    recent_permits = []
    cutoff_date = datetime.now() - timedelta(days=3*365)
    
    for permit in permits:
        if isinstance(permit, dict) and permit.get('permission_date'):
            try:
                permit_date = datetime.fromtimestamp(permit['permission_date'] / 1000)
                if permit_date >= cutoff_date:
                    recent_permits.append(permit)
            except (ValueError, TypeError):
                continue
    
    if recent_permits:
        projects.append(f'היתרי בניה חדשים ({len(recent_permits)} היתרים)')
    
    # Check for ongoing construction sites (new GIS data)
    construction_sites_count = asset.get_property_value('constructionSitesCount') or 0
    if construction_sites_count > 0:
        projects.append(f'אתרי בנייה פעילים ({construction_sites_count})')
    
    # Check for affordable housing projects (new GIS data)
    affordable_housing_count = asset.get_property_value('affordableHousingProjectsCount') or 0
    if affordable_housing_count > 0:
        projects.append(f'פרויקטי דיור מועדף ({affordable_housing_count})')
    
    # Check for ongoing construction
    ongoing_permits = [p for p in recent_permits 
                      if p.get('building_stage', '').lower() in ['בבניה', 'הקמה', 'בתהליך']]
    if ongoing_permits:
        projects.append(f'פרויקטים בהקמה ({len(ongoing_permits)} פרויקטים)')
    
    # Check for TAMA 38 key areas (new GIS data)
    tama38_key_area = asset.get_property_value('tama38KeyArea')
    tama38_areas_count = asset.get_property_value('tama38KeyAreasCount') or 0
    if tama38_key_area and tama38_areas_count > 0:
        projects.append(f'אזורי תמ״א 38 ({tama38_areas_count})')
    
    # Check for TAMA 38 projects in permits (renovation/expansion projects)
    tama38_permits = [p for p in recent_permits 
                     if p.get('sw_tama_38') or p.get('sw_tama_38_chadash') or p.get('sw_tama_38_tosefet')]
    if tama38_permits:
        projects.append(f'פרויקטי תמ״א 38 ({len(tama38_permits)} פרויקטים)')
    
    if projects:
        return f"פרויקטים חדשים באזור: {', '.join(projects)}"
    else:
        return "אין פרויקטים חדשים באזור"

def _calculate_additional_plan_rights(plans: List[Dict[str, Any]], asset) -> str:
    """Calculate additional plan rights from RAMI plans."""
    if not plans:
        return "אין זכויות נוספות"
    
    additional_rights = []
    
    for plan in plans:
        if isinstance(plan, dict):
            plan_name = plan.get('planName', '')
            
            # Look for plans that grant additional rights
            if any(keyword in plan_name.lower() for keyword in ['הרחבה', 'תוספת', 'הגדלה', 'פיתוח']):
                additional_rights.append(f"תכנית {plan.get('planNumber', '')}: {plan_name}")
    
    if additional_rights:
        return f"זכויות נוספות: {'; '.join(additional_rights[:3])}"  # Limit to 3 plans
    else:
        return "אין זכויות נוספות"

def _calculate_public_obligations(plans: List[Dict[str, Any]], permits: List[Dict[str, Any]]) -> str:
    """Calculate public obligations from RAMI plans and permits."""
    obligations = []
    
    # Check RAMI plans for public obligations
    for plan in plans:
        if isinstance(plan, dict):
            plan_name = plan.get('planName', '')
            if any(keyword in plan_name.lower() for keyword in ['חובה', 'תרומה', 'השקעה', 'תשתית']):
                obligations.append(f"תכנית {plan.get('planNumber', '')}: {plan_name}")
    
    # Check permits for public obligations
    for permit in permits:
        if isinstance(permit, dict):
            tochen_bakasha = permit.get('tochen_bakasha', '').lower()
            if any(keyword in tochen_bakasha for keyword in ['חובה', 'תרומה', 'תשתית', 'שירותים']):
                obligations.append(f"היתר {permit.get('permission_num', '')}: חובות ציבוריות")
    
    if obligations:
        return f"חובות ציבוריות: {'; '.join(obligations[:3])}"  # Limit to 3 obligations
    else:
        return "אין חובות ציבוריות"

# ---------------------------------------------------------------------------
# Improved debugging helpers
# ---------------------------------------------------------------------------

@contextmanager
def asset_update_phase(phase: str, asset_id: int | None = None):
    """Context manager to add granular logging & exception tracing to asset update.

    Each logical phase in ``_update_asset_with_collected_data`` is wrapped in this
    context so that if one phase fails we still continue (best‑effort enrichment)
    while having a clear stack trace & phase name in the logs.
    """
    t0 = time.perf_counter()
    logger.debug("[ASSET_UPDATE] ▶ phase=%s asset_id=%s", phase, asset_id)
    try:
        yield
        dt = (time.perf_counter() - t0) * 1000
        logger.debug("[ASSET_UPDATE] ✔ phase=%s asset_id=%s duration_ms=%d", phase, asset_id, dt)
    except Exception as exc:  # noqa: BLE001 - we purposefully capture & log all
        dt = (time.perf_counter() - t0) * 1000
        logger.exception(
            "[ASSET_UPDATE] ✖ phase=%s asset_id=%s duration_ms=%d error=%s", phase, asset_id, dt, exc
        )
        debug = os.getenv("ASSET_UPDATE_DEBUG", "0").lower() in {"1", "true", "yes"}
        if debug:
            raise


__all__ = [
    "update_asset_with_collected_data",
    "create_asset_snapshot",
    "_populate_asset_fields_from_listings",
    "_calculate_market_metrics",
]
