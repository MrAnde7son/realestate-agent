"""
Yad2 Configuration and Constants
Contains common codes and mappings for consistent searches
"""

# Import existing property type utilities to avoid duplication
from .utils.property_types import PropertyTypeUtils

# Property Type Codes - Using existing PropertyTypeUtils for consistency
def get_property_type_code(property_name: str) -> int:
    """Get property type code by name using existing PropertyTypeUtils"""
    return PropertyTypeUtils.hebrew_name_to_code(property_name) or PropertyTypeUtils.english_name_to_code(property_name)

# Common City Codes
CITIES = {
    "תל אביב": 5000,
    "תל אביב יפו": 5000,
    "תל-אביב": 5000,
    "תל-אביב-יפו": 5000,
    "jerusalem": 5000,
    "ירושלים": 5000,
    "חיפה": 4000,
    "haifa": 4000,
    "באר שבע": 6000,
    "beer sheva": 6000,
    "beersheba": 6000,
    "רמת גן": 8600,
    "ramat gan": 8600,
    "גבעתיים": 8700,
    "givatayim": 8700,
    "פתח תקווה": 7900,
    "petah tikva": 7900,
    "ראשון לציון": 8400,
    "rishon lezion": 8400,
    "אשדוד": 8200,
    "ashdod": 8200,
}

# Common Neighborhood Codes (within cities)
NEIGHBORHOODS = {
    # Tel Aviv
    "רמת החייל": {"city": 5000, "code": 203},
    "רמת אביב": {"city": 5000, "code": 201},
    "נווה צדק": {"city": 5000, "code": 202},
    "פלורנטין": {"city": 5000, "code": 204},
    "נווה שאנן": {"city": 5000, "code": 205},
    "שכונת התקווה": {"city": 5000, "code": 206},
    "יפו": {"city": 5000, "code": 207},
    "נווה אושר": {"city": 5000, "code": 208},
    "נווה עופר": {"city": 5000, "code": 209},
    "נווה יוסף": {"city": 5000, "code": 210},
    
    # Jerusalem
    "הר הרצל": {"city": 5000, "code": 301},
    "גבעת שאול": {"city": 5000, "code": 302},
    "בית הכרם": {"city": 5000, "code": 303},
    "רמות": {"city": 5000, "code": 304},
    "גילה": {"city": 5000, "code": 305},
    
    # Haifa
    "הר הכרמל": {"city": 4000, "code": 401},
    "נווה שאנן": {"city": 4000, "code": 402},
    "עין הים": {"city": 4000, "code": 403},
    "בת גלים": {"city": 4000, "code": 404},
}

# Search Presets
SEARCH_PRESETS = {
    "houses_ramat_hahayal": {
        "property": "בית פרטי",
        "city": "תל אביב",
        "neighborhood": "רמת החייל",
        "description": "בתים פרטיים ברמת החייל, תל אביב"
    },
    "apartments_tel_aviv": {
        "property": "דירה",
        "city": "תל אביב",
        "description": "דירות בתל אביב"
    },
    "villas_north": {
        "property": "וילה",
        "city": "רמת גן",
        "description": "וילות ברמת גן"
    },
    "land_tel_aviv": {
        "property": "קרקע",
        "city": "תל אביב",
        "description": "קרקעות בתל אביב"
    }
}

def get_city_code(city_name: str) -> int:
    """Get city code by name"""
    return CITIES.get(city_name, CITIES.get(city_name.lower(), 5000))

def get_neighborhood_code(city_name: str, neighborhood_name: str) -> int:
    """Get neighborhood code by city and neighborhood names"""
    city_code = get_city_code(city_name)
    
    for name, data in NEIGHBORHOODS.items():
        if data["city"] == city_code and neighborhood_name.lower() in name.lower():
            return data["code"]
    
    return None

def get_search_preset(preset_name: str) -> dict:
    """Get search preset by name"""
    return SEARCH_PRESETS.get(preset_name, {})

def validate_search_params(property_type: str, city: str, neighborhood: str = None) -> dict:
    """
    Validate and return search parameters with proper codes
    
    Returns:
        Dict with validated parameters and any validation errors
    """
    errors = []
    params = {}
    
    # Validate property type using existing PropertyTypeUtils
    property_code = get_property_type_code(property_type)
    if property_code:
        params['property'] = property_code
    else:
        errors.append(f"Invalid property type: {property_type}")
    
    # Validate city
    city_code = get_city_code(city)
    if city_code:
        params['city'] = city_code
    else:
        errors.append(f"Invalid city: {city}")
    
    # Validate neighborhood if provided
    if neighborhood:
        hood_code = get_neighborhood_code(city, neighborhood)
        if hood_code:
            params['neighborhood'] = hood_code
        else:
            errors.append(f"Invalid neighborhood: {neighborhood} in {city}")
    
    return {
        'params': params,
        'errors': errors,
        'valid': len(errors) == 0
    }
