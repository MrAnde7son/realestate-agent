#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GIS (Tel Aviv) FastMCP Server

Exposes TelAvivGS functions for address geocoding, permits, and nearby layers.
"""

import os
import sys
from typing import Iterable, Optional

from fastmcp import Context, FastMCP

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from gis.gis_client import TelAvivGS

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
async def geocode_address(
    ctx: Context, street: str, house_number: int, like: bool = True
):
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
    await ctx.info(
        f"Fetching permits near point ({x},{y}) radius={radius}m; download_pdfs={download_pdfs}"
    )
    results = gs.get_building_permits(
        x,
        y,
        radius=radius,
        fields=fields,
        download_pdfs=download_pdfs,
        save_dir=save_dir,
    )
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
    ctx: Context, x: float, y: float, save_dir: Optional[str] = "privilege_pages"
):
    """Download the building privilege ("zchuyot") page for a location."""
    gs = _get_client()
    await ctx.info(f"Downloading building privilege page for point ({x},{y})")

    result = gs.get_building_privilege_page(x, y, save_dir=save_dir)

    if not result:
        await ctx.warning(
            "Failed to download building privilege page - block/parcel values not found"
        )
        return {
            "success": False,
            "file_path": None,
            "content_type": None,
            "parcels": [],
            "pdf_data": None,
            "message": "Could not download building privilege page - block/parcel values not found",
        }

    msg = result.get("message", "Building privilege page downloaded")
    await ctx.info(f"{msg} to: {result.get('file_path')}")

    result["success"] = True
    return result


@mcp.tool()
async def get_affordable_housing_projects(
    ctx: Context, x: float, y: float, radius: int = 500
):
    """Get affordable housing projects within a radius (meters) from point (x,y).
    Pipeline of affordable housing; indicates supply pressure and long-term demographic mix.
    """
    gs = _get_client()
    return gs.get_affordable_housing_projects(x, y, radius=radius)


@mcp.tool()
async def get_bike_paths(ctx: Context, x: float, y: float, radius: int = 300):
    """Get bicycle paths within a radius (meters) from point (x,y).
    Walkability and bike-accessibility = strong QoL indicator.
    """
    gs = _get_client()
    return gs.get_bike_paths(x, y, radius=radius)


@mcp.tool()
async def get_metro_stations(ctx: Context, x: float, y: float, radius: int = 1000):
    """Get metro stations (all lines: Red, Green, Purple) within a radius (meters) from point (x,y).
    Major value driver; buyers pay 10–20% premium near stations.
    """
    gs = _get_client()
    return gs.get_metro_stations(x, y, radius=radius)


@mcp.tool()
async def get_metro_stations_red(ctx: Context, x: float, y: float, radius: int = 1000):
    """Get Red Line metro stations within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_metro_stations_red(x, y, radius=radius)


@mcp.tool()
async def get_metro_stations_green(
    ctx: Context, x: float, y: float, radius: int = 1000
):
    """Get Green Line metro stations within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_metro_stations_green(x, y, radius=radius)


@mcp.tool()
async def get_metro_stations_purple(
    ctx: Context, x: float, y: float, radius: int = 1000
):
    """Get Purple Line metro stations within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_metro_stations_purple(x, y, radius=radius)


@mcp.tool()
async def get_parking_lots(ctx: Context, x: float, y: float, radius: int = 300):
    """Get public and private parking lots within a radius (meters) from point (x,y).
    Parking scarcity strongly affects rental yield.
    """
    gs = _get_client()
    return gs.get_parking_lots(x, y, radius=radius)


@mcp.tool()
async def get_parking_public(ctx: Context, x: float, y: float, radius: int = 300):
    """Get public parking lots within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_parking_public(x, y, radius=radius)


@mcp.tool()
async def get_parking_private(ctx: Context, x: float, y: float, radius: int = 300):
    """Get private parking lots within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_parking_private(x, y, radius=radius)


@mcp.tool()
async def get_soil_contamination(ctx: Context, x: float, y: float, radius: int = 200):
    """Get soil contamination sites (rehabilitation and protection actions) within a radius (meters) from point (x,y).
    Underrated risk factor in Tel Aviv (old industrial lots).
    """
    gs = _get_client()
    return gs.get_soil_contamination(x, y, radius=radius)


@mcp.tool()
async def get_schools(ctx: Context, x: float, y: float, radius: int = 500):
    """Get schools and kindergartens within a radius (meters) from point (x,y).
    School zone relevance for families. Integrates education score and school catchment overlay.
    """
    gs = _get_client()
    return gs.get_schools(x, y, radius=radius)


@mcp.tool()
async def get_schools_kindergartens(
    ctx: Context, x: float, y: float, radius: int = 500
):
    """Get kindergartens within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_schools_kindergartens(x, y, radius=radius)


@mcp.tool()
async def get_schools_only(ctx: Context, x: float, y: float, radius: int = 500):
    """Get schools (excluding kindergartens) within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_schools_only(x, y, radius=radius)


@mcp.tool()
async def get_green_amenities(ctx: Context, x: float, y: float, radius: int = 400):
    """Get green amenities (playgrounds, dog parks, public gardens) within a radius (meters) from point (x,y).
    Green amenity proximity drives price premiums. Enhances livability heatmap or filters.
    """
    gs = _get_client()
    return gs.get_green_amenities(x, y, radius=radius)


@mcp.tool()
async def get_playgrounds(ctx: Context, x: float, y: float, radius: int = 400):
    """Get playgrounds within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_playgrounds(x, y, radius=radius)


@mcp.tool()
async def get_dog_parks(ctx: Context, x: float, y: float, radius: int = 400):
    """Get dog parks within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_dog_parks(x, y, radius=radius)


@mcp.tool()
async def get_public_gardens(ctx: Context, x: float, y: float, radius: int = 400):
    """Get public gardens within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_public_gardens(x, y, radius=radius)


@mcp.tool()
async def get_medical_facilities(ctx: Context, x: float, y: float, radius: int = 500):
    """Get medical facilities (medical centers, health funds, pharmacies) within a radius (meters) from point (x,y).
    Access to health services. Health coverage layer for older buyers.
    """
    gs = _get_client()
    return gs.get_medical_facilities(x, y, radius=radius)


@mcp.tool()
async def get_medical_centers(ctx: Context, x: float, y: float, radius: int = 500):
    """Get medical centers within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_medical_centers(x, y, radius=radius)


@mcp.tool()
async def get_health_funds(ctx: Context, x: float, y: float, radius: int = 500):
    """Get health fund clinics within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_health_funds(x, y, radius=radius)


@mcp.tool()
async def get_pharmacies(ctx: Context, x: float, y: float, radius: int = 500):
    """Get pharmacies within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_pharmacies(x, y, radius=radius)


@mcp.tool()
async def get_community_facilities(ctx: Context, x: float, y: float, radius: int = 400):
    """Get community facilities (community centers, youth and entrepreneurship centers) within a radius (meters) from point (x,y).
    Social & community vitality indicator. "Community Index" per neighborhood.
    """
    gs = _get_client()
    return gs.get_community_facilities(x, y, radius=radius)


@mcp.tool()
async def get_community_centers(ctx: Context, x: float, y: float, radius: int = 400):
    """Get community centers within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_community_centers(x, y, radius=radius)


@mcp.tool()
async def get_youth_entrepreneurship_centers(
    ctx: Context, x: float, y: float, radius: int = 400
):
    """Get youth and entrepreneurship centers within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_youth_entrepreneurship_centers(x, y, radius=radius)


@mcp.tool()
async def get_construction_sites(ctx: Context, x: float, y: float, radius: int = 300):
    """Get construction sites within a radius (meters) from point (x,y).
    Indicates redevelopment intensity. Use for development-activity overlay (use permit + construction + TMA data).
    """
    gs = _get_client()
    return gs.get_construction_sites(x, y, radius=radius)


@mcp.tool()
async def get_tama38_key_areas(ctx: Context, x: float, y: float, radius: int = 500):
    """Get TAMA 38 policy key areas within a radius (meters) from point (x,y).
    Captures buildings eligible for strengthening/redevelopment. Use for potential-rights calculator.
    """
    gs = _get_client()
    return gs.get_tama38_key_areas(x, y, radius=radius)


@mcp.tool()
async def get_road_works(ctx: Context, x: float, y: float, radius: int = 200):
    """Get road works and night works in public space within a radius (meters) from point (x,y).
    Disruption + infrastructure upgrades. Use for temporal map layer ("current works").
    """
    gs = _get_client()
    return gs.get_road_works(x, y, radius=radius)


@mcp.tool()
async def get_road_works_only(ctx: Context, x: float, y: float, radius: int = 200):
    """Get road works within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_road_works_only(x, y, radius=radius)


@mcp.tool()
async def get_night_works_public(ctx: Context, x: float, y: float, radius: int = 200):
    """Get night works in public space within a radius (meters) from point (x,y)."""
    gs = _get_client()
    return gs.get_night_works_public(x, y, radius=radius)


if __name__ == "__main__":
    mcp.run()
