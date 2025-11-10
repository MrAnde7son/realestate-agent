"""Utilities for normalizing listing data across serializers and views."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from django.utils import timezone


def parse_int(
    value: Any,
    default: Optional[int] = None,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> Optional[int]:
    """Safely parse an integer value with optional bounds."""

    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    if minimum is not None:
        parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


def parse_float(value: Any) -> Optional[float]:
    """Safely parse a floating point number."""

    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return None


def format_rooms_value(value: Any) -> Optional[str]:
    """Return a normalized display value for number of rooms."""

    numeric = parse_float(value)
    if numeric is None:
        return None
    if numeric.is_integer():
        return str(int(numeric))
    formatted = f"{numeric:.2f}".rstrip("0").rstrip(".")
    return formatted


def parse_date_value(value: Any) -> Optional[datetime]:
    """Parse a date value from strings, datetimes or timestamps."""

    if not value:
        return None
    dt: Optional[datetime] = None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        try:
            dt = datetime.fromtimestamp(value, tz=timezone.utc)
        except (TypeError, ValueError, OSError, OverflowError):
            return None
    elif isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            if cleaned.endswith("Z"):
                cleaned = cleaned.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
        except (ValueError, TypeError):
            return None
    if dt is None:
        return None
    if timezone.is_naive(dt):
        try:
            dt = timezone.make_aware(dt, timezone.utc)
        except Exception:  # pragma: no cover - fallback for older datetimes
            dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def _coerce_contact_info(value: Any) -> Dict[str, Optional[str]]:
    """Normalize the contact info payload to a predictable dictionary."""

    if value is None:
        return {}
    if isinstance(value, dict):
        return {
            "name": value.get("name"),
            "phone": value.get("phone"),
            "brokerPhone": value.get("brokerPhone"),
            "email": value.get("email"),
        }
    result: Dict[str, Optional[str]] = {}
    for attr in ("name", "phone", "brokerPhone", "email"):
        if hasattr(value, attr):
            result[attr] = getattr(value, attr)
    return result


def _merge_photos(*candidates: Iterable[Any]) -> List[str]:
    """Combine photos and ensure uniqueness."""

    photos: List[str] = []
    for candidate in candidates:
        if not candidate:
            continue
        for item in candidate:
            if isinstance(item, str) and item and item not in photos:
                photos.append(item)
    return photos


def _listing_sort_key(listing: Any) -> float:
    fetched_at = getattr(listing, "fetched_at", None)
    if not fetched_at:
        return float("-inf")
    try:
        return fetched_at.timestamp()
    except (AttributeError, OverflowError, OSError, ValueError):  # pragma: no cover - fallback safety
        return float("-inf")


def normalize_listing_from_model(listing_obj: Any) -> Dict[str, Any]:
    """Normalize a Listing model instance to a consistent payload."""

    raw = listing_obj.raw or {}
    price = listing_obj.price if listing_obj.price is not None else raw.get("price")
    area = listing_obj.area if listing_obj.area is not None else raw.get("area") or raw.get("size")
    rooms_value = listing_obj.rooms if listing_obj.rooms is not None else raw.get("rooms")

    listing_type = listing_obj.listing_type or raw.get("listing_type") or raw.get("listingType")
    ad_type = getattr(listing_obj, "ad_type", None) or raw.get("ad_type") or raw.get("adType")
    contact_info_raw = (
        raw.get("contact_info")
        or raw.get("contactInfo")
        or getattr(listing_obj, "contact_info", None)
    )
    contact_info = _coerce_contact_info(contact_info_raw)

    contact_name = (
        listing_obj.contact_name
        or raw.get("contact_name")
        or raw.get("contactName")
        or contact_info.get("name")
    )
    contact_phone = (
        listing_obj.contact_phone
        or raw.get("contact_phone")
        or raw.get("contactPhone")
        or contact_info.get("phone")
        or contact_info.get("brokerPhone")
    )

    recent_deal = bool(
        getattr(listing_obj, "recent_deal", False)
        or raw.get("recent_deal")
        or raw.get("recentDeal")
    )

    photos = _merge_photos(
        getattr(listing_obj, "photos", None) or [],
        raw.get("photos", []),
        raw.get("images", []),
    )

    video_url = (
        getattr(listing_obj, "video_url", None)
        or raw.get("video_url")
        or raw.get("videoUrl")
        or raw.get("video")
    )

    date_posted = raw.get("date_posted") or raw.get("scraped_at")
    if not date_posted and getattr(listing_obj, "fetched_at", None):
        fetched_at = listing_obj.fetched_at
        if fetched_at:
            date_posted = fetched_at.isoformat()

    normalized_contact_info = {
        "name": contact_name or contact_info.get("name") or contact_info.get("agent"),
        "agent": contact_info.get("agent") or contact_name,
        "phone": contact_phone or contact_info.get("phone") or contact_info.get("brokerPhone"),
        "brokerPhone": contact_info.get("brokerPhone"),
        "email": contact_info.get("email"),
    }

    # Extract high priority fields from raw data
    features_obj = raw.get("features", {})
    if not isinstance(features_obj, dict):
        features_obj = {}
    
    meta_obj = raw.get("meta", {})
    if not isinstance(meta_obj, dict):
        meta_obj = {}
    
    # Extract shelter and accessibility from features
    shelter = features_obj.get("shelter") or features_obj.get("hasShelter") or meta_obj.get("shelter")
    accessibility = features_obj.get("accessibility") or features_obj.get("hasAccessibility") or meta_obj.get("accessibility")
    
    # Extract Madlan-specific fields
    building_class = meta_obj.get("buildingClass") or meta_obj.get("building_class")
    general_condition = meta_obj.get("generalCondition") or meta_obj.get("general_condition")
    
    investors_data = meta_obj.get("investorsData") or meta_obj.get("investors_data") or {}
    if not isinstance(investors_data, dict):
        investors_data = {}
    investment_yield = parse_float(investors_data.get("yield"))
    approximate_rent = parse_int(investors_data.get("approximateRent") or investors_data.get("approximate_rent"))
    commute_time = parse_int(meta_obj.get("commuteTime") or meta_obj.get("commute_time"))
    
    # Extract tags
    tags = meta_obj.get("tags", {})
    if not isinstance(tags, dict):
        tags = {}
    tag_best_school = tags.get("bestSchool") or tags.get("best_school")
    tag_safety = tags.get("safety")
    tag_family_friendly = tags.get("familyFriendly") or tags.get("family_friendly")
    tag_light_rail = tags.get("lightRail") or tags.get("light_rail")
    tag_park_access = tags.get("parkAccess") or tags.get("park_access")
    tag_quiet_street = tags.get("quietStreet") or tags.get("quiet_street")
    tag_commute = tags.get("commute")
    
    # Extract exclusivity - check both Madlan and Yad2 sources
    poc = meta_obj.get("poc", {})
    if not isinstance(poc, dict):
        poc = {}
    exclusivity = poc.get("exclusivity", {})
    if not isinstance(exclusivity, dict):
        exclusivity = {}
    madlan_exclusive = exclusivity.get("exclusive")
    
    # Yad2 exclusivity: check inProperty.isAssetExclusive
    in_property = raw.get("inProperty", {})
    if not isinstance(in_property, dict):
        in_property = {}
    yad2_exclusive = in_property.get("isAssetExclusive")
    
    # Prefer Yad2 exclusive flag, fallback to Madlan
    exclusive = yad2_exclusive if yad2_exclusive is not None else madlan_exclusive
    
    # Extract previous price and calculate priceDropped
    previous_price = parse_int(
        raw.get("previous_price")
        or raw.get("previousPrice")
        or raw.get("priceBeforeTag")
        or raw.get("price_before_tag")
    )
    price_dropped = (
        previous_price is not None
        and price is not None
        and previous_price > price
    )
    
    # Calculate publishedDays if date_posted is available
    published_days = None
    if date_posted:
        try:
            posted_date = parse_date_value(date_posted)
            if posted_date:
                now = timezone.now()
                diff_time = now - posted_date
                diff_days = diff_time.days
                published_days = diff_days if diff_days >= 0 else None
        except Exception:
            pass

    normalized = {
        "id": f"{listing_obj.source}:{listing_obj.external_id}",
        "source": listing_obj.source or raw.get("source") or "external",
        "external_id": listing_obj.external_id,
        "title": listing_obj.title or raw.get("title") or "",
        "price": parse_int(price, None),
        "previous_price": previous_price,
        "address": listing_obj.address or raw.get("address") or "",
        "rooms": parse_float(rooms_value),
        "rooms_display": format_rooms_value(rooms_value),
        "roomsDisplay": format_rooms_value(rooms_value),  # Also include camelCase for frontend compatibility
        "size": parse_float(area),
        "property_type": raw.get("property_type") or raw.get("propertyType"),
        "url": listing_obj.url or raw.get("url"),
        "date_posted": date_posted,
        "datePosted": date_posted,  # Also include camelCase for frontend compatibility
        "images": photos,
        "photos": photos,
        "description": raw.get("description") or "",
        "floor": raw.get("floor"),
        "features": raw.get("features", []),
        "listing_type": listing_type,
        "listingType": listing_type,  # Also include camelCase for frontend compatibility
        "ad_type": ad_type,
        "adType": ad_type,  # Also include camelCase for frontend compatibility
        "contact_name": contact_name,
        "contactName": contact_name,  # Also include camelCase for frontend compatibility
        "contact_phone": contact_phone,
        "contactPhone": contact_phone,  # Also include camelCase for frontend compatibility
        "contact_info": normalized_contact_info,
        "contactInfo": normalized_contact_info,  # Also include camelCase for frontend compatibility
        "recent_deal": recent_deal,
        "recentDeal": recent_deal,  # Also include camelCase for frontend compatibility
        "video_url": video_url,
        "videoUrl": video_url,  # Also include camelCase for frontend compatibility
        "video": video_url,
        # High priority fields
        "priceDropped": price_dropped,
        "previousPrice": previous_price,
        "shelter": bool(shelter) if shelter is not None else None,
        "accessibility": bool(accessibility) if accessibility is not None else None,
        "buildingClass": building_class,
        "generalCondition": general_condition,
        "investmentYield": investment_yield,
        "approximateRent": approximate_rent,
        "commuteTime": commute_time,
        "publishedDays": published_days,
        "tagBestSchool": bool(tag_best_school) if tag_best_school is not None else None,
        "tagSafety": bool(tag_safety) if tag_safety is not None else None,
        "tagFamilyFriendly": bool(tag_family_friendly) if tag_family_friendly is not None else None,
        "tagLightRail": bool(tag_light_rail) if tag_light_rail is not None else None,
        "tagParkAccess": bool(tag_park_access) if tag_park_access is not None else None,
        "tagQuietStreet": bool(tag_quiet_street) if tag_quiet_street is not None else None,
        "tagCommute": bool(tag_commute) if tag_commute is not None else None,
        "exclusive": bool(exclusive) if exclusive is not None else None,
    }
    return normalized


def normalize_listing_from_meta(meta_listing: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """Normalize a legacy metadata listing structure."""

    source = meta_listing.get("source") or "yad2"
    listing_id = meta_listing.get("listing_id") or meta_listing.get("id")
    if not listing_id:
        listing_id = f"{source}_{idx}_{meta_listing.get('url') or meta_listing.get('title') or 'listing'}"

    rooms_value = meta_listing.get("rooms")
    area = meta_listing.get("area") or meta_listing.get("size")

    contact_info = _coerce_contact_info(
        meta_listing.get("contact_info")
        or meta_listing.get("contactInfo")
        or meta_listing.get("contact")
    )

    contact_name = (
        meta_listing.get("contact_name")
        or meta_listing.get("contactName")
        or contact_info.get("name")
    )
    contact_phone = (
        meta_listing.get("contact_phone")
        or meta_listing.get("contactPhone")
        or contact_info.get("phone")
        or contact_info.get("brokerPhone")
    )

    listing_type = meta_listing.get("listing_type") or meta_listing.get("listingType")
    ad_type = meta_listing.get("ad_type") or meta_listing.get("adType")
    photos = _merge_photos(meta_listing.get("photos", []), meta_listing.get("images", []))
    video_url = meta_listing.get("video_url") or meta_listing.get("videoUrl") or meta_listing.get("video")
    recent_deal = bool(meta_listing.get("recent_deal") or meta_listing.get("recentDeal"))

    normalized_contact_info = {
        "name": contact_name or contact_info.get("name") or contact_info.get("agent"),
        "agent": contact_info.get("agent") or contact_name,
        "phone": contact_phone or contact_info.get("phone") or contact_info.get("brokerPhone"),
        "brokerPhone": contact_info.get("brokerPhone"),
        "email": contact_info.get("email"),
    }

    normalized = {
        "id": str(listing_id),
        "source": source,
        "external_id": meta_listing.get("external_id"),
        "title": meta_listing.get("title") or "",
        "price": parse_int(meta_listing.get("price"), None),
        "address": meta_listing.get("address") or "",
        "rooms": parse_float(rooms_value),
        "rooms_display": format_rooms_value(rooms_value),
        "size": parse_float(area),
        "property_type": meta_listing.get("property_type"),
        "url": meta_listing.get("url"),
        "date_posted": meta_listing.get("date_posted") or meta_listing.get("scraped_at"),
        "images": photos,
        "photos": photos,
        "description": meta_listing.get("description") or "",
        "floor": meta_listing.get("floor"),
        "features": meta_listing.get("features", []),
        "listing_type": listing_type,
        "ad_type": ad_type,
        "contact_name": contact_name,
        "contact_phone": contact_phone,
        "contact_info": normalized_contact_info,
        "recent_deal": recent_deal,
        "video_url": video_url,
        "video": video_url,
    }
    return normalized


__all__ = [
    "format_rooms_value",
    "normalize_listing_from_meta",
    "normalize_listing_from_model",
    "parse_date_value",
    "parse_float",
    "parse_int",
    "_listing_sort_key",
]
