#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GIS (Tel Aviv) FastMCP Server

Exposes TelAvivGS functions for address geocoding, permits, and nearby layers.
"""

from fastmcp import FastMCP, Context
from typing import Optional, Iterable, Dict, Any

# Support running via module and direct execution
try:
    from gis.gis_client import TelAvivGS
    from gis.parse_zchuyot import parse_zchuyot
except ModuleNotFoundError:
    import os, sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from gis.gis_client import TelAvivGS
    from gis.parse_zchuyot import parse_zchuyot

# Create an MCP server
mcp = FastMCP(
    "TelAvivGIS",
    dependencies=[
        "requests",
        "beautifulsoup4",
        "lxml",
        "pdfplumber",
        "python-dateutil",
    ],
)

# Persistent client for this server process
_client: Optional[TelAvivGS] = None

def _get_client() -> TelAvivGS:
    global _client
    if _client is None:
        _client = TelAvivGS()
    return _client


@mcp.tool()
async def geocode_address(ctx: Context, street: str, house_number: int, like: bool = True):
    """Return (x,y) EPSG:2039 for a given street and house number."""
    gs = _get_client()
    await ctx.info(f"Geocoding address: {street} {house_number} (like={like})")
    x, y = gs.get_address_coordinates(street, house_number, like=like)
    return {"x": x, "y": y, "srid": 2039}


@mcp.tool()
async def get_building_permits(
    ctx: Context,
    x: float,
    y: float,
    radius: int = 30,
    fields: Optional[Iterable[str]] = None,
    download_pdfs: bool = False,
    save_dir: Optional[str] = "permits",
):
    """Search for building permits near a point (x,y) in meters. Optionally download PDFs."""
    gs = _get_client()
    await ctx.info(f"Fetching permits near point ({x},{y}) radius={radius}m; download_pdfs={download_pdfs}")
    results = gs.get_building_permits(x, y, radius=radius, fields=fields, download_pdfs=download_pdfs, save_dir=save_dir)
    return {"count": len(results), "permits": results}


@mcp.tool()
async def get_land_use_main(ctx: Context, x: float, y: float):
    """Get main land-use categories intersecting point (x,y)."""
    gs = _get_client()
    return gs.get_land_use_main(x, y)


@mcp.tool()
async def get_land_use_detailed(ctx: Context, x: float, y: float):
    """Get detailed land-use categories intersecting point (x,y)."""
    gs = _get_client()
    return gs.get_land_use_detailed(x, y)


@mcp.tool()
async def get_plans_local(ctx: Context, x: float, y: float):
    """Get local/parcel-level plans intersecting point (x,y)."""
    gs = _get_client()
    return gs.get_plans_local(x, y)


@mcp.tool()
async def get_plans_citywide(ctx: Context, x: float, y: float):
    """Get city-wide plans intersecting point (x,y)."""
    gs = _get_client()
    return gs.get_plans_citywide(x, y)


@mcp.tool()
async def get_parcels(ctx: Context, x: float, y: float):
    """Get parcels intersecting point (x,y)."""
    gs = _get_client()
    return gs.get_parcels(x, y)


@mcp.tool()
async def get_blocks(ctx: Context, x: float, y: float):
    """Get blocks intersecting point (x,y)."""
    gs = _get_client()
    return gs.get_blocks(x, y)


@mcp.tool()
async def get_dangerous_buildings(ctx: Context, x: float, y: float, radius: int = 80):
    """Get dangerous buildings within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_dangerous_buildings(x, y, radius=radius)


@mcp.tool()
async def get_preservation(ctx: Context, x: float, y: float, radius: int = 80):
    """Get preservation-listed buildings within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_preservation(x, y, radius=radius)


@mcp.tool()
async def get_noise_levels(ctx: Context, x: float, y: float):
    """Get noise levels intersecting point (x,y)."""
    gs = _get_client()
    return gs.get_noise_levels(x, y)


@mcp.tool()
async def get_cell_antennas(ctx: Context, x: float, y: float, radius: int = 120):
    """Get existing and under-construction cell antennas near point (x,y)."""
    gs = _get_client()
    return gs.get_cell_antennas(x, y, radius=radius)


@mcp.tool()
async def get_green_areas(ctx: Context, x: float, y: float, radius: int = 150):
    """Get green areas within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_green_areas(x, y, radius=radius)


@mcp.tool()
async def get_shelters(ctx: Context, x: float, y: float, radius: int = 200):
    """Get shelters within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_shelters(x, y, radius=radius)


@mcp.tool()
async def get_building_privilege_page(
    ctx: Context,
    x: float,
    y: float,
    save_dir: Optional[str] = "privilege_pages"
):
    """Download and parse the building privilege ("zchuyot") page for a location."""
    gs = _get_client()
    await ctx.info(f"Downloading building privilege page for point ({x},{y})")
    
    privilege_path = gs.get_building_privilege_page(x, y, save_dir=save_dir)
    data: Optional[Dict[str, Any]] = None

    
    if not privilege_path:
        await ctx.warning("Failed to download building privilege page - gush/helka values not found")
        return {
            "success": False,
            "file_path": None,
            "data": None,
            "message": "Could not download building privilege page - gush/helka values not found",
        }
    
    if privilege_path.lower().endswith(".pdf"):
        try:
            data = parse_zchuyot(privilege_path)
            await ctx.info("Privilege page parsed successfully")
        except Exception as e:  
            await ctx.warning(f"Failed to parse privilege page: {e}")

    msg = "Building privilege page downloaded"
    if data:
        msg += " and parsed"
    await ctx.info(f"{msg} to: {privilege_path}")
    return {
        "success": True,
        "file_path": privilege_path,
        "data": data,
        "message": msg,
    }


if __name__ == "__main__":
    mcp.run() 