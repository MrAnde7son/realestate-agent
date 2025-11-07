#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Madlan FastMCP Server

FastMCP-based Model Context Protocol server for Madlan real estate search integration with LLMs.

Available Tools:

CORE SEARCH FUNCTIONALITY:
- search_real_estate: Search for real estate listings with filters
- get_addresses: Autocomplete addresses and get address details
- fetch_listings: Fetch listings by location document ID

Usage Examples:
1. Search addresses: get_addresses(text="רוזוב 14 תל")
2. Search real estate: search_real_estate(location_doc_id="רוזוב-14-תל-אביב-יפו-ישראל", deal_type="unitBuy")
3. Fetch listings: fetch_listings(location_doc_id="...", price_range=[1000000, 5000000])
"""

import os
import sys
from typing import Optional, List, Dict, Any

from fastmcp import Context, FastMCP

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from madlan.api_client import MadlanAPIClient, DealType
from yad2.core.models import RealEstateListing

# Create an MCP server
mcp = FastMCP("MadlanRealEstate", dependencies=["requests"])

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
        - docId: Document ID (use this for search_real_estate)
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
async def search_real_estate(
    ctx: Context,
    location_doc_id: Optional[str] = None,
    deal_type: str = "unitBuy",
    price_range: Optional[List[Optional[int]]] = None,
    rooms_range: Optional[List[Optional[float]]] = None,
    area_range: Optional[List[Optional[int]]] = None,
    floor_range: Optional[List[Optional[int]]] = None,
    baths_range: Optional[List[Optional[float]]] = None,
    building_class: Optional[List[str]] = None,
    general_condition: Optional[List[str]] = None,
    seller_type: Optional[List[str]] = None,
    amenities: Optional[Dict[str, Any]] = None,
    limit: int = 50,
    offset: int = 0,
    no_fee: bool = False,
    price_drop: bool = False,
    under_price_estimation: bool = False,
    discounted_projects: bool = False,
    only_immediate: bool = False,
    is_commercial_real_estate: bool = False,
):
    """Search for real estate listings on Madlan with optional filters.
    
    This tool searches for property listings based on various filters including
    location, price, rooms, area, and other property characteristics.
    
    Args:
        location_doc_id: Document ID for location (e.g., from get_addresses)
        deal_type: Type of deal - "unitBuy" (for sale) or "unitRent" (for rent)
        price_range: [min, max] price range (None means no limit)
        rooms_range: [min, max] number of rooms range
        area_range: [min, max] area in square meters range
        floor_range: [min, max] floor number range
        baths_range: [min, max] number of bathrooms range
        building_class: List of building class filters
        general_condition: List of general condition filters
        seller_type: List of seller type filters
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
        
        listings = _current_client.fetch_listings(
            location_doc_id=location_doc_id,
            deal_type=deal_type_enum,
            price_range=price_range,
            rooms_range=rooms_range,
            area_range=area_range,
            floor_range=floor_range,
            baths_range=baths_range,
            building_class=building_class,
            general_condition=general_condition,
            seller_type=seller_type,
            amenities=amenities,
            limit=limit,
            offset=offset,
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


@mcp.tool()
async def fetch_listings(
    ctx: Context,
    location_doc_id: str,
    deal_type: str = "unitBuy",
    price_range: Optional[List[Optional[int]]] = None,
    rooms_range: Optional[List[Optional[float]]] = None,
    limit: int = 50,
):
    """Fetch real estate listings by location document ID.
    
    This is a convenience wrapper around search_real_estate with simplified parameters.
    
    Args:
        location_doc_id: Document ID for location (required, from get_addresses)
        deal_type: Type of deal - "unitBuy" (for sale) or "unitRent" (for rent)
        price_range: [min, max] price range (None means no limit)
        rooms_range: [min, max] number of rooms range
        limit: Maximum number of results to return (default: 50)
    
    Returns:
        Dictionary with success status and list of listings
    """
    return await search_real_estate(
        ctx=ctx,
        location_doc_id=location_doc_id,
        deal_type=deal_type,
        price_range=price_range,
        rooms_range=rooms_range,
        limit=limit,
    )


if __name__ == "__main__":
    mcp.run()

