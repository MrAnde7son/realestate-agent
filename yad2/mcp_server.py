#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 FastMCP Server

FastMCP-based Model Context Protocol server for real estate search integration with LLMs.
Exposes all Yad2 API client functions as tools.

Available Tools:

API CLIENT FUNCTIONS:
- fetch_listings: Fetch active listings via Yad2's public map feed API
- fetch_contact_info: Fetch contact information for a listing token
- fetch_project_autocomplete: Fetch project data from Yad1 developers autocomplete API
- fetch_location_autocomplete: Fetch location data from Yad2 address autocomplete API
- fetch_latest_deals: Fetch completed deal records from Yad2's latest-deals endpoint

UTILITY TOOLS:
- get_search_parameters_reference: Get reference of all search parameters
- get_all_property_types: Get all property type codes with names

Usage Examples:
1. Fetch listings: fetch_listings(city="5000", property="1", listing_type="sale")
2. Fetch contact info: fetch_contact_info(token="abc123")
3. Search locations: fetch_location_autocomplete(search_text="רמת החייל")
4. Fetch latest deals: fetch_latest_deals(city=5000, limit=10)
"""

import os
import sys
import traceback
import logging
from typing import Literal, Optional, Dict, Any

from fastmcp import Context, FastMCP

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from yad2.core import Yad2ParameterReference, Yad2SearchParameters
from yad2.core.utils import DataUtils
from yad2.api_client import Yad2APIClient, ListingType
from yad2.utils.property_types import PropertyTypeUtils

logger = logging.getLogger(__name__)

# Create an MCP server
mcp = FastMCP("Yad2RealEstate", dependencies=["requests", "beautifulsoup4", "lxml", "pandas"]) 

# Module-level state (persists across tool calls within the same server process)
_api_client = Yad2APIClient()
_last_search_results = []


@mcp.tool()
async def fetch_listings(
    ctx: Context,
    # Price parameters
    maxPrice: Optional[int | str] = None,
    minPrice: Optional[int | str] = None,
    # Location parameters
    topArea: Optional[int | str] = None,
    area: Optional[int | str] = None,
    city: Optional[int | str] = None,
    neighborhood: Optional[int | str] = None,
    street: Optional[str] = None,
    # Property type
    property: Optional[str] = None,
    # Property details
    rooms: Optional[str] = None,
    minRooms: Optional[int | str] = None,
    maxRooms: Optional[int | str] = None,
    floor: Optional[str] = None,
    size: Optional[str] = None,
    minSize: Optional[int | str] = None,
    maxSize: Optional[int | str] = None,
    # Features
    parking: Optional[int | str] = None,
    elevator: Optional[int | str | bool] = None,
    balcony: Optional[int | str | bool] = None,
    renovated: Optional[int | str | bool] = None,
    accessibility: Optional[int | str | bool] = None,
    airCondition: Optional[int | str | bool] = None,
    bars: Optional[int | str | bool] = None,
    shelter: Optional[int | str | bool] = None,
    storage: Optional[int | str | bool] = None,
    terrace: Optional[int | str | bool] = None,
    garden: Optional[int | str | bool] = None,
    pets: Optional[int | str | bool] = None,
    furniture: Optional[int | str | bool] = None,
    # Building details
    buildingFloors: Optional[int | str] = None,
    entranceDate: Optional[str] = None,
    propertyCondition: Optional[str] = None,
    # Search parameters
    page: Optional[int | str] = None,
    order: Optional[str] = None,
    priceOnly: Optional[int | str | bool] = None,
    priceDropped: Optional[int | str | bool] = None,
    saleType: Optional[str] = None,
    exclusive: Optional[int | str | bool] = None,
    publishedDays: Optional[int | str] = None,
    # Advanced filters
    fromFloor: Optional[int | str] = None,
    toFloor: Optional[int | str] = None,
    yearBuilt: Optional[int | str] = None,
    minYear: Optional[int | str] = None,
    maxYear: Optional[int | str] = None,
    # API options
    zoom: Optional[int] = None,
    listing_type: str = ListingType.ALL,
    pull_contacts: bool = False,
    limit: Optional[int | str] = None,
) -> Dict[str, Any]:
    """Fetch active listings via Yad2's public map feed API.
    
    Supports all Yad2 search parameters. Boolean parameters accept: 1/0, true/false, yes/no.
    
    Args:
        maxPrice: Maximum price filter
        minPrice: Minimum price filter
        topArea: Top area ID
        area: Area ID
        city: City ID
        neighborhood: Neighborhood ID
        street: Street name or ID
        property: Property type code or Hebrew name (e.g., "1" or "דירה")
        rooms: Number of rooms (e.g., "3-4", "4+")
        minRooms: Minimum number of rooms
        maxRooms: Maximum number of rooms
        floor: Floor range (e.g., "1-3", "4+")
        size: Property size in sqm (e.g., "80-120")
        minSize: Minimum size in sqm
        maxSize: Maximum size in sqm
        parking: Number of parking spaces
        elevator: Has elevator (1/0, true/false)
        balcony: Has balcony (1/0, true/false)
        renovated: Is renovated (1/0, true/false)
        accessibility: Has accessibility features (1/0, true/false)
        airCondition: Has air conditioning (1/0, true/false)
        bars: Has security bars (1/0, true/false)
        shelter: Has safe room (1/0, true/false)
        storage: Has storage (1/0, true/false)
        terrace: Has terrace (1/0, true/false)
        garden: Has garden (1/0, true/false)
        pets: Pets allowed (1/0, true/false)
        furniture: Is furnished (1/0, true/false)
        buildingFloors: Total building floors
        entranceDate: Move-in date
        propertyCondition: Property condition
        page: Page number
        order: Sort order (date, price_asc, price_desc, size_asc, size_desc)
        priceOnly: Show price only assets (1/0, true/false)
        priceDropped: Filter for properties with price drops (1/0, true/false)
        saleType: Sale type
        exclusive: Exclusive assets only (1/0, true/false)
        publishedDays: Published within X days
        fromFloor: From floor
        toFloor: To floor
        yearBuilt: Year built
        minYear: Minimum year built
        maxYear: Maximum year built
        zoom: Zoom level (defaults to 15)
        listing_type: Type of listing - "sale", "rent", "commercial", or "all"
        pull_contacts: Whether to fetch contact information for listings
        limit: Maximum number of listings to return (applied after fetching)
    
    Returns:
        Dictionary with listings data and statistics
    """
    global _api_client, _last_search_results

    params = {
        k: v
        for k, v in dict(
            maxPrice=maxPrice,
            minPrice=minPrice,
            topArea=topArea,
            area=area,
            city=city,
            neighborhood=neighborhood,
            street=street,
            property=property,
            rooms=rooms,
            minRooms=minRooms,
            maxRooms=maxRooms,
            floor=floor,
            size=size,
            minSize=minSize,
            maxSize=maxSize,
            parking=parking,
            elevator=elevator,
            balcony=balcony,
            renovated=renovated,
            accessibility=accessibility,
            airCondition=airCondition,
            bars=bars,
            shelter=shelter,
            storage=storage,
            terrace=terrace,
            garden=garden,
            pets=pets,
            furniture=furniture,
            buildingFloors=buildingFloors,
            entranceDate=entranceDate,
            propertyCondition=propertyCondition,
            page=page,
            order=order,
            priceOnly=priceOnly,
            priceDropped=priceDropped,
            saleType=saleType,
            exclusive=exclusive,
            publishedDays=publishedDays,
            fromFloor=fromFloor,
            toFloor=toFloor,
            yearBuilt=yearBuilt,
            minYear=minYear,
            maxYear=maxYear,
        ).items()
        if v is not None
    }

    # Convert Hebrew property type names to codes if needed
    if 'property' in params and params['property']:
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


    await ctx.info("Fetching listings from Yad2 API...")
    await ctx.info(f"Search parameters: {search_params.get_active_parameters()}")
    await ctx.info(f"Fetching map listings from Yad2 map feed API (listing_type={listing_type}, zoom={zoom})...")
    try:
        listings = _api_client.fetch_listings(
            search_params=search_params,
            zoom=zoom,
            listing_type=listing_type,
            pull_contacts=pull_contacts
        )
        _last_search_results = listings
        
        await ctx.info(f"Fetched {len(listings)} listings from Yad2 map endpoint")

        if not listings:
            return {
                "success": False,
                "message": "No listings found for the specified criteria.",
                "parameters": search_params.get_active_parameters(),
            }

        # Apply limit if specified (convert string to int if needed)
        limit_int = None
        if limit is not None:
            try:
                limit_int = int(limit) if isinstance(limit, str) else limit
                if limit_int > 0:
                    listings = listings[:limit_int]
            except (ValueError, TypeError):
                await ctx.warning(f"Invalid limit value: {limit}, ignoring limit")
                limit_int = None

        # Format listings for output (limit to first 20 for brevity in preview)
        preview_limit = min(20, len(listings))
        formatted = []
        for l in listings[:preview_limit]:
            formatted.append({
                "title": l.title,
                "price": l.price,
                "address": l.address,
                "rooms": l.rooms,
                "size": l.size,
                "floor": l.floor,
                "property_type": l.property_type,
                "url": l.url,
                "listing_id": l.listing_id,
                "contact_info": l.contact_info.to_dict() if l.contact_info else None,
            })

        price_stats = DataUtils.calculate_price_stats(listings) if listings else None

        return {
            "success": True,
            "total_listings": len(listings),
            "total_fetched": len(_last_search_results) if _last_search_results else len(listings),
            "limit_applied": limit_int,
            "parameters": search_params.get_active_parameters(),
            "listings_preview": formatted,
            "price_stats": price_stats,
        }
    except Exception as e:
        error_traceback = traceback.format_exc()
        await ctx.error(f"Error fetching listings: {str(e)}")
        await ctx.error(f"Traceback: {error_traceback}")
        logger.error(
            "Exception in fetch_listings handler. Params: %s, Error: %s",
            search_params.get_active_parameters(),
            error_traceback,
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "parameters": search_params.get_active_parameters(),
        }


@mcp.tool()
async def fetch_contact_info(ctx: Context, token: str) -> Dict[str, Any]:
    """Fetch contact information for a listing token.
    
    Args:
        token: Listing token from Yad2 URL (e.g., from /item/{token})
    
    Returns:
        Dictionary with contact information or error message
    """
    global _api_client
    
    try:
        contact = _api_client.fetch_contact_info(token)
        if contact:
            return {
                "success": True,
                "contact": contact.to_dict(),
            }
        else:
            return {
                "success": False,
                "message": "Contact information not found or unavailable.",
            }
    except Exception as e:
        await ctx.error(f"Error fetching contact info: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def fetch_project_autocomplete(ctx: Context, phrase: str) -> Dict[str, Any]:
    """Fetch project data from Yad1 developers autocomplete API.
    
    Args:
        phrase: Free-text phrase, e.g. project name
    
    Returns:
        Dictionary with project data or None if not found
    """
    global _api_client
    
    try:
        project_data = _api_client.fetch_project_autocomplete(phrase)
        if project_data:
            return {
                "success": True,
                "project": project_data,
            }
        else:
            return {
                "success": False,
                "message": f"No project found matching '{phrase}'",
            }
    except Exception as e:
        await ctx.error(f"Error fetching project autocomplete: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def fetch_location_autocomplete(ctx: Context, search_text: str) -> Dict[str, Any]:
    """Fetch location data from Yad2 address autocomplete API and return prepared search parameters.
    
    Args:
        search_text: Address text to search for (e.g., "רוזוב תל אביב")
    
    Returns:
        Dictionary with prepared search parameters (city, area, neighborhood, street, etc.)
    """
    global _api_client
    
    try:
        location_params = _api_client.fetch_location_autocomplete(search_text)
        if location_params:
            # Convert Yad2SearchParameters to dictionary for JSON serialization
            params_dict = location_params.get_active_parameters()
            return {
                "success": True,
                "search_text": search_text,
                "search_parameters": params_dict,
            }
        else:
            return {
                "success": False,
                "message": f"No location found matching '{search_text}'",
            }
    except Exception as e:
        await ctx.error(f"Error fetching location autocomplete: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def fetch_latest_deals(
    ctx: Context,
    city: Optional[int] = None,
    neighborhood: Optional[int] = None,
    coords: str = "10.0,10.0",
    limit: int = 8,
    page: int = 1,
    sort_by: str = "saleDate",
    order: str = "desc",
    max_pages: int = 1,
) -> Dict[str, Any]:
    """Fetch completed deal records from Yad2's latest-deals endpoint.
    
    Args:
        city: Optional city identifier
        neighborhood: Optional neighborhood identifier
        coords: Latitude/longitude pair as string "lat,long" (default: "10.0,10.0")
        limit: Number of results per page (default: 8)
        page: Result page to request (default: 1)
        sort_by: Sorting field (e.g., "distance", "saleDate") (default: "saleDate")
        order: Sort order "asc" or "desc" (default: "desc")
        max_pages: Number of pages to fetch (default: 1)
    
    Returns:
        Dictionary with deal records
    """
    global _api_client
    
    try:
        search_params = Yad2SearchParameters()
        if city:
            search_params.set_parameter("city", city)
        if neighborhood:
            search_params.set_parameter("neighborhood", neighborhood)
        
        deals = _api_client.fetch_latest_deals(
            search_params=search_params,
            city=city,
            neighborhood=neighborhood,
            coords=coords,
            limit=limit,
            page=page,
            sort_by=sort_by,
            order=order,
            max_pages=max_pages
        )
        
        if not deals:
            return {
                "success": False,
                "message": "No deals found for the specified criteria.",
            }
        
        # Format deals for output
        formatted = []
        for deal in deals[:20]:
            formatted.append({
                "title": deal.title,
                "price": deal.price,
                "address": deal.address,
                "rooms": deal.rooms,
                "size": deal.size,
                "floor": deal.floor,
                "property_type": deal.property_type,
                "date_posted": deal.date_posted,
                "recent_deal": deal.recent_deal,
            })
        
        return {
            "success": True,
            "total_deals": len(deals),
            "deals_preview": formatted,
        }
    except Exception as e:
        await ctx.error(f"Error fetching latest deals: {str(e)}")
        return {
            "success": False,
            "error": str(e),
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
            "airCondition", "bars", "shelter", "storage", "terrace", "garden",
            "pets", "furniture", "shelter"
        ],
        "Search Options": ["page", "order", "priceOnly", "priceDropped", "exclusive", "publishedDays"],
    }

    result = {"categories": {}, "all_parameters": params}
    for cat, plist in categories.items():
        result["categories"][cat] = {p: params[p] for p in plist if p in params}

    return result



@mcp.tool()
async def get_all_property_types(ctx: Context):
    """Get all available property type codes with Hebrew and English names."""
    global _api_client
    try:
        property_types = _api_client.param_reference.get_property_types()
        
        # Add English translations for each
        enhanced_types = {}
        for code, hebrew_name in property_types.items():
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


if __name__ == "__main__":
    mcp.run()
