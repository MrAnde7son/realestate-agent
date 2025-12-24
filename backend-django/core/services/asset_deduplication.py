"""Asset deduplication service to identify and update existing assets.

This service provides logic to find existing assets based on:
1. Full location: city + street + number
2. Parcel information: city + block + parcel + subparcel

The service handles missing parameters gracefully by only matching on available fields.
"""

import re
from typing import Optional, Union

from django.db.models import Q

try:
    from orchestration.location import LocationQuery
except ImportError:
    LocationQuery = None  # type: ignore


def find_existing_asset(
    location: LocationQuery,
    scope_type: Optional[str] = None,
) -> Optional[object]:
    """Find an existing asset matching the provided location or parcel information.

    This function uses a two-tier matching strategy:
    1. Address-based matching: city + street + number
    2. Parcel-based matching: city + block + parcel + subparcel

    Parameters are normalized (stripped, case-insensitive) before matching.
    Missing parameters are handled gracefully - only available fields are used for matching.

    Args:
        location: LocationQuery object containing location information
        scope_type: Scope type filter (optional, e.g., 'address', 'parcel')

    Returns:
        Existing Asset instance if found, None otherwise
    """
    from ..models import Asset

    # Extract values from LocationQuery
    city = location.city
    street = location.street
    number = location.house_number
    block = location.block
    parcel = location.parcel
    subparcel = location.subparcel

    queryset = Asset.objects.all()

    # Filter by scope_type if provided
    if scope_type:
        queryset = queryset.filter(scope_type=scope_type)

    # Normalize string values (convert int to str for block/parcel/subparcel)
    city_norm = _normalize_string(city)
    street_norm = _normalize_string(street)
    block_norm = _normalize_string(_convert_to_str(block))
    parcel_norm = _normalize_string(_convert_to_str(parcel))
    subparcel_norm = _normalize_string(_convert_to_str(subparcel))

    # Build query conditions
    conditions = Q()

    # Strategy 1: Address-based matching (city + street + number)
    # This should always be tried if we have city + (street or number)
    address_match = _build_address_match(city_norm, street_norm, number)

    # Strategy 2: Parcel-based matching (city + block + parcel + subparcel)
    # This is tried if we have block + parcel
    parcel_match = _build_parcel_match(
        city_norm, block_norm, parcel_norm, subparcel_norm
    )

    # Combine both strategies with OR
    # Always try address match if available, even if we have parcel info
    if address_match is not None and parcel_match is not None:
        conditions = address_match | parcel_match
    elif address_match is not None:
        conditions = address_match
    elif parcel_match is not None:
        conditions = parcel_match

    # If no valid conditions, return None
    if not conditions:
        return None

    # Execute query and return first match
    matches = queryset.filter(conditions).order_by("-created_at")
    return matches.first() if matches.exists() else None


def _build_address_match(
    city: Optional[str],
    street: Optional[str],
    number: Optional[int],
) -> Optional[Q]:
    """Build Q object for address-based matching.

    Requires at least city + (street or number) to be meaningful.
    Uses normalized city comparison to handle variations like "תל אביב-יפו" vs "תל אביב יפו".
    """
    if not city:
        return None

    # Need at least street or number for address matching
    if not street and number is None:
        return None

    # Build city matching with variations
    # Normalize city name and try multiple variations
    # Get all possible city variations
    city_variations = _get_city_variations(city)

    # Build city condition with all variations
    city_conditions = Q()
    for variation in city_variations:
        city_conditions |= Q(city__iexact=variation)

    # Also try regex matching for hyphen/space variations
    # This handles cases like "תל אביב-יפו" vs "תל אביב יפו"
    city_normalized = _normalize_city_for_regex(city)
    if city_normalized:
        city_conditions |= Q(city__iregex=city_normalized)

    conditions = city_conditions

    if street:
        conditions &= Q(street__iexact=street)

    if number is not None:
        conditions &= Q(number=number)

    return conditions


def _get_city_variations(city: str) -> list[str]:
    """Get possible variations of a city name for matching.

    Handles common variations like:
    - "תל אביב-יפו" vs "תל אביב יפו" vs "תל אביב יפו"
    - Hyphens vs spaces
    """
    if not city:
        return []

    variations = []

    # Add normalized version
    city_norm = _normalize_string(city)
    if city_norm:
        variations.append(city_norm)

    # Add original (normalized)
    if city_norm != city:
        variations.append(city)

    # Replace hyphen with space
    if "-" in city:
        city_with_space = city.replace("-", " ")
        city_with_space_norm = _normalize_string(city_with_space)
        if city_with_space_norm and city_with_space_norm not in variations:
            variations.append(city_with_space_norm)

    # Replace space with hyphen (if no hyphen exists)
    if "-" not in city and " " in city:
        city_with_hyphen = city.replace(" ", "-")
        city_with_hyphen_norm = _normalize_string(city_with_hyphen)
        if city_with_hyphen_norm and city_with_hyphen_norm not in variations:
            variations.append(city_with_hyphen_norm)

    # Special handling for Tel Aviv variations
    if "תל" in city and "אביב" in city:
        if "יפו" in city:
            # Try "תל אביב-יפו" variations
            variations.append(_normalize_string("תל אביב-יפו") or "תל אביב-יפו")
            variations.append(_normalize_string("תל אביב יפו") or "תל אביב יפו")
        else:
            # Just "תל אביב"
            variations.append(_normalize_string("תל אביב") or "תל אביב")

    # Remove duplicates while preserving order
    seen = set()
    unique_variations = []
    for var in variations:
        if var and var not in seen:
            seen.add(var)
            unique_variations.append(var)

    return unique_variations if unique_variations else [city_norm or city]


def _normalize_city_for_regex(city: str) -> Optional[str]:
    """Create a regex pattern for city matching that handles hyphen/space variations.

    Returns a regex pattern that matches the city with hyphen or space variations.
    """
    if not city:
        return None

    # Escape special regex characters
    city_escaped = re.escape(city)

    # Replace hyphen with pattern that matches hyphen or space
    # This allows matching "תל אביב-יפו" with "תל אביב יפו"
    pattern = city_escaped.replace(r"\-", r"[\s\-]+")

    # If city has spaces, also try replacing spaces with hyphen pattern
    if " " in city:
        city_with_hyphen = city.replace(" ", "-")
        city_with_hyphen_escaped = re.escape(city_with_hyphen)
        pattern_alt = city_with_hyphen_escaped.replace(r"\-", r"[\s\-]+")
        # Combine both patterns
        if pattern != pattern_alt:
            pattern = f"({pattern}|{pattern_alt})"

    return f"^{pattern}$"


def _build_parcel_match(
    city: Optional[str],
    block: Optional[str],
    parcel: Optional[str],
    subparcel: Optional[str],
) -> Optional[Q]:
    """Build Q object for parcel-based matching.

    Requires at least block + parcel to be meaningful.
    """
    # Need at least block and parcel for parcel matching
    if not block or not parcel:
        return None

    conditions = Q(block__iexact=block) & Q(parcel__iexact=parcel)

    # Add city if available (makes match more precise)
    if city:
        conditions &= Q(city__iexact=city)

    # Add subparcel if available (makes match more precise)
    if subparcel:
        conditions &= Q(subparcel__iexact=subparcel)

    return conditions


def _normalize_string(value: Optional[str]) -> Optional[str]:
    """Normalize string value for comparison.

    Strips whitespace, normalizes hyphens/dashes, removes extra spaces,
    and converts to lowercase.
    Returns None if value is empty after normalization.
    """
    if value is None:
        return None

    import re

    normalized = str(value).strip()
    if not normalized:
        return None

    # Normalize hyphens and dashes (replace various dash types with standard hyphen)
    normalized = re.sub(r"[־\u2010-\u2015\u2212-]", "-", normalized)

    # Normalize whitespace (replace multiple spaces/tabs with single space)
    normalized = re.sub(r"\s+", " ", normalized)

    # Remove spaces around hyphens (e.g., "תל אביב - יפו" -> "תל אביב-יפו")
    normalized = re.sub(r"\s*-\s*", "-", normalized)

    # Convert to lowercase
    normalized = normalized.lower()

    return normalized if normalized else None


def _convert_to_str(value: Optional[Union[str, int]]) -> Optional[str]:
    """Convert value to string if it's an integer, otherwise return as-is.

    This handles the case where LocationQuery uses int for block/parcel/subparcel
    but Asset model uses str.
    """
    if value is None:
        return None
    if isinstance(value, int):
        return str(value)
    return value


def get_or_create_asset(
    location: LocationQuery,
    scope_type: Optional[str] = None,
    defaults: Optional[dict] = None,
) -> tuple[object, bool]:
    """Get existing asset or create a new one.

    This is a convenience wrapper around find_existing_asset that follows
    Django's get_or_create pattern.

    Args:
        location: LocationQuery object containing location information
        scope_type: Scope type (optional)
        defaults: Dictionary of default values for creating new asset

    Returns:
        Tuple of (asset, created) where created is True if asset was created
    """
    from ..models import Asset

    existing = find_existing_asset(
        location=location,
        scope_type=scope_type,
    )

    if existing:
        return existing, False

    # Create new asset (convert int to str for block/parcel/subparcel to match Asset model)
    create_data = {
        "scope_type": scope_type or "address",
        "city": location.city,
        "street": location.street,
        "number": location.house_number,
        "block": _convert_to_str(location.block),
        "parcel": _convert_to_str(location.parcel),
        "subparcel": _convert_to_str(location.subparcel),
    }

    if defaults:
        create_data.update(defaults)

    # Remove None values
    create_data = {k: v for k, v in create_data.items() if v is not None}

    asset = Asset.objects.create(**create_data)
    return asset, True
