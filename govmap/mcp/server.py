#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GovMap FastMCP Server

Exposes GovMap tools for autocomplete, WFS queries, and parcel lookup.
"""

import os
import sys
from typing import Any, Dict, Optional

from fastmcp import Context, FastMCP

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from govmap.api_client import GovMapClient

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
async def govmap_autocomplete(ctx: Context, query: str) -> Dict[str, Any]:
    """GovMap public autocomplete (no token). Returns raw JSON buckets."""
    client = _get_client()
    await ctx.info(f"Searching GovMap autocomplete for: {query}")
    return client.autocomplete(query)


@mcp.tool()
async def govmap_wfs(ctx: Context, type_name: str, cql_filter: str = "", max_features: int = 50) -> Dict[str, Any]:
    """Call WFS GetFeature on an OpenData layer with an optional CQL filter."""
    client = _get_client()
    await ctx.info(f"Querying WFS layer {type_name} with filter: {cql_filter or 'none'}")
    return client.wfs_get_features(layer=type_name, cql_filter=cql_filter or None, max_features=max_features)


@mcp.tool()
async def govmap_featureinfo(ctx: Context, layer: str, x: float, y: float, buffer_m: int = 5) -> Dict[str, Any]:
    """WMS GetFeatureInfo around a point (EPSG:2039)."""
    client = _get_client()
    await ctx.info(f"Getting feature info for layer {layer} at point ({x}, {y})")
    infos = client.wms_getfeatureinfo(layer=layer, x=x, y=y, buffer_m=buffer_m)
    return {"layer": layer, "features": [fi.attributes for fi in infos]}


@mcp.tool()
async def govmap_parcel_at_point(ctx: Context, x: float, y: float, type_name: str = "opendata:PARCEL_ALL") -> Dict[str, Any]:
    """Get parcel feature at a point (EPSG:2039)."""
    client = _get_client()
    await ctx.info(f"Looking up parcel at point ({x}, {y})")
    f = client.get_parcel_at_point(x, y, layer=type_name)
    return {"feature": f}


@mcp.tool()
async def govmap_coordinate_conversion(ctx: Context, x: float, y: float, from_crs: str = "ITM", to_crs: str = "WGS84") -> Dict[str, Any]:
    """Convert coordinates between ITM (EPSG:2039) and WGS84 (EPSG:4326)."""
    from govmap.api_client import itm_to_wgs84, wgs84_to_itm
    
    if from_crs.upper() == "ITM" and to_crs.upper() == "WGS84":
        lon, lat = itm_to_wgs84(x, y)
        return {"x": lon, "y": lat, "crs": "EPSG:4326"}
    elif from_crs.upper() == "WGS84" and to_crs.upper() == "ITM":
        x_itm, y_itm = wgs84_to_itm(x, y)
        return {"x": x_itm, "y": y_itm, "crs": "EPSG:2039"}
    else:
        return {"error": f"Unsupported conversion from {from_crs} to {to_crs}"}


if __name__ == "__main__":
    mcp.run()
