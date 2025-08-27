#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAMI (Land Registry Planning API) FastMCP Server

Exposes RamiClient functions for searching plans and downloading planning documents
from the Israeli land.gov.il TabaSearch API.
"""

import os
import sys
from typing import Any, Dict, List, Optional

from fastmcp import Context, FastMCP

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from rami.rami_client import RamiClient

# Create an MCP server
mcp = FastMCP(
    "RamiPlanning",
    dependencies=[
        "requests",
        "pandas",
    ],
)

# Persistent client for this server process
_client: Optional[RamiClient] = None

def _get_client() -> RamiClient:
    global _client
    if _client is None:
        _client = RamiClient()
    return _client


@mcp.tool()
async def search_plans(
    ctx: Context,
    plan_number: str = "",
    city: Optional[int] = None,
    gush: str = "",
    chelka: str = "",
    statuses: Optional[List[int]] = None,
    plan_types: Optional[List[int]] = None,
    from_status_date: Optional[str] = None,
    to_status_date: Optional[str] = None,
    plan_types_used: bool = False
):
    """Search for planning documents using RAMI TabaSearch API.
    
    Args:
        plan_number: Plan number to search for
        city: City code (e.g., 5000 for Tel Aviv area)
        gush: Gush (block) number
        chelka: Chelka (plot) number  
        statuses: List of status codes to filter by
        plan_types: List of plan type codes to filter by
        from_status_date: Start date for status filter (YYYY-MM-DD)
        to_status_date: End date for status filter (YYYY-MM-DD)
        plan_types_used: Whether plan types filter is being used
        
    Returns:
        Dict with plan count and list of plans found
    """
    client = _get_client()
    
    search_params = {
        "planNumber": plan_number,
        "city": city,
        "gush": gush,
        "chelka": chelka,
        "statuses": statuses,
        "planTypes": plan_types,
        "fromStatusDate": from_status_date,
        "toStatusDate": to_status_date,
        "planTypesUsed": plan_types_used
    }
    
    # Remove None values
    search_params = {k: v for k, v in search_params.items() if v is not None}
    
    await ctx.info(f"Searching RAMI plans with parameters: {search_params}")
    
    try:
        df = client.fetch_plans(search_params)
        plans = df.to_dict('records')
        
        await ctx.info(f"Found {len(plans)} plans")
        
        return {
            "total_records": len(plans),
            "plans": plans,
            "search_params": search_params
        }
        
    except Exception as e:
        await ctx.warning(f"Error searching plans: {str(e)}")
        return {
            "total_records": 0,
            "plans": [],
            "error": str(e),
            "search_params": search_params
        }


@mcp.tool()
async def search_tel_aviv_plans(
    ctx: Context,
    plan_number: str = "",
    gush: str = "",
    chelka: str = "",
    statuses: Optional[List[int]] = None
):
    """Search for planning documents in Tel Aviv area (convenience function).
    
    Args:
        plan_number: Plan number to search for
        gush: Gush (block) number
        chelka: Chelka (plot) number
        statuses: List of status codes to filter by
        
    Returns:
        Dict with plan count and list of plans found
    """
    # Pre-configured for Tel Aviv with common plan types
    common_plan_types = [72, 21, 1, 8, 9, 10, 12, 20, 62, 31, 41, 25, 22, 2, 11, 13, 
                        61, 32, 74, 78, 77, 73, 76, 75, 80, 79, 40, 60, 71, 70, 67, 
                        68, 69, 30, 50, 3]
    
    return await search_plans(
        ctx=ctx,
        plan_number=plan_number,
        city=5000,  # Tel Aviv area code
        gush=gush,
        chelka=chelka,
        statuses=statuses,
        plan_types=common_plan_types,
        plan_types_used=True
    )


@mcp.tool()
async def download_plan_documents(
    ctx: Context,
    plan_id: int,
    plan_number: str,
    base_dir: str = "rami_plans",
    doc_types: Optional[List[str]] = None,
    overwrite: bool = False
):
    """Download documents for a specific plan.
    
    Args:
        plan_id: The plan ID number
        plan_number: The plan number/name
        base_dir: Directory to save documents (default: "rami_plans")
        doc_types: Document types to download: 'takanon', 'tasrit', 'nispach', 'mmg' 
                  (default: all types)
        overwrite: Whether to overwrite existing files
        
    Returns:
        Dict with download results
    """
    client = _get_client()
    
    # Create a plan dict from the provided info
    plan = {
        "planId": plan_id,
        "planNumber": plan_number
    }
    
    # First we need to fetch the plan to get the full documentsSet
    await ctx.info(f"Fetching plan details for {plan_number} (ID: {plan_id})")
    
    try:
        # Search for this specific plan to get documentsSet
        search_params = {"planNumber": plan_number}
        df = client.fetch_plans(search_params)
        
        if df.empty:
            await ctx.warning(f"Plan {plan_number} not found")
            return {
                "success": False,
                "error": f"Plan {plan_number} not found",
                "files_downloaded": [],
                "files_failed": []
            }
        
        # Find the specific plan by ID
        matching_plans = df[df['planId'] == plan_id]
        if matching_plans.empty:
            await ctx.warning(f"Plan ID {plan_id} not found for plan number {plan_number}")
            return {
                "success": False,
                "error": f"Plan ID {plan_id} not found",
                "files_downloaded": [],
                "files_failed": []
            }
        
        plan_dict = matching_plans.iloc[0].to_dict()
        
        await ctx.info(f"Downloading documents for plan {plan_number} to {base_dir}")
        
        results = client.download_plan_documents(
            plan_dict, 
            base_dir=base_dir, 
            doc_types=doc_types, 
            overwrite=overwrite
        )
        
        success_count = len(results.get('success', []))
        failed_count = len(results.get('failed', []))
        
        await ctx.info(f"Download completed: {success_count} success, {failed_count} failed")
        
        return {
            "success": True,
            "plan_id": plan_id,
            "plan_number": plan_number,
            "files_downloaded": results.get('success', []),
            "files_failed": results.get('failed', []),
            "download_summary": {
                "success_count": success_count,
                "failed_count": failed_count
            }
        }
        
    except Exception as e:
        await ctx.warning(f"Error downloading plan documents: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "plan_id": plan_id,
            "plan_number": plan_number,
            "files_downloaded": [],
            "files_failed": []
        }


@mcp.tool()
async def download_multiple_plans_documents(
    ctx: Context,
    plans: List[Dict[str, Any]],
    base_dir: str = "rami_plans",
    doc_types: Optional[List[str]] = None,
    overwrite: bool = False,
    max_plans: int = 10
):
    """Download documents for multiple plans.
    
    Args:
        plans: List of plan dictionaries (must contain planId and planNumber)
        base_dir: Directory to save documents (default: "rami_plans")
        doc_types: Document types to download: 'takanon', 'tasrit', 'nispach', 'mmg'
                  (default: all types)
        overwrite: Whether to overwrite existing files
        max_plans: Maximum number of plans to process (safety limit)
        
    Returns:
        Dict with overall download results
    """
    client = _get_client()
    
    if len(plans) > max_plans:
        await ctx.warning(f"Too many plans requested ({len(plans)}), limiting to {max_plans}")
        plans = plans[:max_plans]
    
    await ctx.info(f"Downloading documents for {len(plans)} plans to {base_dir}")
    
    try:
        results = client.download_multiple_plans_documents(
            plans,
            base_dir=base_dir,
            doc_types=doc_types,
            overwrite=overwrite
        )
        
        await ctx.info(
            f"Bulk download completed: {results['summary']['total_files_downloaded']} files "
            f"from {results['summary']['plans_processed']} plans"
        )
        
        return results
        
    except Exception as e:
        await ctx.warning(f"Error in bulk download: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "summary": {
                "plans_processed": 0,
                "total_files_downloaded": 0,
                "total_files_failed": 0
            },
            "plan_results": []
        }


@mcp.tool()
async def get_document_types_info(ctx: Context):
    """Get information about available document types.
    
    Returns:
        Dict with document type descriptions
    """
    await ctx.info("Returning RAMI document types information")
    
    return {
        "document_types": {
            "takanon": {
                "name": "תקנון", 
                "description": "Regulations - Planning regulations and rules (PDF)",
                "english": "Planning Regulations"
            },
            "tasrit": {
                "name": "תשריט", 
                "description": "Drawings/Blueprints - Planning drawings and maps (PDF)", 
                "english": "Planning Drawings"
            },
            "nispach": {
                "name": "נספח", 
                "description": "Appendices - Additional supporting documents (PDF)",
                "english": "Appendices" 
            },
            "mmg": {
                "name": "ממ\"ג", 
                "description": "MMG files - Digital planning data archive (ZIP)",
                "english": "Digital Planning Archive"
            }
        },
        "usage_notes": [
            "Leave doc_types empty to download all available document types",
            "Specify doc_types=['takanon', 'tasrit'] to download only specific types",
            "Documents are organized in subdirectories by type",
            "Large files (blueprints, archives) may take time to download"
        ]
    }


if __name__ == "__main__":
    mcp.run()
