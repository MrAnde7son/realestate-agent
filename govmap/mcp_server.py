#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GovMap FastMCP Server

Exposes GovMap tools for autocomplete, search, parcel lookup, and coordinate conversion.
"""

import os
import sys
from typing import Any, Dict, List, Optional, Union

from fastmcp import Context, FastMCP

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from govmap.api_client import GovMapClient, DealType, itm_to_wgs84, wgs84_to_itm  # noqa: E402

# Create an MCP server
mcp = FastMCP(
    "GovMap",
    dependencies=[
        "requests",
        "pyproj",
    ],
)

# Persistent client for this server process
_client: Optional[GovMapClient] = None

def _get_client() -> GovMapClient:
    global _client
    if _client is None:
        _client = GovMapClient()
    return _client


@mcp.tool()
async def autocomplete(ctx: Context, query: str, language: str = "he", max_results: int = 10) -> Dict[str, Any]:
    """GovMap public autocomplete (no token). Returns raw JSON buckets."""
    client = _get_client()
    await ctx.info(f"Searching GovMap autocomplete for: {query}")
    return client.autocomplete(query, language=language, max_results=max_results)


@mcp.tool()
async def extract_coordinates_from_shapes(ctx: Context, result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract ITM coordinates from an autocomplete result.
    
    Use this tool to extract coordinates from a result returned by the autocomplete tool.
    This enables the workflow: autocomplete -> extract_coordinates_from_shapes -> get_deals_by_location.
    
    Parameters:
    -----------
    result : Dict[str, Any]
        A single result dictionary from the autocomplete API response (e.g., autocomplete_result["results"][0])
        
    Returns:
    --------
    Dict[str, Any]
        Dictionary with 'x' and 'y' coordinates (ITM EPSG:2039) if found,
        or {'error': 'message'} if coordinates could not be extracted
    """
    coords = GovMapClient.extract_coordinates_from_shapes(result)
    if coords:
        x, y = coords
        await ctx.info(f"Extracted coordinates: ({x}, {y})")
        return {"x": x, "y": y, "crs": "EPSG:2039"}
    else:
        return {"error": "Could not extract coordinates from result. Make sure the result contains a 'shape' field with POINT format."}


@mcp.tool()
async def coordinate_conversion(ctx: Context, x: float, y: float, from_crs: str = "ITM", to_crs: str = "WGS84") -> Dict[str, Any]:
    """Convert coordinates between ITM (EPSG:2039) and WGS84 (EPSG:4326)."""
    if from_crs.upper() == "ITM" and to_crs.upper() == "WGS84":
        lon, lat = itm_to_wgs84(x, y)
        return {"x": lon, "y": lat, "crs": "EPSG:4326"}
    elif from_crs.upper() == "WGS84" and to_crs.upper() == "ITM":
        x_itm, y_itm = wgs84_to_itm(x, y)
        return {"x": x_itm, "y": y_itm, "crs": "EPSG:2039"}
    else:
        return {"error": f"Unsupported conversion from {from_crs} to {to_crs}"}


@mcp.tool()
async def get_parcel_data(ctx: Context, x: float, y: float) -> Dict[str, Any]:
    """Get parcel data for specific coordinates (EPSG:2039)."""
    client = _get_client()
    await ctx.info(f"Getting parcel data at point ({x}, {y})")
    return client.get_parcel_data(x, y)


@mcp.tool()
async def get_parcel_addresses(ctx: Context, objectid: int) -> List[Dict[str, Any]]:
    """Get detailed address information for a parcel using its objectid."""
    client = _get_client()
    await ctx.info(f"Getting parcel addresses for objectid: {objectid}")
    return client.get_parcel_addresses(objectid)


@mcp.tool()
async def get_addresses_by_block_parcel(ctx: Context, block: str, parcel: str) -> List[Dict[str, Any]]:
    """Get addresses for a given block and parcel using GovMap autocomplete API."""
    client = _get_client()
    await ctx.info(f"Looking up addresses by block/parcel: {block}/{parcel}")
    return client.get_addresses_by_block_parcel(block, parcel)


@mcp.tool()
async def entities_by_point(
    ctx: Context,
    x: float,
    y: float,
    layer_ids: List[Union[str, int]],
    radius: float = 30.0
) -> Dict[str, Any]:
    """Get entities by point with specified layer IDs (EPSG:2039)."""
    client = _get_client()
    await ctx.info(f"Getting entities at point ({x}, {y}) for {len(layer_ids)} layers")
    return client.entities_by_point(x, y, layer_ids, radius=radius)


@mcp.tool()
async def get_deals_by_location(
    ctx: Context,
    x: float,
    y: float,
    start_date: str = "1998-01",
    end_date: str = "2025-11",
    radius: float = 100.0,
    deal_type: str = "street",
    limit: int = 9,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Get real estate deals for a specific location and radius.
    
    Returns standardized Deal objects with address, deal_date, deal_amount, rooms, 
    floor, asset_type, area, neighborhood, parcel information, etc.
    
    This function supports three levels of deal aggregation:
    - "street" (רמת הרחוב): Deals aggregated by street level
    - "neighborhood" (רמת השכונה): Deals aggregated by neighborhood level
    - "settlement" (רמת היישוב): Deals aggregated by settlement level
    
    Parameters:
    -----------
    x : float
        ITM X coordinate (EPSG:2039)
    y : float
        ITM Y coordinate (EPSG:2039)
    start_date : str
        Start date in format "YYYY-MM" (e.g., "1998-01")
    end_date : str
        End date in format "YYYY-MM" (e.g., "2025-11")
    radius : float
        Radius in meters to search for deals (default: 100.0)
    deal_type : str
        Type of deals: "street" (רמת הרחוב), "neighborhood" (רמת השכונה), 
        or "settlement" (רמת היישוב). Default: "street"
    limit : int
        Maximum number of deals to return per polygon (default: 9)
    offset : int
        Offset for pagination (default: 0)
    
    Returns:
    --------
    List[Dict[str, Any]]
        List of Deal objects as dictionaries, each containing:
        - address: Property address
        - deal_date: Date of the deal (DD/MM/YYYY format)
        - deal_amount: Deal amount in ILS
        - rooms: Number of rooms (can be None)
        - floor: Floor number (Hebrew text)
        - asset_type: Type of asset (e.g., "דירה", "בנין")
        - area: Area in square meters
        - neighborhood: Neighborhood name
        - parcel_block: Block number (גוש)
        - parcel_parcel: Parcel number (חלקה)
        - parcel_sub_parcel: Sub-parcel number (תת-חלקה)
        - raw: Raw data from the API
    """
    client = _get_client()
    
    # Convert deal_type string to DealType enum
    deal_type_enum = DealType.STREET
    if deal_type.lower() == "neighborhood":
        deal_type_enum = DealType.NEIGHBORHOOD
    elif deal_type.lower() == "settlement":
        deal_type_enum = DealType.SETTLEMENT
    
    await ctx.info(f"Getting deals by location at ({x}, {y}) with radius {radius}m")
    
    # Get deals from GovMap
    deals = client.get_deals_by_location(
        x=x,
        y=y,
        start_date=start_date,
        end_date=end_date,
        radius=radius,
        deal_type=deal_type_enum,
        limit=limit,
        offset=offset,
    )
    
    # Convert Deal objects to dictionaries
    result = []
    for deal in deals:
        deal_dict = {
            "address": deal.address,
            "deal_date": deal.deal_date,
            "deal_amount": deal.deal_amount,
            "rooms": deal.rooms,
            "floor": deal.floor,
            "asset_type": deal.asset_type,
            "year_built": deal.year_built,
            "area": deal.area,
            "neighborhood": deal.neighborhood,
            "block": deal.parcel_block,
            "parcel": deal.parcel_parcel,
            "sub_parcel": deal.parcel_sub_parcel,
        }
        result.append(deal_dict)
    
    await ctx.info(f"Found {len(result)} deals")
    return result


if __name__ == "__main__":
    mcp.run()
