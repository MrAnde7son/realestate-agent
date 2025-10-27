from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List

logger = logging.getLogger(__name__)


def _object_to_payload(obj: Any) -> Dict[str, Any]:
    """Convert arbitrary objects into plain dictionaries for serialization."""

    if obj is None:
        return {}

    if isinstance(obj, dict):
        return {k: v for k, v in obj.items() if not k.startswith("_")}

    data: Dict[str, Any] = {}
    try:
        for key, value in vars(obj).items():
            if key.startswith("_"):
                continue
            data[key] = value
    except TypeError:
        # ``vars`` might fail for certain built-in types – fall back to repr
        pass

    # Preserve contact_info property even though its backing attribute is private
    # and filtered out by the vars() copy above. This ensures contact details
    # flow through the pipeline and can populate serializers/filters.
    try:
        if "contact_info" not in data and hasattr(obj, "contact_info"):
            contact_info = getattr(obj, "contact_info")
            if contact_info is not None:
                if hasattr(contact_info, "to_dict"):
                    try:
                        contact_info = contact_info.to_dict()
                    except Exception:
                        # Best-effort: if to_dict fails, leave as-is
                        pass
                data["contact_info"] = contact_info
                # Backfill simple fields when missing
                if data.get("contact_name") in (None, ""):
                    if isinstance(contact_info, dict):
                        data["contact_name"] = contact_info.get("name")
                if data.get("contact_phone") in (None, ""):
                    if isinstance(contact_info, dict):
                        data["contact_phone"] = contact_info.get("phone") or contact_info.get("brokerPhone")
    except Exception:
        # Do not let best-effort enrichment break payload building
        pass
    return data


def _build_listing_snapshot(raw_listing: Any, db_listing: Any) -> SimpleNamespace:
    """Create an immutable snapshot of the listing for async notifications."""

    payload: Dict[str, Any] = {}
    payload.update(_object_to_payload(raw_listing))
    payload.update(_object_to_payload(db_listing))
    payload.setdefault("id", getattr(db_listing, "id", None))
    return SimpleNamespace(**payload)


def _listing_to_dict(listing: Any) -> Dict[str, Any]:
    """Convert Yad2 listings into plain dictionaries for downstream processing."""

    if isinstance(listing, dict):
        data = dict(listing)
    elif hasattr(listing, "to_dict"):
        data = listing.to_dict()
    else:
        keys = (
            "title",
            "price",
            "address",
            "rooms",
            "floor",
            "size",
            "property_type",
            "description",
            "images",
            "video",
            "documents",
            "contact_info",
            "contact_name",
            "contact_phone",
            "features",
            "url",
            "listing_id",
            "date_posted",
            "coordinates",
            "listing_type",
            "ad_type",
            "recent_deal",
            "scraped_at",
            "meta",
        )
        data = {key: getattr(listing, key, None) for key in keys}

    if "area" not in data or data.get("area") in (None, ""):
        size_value = data.get("size")
        if size_value in (None, "") and hasattr(listing, "size"):
            size_value = getattr(listing, "size")
        if size_value not in (None, ""):
            data["area"] = size_value

    if "photos" not in data and data.get("images") is not None:
        data["photos"] = data.get("images")

    return data


def _normalize_listings(listings: Iterable[Any]) -> List[Dict[str, Any]]:
    """Return a list of dictionaries regardless of the original listing type."""

    normalized: List[Dict[str, Any]] = []
    if not listings:
        return normalized

    for listing in listings:
        if listing is None:
            continue
        try:
            normalized.append(_listing_to_dict(listing))
        except Exception as exc:  # pragma: no cover - extremely defensive
            logger.debug("Skipping listing that cannot be normalized: %s", exc)
    return normalized


__all__ = [
    "_object_to_payload",
    "_build_listing_snapshot",
    "_listing_to_dict",
    "_normalize_listings",
]
