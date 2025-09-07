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

    rooms = _first_nonempty(asset.rooms, meta.get("rooms"), raw.get("rooms"))
    bedrooms = _first_nonempty(
        asset.bedrooms, meta.get("bedrooms"), raw.get("bedrooms")
    )
    net_sqm = _first_nonempty(
        asset.area,
        meta.get("netSqm"),
        meta.get("area"),
        raw.get("size"),
        raw.get("area"),
    )
    total_sqm = _first_nonempty(
        getattr(asset, "total_area", None), meta.get("totalSqm"), raw.get("total_size")
    )
    price = _first_nonempty(meta.get("price"), raw.get("price"))
    ptype = _first_nonempty(
        asset.building_type, meta.get("type"), raw.get("property_type")
    )

    if asset.normalized_address:
        address = asset.normalized_address
    else:
        parts = [asset.street, asset.number, asset.city]
        address = " ".join(str(p) for p in parts if p)

    ppsqm = round(price / net_sqm) if price and net_sqm else None

    return {
        "id": asset.id,
        "address": address,
        "city": asset.city,
        "neighborhood": asset.neighborhood,
        "street": asset.street,
        "number": asset.number,
        "gush": asset.gush,
        "helka": asset.helka,
        "subhelka": asset.subhelka,
        "type": ptype,
        "rooms": rooms,
        "bedrooms": bedrooms,
        "netSqm": net_sqm,
        "totalSqm": total_sqm,
        "price": price,
        "pricePerSqm": ppsqm,
        "remainingRightsSqm": meta.get("remainingRightsSqm"),
        "program": meta.get("program"),
        "lastPermitQ": meta.get("lastPermitQ"),
        "noiseLevel": meta.get("noiseLevel"),
        "competition1km": meta.get("competition1km"),
        "zoning": meta.get("zoning"),
        "priceGapPct": meta.get("priceGapPct"),
        "expectedPriceRange": meta.get("expectedPriceRange"),
        "modelPrice": meta.get("modelPrice"),
        "confidencePct": meta.get("confidencePct"),
        "capRatePct": meta.get("capRatePct"),
        "rentEstimate": meta.get("rentEstimate"),
        "riskFlags": meta.get("riskFlags") or [],
        "documents": meta.get("documents") or [],
        "asset_status": asset.status,
    }
