#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mavat FastMCP Server

FastMCP-based Model Context Protocol server for Mavat planning information system integration.
Provides tools for searching and retrieving planning information from mavat.iplan.gov.il using the REST API.

Available Tools:
- search_plans: Search for plans matching a free-text query
- get_plan_details: Retrieve detailed information for a specific plan
- get_plan_documents: Get documents associated with a plan
- search_by_location: Search plans by city/district/street
- search_by_block_parcel: Search plans by block and parcel numbers
- get_lookup_tables: Get all available lookup tables
- get_districts: Get available districts
- get_cities: Get available cities
- get_streets: Get available streets
- search_lookup: Search lookup tables by text

Usage Examples:
1. Search plans: search_plans(query="רמת החייל", limit=10)
2. Get plan details: get_plan_details(plan_id="12345")
3. Search by location: search_by_location(city="תל אביב", street="הירקון")
4. Search by block/parcel: search_by_block_parcel(block_number="666", parcel_number="1")
5. Get cities: get_cities()
6. Search lookup: search_lookup("תל אביב", table_type="5")
"""

import os
import sys
from fastmcp import FastMCP, Context
from typing import Any, Dict, List, Optional

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mavat.scrapers.mavat_api_client import MavatAPIClient, MavatSearchHit, MavatPlan, MavatAttachment, MavatLookupItem

# Create an MCP server
mcp = FastMCP("MavatPlanning", dependencies=["requests"])

# Module-level state (persists across tool calls within the same server process)
_current_client = None


@mcp.tool()
async def search_plans(
    ctx: Context,
    query: Optional[str] = None,
    city: Optional[str] = None,
    district: Optional[str] = None,
    plan_area: Optional[str] = None,
    street: Optional[str] = None,
    block_number: Optional[str] = None,
    parcel_number: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    page: int = 1
) -> Dict[str, Any]:
    """Search for plans using various criteria.
    
    Parameters:
    -----------
    query: str, optional
        Free text to search for in plan names.
    city: str, optional
        City name for location-based search.
    district: str, optional
        District name for location-based search.
    plan_area: str, optional
        Plan area name for location-based search.
    street: str, optional
        Street name for location-based search.
    block_number: str, optional
        Block number for cadastral search.
    parcel_number: str, optional
        Parcel number for cadastral search.
    status: str, optional
        Plan status filter.
    limit: int, optional
        Maximum number of results to return (default: 20).
    page: int, optional
        Page number for pagination (default: 1).
        
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing search results and metadata.
    """
    global _current_client
    
    try:
        await ctx.info(f"Searching for plans with criteria: query='{query}', city='{city}', limit={limit}")
        
        # Create API client instance
        _current_client = MavatAPIClient()
        
        # Perform search
        await ctx.info("Executing API search...")
        hits: List[MavatSearchHit] = _current_client.search_plans(
            query=query,
            city=city,
            district=district,
            plan_area=plan_area,
            street=street,
            block_number=block_number,
            parcel_number=parcel_number,
            status=status,
            limit=limit,
            page=page
        )
        
        # Format results
        formatted_hits = []
        for hit in hits:
            formatted_hits.append({
                "plan_id": hit.plan_id,
                "title": hit.title,
                "status": hit.status,
                "authority": hit.authority,
                "jurisdiction": hit.jurisdiction,
                "entity_number": hit.entity_number,
                "entity_name": hit.entity_name,
                "approval_date": hit.approval_date,
                "status_date": hit.status_date,
                "raw": hit.raw
            })
        
        await ctx.info(f"Successfully found {len(hits)} plans")
        
        return {
            "success": True,
            "search_criteria": {
                "query": query,
                "city": city,
                "district": district,
                "plan_area": plan_area,
                "street": street,
                "block_number": block_number,
                "parcel_number": parcel_number,
                "status": status
            },
            "pagination": {
                "page": page,
                "limit": limit,
                "total_results": len(hits)
            },
            "plans": formatted_hits,
            "source": "mavat.iplan.gov.il REST API"
        }
        
    except Exception as e:
        await ctx.error(f"Search failed: {str(e)}")
        return {
            "success": False,
            "error": "Search failed",
            "message": str(e)
        }


@mcp.tool()
async def get_plan_details(
    ctx: Context,
    plan_id: str
) -> Dict[str, Any]:
    """Retrieve detailed information for a specific plan.
    
    Parameters:
    -----------
    plan_id: str
        The unique identifier of the plan to fetch.
        
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing plan details and metadata.
    """
    global _current_client
    
    try:
        await ctx.info(f"Fetching details for plan: {plan_id}")
        
        # Create API client instance if not exists
        if _current_client is None:
            _current_client = MavatAPIClient()
        
        # Fetch plan details
        await ctx.info("Retrieving plan details from API...")
        plan: MavatPlan = _current_client.get_plan_details(plan_id)
        
        # Format plan details
        plan_data = {
            "plan_id": plan.plan_id,
            "plan_name": plan.plan_name,
            "status": plan.status,
            "authority": plan.authority,
            "jurisdiction": plan.jurisdiction,
            "last_update": plan.last_update,
            "entity_number": plan.entity_number,
            "approval_date": plan.approval_date,
            "status_date": plan.status_date,
            "raw": plan.raw
        }
        
        await ctx.info(f"Successfully retrieved details for plan: {plan_id}")
        
        return {
            "success": True,
            "plan": plan_data,
            "source": "mavat.iplan.gov.il REST API"
        }
        
    except Exception as e:
        await ctx.error(f"Failed to get plan details: {str(e)}")
        return {
            "success": False,
            "error": "Failed to get plan details",
            "message": str(e)
        }


@mcp.tool()
async def get_plan_documents(
    ctx: Context,
    plan_id: str,
    entity_name: Optional[str] = None
) -> Dict[str, Any]:
    """Get documents associated with a specific plan.
    
    Parameters:
    -----------
    plan_id: str
        The unique identifier of the plan.
    entity_name: str, optional
        The entity name for constructing attachment URLs.
        
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing plan documents and metadata.
    """
    try:
        await ctx.info(f"Fetching documents for plan: {plan_id}")
        
        # Get plan details first to access entity name if not provided
        if not entity_name:
            plan_result = await get_plan_details(ctx, plan_id)
            if not plan_result.get("success"):
                return plan_result
            entity_name = plan_result["plan"].get("entity_name", "Unknown")
        
        # Create API client
        client = MavatAPIClient()
        attachments = client.get_plan_attachments(plan_id, entity_name)
        
        await ctx.info(f"Found {len(attachments)} documents for plan: {plan_id}")
        
        # Format attachments
        formatted_attachments = []
        for attachment in attachments:
            formatted_attachments.append({
                "filename": attachment.filename,
                "file_type": attachment.file_type,
                "size": attachment.size,
                "url": attachment.url,
                "raw": attachment.raw
            })
        
        return {
            "success": True,
            "plan_id": plan_id,
            "entity_name": entity_name,
            "documents_count": len(attachments),
            "documents": formatted_attachments,
            "source": "mavat.iplan.gov.il REST API"
        }
        
    except Exception as e:
        await ctx.error(f"Error while fetching plan documents: {str(e)}")
        return {
            "success": False,
            "error": "Error fetching documents",
            "message": str(e)
        }


@mcp.tool()
async def search_by_location(
    ctx: Context,
    city: str,
    district: Optional[str] = None,
    plan_area: Optional[str] = None,
    street: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """Search for plans by location criteria.
    
    Parameters:
    -----------
    city: str
        City name (required).
    district: str, optional
        District name.
    plan_area: str, optional
        Plan area name.
    street: str, optional
        Street name.
    limit: int, optional
        Maximum number of results (default: 20).
        
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing location-based search results.
    """
    try:
        await ctx.info(f"Searching for plans in location: city='{city}', district='{district}', street='{street}'")
        
        # Use the main search function with location parameters
        result = await search_plans(
            ctx,
            city=city,
            district=district,
            plan_area=plan_area,
            street=street,
            limit=limit
        )
        
        if result.get("success"):
            result["search_type"] = "location"
            result["location_criteria"] = {
                "city": city,
                "district": district,
                "plan_area": plan_area,
                "street": street
            }
        
        return result
        
    except Exception as e:
        await ctx.error(f"Location search failed: {str(e)}")
        return {
            "success": False,
            "error": "Location search failed",
            "message": str(e)
        }


@mcp.tool()
async def search_by_block_parcel(
    ctx: Context,
    block_number: str,
    parcel_number: str,
    limit: int = 20
) -> Dict[str, Any]:
    """Search for plans by block and parcel numbers.
    
    Parameters:
    -----------
    block_number: str
        Block number for cadastral search.
    parcel_number: str
        Parcel number for cadastral search.
        limit: int, optional
        Maximum number of results (default: 20).
        
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing cadastral search results.
    """
    try:
        await ctx.info(f"Searching for plans by block/parcel: block={block_number}, parcel={parcel_number}")
        
        # Use the main search function with cadastral parameters
        result = await search_plans(
            ctx,
            block_number=block_number,
            parcel_number=parcel_number,
            limit=limit
        )
        
        if result.get("success"):
            result["search_type"] = "cadastral"
            result["cadastral_criteria"] = {
                "block_number": block_number,
                "parcel_number": parcel_number
            }
        
        return result
        
    except Exception as e:
        await ctx.error(f"Block/parcel search failed: {str(e)}")
        return {
            "success": False,
            "error": "Block/parcel search failed",
            "message": str(e)
        }


@mcp.tool()
async def get_lookup_tables(
    ctx: Context,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Get all available lookup tables for districts, cities, streets, etc.
    
    Parameters:
    -----------
    force_refresh: bool, optional
        Whether to force refresh the cache (default: False).
        
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing all lookup tables.
    """
    try:
        await ctx.info("Fetching lookup tables from Mavat API...")
        
        client = MavatAPIClient()
        lookup_tables = client.get_lookup_tables(force_refresh)
        
        # Format the response
        formatted_tables = {}
        for table_type, items in lookup_tables.items():
            formatted_tables[table_type] = {
                "count": len(items),
                "items": [
                    {
                        "code": item.code,
                        "description": item.description,
                        "raw": item.raw
                    }
                    for item in items
                ]
            }
        
        await ctx.info(f"Successfully retrieved {len(lookup_tables)} lookup tables")
        
        return {
            "success": True,
            "lookup_tables": formatted_tables,
            "total_tables": len(lookup_tables),
            "source": "mavat.iplan.gov.il REST API"
        }
        
    except Exception as e:
        await ctx.error(f"Failed to get lookup tables: {str(e)}")
        return {
            "success": False,
            "error": "Failed to get lookup tables",
            "message": str(e)
        }


@mcp.tool()
async def get_districts(
    ctx: Context,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Get available districts.
    
    Parameters:
    -----------
    force_refresh: bool, optional
        Whether to force refresh the cache (default: False).
        
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing available districts.
    """
    try:
        await ctx.info("Fetching available districts...")
        
        client = MavatAPIClient()
        districts = client.get_districts(force_refresh)
        
        formatted_districts = [
            {
                "code": district.code,
                "description": district.description,
                "raw": district.raw
            }
            for district in districts
        ]
        
        await ctx.info(f"Successfully retrieved {len(districts)} districts")
        
        return {
            "success": True,
            "districts": formatted_districts,
            "count": len(districts),
            "source": "mavat.iplan.gov.il REST API"
        }
        
    except Exception as e:
        await ctx.error(f"Failed to get districts: {str(e)}")
        return {
            "success": False,
            "error": "Failed to get districts",
            "message": str(e)
        }


@mcp.tool()
async def get_cities(
    ctx: Context,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Get available cities.
    
    Parameters:
    -----------
    force_refresh: bool, optional
        Whether to force refresh the cache (default: False).
        
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing available cities.
    """
    try:
        await ctx.info("Fetching available cities...")
        
        client = MavatAPIClient()
        cities = client.get_cities(force_refresh)
        
        formatted_cities = [
            {
                "code": city.code,
                "description": city.description,
                "raw": city.raw
            }
            for city in cities
        ]
        
        await ctx.info(f"Successfully retrieved {len(cities)} cities")
        
        return {
            "success": True,
            "cities": formatted_cities,
            "count": len(cities),
            "source": "mavat.iplan.gov.il REST API"
        }
        
    except Exception as e:
        await ctx.error(f"Failed to get cities: {str(e)}")
        return {
            "success": False,
            "error": "Failed to get cities",
            "message": str(e)
        }


@mcp.tool()
async def get_streets(
    ctx: Context,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Get available streets.
    
    Parameters:
    -----------
    force_refresh: bool, optional
        Whether to force refresh the cache (default: False).
        
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing available streets.
    """
    try:
        await ctx.info("Fetching available streets...")
        
        client = MavatAPIClient()
        streets = client.get_streets(force_refresh)
        
        formatted_streets = [
            {
                "code": street.code,
                "description": street.description,
                "raw": street.raw
            }
            for street in streets
        ]
        
        await ctx.info(f"Successfully retrieved {len(streets)} streets")
        
        return {
            "success": True,
            "streets": formatted_streets,
            "count": len(streets),
            "source": "mavat.iplan.gov.il REST API"
        }
        
    except Exception as e:
        await ctx.error(f"Failed to get streets: {str(e)}")
        return {
            "success": False,
            "error": "Failed to get streets",
            "message": str(e)
        }


@mcp.tool()
async def search_lookup(
    ctx: Context,
    search_text: str,
    table_type: Optional[str] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Search lookup tables by text.
    
    Parameters:
    -----------
    search_text: str
        Text to search for in lookup tables.
    table_type: str, optional
        Specific table type to search (4=districts, 5=cities, 6=plan_areas, 7=streets, etc.).
    force_refresh: bool, optional
        Whether to force refresh the cache (default: False).
        
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing matching lookup items.
        """
        try:
        table_type_desc = table_type if table_type else "all tables"
        await ctx.info(f"Searching lookup tables for '{search_text}' in {table_type_desc}")
        
        client = MavatAPIClient()
        results = client.search_lookup_by_text(search_text, table_type, force_refresh)
        
        formatted_results = [
            {
                "code": item.code,
                "description": item.description,
                "raw": item.raw
            }
            for item in results
        ]
        
        await ctx.info(f"Found {len(results)} matching items")
        
        return {
            "success": True,
            "search_text": search_text,
            "table_type": table_type,
            "results": formatted_results,
            "count": len(results),
            "source": "mavat.iplan.gov.il REST API"
        }
        
    except Exception as e:
        await ctx.error(f"Lookup search failed: {str(e)}")
        return {
            "success": False,
            "error": "Lookup search failed",
            "message": str(e)
        }


@mcp.tool()
async def get_plan_summary(
    ctx: Context,
    plan_id: str
) -> Dict[str, Any]:
    """Get a comprehensive summary of a plan including details and documents.
    
    Parameters:
    -----------
        plan_id: str
        The unique identifier of the plan.
        
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing comprehensive plan information.
        """
        try:
        await ctx.info(f"Generating comprehensive summary for plan: {plan_id}")
        
        # Get plan details and documents
        details_result = await get_plan_details(ctx, plan_id)
        documents_result = await get_plan_documents(ctx, plan_id)
        
        # Check if all operations were successful
        if not all([
            details_result.get("success"),
            documents_result.get("success")
        ]):
            return {
                "success": False,
                "error": "Failed to retrieve complete plan information",
                "details": details_result,
                "documents": documents_result
            }
        
        await ctx.info(f"Successfully generated comprehensive summary for plan: {plan_id}")
        
        return {
            "success": True,
            "plan_id": plan_id,
            "summary": {
                "details": details_result["plan"],
                "documents": documents_result["documents"]
            },
            "source": "mavat.iplan.gov.il REST API"
        }
        
    except Exception as e:
        await ctx.error(f"Error while generating plan summary: {str(e)}")
        return {
            "success": False,
            "error": "Error generating summary",
            "message": str(e)
        }


if __name__ == "__main__":
    mcp.run()