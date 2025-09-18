from typing import Dict, Any, Optional, Iterable

from .models import Asset, SourceRecord


def _first_nonempty(*vals):
    for v in vals:
        if v not in (None, "", [], {}, 0):
            return v
    return None


def build_listing(
    asset: Asset, source_records: Optional[Iterable[SourceRecord]] = None
) -> Dict[str, Any]:
    meta = asset.meta or {}
    raw = {}
    if source_records:
        sr = next(iter(source_records), None)
        raw = (sr.raw or {}) if sr else {}

    # Use asset model fields first, then fall back to meta/raw
    bedrooms = _first_nonempty(
        asset.bedrooms, meta.get("bedrooms"), raw.get("bedrooms")
    )
    rooms = _first_nonempty(asset.rooms, meta.get("rooms"), raw.get("rooms"), bedrooms)
    net_sqm = _first_nonempty(
        asset.area,
        meta.get("netSqm"),
        meta.get("area"),
        raw.get("size"),
        raw.get("area"),
    )
    total_sqm = _first_nonempty(
        asset.total_area, meta.get("totalSqm"), raw.get("total_size")
    )
    price = _first_nonempty(asset.price, meta.get("price"), raw.get("price"))
    ptype = _first_nonempty(
        asset.building_type, meta.get("type"), raw.get("property_type")
    )

    if asset.normalized_address:
        address = asset.normalized_address
    else:
        # Build address from components
        parts = []
        if asset.street:
            parts.append(asset.street)
        if asset.number:
            parts.append(str(asset.number))
        if asset.building_type and asset.floor:
            parts.append(f"{asset.building_type} {asset.floor}")
        elif asset.building_type:
            parts.append(asset.building_type)
        if asset.apartment:
            parts.append(f"דירה {asset.apartment}")
        if asset.city:
            parts.append(asset.city)
        address = " ".join(parts) if parts else None

    ppsqm = _first_nonempty(
        asset.price_per_sqm,
        round(price / net_sqm) if price and net_sqm else None,
        meta.get("pricePerSqm")
    )

    # Build the base listing data
    listing_data = {
        "id": asset.id,
        "address": address,
        "city": asset.city,
        "neighborhood": asset.neighborhood,
        "street": asset.street,
        "number": asset.number,
        "block": asset.block,
        "parcel": asset.parcel,
        "subparcel": asset.subparcel,
        "type": ptype,
        "rooms": rooms,
        "bedrooms": bedrooms,
        "netSqm": net_sqm,
        "totalSqm": total_sqm,
        "price": price,
        "pricePerSqm": ppsqm,
        "asset_status": asset.status,
        "lat": asset.lat,
        "lon": asset.lon,
        "normalizedAddress": asset.normalized_address,
    }
    
    # Process unified metadata structure
    _meta = {}
    for key, value in meta.items():
        if key not in ['gis_data', 'government_data', 'rami_plans', 'mavat_plans', 'yad2_listings', 'market_data', 'last_enrichment']:
            if isinstance(value, dict) and "value" in value:
                # This is a unified metadata entry
                listing_data[key] = value.get("value")
                _meta[key] = {
                    "source": value.get("source"),
                    "fetched_at": value.get("fetched_at"),
                    "url": value.get("url")
                }
            else:
                # This is a simple value (backward compatibility)
                listing_data[key] = value
    
    # Add _meta to listing data if we have any metadata
    if _meta:
        listing_data["_meta"] = _meta
    
    # Helper function to get value from unified metadata
    def get_meta_value(key):
        value = meta.get(key)
        if isinstance(value, dict) and "value" in value:
            return value.get("value")
        return value
    
    # Add specific fields with fallback logic
    listing_data.update({
        "zoning": _first_nonempty(asset.zoning, get_meta_value("zoning")),
        "rentEstimate": _first_nonempty(asset.rent_estimate, get_meta_value("rentEstimate")),
        "riskFlags": get_meta_value("riskFlags") or [],
        "documents": get_meta_value("documents") or [],
        "bathrooms": _first_nonempty(asset.bathrooms, get_meta_value("bathrooms")),
        "balconyArea": _first_nonempty(asset.balcony_area, get_meta_value("balconyArea")),
        "parkingSpaces": _first_nonempty(asset.parking_spaces, get_meta_value("parkingSpaces")),
        "storageRoom": _first_nonempty(asset.storage_room, get_meta_value("storageRoom")),
        "elevator": _first_nonempty(asset.elevator, get_meta_value("elevator")),
        "airConditioning": _first_nonempty(asset.air_conditioning, get_meta_value("airConditioning")),
        "furnished": _first_nonempty(asset.furnished, get_meta_value("furnished")),
        "renovated": _first_nonempty(asset.renovated, get_meta_value("renovated")),
        "yearBuilt": _first_nonempty(asset.year_built, get_meta_value("yearBuilt")),
        "lastRenovation": _first_nonempty(asset.last_renovation, get_meta_value("lastRenovation")),
        "floor": _first_nonempty(asset.floor, get_meta_value("floor")),
        "totalFloors": _first_nonempty(asset.total_floors, get_meta_value("totalFloors")),
        "buildingRights": _first_nonempty(asset.building_rights, get_meta_value("buildingRights")),
        "permitStatus": _first_nonempty(asset.permit_status, get_meta_value("permitStatus")),
        "permitDate": asset.permit_date.isoformat() if asset.permit_date else None,
        "antennaDistanceM": get_meta_value("antennaDistanceM"),
    })
    
    return listing_data
