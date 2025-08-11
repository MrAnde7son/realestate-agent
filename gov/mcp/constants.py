# -*- coding: utf-8 -*-
"""Configuration constants and tag metadata for the DataGov MCP server."""

CKAN_BASE_URL = "https://data.gov.il/api/3/action"

# Timeouts are expressed in seconds
DEFAULT_TIMEOUT = 10
SEARCH_TIMEOUT = 15

USER_AGENT = "MCP-DataGovIL-Client/2.0.0"

DEFAULT_LIMITS = {
    "list": 10,
    "search": 100,
    "max": 1000,
}

POPULAR_DATASETS = [
    "branches",
    "jerusalem-municipality-budget",
    "mechir-lamishtaken",
    "traffic-counts",
    "population-and-recipients-of-benefits-under-settlement-2012",
]

# Popular organizations for the organization tool
POPULAR_ORGANIZATIONS = [
    "ministry-of-health",
    "tel-aviv-yafo",
    "jerusalem",
    "cbs",
    "ministry-of-finance",
]

# Frequently searched topics used as keyword examples
POPULAR_TOPICS = [
    "אוצר וכלכלה",
    "סביבה",
    "משרד התחבורה",
    "תחבורה",
    "GIS",
    "אוכלוסיה",
    "מים",
    "תקציב",
]

# Available topic categories
TOPIC_CATEGORIES = [
    "government",
    "transportation",
    "environment",
    "health_welfare",
    "education",
    "demographics",
    "technology",
    "economy",
    "agriculture",
    "tourism",
    "organizations",
]

# Example resource IDs used for documentation and tests
EXAMPLE_RESOURCE_IDS = {
    "bankBranches": "2202bada-4baf-45f5-aa61-8c5bad9646d3",
    "airStations": "782cfb94-ebbd-4f41-aba2-80c298457a58",
    "contaminatedLand": "54aa9ff1-2d89-4899-bb57-bf2a749ff4b3",
}

# Common search keywords in Hebrew and English
COMMON_KEYWORDS = {
    "hebrew": [
        "תקציב (budget)",
        "אוכלוסיה (population)",
        "תחבורה (transport)",
        "בריאות (health)",
        "חינוך (education)",
        "סביבה (environment)",
    ],
    "english": [
        "budget",
        "population",
        "transport",
        "health",
        "education",
        "environment",
        "municipality",
        "government",
        "public",
    ],
}

# Example queries for a find_datasets tool (topic based)
FIND_EXAMPLES = [
    'find_datasets("תחבורה") → transportation datasets',
    'find_datasets("תקציב עירייה") → municipal budgets',
    'find_datasets("בנק") → banking related datasets',
    'find_datasets("traffic") → transportation data',
    'find_datasets("health בריאות") → health datasets',
    'find_datasets("סביבה") → environment datasets',
    'find_datasets("אוכלוסיה") → demographics datasets',
]

# Tag metadata organised by categories
TAGS_DATA = {
    "metadata": {
        "source": "data.gov.il",
        "total_tags": 50,
        "last_updated": "2025-01-28",
        "note": "Numbers indicate dataset count per tag",
    },
    "popular_tags": {
        "top_10": [
            {"tag": "אוצר וכלכלה", "count": 102, "category": "government"},
            {"tag": "סביבה", "count": 78, "category": "environment"},
            {"tag": "משרד התחבורה", "count": 74, "category": "organization"},
            {"tag": "חצב", "count": 69, "category": "organization"},
            {"tag": "תחבורה", "count": 69, "category": "transportation"},
            {"tag": "ממג", "count": 67, "category": "organization"},
            {"tag": "GIS", "count": 63, "category": "technology"},
            {"tag": "אוכלוסיה", "count": 59, "category": "demographics"},
            {"tag": "מים", "count": 50, "category": "environment"},
            {"tag": "תקציב", "count": 50, "category": "finance"},
        ],
    },
    "categories": {
        "government": {
            "hebrew": "ממשל",
            "tags": [
                {"tag": "אוצר וכלכלה", "count": 102},
                {"tag": "תקציב", "count": 50},
                {"tag": "תקציב וביצוע", "count": 14},
                {"tag": "שינויים בתקציב", "count": 12},
                {"tag": "תכנון", "count": 16},
                {"tag": "משפט", "count": 13},
                {"tag": "דת", "count": 12},
            ],
        },
        "transportation": {
            "hebrew": "תחבורה",
            "tags": [
                {"tag": "תחבורה", "count": 69},
                {"tag": "תחבורה ציבורית", "count": 31},
                {"tag": "כלי רכב", "count": 27},
                {"tag": "רכב", "count": 27},
                {"tag": "רכבת", "count": 15},
                {"tag": "אוטובוסים", "count": 12},
                {"tag": "רכבת כבדה", "count": 11},
                {"tag": "דרכים", "count": 10},
                {"tag": "שאלות תאוריה", "count": 13},
                {"tag": "מבחן נהיגה עיוני", "count": 12},
            ],
        },
        "environment": {
            "hebrew": "סביבה",
            "tags": [
                {"tag": "סביבה", "count": 78},
                {"tag": "מים", "count": 50},
                {"tag": "water", "count": 44},
                {"tag": "הגנת הסביבה", "count": 14},
                {"tag": "זיהום אוויר", "count": 12},
                {"tag": "פליטות", "count": 11},
                {"tag": "פסולת", "count": 10},
                {"tag": "הידרומטריה", "count": 10},
                {"tag": "borehole", "count": 10},
            ],
        },
        "health_welfare": {
            "hebrew": "בריאות ורווחה",
            "tags": [
                {"tag": "בריאות ורווחה", "count": 38},
                {"tag": "בריאות", "count": 20},
            ],
        },
        "education": {
            "hebrew": "חינוך",
            "tags": [
                {"tag": "חינוך", "count": 28},
                {"tag": "חינוך ותרבות", "count": 17},
                {"tag": "מדע", "count": 12},
            ],
        },
        "demographics": {
            "hebrew": "דמוגרפיה",
            "tags": [
                {"tag": "אוכלוסיה", "count": 59},
                {"tag": "עולים חדשים", "count": 13},
                {"tag": "עלייה", "count": 10},
            ],
        },
        "technology": {
            "hebrew": "טכנולוגיה",
            "tags": [
                {"tag": "GIS", "count": 63},
                {"tag": "gis", "count": 15},
            ],
        },
        "economy": {
            "hebrew": "כלכלה",
            "tags": [
                {"tag": "כלכלה", "count": 11},
            ],
        },
        "agriculture": {
            "hebrew": "חקלאות",
            "tags": [
                {"tag": "חקלאות", "count": 14},
            ],
        },
        "tourism": {
            "hebrew": "תיירות",
            "tags": [
                {"tag": "תיירות", "count": 15},
            ],
        },
        "organizations": {
            "hebrew": "ארגונים",
            "tags": [
                {"tag": "משרד התחבורה", "count": 74},
                {"tag": "חצב", "count": 69, "full_name": "החברה הממשלתית לביטוח בריאות"},
                {"tag": "ממג", "count": 67, "full_name": "מרכז מיפוי ישראל"},
                {"tag": "רשות המים", "count": 48},
                {"tag": "משרד המשפטים", "count": 46},
                {"tag": "משרד הבריאות", "count": 16},
                {"tag": "בנק ישראל", "count": 15},
                {"tag": "המרכז למיפוי ישראל", "count": 15},
                {"tag": "משרד התקשורת", "count": 13},
                {"tag": "משרד התיירות", "count": 11},
                {"tag": "מינהל התכנון", "count": 10},
            ],
        },
    },
    "duplicates": {
        "note": "Tags that represent the same concept",
        "gis": ["GIS", "gis"],
        "water": ["מים", "water"],
        "mapping": ["ממג", "המרכז למיפוי ישראל"],
    },
    "search_suggestions": {
        "by_theme": {
            "financial": ["אוצר וכלכלה", "תקציב", "כלכלה", "בנק ישראל"],
            "transportation": ["תחבורה", "תחבורה ציבורית", "משרד התחבורה"],
            "environmental": ["סביבה", "מים", "הגנת הסביבה"],
            "health": ["בריאות", "בריאות ורווחה", "משרד הבריאות"],
            "geographic": ["GIS", "ממג", "המרכז למיפוי ישראל"],
            "demographic": ["אוכלוסיה", "עלייה", "עולים חדשים"],
        },
    },
}

def get_tags_by_category(category: str):
    """Return tag objects for a given category key."""
    return TAGS_DATA.get("categories", {}).get(category, {}).get("tags", [])

def search_tags(keyword: str):
    """Search tags by a keyword across all categories."""
    results = []
    lower_keyword = keyword.lower()
    for category in TAGS_DATA.get("categories", {}).values():
        for tag_obj in category.get("tags", []):
            if lower_keyword in tag_obj["tag"].lower():
                results.append({**tag_obj, "category": category["hebrew"]})
    results.sort(key=lambda x: x["count"], reverse=True)
    return results

def get_popular_tags(limit: int = 10):
    """Return a list of the most popular tags."""
    return TAGS_DATA.get("popular_tags", {}).get("top_10", [])[:limit]

def get_tag_suggestions(theme: str):
    """Return search suggestions for a given theme."""
    return (
        TAGS_DATA.get("search_suggestions", {})
        .get("by_theme", {})
        .get(theme, [])
    )
