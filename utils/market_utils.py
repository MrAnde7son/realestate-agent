"""
Market utilities for real estate calculations.

This module provides functions for calculating market metrics such as
rent estimates based on city-specific gross yields.
"""

import logging

logger = logging.getLogger(__name__)


def get_city_gross_yield(city: str, neighborhood: str = None) -> float:
    """
    Get gross yield percentage for a city based on location (center vs outside center).

    Args:
        city: City name
        neighborhood: Neighborhood name (optional, for future use to determine center vs outside)

    Returns:
        Gross yield percentage as a float (e.g., 2.05 for 2.05%)

    Note:
        Returns the national average if city not found in the mapping.
        Currently defaults to 'center' yields until neighborhood logic is implemented.

    Data source: Numbeo (as of the user's table)
    """
    # City-specific gross yields (%)
    # Format: {'city_name': {'center': %, 'outside': %}}
    CITY_YIELDS = {
        "תל אביב – יפו": {"center": 2.80, "outside": 3.10},
        "תל אביב-יפו": {"center": 2.80, "outside": 3.10},
        "תל אביב": {"center": 2.80, "outside": 3.10},
        "תל אביב יפו": {"center": 2.80, "outside": 3.10},
        "ירושלים": {"center": 3.10, "outside": 3.40},
        "חיפה": {"center": 3.50, "outside": 3.80},
        "באר־שבע": {"center": 4.10, "outside": 4.30},
        "באר שבע": {"center": 4.10, "outside": 4.30},
        "רמת גן": {"center": 2.90, "outside": 3.20},
        "הרצליה": {"center": 2.70, "outside": 3.00},
        "הרצלייה": {"center": 2.70, "outside": 3.00},
        "נתניה": {"center": 3.10, "outside": 3.30},
        "אשדוד": {"center": 3.20, "outside": 3.50},
        "בת־ים": {"center": 2.90, "outside": 3.30},
        "בת ים": {"center": 2.90, "outside": 3.30},
        "אשקלון": {"center": 3.60, "outside": 3.90},
        "פתח־תקווה": {"center": 3.00, "outside": 3.20},
        "פתח תקווה": {"center": 3.00, "outside": 3.20},
        "ראשון־לציון": {"center": 2.90, "outside": 3.20},
        "ראשון לציון": {"center": 2.90, "outside": 3.20},
    }

    # National average default for center (used as fallback)
    NATIONAL_AVG_CENTER = 2.79

    if not city:
        return NATIONAL_AVG_CENTER

    # Lookup city (case-insensitive)
    city_normalized = city.strip()
    city_data = CITY_YIELDS.get(city_normalized)

    if not city_data:
        # Try with common variations
        for key, value in CITY_YIELDS.items():
            if (
                city_normalized.lower() in key.lower()
                or key.lower() in city_normalized.lower()
            ):
                city_data = value
                break

    if not city_data:
        # Return national average for unknown cities
        logger.debug(
            "City not found in yield mapping: %s, using national average %.2f%%",
            city,
            NATIONAL_AVG_CENTER,
        )
        return NATIONAL_AVG_CENTER

    # Default to 'center' for now since we don't have neighborhood-level data
    # Future enhancement: determine center vs outside center based on neighborhood
    yield_pct = city_data["center"]

    logger.debug(
        "City yield lookup: city=%s, neighborhood=%s, yield=%.2f%%",
        city,
        neighborhood or "N/A",
        yield_pct,
    )

    return yield_pct


def calculate_rent_estimate(price: int, city: str, neighborhood: str = None) -> dict:
    """
    Calculate rent estimate and cap rate based on property price and city gross yield.

    Args:
        price: Property price in NIS
        city: City name
        neighborhood: Optional neighborhood name

    Returns:
        Dictionary with 'rent_estimate' (monthly) and 'cap_rate_pct' keys
    """
    gross_yield_pct = get_city_gross_yield(city, neighborhood)

    # Gross Yield = Annual Rent / Property Price
    # Therefore: Annual Rent = Property Price × Gross Yield %
    annual_rent = price * (gross_yield_pct / 100)
    monthly_rent = annual_rent / 12

    return {
        "rent_estimate": int(monthly_rent),
        "cap_rate_pct": round(gross_yield_pct, 2),
        "annual_rent": int(annual_rent),
    }
