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

Usage Examples:
1. Search plans: search_plans(query="רמת החייל", limit=10)
2. Get plan details: get_plan_details(plan_id="12345")
"""

import os
import sys
from typing import Any, Dict, List, Optional

from fastmcp import Context, FastMCP

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mavat.mavat_api_client import MavatAPIClient, MavatPlan, MavatSearchHit

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
            plan_result = await get_plan_details.fn(ctx, plan_id)
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

if __name__ == "__main__":
    mcp.run()