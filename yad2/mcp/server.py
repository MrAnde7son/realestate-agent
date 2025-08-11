#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 FastMCP Server

FastMCP-based Model Context Protocol server for real estate search integration with LLMs.
Aligned in structure with the gov.il FastMCP server.
"""

from fastmcp import FastMCP, Context
from typing import Optional

# Support both package execution (python -m) and direct script execution
try:
    from yad2.core import Yad2SearchParameters, Yad2ParameterReference
    from yad2.core.utils import DataUtils
    from yad2.scrapers import Yad2Scraper
except ModuleNotFoundError:
    import os, sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from yad2.core import Yad2SearchParameters, Yad2ParameterReference
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
    maxPrice: Optional[int] = None,
    minPrice: Optional[int] = None,
    topArea: Optional[int] = None,
    area: Optional[int] = None,
    city: Optional[int] = None,
    neighborhood: Optional[int] = None,
    property: Optional[str] = None,
    rooms: Optional[str] = None,
    parking: Optional[int] = None,
    elevator: Optional[int] = None,
    balcony: Optional[int] = None,
    renovated: Optional[int] = None,
    max_pages: int = 3,
):
    """Search for real estate listings on Yad2 with optional filters."""
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
            parking=parking,
            elevator=elevator,
            balcony=balcony,
            renovated=renovated,
        ).items()
        if v is not None
    }

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
    listings = _current_scraper.scrape_all_pages(max_pages=max_pages, delay=1)
    _last_search_results = listings

    if not listings:
        return {
            "success": False,
            "message": "No listings found for the specified criteria.",
            "search_url": summary["search_url"],
            "parameters": summary.get("parameters"),
            "parameter_descriptions": summary.get("parameter_descriptions"),
        }

    # Format listings for output (limit to first 10 for brevity)
    formatted = []
    for l in listings[:10]:
        formatted.append({
            "title": l.title,
            "price": l.price,
            "address": l.address,
            "rooms": l.rooms,
            "size": l.size,
            "floor": l.floor,
            "url": l.url,
        })

    price_stats = DataUtils.calculate_price_stats(listings)

    return {
        "success": True,
        "total_listings": len(listings),
        "search_url": summary["search_url"],
        "parameters": summary.get("parameters"),
        "parameter_descriptions": summary.get("parameter_descriptions"),
        "listings_preview": formatted,
        "price_stats": price_stats,
    }


@mcp.tool()
async def build_search_url(
    ctx: Context,
    maxPrice: Optional[int] = None,
    minPrice: Optional[int] = None,
    topArea: Optional[int] = None,
    area: Optional[int] = None,
    city: Optional[int] = None,
    neighborhood: Optional[int] = None,
    property: Optional[str] = None,
    rooms: Optional[str] = None,
    parking: Optional[int] = None,
    elevator: Optional[int] = None,
    balcony: Optional[int] = None,
    renovated: Optional[int] = None,
):
    """Build a Yad2 search URL for the given parameters (no scraping)."""
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
            parking=parking,
            elevator=elevator,
            balcony=balcony,
            renovated=renovated,
        ).items()
        if v is not None
    }

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

    # Organize into categories similar to the legacy server
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
async def analyze_search_results(ctx: Context, analysis_type: str = "summary"):
    """Analyze the last search results. Run search_real_estate first."""
    if not _last_search_results:
        return {"success": False, "message": "No search results available. Run search_real_estate first."}

    if analysis_type == "summary":
        total = len(_last_search_results)
        with_price = len([l for l in _last_search_results if l.price])
        with_address = len([l for l in _last_search_results if l.address])
        with_rooms = len([l for l in _last_search_results if l.rooms])
        with_size = len([l for l in _last_search_results if l.size])
        return {
            "success": True,
            "total": total,
            "with_price": with_price,
            "with_address": with_address,
            "with_rooms": with_rooms,
            "with_size": with_size,
        }

    if analysis_type == "price_analysis":
        stats = DataUtils.calculate_price_stats(_last_search_results)
        if not stats:
            return {"success": False, "message": "No price data available."}

        prices = [l.price for l in _last_search_results if l.price and isinstance(l.price, (int, float))]
        ranges = [
            (0, 3_000_000, "Under 3M NIS"),
            (3_000_000, 5_000_000, "3M - 5M NIS"),
            (5_000_000, 8_000_000, "5M - 8M NIS"),
            (8_000_000, 12_000_000, "8M - 12M NIS"),
            (12_000_000, float("inf"), "Over 12M NIS"),
        ]
        distribution = []
        for min_p, max_p, label in ranges:
            count_in_range = len([p for p in prices if min_p <= p < max_p])
            if count_in_range > 0:
                distribution.append({
                    "label": label,
                    "count": count_in_range,
                    "percentage": count_in_range / len(prices) * 100,
                })
        return {"success": True, "stats": stats, "distribution": distribution}

    if analysis_type == "location_breakdown":
        groups = DataUtils.group_by_location(_last_search_results)
        if not groups:
            return {"success": False, "message": "No address data available."}
        breakdown = {loc: len(listings) for loc, listings in groups.items()}
        total_with_address = sum(breakdown.values())
        top = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:10]
        top_formatted = [
            {"location": loc, "count": count, "percentage": count / total_with_address * 100}
            for loc, count in top
        ]
        return {"success": True, "total_with_address": total_with_address, "top_locations": top_formatted}

    if analysis_type == "property_types":
        room_counts = {}
        sizes = []
        for l in _last_search_results:
            if l.rooms:
                key = str(l.rooms)
                room_counts[key] = room_counts.get(key, 0) + 1
            if l.size and isinstance(l.size, (int, float)):
                sizes.append(l.size)
        result = {"room_distribution": room_counts}
        if sizes:
            result["size_average"] = sum(sizes) / len(sizes)
            result["size_min"] = min(sizes)
            result["size_max"] = max(sizes)
        return {"success": True, **result}

    return {"success": False, "message": f"Unknown analysis_type: {analysis_type}"}


@mcp.tool()
async def save_search_results(ctx: Context, filename: Optional[str] = None):
    """Save the last search results to a JSON file."""
    if _current_scraper is None or not _last_search_results:
        return {"success": False, "message": "No search results available to save."}
    try:
        saved_file = _current_scraper.save_to_json(filename)
        return {"success": True, "file": saved_file}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    mcp.run()
