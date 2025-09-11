#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 FastMCP Server - Cleaned Up Version

FastMCP-based Model Context Protocol server for real estate search integration with LLMs.
Streamlined to include only essential tools for real estate search and property type conversion.

Available Tools:

CORE SEARCH FUNCTIONALITY:
- search_real_estate: Search for real estate assets with filters
- build_search_url: Build search URLs with parameters
- get_search_parameters_reference: Get reference of all search parameters

PROPERTY TYPE UTILITIES:
- get_all_property_types: Get all property type codes with names
- hebrew_to_property_code: Convert Hebrew property type names to Yad2 codes
- validate_property_type_code: Validate property type codes

LOCATION SERVICES:
- search_locations: Search locations using autocomplete API

Usage Examples:
1. Get all property types: get_all_property_types()
2. Convert Hebrew to code: hebrew_to_property_code(hebrew_name="בית פרטי")
3. Search locations: search_locations(search_text="רמת החייל")
4. Search real estate: search_real_estate(property="5", city="5000", neighborhood="203")
"""

import os
import sys
from typing import Optional

from fastmcp import Context, FastMCP

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from yad2.core import Yad2ParameterReference, Yad2SearchParameters
from yad2.core.utils import DataUtils
from yad2.scrapers import Yad2Scraper

# Create an MCP server
mcp = FastMCP("Yad2RealEstate", dependencies=["requests", "beautifulsoup4", "lxml", "pandas"]) 

# Module-level state (persists across tool calls within the same server process)
_current_scraper = None
_last_search_results = []


@mcp.tool()
async def search_real_estate(
    ctx: Context,
    maxPrice: Optional[int | str] = None,
    minPrice: Optional[int | str] = None,
    topArea: Optional[int | str] = None,
    area: Optional[int | str] = None,
    city: Optional[int | str] = None,
    neighborhood: Optional[int | str] = None,
    property: Optional[str] = None,
    rooms: Optional[str] = None,
    minRooms: Optional[int | str] = None,
    maxRooms: Optional[int | str] = None,
    parking: Optional[int | str] = None,
    elevator: Optional[int | str] = None,
    balcony: Optional[int | str] = None,
    renovated: Optional[int | str] = None,
    max_pages: int | str = 3,
):
    """Search for real estate assets on Yad2 with optional filters.
    
    The 'property' parameter accepts both Yad2 codes (e.g., "5") and Hebrew names (e.g., "בית פרטי").
    Hebrew names are automatically converted to their corresponding Yad2 codes.
    
    Common property types:
    - "בית פרטי" or "5" = House (Private house)
    - "בית דו משפחתי" or "39" = Two-family house
    - "דירה" or "1" = Apartment
    - "וילה" or "5" = Villa
    - "נטהאוס" or "6" = Penthouse
    """
    global _current_scraper, _last_search_results

    params = {
        k: v
        for k, v in dict(
            maxPrice=maxPrice,
            minPrice=minPrice,
            topArea=topArea,
            area=area,
            city=city,
            neighborhood=neighborhood,
            property=property,
            rooms=rooms,
            minRooms=minRooms,
            maxRooms=maxRooms,
            parking=parking,
            elevator=elevator,
            balcony=balcony,
            renovated=renovated,
        ).items()
        if v is not None
    }

    # Convert Hebrew property type names to codes if needed
    if 'property' in params and params['property']:
        from ..utils.property_types import PropertyTypeUtils
        property_value = params['property']
        
        # If it's a string (Hebrew name), try to convert to code
        if isinstance(property_value, str) and not property_value.isdigit():
            # Try exact match first
            code = PropertyTypeUtils.hebrew_name_to_code(property_value)
            if code is not None:
                params['property'] = str(code)
                await ctx.info(f"Converted property type '{property_value}' to code: {code}")
            else:
                # Try partial match
                matching_codes = PropertyTypeUtils.search_hebrew_name_to_code(property_value)
                if matching_codes:
                    # Use the first match
                    code, hebrew_name = matching_codes[0]
                    params['property'] = str(code)
                    await ctx.info(f"Converted property type '{property_value}' to code: {code} (matched: {hebrew_name})")
                else:
                    await ctx.warning(f"Could not convert property type '{property_value}' to code. Using as-is.")

    search_params = Yad2SearchParameters()
    for key, value in params.items():
        try:
            search_params.set_parameter(key, value)
        except ValueError:
            search_params.parameters[key] = value

    try:
        max_pages = int(max_pages)
    except (TypeError, ValueError):
        max_pages = 3

    await ctx.info("Initializing scraper and generating search summary...")
    _current_scraper = Yad2Scraper(search_params)
    summary = _current_scraper.get_search_summary()

    await ctx.info(f"Scraping up to {max_pages} page(s)...")
    assets = _current_scraper.scrape_all_pages(max_pages=max_pages, delay=1)
    _last_search_results = assets

    if not assets:
        return {
            "success": False,
            "message": "No assets found for the specified criteria.",
            "search_url": summary["search_url"],
            "parameters": summary.get("parameters"),
            "parameter_descriptions": summary.get("parameter_descriptions"),
        }

    # Format assets for output (limit to first 10 for brevity)
    formatted = []
    for l in assets[:10]:
        formatted.append({
            "title": l.title,
            "price": l.price,
            "address": l.address,
            "rooms": l.rooms,
            "size": l.size,
            "floor": l.floor,
            "url": l.url,
        })

    price_stats = DataUtils.calculate_price_stats(assets)

    return {
        "success": True,
        "total_assets": len(assets),
        "search_url": summary["search_url"],
        "parameters": summary.get("parameters"),
        "parameter_descriptions": summary.get("parameter_descriptions"),
        "assets_preview": formatted,
        "price_stats": price_stats,
    }


@mcp.tool()
async def build_search_url(
    ctx: Context,
    maxPrice: Optional[int | str] = None,
    minPrice: Optional[int | str] = None,
    topArea: Optional[int | str] = None,
    area: Optional[int | str] = None,
    city: Optional[int | str] = None,
    neighborhood: Optional[int | str] = None,
    property: Optional[str] = None,
    rooms: Optional[str] = None,
    minRooms: Optional[int | str] = None,
    maxRooms: Optional[int | str] = None,
    parking: Optional[int | str] = None,
    elevator: Optional[int | str] = None,
    balcony: Optional[int | str] = None,
    renovated: Optional[int | str] = None,
):
    """Build a Yad2 search URL for the given parameters (no scraping).
    
    The 'property' parameter accepts both Yad2 codes (e.g., "5") and Hebrew names (e.g., "בית פרטי").
    Hebrew names are automatically converted to their corresponding Yad2 codes.
    
    Common property types:
    - "בית פרטי" or "5" = House (Private house)
    - "בית דו משפחתי" or "39" = Two-family house
    - "דירה" or "1" = Apartment
    - "נטהאוס" or "6" = Penthouse
    """
    params = {
        k: v
        for k, v in dict(
            maxPrice=maxPrice,
            minPrice=minPrice,
            topArea=topArea,
            area=area,
            city=city,
            neighborhood=neighborhood,
            property=property,
            rooms=rooms,
            minRooms=minRooms,
            maxRooms=maxRooms,
            parking=parking,
            elevator=elevator,
            balcony=balcony,
            renovated=renovated,
        ).items()
        if v is not None
    }

    # Convert Hebrew property type names to codes if needed
    if 'property' in params and params['property']:
        from ..utils.property_types import PropertyTypeUtils
        property_value = params['property']
        
        # If it's a string (Hebrew name), try to convert to code
        if isinstance(property_value, str) and not property_value.isdigit():
            # Try exact match first
            code = PropertyTypeUtils.hebrew_name_to_code(property_value)
            if code is not None:
                params['property'] = str(code)
            else:
                # Try partial match
                matching_codes = PropertyTypeUtils.search_hebrew_name_to_code(property_value)
                if matching_codes:
                    # Use the first match
                    code, hebrew_name = matching_codes[0]
                    params['property'] = str(code)

    search_params = Yad2SearchParameters()
    for key, value in params.items():
        try:
            search_params.set_parameter(key, value)
        except ValueError:
            search_params.parameters[key] = value

    url = search_params.build_url()

    # Provide parameter descriptions
    ref = Yad2ParameterReference()
    descriptions = {}
    for param, value in search_params.get_active_parameters().items():
        info = ref.get_parameter_info(param)
        descriptions[param] = {
            "value": value,
            "description": info["description"],
        }

    return {
        "success": True,
        "url": url,
        "parameters": search_params.get_active_parameters(),
        "descriptions": descriptions,
    }


@mcp.tool()
async def get_search_parameters_reference(ctx: Context):
    """Return a comprehensive reference of available search parameters."""
    ref = Yad2ParameterReference()
    params = ref.list_all_parameters()

    # Organize into categories
    categories = {
        "Price Parameters": ["maxPrice", "minPrice"],
        "Location Parameters": ["topArea", "area", "city", "neighborhood"],
        "Property Types": ["property"],
        "Property Details": ["rooms", "floor", "size", "minSize", "maxSize"],
        "Features & Amenities": [
            "parking", "elevator", "balcony", "renovated", "accessibility",
            "airCondition", "bars", "mamad", "storage", "terrace", "garden",
            "pets", "furniture",
        ],
        "Search Options": ["page", "order", "dealType", "priceOnly", "exclusive", "publishedDays"],
    }

    result = {"categories": {}, "all_parameters": params}
    for cat, plist in categories.items():
        result["categories"][cat] = {p: params[p] for p in plist if p in params}

    return result



@mcp.tool()
async def get_all_property_types(ctx: Context):
    """Get all available property type codes with Hebrew and English names."""
    scraper = Yad2Scraper()
    try:
        property_types = scraper.get_property_types()
        
        # Add English translations for each
        enhanced_types = {}
        for code, hebrew_name in property_types.items():
            from ..utils.property_types import PropertyTypeUtils
            english_name = PropertyTypeUtils.translate_to_english(hebrew_name)
            enhanced_types[code] = {
                "hebrew": hebrew_name,
                "english": english_name,
                "code": code
            }
        
        return {
            "success": True,
            "total_types": len(enhanced_types),
            "property_types": enhanced_types
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def search_locations(ctx: Context, search_text: str):
    """Search for locations using Yad2's address autocomplete API."""
    scraper = Yad2Scraper()
    try:
        location_data = scraper.fetch_location_data(search_text)
        
        return {
            "success": True,
            "search_text": search_text,
            "locations": location_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    mcp.run()
