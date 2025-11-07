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

from govmap.api_client import GovMapClient, itm_to_wgs84, wgs84_to_itm  # noqa: E402

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
async def get_layers_catalog(ctx: Context, language: str = "he") -> Dict[str, Any]:
    """Get the layers catalog from GovMap."""
    client = _get_client()
    await ctx.info(f"Getting layers catalog (language: {language})")
    return client.get_layers_catalog(language=language)


@mcp.tool()
async def get_search_types(ctx: Context, language: str = "he") -> Dict[str, Any]:
    """Get search types from GovMap."""
    client = _get_client()
    await ctx.info(f"Getting search types (language: {language})")
    return client.get_search_types(language=language)


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
async def get_base_layers(ctx: Context) -> Dict[str, Any]:
    """Get base layers from GovMap API."""
    client = _get_client()
    await ctx.info("Getting base layers")
    return client.get_base_layers()


@mcp.tool()
async def entities_by_point(
    ctx: Context,
    x: float,
    y: float,
    layer_ids: List[Union[str, int]],
    tolerance_m: float = 30.0
) -> Dict[str, Any]:
    """Get entities by point with specified layer IDs (EPSG:2039)."""
    client = _get_client()
    await ctx.info(f"Getting entities at point ({x}, {y}) for {len(layer_ids)} layers")
    return client.entities_by_point(x, y, layer_ids, tolerance_m=tolerance_m)


if __name__ == "__main__":
    mcp.run()
