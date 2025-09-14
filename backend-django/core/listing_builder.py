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
    
    # Add all meta fields to the listing data
    for key, value in meta.items():
        if key not in ['gis_data', 'government_data', 'rami_plans', 'mavat_plans', 'yad2_listings', 'market_data', 'last_enrichment']:
            listing_data[key] = value
    
    # Add specific fields with fallback logic
    listing_data.update({
        "zoning": _first_nonempty(asset.zoning, meta.get("zoning")),
        "rentEstimate": _first_nonempty(asset.rent_estimate, meta.get("rentEstimate")),
        "riskFlags": meta.get("riskFlags") or [],
        "documents": meta.get("documents") or [],
        "bathrooms": _first_nonempty(asset.bathrooms, meta.get("bathrooms")),
        "balconyArea": _first_nonempty(asset.balcony_area, meta.get("balconyArea")),
        "parkingSpaces": _first_nonempty(asset.parking_spaces, meta.get("parkingSpaces")),
        "storageRoom": _first_nonempty(asset.storage_room, meta.get("storageRoom")),
        "elevator": _first_nonempty(asset.elevator, meta.get("elevator")),
        "airConditioning": _first_nonempty(asset.air_conditioning, meta.get("airConditioning")),
        "furnished": _first_nonempty(asset.furnished, meta.get("furnished")),
        "renovated": _first_nonempty(asset.renovated, meta.get("renovated")),
        "yearBuilt": _first_nonempty(asset.year_built, meta.get("yearBuilt")),
        "lastRenovation": _first_nonempty(asset.last_renovation, meta.get("lastRenovation")),
        "floor": _first_nonempty(asset.floor, meta.get("floor")),
        "totalFloors": _first_nonempty(asset.total_floors, meta.get("totalFloors")),
        "buildingRights": _first_nonempty(asset.building_rights, meta.get("buildingRights")),
        "permitStatus": _first_nonempty(asset.permit_status, meta.get("permitStatus")),
        "permitDate": asset.permit_date.isoformat() if asset.permit_date else None,
    })
    
    return listing_data
