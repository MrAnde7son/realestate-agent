#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Madlan FastMCP Server

FastMCP-based Model Context Protocol server for Madlan real estate search integration with LLMs.

Available Tools:

CORE SEARCH FUNCTIONALITY:
- madlan_search_real_estate: Search for real estate listings with filters
- get_addresses: Autocomplete addresses and get address details
- fetch_listings: Fetch listings by location document ID

Usage Examples:
1. Search addresses: get_addresses(text="רוזוב 14 תל")
2. Search real estate: madlan_search_real_estate(location_doc_id="רוזוב-14-תל-אביב-יפו-ישראל", deal_type="unitBuy", max_price=9000000)
3. Search with filters: madlan_search_real_estate(location_doc_id="...", min_price=1000000, max_price=5000000, min_rooms=3, max_rooms=5)
"""

import os
import sys
from typing import Literal, Optional, List, Dict, Any

from fastmcp import Context, FastMCP

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from madlan.api_client import MadlanAPIClient, DealType
from yad2.core.models import RealEstateListing

# Create an MCP server
mcp = FastMCP("MadlanRealEstate")

# Module-level state (persists across tool calls within the same server process)
_current_client: Optional[MadlanAPIClient] = None
_last_search_results: List[RealEstateListing] = []


@mcp.tool()
async def get_addresses(
    ctx: Context,
    text: str,
    completion_types: Optional[List[str]] = None,
):
    """Autocomplete addresses and get address details from Madlan.
    
    This tool searches for addresses matching the provided text and returns
    detailed address information including location, hierarchy, and relevant
    document IDs.
    
    Args:
        text: Search text for address autocomplete (e.g., "רוזוב 14 תל")
        completion_types: Optional list of completion types to search.
                         Defaults to all available types if not provided.
    
    Returns:
        Dictionary with success status and list of addresses, each containing:
        - id: Address identifier
        - docId: Document ID (use this for madlan_search_real_estate)
        - name: Display name
        - type: Address type (address, street, city, etc.)
        - location: [longitude, latitude] coordinates
        - Additional fields depend on the address type
    """
    global _current_client
    
    try:
        if _current_client is None:
            _current_client = MadlanAPIClient()
        
        addresses = _current_client.get_addresses(text, completion_types)
        
        if not addresses:
            return {
                "success": False,
                "message": f"No addresses found for query: {text}",
                "addresses": [],
            }
        
        # Format addresses for output
        formatted = []
        for addr in addresses[:20]:  # Limit to first 20 for brevity
            formatted.append({
                "id": addr.get("id"),
                "docId": addr.get("docId"),
                "name": addr.get("name"),
                "type": addr.get("type"),
                "location": addr.get("location"),
                "identityDocId": addr.get("identityDocId"),
            })
        
        return {
            "success": True,
            "total_addresses": len(addresses),
            "addresses": formatted,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "addresses": [],
        }


@mcp.tool()
async def madlan_search_real_estate(
    ctx: Context,
    location_doc_id: Optional[str] = None,
    deal_type: Literal["unitBuy", "unitRent"] = "unitBuy",
    min_price: Optional[int | str] = None,
    max_price: Optional[int | str] = None,
    min_rooms: Optional[float | str] = None,
    max_rooms: Optional[float | str] = None,
    min_area: Optional[int | str] = None,
    max_area: Optional[int | str] = None,
    min_floor: Optional[int | str] = None,
    max_floor: Optional[int | str] = None,
    min_baths: Optional[float | str] = None,
    max_baths: Optional[float | str] = None,
    building_class: Optional[str] = None,
    general_condition: Optional[str] = None,
    seller_type: Optional[str] = None,
    amenities: Optional[Dict[str, Any]] = None,
    limit: int | str = 50,
    offset: int | str = 0,
    no_fee: bool = False,
    price_drop: bool = False,
    under_price_estimation: bool = False,
    discounted_projects: bool = False,
    only_immediate: bool = False,
    is_commercial_real_estate: bool = False

):
    """Search for real estate listings on Madlan with optional filters.
    
    This tool searches for property listings based on various filters including
    location, price, rooms, area, and other property characteristics.
    
    Args:
        location_doc_id: Document ID for location (e.g., from get_addresses)
        deal_type: Type of deal - "unitBuy" (for sale) or "unitRent" (for rent)
        min_price: Minimum price filter (None means no minimum)
        max_price: Maximum price filter (None means no maximum)
        min_rooms: Minimum number of rooms (None means no minimum)
        max_rooms: Maximum number of rooms (None means no maximum)
        min_area: Minimum area in square meters (None means no minimum)
        max_area: Maximum area in square meters (None means no maximum)
        min_floor: Minimum floor number (None means no minimum)
        max_floor: Maximum floor number (None means no maximum)
        min_baths: Minimum number of bathrooms (None means no minimum)
        max_baths: Maximum number of bathrooms (None means no maximum)
        building_class: Comma-separated building class filters (e.g., "A,B")
        general_condition: Comma-separated general condition filters
        seller_type: Comma-separated seller type filters
        amenities: Dictionary of amenity filters
        limit: Maximum number of results to return (default: 50)
        offset: Offset for pagination (default: 0)
        no_fee: Filter for no fee listings
        price_drop: Filter for listings with price drops
        under_price_estimation: Filter for listings under price estimation
        discounted_projects: Filter for discounted projects
        only_immediate: Filter for immediate availability only
        is_commercial_real_estate: Filter for commercial real estate
    
    Returns:
        Dictionary with success status and list of listings
    """
    global _current_client, _last_search_results
    
    try:
        if _current_client is None:
            _current_client = MadlanAPIClient()
        
        # Convert deal_type string to DealType enum
        deal_type_enum = DealType.UNIT_BUY if deal_type == "unitBuy" else DealType.UNIT_RENT
        
        await ctx.info(f"Searching Madlan for {deal_type} listings...")
        
        # Convert string inputs to appropriate numeric types
        def to_int(value):
            if value is None:
                return None
            return int(value) if isinstance(value, str) else value
        
        def to_float(value):
            if value is None:
                return None
            return float(value) if isinstance(value, str) else value
        
        min_price_num = to_int(min_price)
        max_price_num = to_int(max_price)
        min_rooms_num = to_float(min_rooms)
        max_rooms_num = to_float(max_rooms)
        min_area_num = to_int(min_area)
        max_area_num = to_int(max_area)
        min_floor_num = to_int(min_floor)
        max_floor_num = to_int(max_floor)
        min_baths_num = to_float(min_baths)
        max_baths_num = to_float(max_baths)
        limit_num = to_int(limit) if limit else 50
        offset_num = to_int(offset) if offset else 0
        
        # Convert min/max parameters to ranges
        price_range = [min_price_num, max_price_num] if (min_price_num is not None or max_price_num is not None) else None
        rooms_range = [min_rooms_num, max_rooms_num] if (min_rooms_num is not None or max_rooms_num is not None) else None
        area_range = [min_area_num, max_area_num] if (min_area_num is not None or max_area_num is not None) else None
        floor_range = [min_floor_num, max_floor_num] if (min_floor_num is not None or max_floor_num is not None) else None
        baths_range = [min_baths_num, max_baths_num] if (min_baths_num is not None or max_baths_num is not None) else None
        
        # Convert comma-separated strings to lists
        building_class_list = None
        if building_class:
            building_class_list = [item.strip() for item in building_class.split(",") if item.strip()]
        
        general_condition_list = None
        if general_condition:
            general_condition_list = [item.strip() for item in general_condition.split(",") if item.strip()]
        
        seller_type_list = None
        if seller_type:
            seller_type_list = [item.strip() for item in seller_type.split(",") if item.strip()]
        
        listings = _current_client.fetch_listings(
            location_doc_id=location_doc_id,
            deal_type=deal_type_enum,
            price_range=price_range,
            rooms_range=rooms_range,
            area_range=area_range,
            floor_range=floor_range,
            baths_range=baths_range,
            building_class=building_class_list,
            general_condition=general_condition_list,
            seller_type=seller_type_list,
            amenities=amenities,
            limit=limit_num,
            offset=offset_num,
            no_fee=no_fee,
            price_drop=price_drop,
            under_price_estimation=under_price_estimation,
            discounted_projects=discounted_projects,
            only_immediate=only_immediate,
            is_commercial_real_estate=is_commercial_real_estate,
        )
        
        _last_search_results = listings
        
        if not listings:
            return {
                "success": False,
                "message": "No listings found for the specified criteria.",
                "listings": [],
            }
        
        # Format listings for output (limit to first 10 for brevity)
        formatted = []
        for listing in listings[:10]:
            formatted.append({
                "listing_id": listing.listing_id,
                "title": listing.title,
                "address": listing.address,
                "price": listing.price,
                "rooms": listing.rooms,
                "size": listing.size,
                "floor": listing.floor,
                "url": listing.url,
                "listing_type": listing.listing_type,
            })
        
        return {
            "success": True,
            "total_listings": len(listings),
            "listings": formatted,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "listings": [],
        }



if __name__ == "__main__":
    mcp.run()

