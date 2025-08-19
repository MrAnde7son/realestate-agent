#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 FastMCP Server

FastMCP-based Model Context Protocol server for real estate search integration with LLMs.
Enhanced with comprehensive property type functionality and location services.

Available Tools:

CORE SEARCH FUNCTIONALITY:
- search_real_estate: Search for real estate listings with filters
- build_search_url: Build search URLs with parameters
- get_search_parameters_reference: Get reference of all search parameters
- analyze_search_results: Analyze last search results
- save_search_results: Save search results to JSON

PROPERTY TYPES:
- get_all_property_types: Get all property type codes with names
- search_property_types: Search property types by name
- get_property_type_details: Get detailed info about specific property type
- convert_property_type: Convert between formats (yad2/hebrew/english)
- get_property_type_recommendations: Get recommendations based on criteria
- compare_property_types: Compare two property types
- get_property_type_trends: Get market trends for property types
- validate_property_type_code: Validate property type codes
- export_property_types: Export data to JSON/CSV/Excel

LOCATION SERVICES:
- search_locations: Search locations using autocomplete API
- get_location_codes: Get all location codes (cities/areas/neighborhoods)
- get_city_info: Get city information by ID

ANALYSIS & STATISTICS:
- get_property_type_statistics: Get comprehensive statistics
- get_market_analysis: Get market analysis for property types
- get_comparison_table: Generate comparison table

ADVANCED SEARCH:
- search_with_property_type: Search using property type name
- get_search_recommendations: Get intelligent search recommendations

BULK OPERATIONS:
- bulk_property_type_operations: Perform bulk operations
- get_api_status: Check API status and availability
- test_property_type_functionality: Run comprehensive tests

HELP & DOCUMENTATION:
- get_property_types_help: Get help and documentation
- get_property_types_faq: Get frequently asked questions
- get_troubleshooting_guide: Get troubleshooting guide
- print_property_types_summary: Print formatted summary

Usage Examples:
1. Get all property types: get_all_property_types()
2. Search for apartments: search_property_types(search_term="דירה")
3. Get property details: get_property_type_details(property_code=1)
4. Convert to English: convert_property_type(value="1", from_format="yad2", to_format="english")
5. Search with criteria: get_property_type_recommendations(budget=3000000, family_size=4)
6. Search locations: search_locations(search_text="רמת גן")
"""

from fastmcp import FastMCP, Context
from typing import Optional, Dict, Any, List
import os
import sys
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from yad2.core import Yad2SearchParameters, Yad2ParameterReference
from yad2.core.utils import DataUtils
from yad2.scrapers import Yad2Scraper

# Create an MCP server
mcp = FastMCP("Yad2RealEstate", dependencies=["requests", "beautifulsoup4", "lxml", "pandas", "openpyxl"]) 

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
    parking: Optional[int | str] = None,
    elevator: Optional[int | str] = None,
    balcony: Optional[int | str] = None,
    renovated: Optional[int | str] = None,
    max_pages: int | str = 3,
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
    maxPrice: Optional[int | str] = None,
    minPrice: Optional[int | str] = None,
    topArea: Optional[int | str] = None,
    area: Optional[int | str] = None,
    city: Optional[int | str] = None,
    neighborhood: Optional[int | str] = None,
    property: Optional[str] = None,
    rooms: Optional[str] = None,
    parking: Optional[int | str] = None,
    elevator: Optional[int | str] = None,
    balcony: Optional[int | str] = None,
    renovated: Optional[int | str] = None,
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


# =============================================================================
# PROPERTY TYPES FUNCTIONALITY
# =============================================================================

@mcp.tool()
async def get_all_property_types(ctx: Context):
    """Get all available property type codes with Hebrew and English names."""
    scraper = Yad2Scraper()
    try:
        property_types = scraper.get_all_property_type_codes()
        
        # Add English translations for each
        enhanced_types = {}
        for code, hebrew_name in property_types.items():
            english_name = scraper.convert_property_type(code, "yad2", "english")
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
async def search_property_types(ctx: Context, search_term: str):
    """Search for property types by name (Hebrew or English)."""
    scraper = Yad2Scraper()
    try:
        # Search by term
        matching_types = scraper.search_property_types(search_term)
        
        # Also try to find by alias
        alias_matches = scraper.find_property_type_by_alias(search_term)
        
        # Get suggestions
        suggestions = scraper.get_property_type_suggestions(search_term)
        
        return {
            "success": True,
            "search_term": search_term,
            "exact_matches": matching_types,
            "alias_matches": alias_matches,
            "suggestions": suggestions[:5],  # Top 5 suggestions
            "total_found": len(matching_types)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_property_type_details(ctx: Context, property_code: int):
    """Get detailed information about a specific property type."""
    scraper = Yad2Scraper()
    try:
        details = scraper.get_property_type_details(property_code)
        if not details:
            return {"success": False, "message": f"Property type code {property_code} not found"}
        
        # Add market analysis
        market_analysis = scraper.get_property_type_market_analysis(property_code)
        
        return {
            "success": True,
            "property_type": details,
            "market_analysis": market_analysis
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def convert_property_type(ctx: Context, value: str, from_format: str = "yad2", to_format: str = "english"):
    """Convert property type between different formats (yad2, hebrew, english)."""
    scraper = Yad2Scraper()
    try:
        # Try to convert to int if it's a numeric string
        if from_format == "yad2" and isinstance(value, str) and value.isdigit():
            value = int(value)
        
        converted = scraper.convert_property_type(value, from_format, to_format)
        
        if converted is None:
            return {
                "success": False,
                "message": f"Could not convert '{value}' from {from_format} to {to_format}"
            }
        
        return {
            "success": True,
            "original_value": value,
            "from_format": from_format,
            "to_format": to_format,
            "converted_value": converted
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_property_type_recommendations(
    ctx: Context,
    budget: Optional[int] = None,
    family_size: Optional[int] = None,
    location: Optional[str] = None,
    investment: bool = False
):
    """Get property type recommendations based on criteria."""
    scraper = Yad2Scraper()
    try:
        criteria = {}
        if budget is not None:
            criteria['budget'] = budget
        if family_size is not None:
            criteria['family_size'] = family_size
        if location is not None:
            criteria['location'] = location
        if investment:
            criteria['investment'] = investment
        
        recommendations = scraper.get_property_type_recommendations(criteria)
        
        return {
            "success": True,
            "criteria": criteria,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def compare_property_types(ctx: Context, type1: str, type2: str):
    """Compare two property types and show their differences."""
    scraper = Yad2Scraper()
    try:
        # Convert to int if they're numeric strings
        if type1.isdigit():
            type1 = int(type1)
        if type2.isdigit():
            type2 = int(type2)
        
        comparison = scraper.compare_property_types(type1, type2)
        
        return {
            "success": True,
            "comparison": comparison
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_property_type_trends(ctx: Context):
    """Get current market trends for different property types."""
    scraper = Yad2Scraper()
    try:
        trends = scraper.get_property_type_trends()
        return {
            "success": True,
            "trends": trends
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def validate_property_type_code(ctx: Context, code: str):
    """Validate if a property type code exists and is valid."""
    scraper = Yad2Scraper()
    try:
        validation = scraper.validate_property_type_code(code)
        return {
            "success": True,
            "validation": validation
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def export_property_types(ctx: Context, format: str = "json", filename: Optional[str] = None):
    """Export property types data to different formats (json, csv, excel)."""
    scraper = Yad2Scraper()
    try:
        if format.lower() == "json":
            saved_file = scraper.export_codes_to_json(filename)
        elif format.lower() == "csv":
            saved_file = scraper.export_property_types_to_csv(filename)
        elif format.lower() == "excel":
            saved_file = scraper.export_property_types_to_excel(filename)
        else:
            return {"success": False, "message": f"Unsupported format: {format}. Use json, csv, or excel."}
        
        return {
            "success": True,
            "format": format,
            "filename": saved_file
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# LOCATION SERVICES
# =============================================================================

@mcp.tool()
async def search_locations(ctx: Context, search_text: str):
    """Search for locations using Yad2's address autocomplete API."""
    scraper = Yad2Scraper()
    try:
        location_data = scraper.search_locations(search_text)
        
        return {
            "success": True,
            "search_text": search_text,
            "locations": location_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_location_codes(ctx: Context):
    """Get all available location codes (cities, areas, neighborhoods)."""
    scraper = Yad2Scraper()
    try:
        location_codes = scraper.get_all_location_codes()
        
        return {
            "success": True,
            "location_codes": location_codes
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_city_info(ctx: Context, city_id: str):
    """Get information about a specific city by ID."""
    scraper = Yad2Scraper()
    try:
        city_info = scraper.get_city_by_id(city_id)
        
        if not city_info:
            return {"success": False, "message": f"City ID {city_id} not found"}
        
        return {
            "success": True,
            "city_info": city_info
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# COMPREHENSIVE ANALYSIS AND STATISTICS
# =============================================================================

@mcp.tool()
async def get_property_type_statistics(ctx: Context):
    """Get comprehensive statistics about property types."""
    scraper = Yad2Scraper()
    try:
        stats = scraper.get_property_type_statistics()
        popularity = scraper.get_property_type_popularity()
        
        return {
            "success": True,
            "statistics": stats,
            "popularity": popularity
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_market_analysis(ctx: Context, property_type_code: Optional[int] = None):
    """Get comprehensive market analysis for property types."""
    scraper = Yad2Scraper()
    try:
        analysis = scraper.get_property_type_market_analysis(property_type_code)
        
        return {
            "success": True,
            "market_analysis": analysis
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_comparison_table(ctx: Context):
    """Generate a comprehensive comparison table for all property types."""
    scraper = Yad2Scraper()
    try:
        comparison_table = scraper.get_property_type_comparison_table()
        
        return {
            "success": True,
            "comparison_table": comparison_table
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# HELP AND DOCUMENTATION
# =============================================================================

@mcp.tool()
async def get_property_types_help(ctx: Context):
    """Get comprehensive help and documentation for property types functionality."""
    scraper = Yad2Scraper()
    try:
        help_info = scraper.get_property_type_help()
        examples = scraper.get_property_type_examples()
        cheat_sheet = scraper.get_property_type_cheat_sheet()
        
        return {
            "success": True,
            "help": help_info,
            "examples": examples,
            "cheat_sheet": cheat_sheet
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_property_types_faq(ctx: Context):
    """Get frequently asked questions about property types."""
    scraper = Yad2Scraper()
    try:
        faq = scraper.get_property_type_faq()
        
        return {
            "success": True,
            "faq": faq
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_troubleshooting_guide(ctx: Context):
    """Get troubleshooting guide for common property type issues."""
    scraper = Yad2Scraper()
    try:
        troubleshooting = scraper.get_property_type_troubleshooting()
        
        return {
            "success": True,
            "troubleshooting": troubleshooting
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def print_property_types_summary(ctx: Context):
    """Print a formatted summary of all property types to console and return summary data."""
    scraper = Yad2Scraper()
    try:
        # This will print to console
        scraper.print_codes_summary()
        
        # Also return the summary data
        summary = scraper.get_property_type_summary()
        
        return {
            "success": True,
            "message": "Property types summary printed to console",
            "summary": summary
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# ADVANCED SEARCH INTEGRATION
# =============================================================================

@mcp.tool()
async def search_with_property_type(
    ctx: Context,
    property_type_name: str,
    maxPrice: Optional[int | str] = None,
    minPrice: Optional[int | str] = None,
    location: Optional[str] = None,
    max_pages: int | str = 3
):
    """Search for real estate using property type name instead of code."""
    scraper = Yad2Scraper()
    try:
        # Find property type codes by name
        matching_codes = scraper.get_property_type_codes_by_name(property_type_name)
        
        if not matching_codes:
            return {
                "success": False,
                "message": f"No property types found for '{property_type_name}'"
            }
        
        # Use the first matching code
        property_code = matching_codes[0]
        
        # Now perform the search with the found property type
        result = await search_real_estate(
            ctx=ctx,
            property=str(property_code),
            maxPrice=maxPrice,
            minPrice=minPrice,
            max_pages=max_pages
        )
        
        # Add property type information to result
        if result.get("success"):
            property_details = scraper.get_property_type_details(property_code)
            result["property_type_used"] = {
                "code": property_code,
                "name": property_type_name,
                "details": property_details
            }
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_search_recommendations(
    ctx: Context,
    budget: Optional[int] = None,
    family_size: Optional[int] = None,
    location: Optional[str] = None,
    investment: bool = False
):
    """Get search recommendations including property types and locations."""
    scraper = Yad2Scraper()
    try:
        # Get property type recommendations
        criteria = {}
        if budget is not None:
            criteria['budget'] = budget
        if family_size is not None:
            criteria['family_size'] = family_size
        if location is not None:
            criteria['location'] = location
        if investment:
            criteria['investment'] = investment
        
        property_recommendations = scraper.get_property_type_recommendations(criteria)
        
        # Get location data if location is provided
        location_data = None
        if location:
            location_data = scraper.search_locations(location)
        
        # Generate search parameters for top recommendations
        suggested_searches = []
        for rec in property_recommendations[:3]:  # Top 3 recommendations
            search_params = {
                "property": str(rec['code']),
                "description": f"Search for {rec['name']} - {rec['reasons'][0] if rec['reasons'] else 'Recommended'}"
            }
            
            if budget:
                search_params["maxPrice"] = budget
            
            suggested_searches.append(search_params)
        
        return {
            "success": True,
            "criteria": criteria,
            "property_recommendations": property_recommendations,
            "location_data": location_data,
            "suggested_searches": suggested_searches
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# BULK OPERATIONS AND UTILITIES
# =============================================================================

@mcp.tool()
async def bulk_property_type_operations(ctx: Context, operation: str = "summary"):
    """Perform bulk operations on property types (summary, export_all, validate_all)."""
    scraper = Yad2Scraper()
    try:
        if operation == "summary":
            # Get comprehensive summary
            summary = scraper.get_property_type_summary()
            stats = scraper.get_property_type_statistics()
            
            return {
                "success": True,
                "operation": "summary",
                "summary": summary,
                "statistics": stats
            }
        
        elif operation == "export_all":
            # Export to all formats
            json_file = scraper.export_codes_to_json()
            csv_file = scraper.export_property_types_to_csv()
            
            try:
                excel_file = scraper.export_property_types_to_excel()
            except Exception:
                excel_file = "Excel export failed - pandas/openpyxl not available"
            
            return {
                "success": True,
                "operation": "export_all",
                "files": {
                    "json": json_file,
                    "csv": csv_file,
                    "excel": excel_file
                }
            }
        
        elif operation == "validate_all":
            # Validate all property type codes
            all_types = scraper.get_all_property_type_codes()
            validation_results = {}
            
            for code in all_types.keys():
                validation_results[code] = scraper.validate_property_type_code(str(code))
            
            return {
                "success": True,
                "operation": "validate_all",
                "validation_results": validation_results
            }
        
        else:
            return {
                "success": False,
                "message": f"Unknown operation: {operation}. Use: summary, export_all, validate_all"
            }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_api_status(ctx: Context):
    """Get status of Yad2 API endpoints and functionality."""
    scraper = Yad2Scraper()
    try:
        # Test basic functionality
        property_types_available = bool(scraper.get_all_property_type_codes())
        
        # Test location API
        try:
            location_test = scraper.fetch_location_data("תל")
            location_api_available = bool(location_test)
        except Exception:
            location_api_available = False
        
        # Get API endpoints info
        api_endpoints = scraper.get_property_type_api_endpoints()
        
        return {
            "success": True,
            "status": {
                "property_types_available": property_types_available,
                "location_api_available": location_api_available,
                "total_property_types": len(scraper.get_all_property_type_codes()),
                "api_endpoints": api_endpoints
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# TESTING AND DEVELOPMENT TOOLS
# =============================================================================

@mcp.tool()
async def test_property_type_functionality(ctx: Context):
    """Run comprehensive tests on property type functionality."""
    scraper = Yad2Scraper()
    try:
        test_results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "details": []
        }
        
        # Test 1: Get all property types
        test_results["tests_run"] += 1
        try:
            all_types = scraper.get_all_property_type_codes()
            assert len(all_types) > 0
            test_results["tests_passed"] += 1
            test_results["details"].append({"test": "get_all_property_types", "status": "PASS", "details": f"Found {len(all_types)} types"})
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["details"].append({"test": "get_all_property_types", "status": "FAIL", "error": str(e)})
        
        # Test 2: Search property types
        test_results["tests_run"] += 1
        try:
            apartments = scraper.search_property_types("דירה")
            assert len(apartments) > 0
            test_results["tests_passed"] += 1
            test_results["details"].append({"test": "search_property_types", "status": "PASS", "details": f"Found {len(apartments)} apartment types"})
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["details"].append({"test": "search_property_types", "status": "FAIL", "error": str(e)})
        
        # Test 3: Get property type details
        test_results["tests_run"] += 1
        try:
            details = scraper.get_property_type_details(1)
            assert details is not None
            assert details['code'] == 1
            test_results["tests_passed"] += 1
            test_results["details"].append({"test": "get_property_type_details", "status": "PASS", "details": f"Got details for code 1: {details['name']}"})
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["details"].append({"test": "get_property_type_details", "status": "FAIL", "error": str(e)})
        
        # Test 4: Convert property type
        test_results["tests_run"] += 1
        try:
            english_name = scraper.convert_property_type(1, "yad2", "english")
            assert english_name is not None
            test_results["tests_passed"] += 1
            test_results["details"].append({"test": "convert_property_type", "status": "PASS", "details": f"Code 1 = {english_name}"})
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["details"].append({"test": "convert_property_type", "status": "FAIL", "error": str(e)})
        
        # Test 5: Location search
        test_results["tests_run"] += 1
        try:
            locations = scraper.search_locations("רמת")
            assert locations is not None
            test_results["tests_passed"] += 1
            test_results["details"].append({"test": "search_locations", "status": "PASS", "details": f"Found location data for 'רמת'"})
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["details"].append({"test": "search_locations", "status": "FAIL", "error": str(e)})
        
        test_results["success_rate"] = (test_results["tests_passed"] / test_results["tests_run"]) * 100
        
        return {
            "success": True,
            "test_results": test_results
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# LEGACY FUNCTIONS (MAINTAINED FOR BACKWARD COMPATIBILITY)
# =============================================================================

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
