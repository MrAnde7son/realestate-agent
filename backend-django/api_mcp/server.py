#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real Estate API FastMCP Server

FastMCP-based Model Context Protocol server for the Real Estate API integration with LLMs.
Provides tools for accessing assets, deal management, calculations, and CRM functionality.

Available Tools:

ASSETS:
- list_assets: List all assets with filtering and pagination
- get_asset: Get detailed information for a specific asset
- create_asset: Create a new asset
- sync_asset: Trigger synchronization for an asset
- get_asset_data: Get asset sub-resource (transactions/permits/plans/appraisal/listings/documents)
- generate_pdf_report: Generate a PDF report for an asset

DEAL MANAGEMENT:
- list_deals: List all deals
- get_deal: Get deal details
- create_deal: Create a new deal
- list_negotiations: List negotiations for a deal
- get_negotiation: Get negotiation details
- list_offers: List offers for a negotiation
- get_offer: Get offer details

CALCULATIONS:
- estimate_build_cost: Estimate building construction costs
- get_cost_options: Get available options for cost estimation
- calculate_deal_expenses: Calculate complete deal expenses including purchase tax, service costs, and construction costs
- analyze_mortgage: Analyze mortgage affordability and payment scenarios

CRM:
- list_contacts: List all contacts
- get_contact: Get contact details
- create_contact: Create a new contact
- search_contacts: Search contacts by name, email, phone, or tags
- list_leads: List all leads
- get_lead: Get lead details
- create_lead: Create a new lead
- update_lead_status: Update lead status
- add_lead_note: Add a note to a lead
- list_tasks: List all tasks
- create_task: Create a new task
- complete_task: Mark a task as completed
- list_meetings: List all meetings
- create_meeting: Create a new meeting
- list_interactions: List all interactions
- create_interaction: Create a new interaction

FILE READING:
- read_file: Read files (PDF, image, text) from filesystem. Read-only, for uploads/data pipeline.
  Supports permits, zchuyot (building privilege pages), tabu documents, etc.
  Default limits: 10 MB, 10 pages. Can expand limits on request.

Usage Examples:
1. List assets: list_assets(city="תל אביב", page=1)
2. Get asset: get_asset(asset_id=123)
3. Get asset transactions: get_asset_data(asset_id=123, kind="transactions")
4. Generate PDF report: generate_pdf_report(asset_id=123, sections=["summary", "plans", "environment"])
5. Analyze mortgage: analyze_mortgage(property_price=4500000, savings_total=900000)
6. List contacts: list_contacts()
7. Create deal: create_deal(asset_id=123, stage="discovery")
8. Calculate deal expenses: calculate_deal_expenses(price=3000000, buyers=[{"sharePct": 100, "isFirstHome": True}], area=100)
9. Read file: read_file(file_path="permits/document.pdf", max_pages=10)
10. Read file with expanded limits: read_file(file_path="zchuyot/page.pdf", expand_limits=True, max_pages=50)
"""

import sys
import json
import logging
import os
from typing import Optional, Dict, Any, List

from fastmcp import Context, FastMCP

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Create an MCP server
mcp = FastMCP("RealEstateAPI", instructions="Real-estate API tools.", dependencies=["requests"])

# Module-level state
_api_base_url: Optional[str] = None
_api_token: Optional[str] = None

logger = logging.getLogger(__name__)


def _assign_to_module(**kwargs):
    """Helper function to assign attributes to the module namespace.
    
    This is cleaner than using globals() directly and makes the intent explicit.
    Works correctly even when module is loaded via importlib.
    """
    # Get the module's namespace - works for both regular imports and importlib
    import inspect
    frame = inspect.currentframe()
    try:
        # Get the caller's globals (the module namespace)
        caller_globals = frame.f_back.f_globals
        caller_globals.update(kwargs)
    finally:
        del frame


def prune_json(obj: Any, max_chars: int = 15_000, list_limit: int = 20, str_limit: int = 300, depth: int = 0) -> Any:
    """
    Prune JSON objects to limit size before sending to model.
    
    Recursively limits:
    - Lists to list_limit items
    - Strings to str_limit characters
    - Total JSON size to max_chars
    - Deep nesting (max depth 3)
    
    Args:
        obj: Object to prune
        max_chars: Maximum total JSON string length (default: 15k)
        list_limit: Maximum items per list (default: 20)
        str_limit: Maximum characters per string (default: 300)
        depth: Current nesting depth (internal use)
        
    Returns:
        Pruned object
    """
    # Limit nesting depth to prevent deep recursion
    if depth > 3:
        return "..."
    
    def _prune(x: Any, d: int = 0) -> Any:
        if isinstance(x, dict):
            # Limit dict size at deeper levels
            max_dict_items = 10 if d >= 2 else 50
            items = list(x.items())[:max_dict_items]
            return {k: _prune(v, d + 1) for k, v in items}
        if isinstance(x, list):
            # Aggressively limit lists
            limited = x[:list_limit]
            return [_prune(v, d + 1) for v in limited]
        if isinstance(x, str):
            # Truncate long strings
            if len(x) <= str_limit:
                return x
            return x[:str_limit] + "…"
        # Truncate very long numbers/other types
        if isinstance(x, (int, float)) and abs(x) > 1e10:
            return str(x)[:20] + "…"
        return x
    
    pruned = _prune(obj, depth)
    s = json.dumps(pruned, ensure_ascii=False)
    
    if len(s) <= max_chars:
        return pruned
    
    # Second pass: shrink lists harder
    pruned = prune_json(
        pruned,
        max_chars=max_chars,
        list_limit=max(3, list_limit // 3),
        str_limit=max(100, str_limit // 2),
        depth=depth
    )
    
    # Third pass if still too large: very aggressive
    s = json.dumps(pruned, ensure_ascii=False)
    if len(s) > max_chars:
        return prune_json(
            pruned,
            max_chars=max_chars,
            list_limit=5,
            str_limit=50,
            depth=depth
        )
    
    return pruned


def process_list_result(
    raw: Dict[str, Any],
    fields: Optional[List[str]] = None,
    limit: int = 5,
    compact: bool = True,
) -> Dict[str, Any]:
    """
    Process list/collection API results with field projection, limiting, and compaction.
    
    Args:
        raw: Raw API response with success/data structure
        fields: Optional list of field names to keep (projection)
        limit: Maximum number of items to return (default: 5)
        compact: If True, drop bulky nested fields automatically
        
    Returns:
        Processed response dict
    """
    # Handle case where raw is a list directly (shouldn't happen but defensive)
    if isinstance(raw, list):
        raw = {"success": True, "data": raw}
    
    if not isinstance(raw, dict) or not raw.get("success"):
        return raw if isinstance(raw, dict) else {"success": True, "data": raw}
    
    data = raw.get("data", {})
    
    # Extract items from various response formats
    # API returns "rows" for assets list, "results" for other endpoints, or direct list
    if isinstance(data, list):
        items = data
    else:
        items = data.get("rows") or data.get("results") or data.get("data") or []
    
    if not isinstance(items, list):
        # Not a list response, return as-is
        return raw
    
    def project(item: Dict[str, Any], keep: List[str]) -> Dict[str, Any]:
        """Project only specified fields from item."""
        # Include all requested fields, even if they're None or missing
        # This ensures consistent output format
        result = {}
        for k in keep:
            # Always include the field if it's in the item (even if None)
            if k in item:
                result[k] = item.get(k)
            # If field doesn't exist at all, include None for essential fields
            # This prevents empty dicts when essential fields are missing
            elif k in ("id", "address", "price"):
                result[k] = None
        return result
    
    def compact_item(item: Dict[str, Any]) -> Dict[str, Any]:
        """Aggressively compact a single item."""
        bulky = {
            "documents",
            "plans",
            "appraisal",
            "listings",
            "history",
            "raw_html",
            "raw_text",
            "transactions",
            "permits",
            "metadata",
            "notes",
            "interactions",
            "description",
            "content",
            "body",
            "html_content",
            "text_content",
            "raw_data",
            "full_data",
            "details",
            "extended_info",
            "additional_info",
            "extra_data",
            "related_items",
            "children",
            "subitems",
            "attachments",
            "files",
            "images",
            "photos",
            "media",
        }
        
        result = {}
        for k, v in item.items():
            if k in bulky:
                continue
            
            # Skip very large nested structures
            if isinstance(v, (dict, list)):
                v_str = json.dumps(v, ensure_ascii=False)
                if len(v_str) > 500:
                    result[k] = f"[{type(v).__name__} with {len(v) if isinstance(v, list) else len(v)} items]"
                    continue
            
            # Truncate very long strings even in non-bulky fields
            if isinstance(v, str) and len(v) > 200:
                result[k] = v[:200] + "…"
                continue
            
            result[k] = v
        
        return result
    
    # Apply field projection if specified
    if fields:
        # Debug: Check if requested fields exist in raw data
        # This helps identify if fields are missing or None
        if items and fields:
            sample_item = items[0]
            missing_fields = [f for f in fields if f not in sample_item]
            if missing_fields:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Fields requested but not in API response: {missing_fields}. Available fields: {list(sample_item.keys())[:20]}")
        
        items = [project(x, fields) for x in items]
    
    # Apply compaction (drop bulky nested fields)
    if compact:
        items = [compact_item(x) for x in items]
    
    # Apply limit
    items = items[:limit]
    
    return {"success": True, "data": items}


def _get_api_base_url() -> str:
    """Get the API base URL from environment or default."""
    global _api_base_url
    if _api_base_url is None:
        _api_base_url = os.getenv("REALESTATE_API_URL", "http://127.0.0.1:8000/api")
    logger.info(f"API base URL: {_api_base_url}")
    return _api_base_url


def _get_api_token() -> Optional[str]:
    """Get the API token from environment."""
    global _api_token
    if _api_token is None:
        _api_token = os.getenv("REALESTATE_API_TOKEN")
    return _api_token


def _get_user_profile(ctx: Context) -> Optional[Dict[str, Any]]:
    """Get the current user's profile from the API."""
    try:
        result = _make_request(ctx, "GET", "/auth/profile")
        if isinstance(result, dict) and result.get("success"):
            return result.get("data", {}).get("user")
    except Exception as e:
        logger.warning(f"Failed to get user profile: {e}")
    return None


def _make_request(
    ctx: Context,
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Make an HTTP request to the API."""
    import requests
    import logging
    
    logger = logging.getLogger(__name__)

    url = f"{_get_api_base_url()}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    token = _get_api_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
        logger.debug(f"MCP request to {url} with token: {token[:20]}...")
    else:
        logger.warning(f"MCP request to {url} without token - REALESTATE_API_TOKEN not set")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, params=params, timeout=30)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, params=params, timeout=30)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data, params=params, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, params=params, timeout=30)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        # Log response status for debugging
        if response.status_code == 401:
            logger.warning(f"401 Unauthorized for {url}. Token present: {bool(token)}, Token preview: {token[:20] if token else 'None'}...")
            # Try to get error details
            try:
                error_data = response.json()
                logger.warning(f"Error details: {error_data}")
            except Exception:
                error_text = response.text[:200]
                logger.warning(f"Error text: {error_text}")
        
        response.raise_for_status()
        
        # Handle empty responses
        if response.status_code == 204 or not response.content:
            return {"success": True, "data": None}
        
        raw_data = response.json()
        # Prune JSON before returning to model
        pruned_data = prune_json(raw_data)
        return {"success": True, "data": pruned_data}
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') and e.response else None
        error_msg = str(e)
        try:
            if hasattr(e, 'response') and e.response:
                error_data = e.response.json()
                error_msg = error_data.get('error', error_msg)
        except Exception:
            pass
        return {
            "success": False,
            "error": error_msg,
            "status_code": status_code,
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
        }


# ============================================================================
# ASSETS TOOLS
# ============================================================================

def register_assets_tools():
    """Register asset-related tools."""
    
    @mcp.tool(description="List assets (filters + pagination).")
    async def list_assets(
        ctx: Context,
        city: Optional[str] = None,
        neighborhood: Optional[str] = None,
        max_price: Optional[int | str] = None,
        min_price: Optional[int | str] = None,
        rooms: Optional[int | str] = None,
        area_min: Optional[float | str] = None,
        area_max: Optional[float | str] = None,
        rent_price_min: Optional[int | str] = None,
        rent_price_max: Optional[int | str] = None,
        ad_type: Optional[str] = None,
        type: Optional[str] = None,
        rental_sale: Optional[str] = None,
        status: Optional[str] = None,
        zoning: Optional[str] = None,
        user_assets: Optional[str] = None,
        page: Optional[int | str] = None,
        page_size: Optional[int | str] = None,
        fields: Optional[List[str]] = None,
        limit: int = 5,
        compact: bool = True,
    ) -> Dict[str, Any]:
        def _to_int(value):
            """Convert value to int, handling both int and string inputs."""
            if value is None:
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        
        def _to_float(value):
            """Convert value to float, handling both float and string inputs."""
            if value is None:
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        
        params = {}
        if city:
            params["city"] = city
        if neighborhood:
            params["neighborhood"] = neighborhood
        if type and type != "all":
            params["type"] = type
        if zoning and zoning != "all":
            params["zoning"] = zoning
        if status and status != "all":
            params["status"] = status
        if rental_sale and rental_sale != "all":
            params["rentalSale"] = rental_sale
        if ad_type and ad_type != "all":
            params["adType"] = ad_type
        if user_assets and user_assets != "all":
            params["userAssets"] = user_assets
        price_max_int = _to_int(max_price)
        if price_max_int is not None:
            params["priceMax"] = price_max_int
        price_min_int = _to_int(min_price)
        if price_min_int is not None:
            params["priceMin"] = price_min_int
        rooms_int = _to_int(rooms)
        if rooms_int is not None:
            params["rooms"] = rooms_int
        area_min_float = _to_float(area_min)
        if area_min_float is not None:
            params["areaMin"] = area_min_float
        area_max_float = _to_float(area_max)
        if area_max_float is not None:
            params["areaMax"] = area_max_float
        rent_price_min_int = _to_int(rent_price_min)
        if rent_price_min_int is not None:
            params["rentPriceMin"] = rent_price_min_int
        rent_price_max_int = _to_int(rent_price_max)
        if rent_price_max_int is not None:
            params["rentPriceMax"] = rent_price_max_int
        page_int = _to_int(page)
        if page_int is not None:
            params["page"] = page_int
        # Clamp page_size to limit and max 50
        page_size_int = _to_int(page_size) if page_size is not None else None
        final_limit = min(page_size_int or limit, 50)
        # Send both limit and page_size for compatibility
        params["limit"] = final_limit
        params["page_size"] = final_limit
        
        raw = _make_request(ctx, "GET", "/assets", params=params)
        return process_list_result(raw, fields=fields, limit=limit, compact=compact)

    @mcp.tool(description="Get available filter options (cities, types, neighborhoods, etc.) from the API.")
    async def get_asset_filters(
        ctx: Context,
    ) -> Dict[str, Any]:
        """Get available filter options including cities, property types, neighborhoods, etc.
        
        This is useful to get the exact city names available in the system.
        For example, if you're looking for Tel Aviv properties, check the 'cities' list
        to see the exact name format (e.g., 'תל אביב יפו', 'תל אביב-יפו', etc.)
        """
        # Make a request with page_size=1 to get filters without fetching many assets
        params = {"page_size": 1}
        raw = _make_request(ctx, "GET", "/assets", params=params)
        
        if raw.get("success") and isinstance(raw.get("data"), dict):
            filters = raw.get("data", {}).get("filters", {})
            return {"success": True, "filters": filters}
        
        return raw

    @mcp.tool(description="Get asset details.")
    async def get_asset(
        ctx: Context,
        asset_id: int,
        include_documents: bool = False,
    ) -> Dict[str, Any]:
        params = {}
        if include_documents:
            params["include_documents"] = "true"
        
        raw = _make_request(ctx, "GET", f"/assets/{asset_id}", params=params)
        
        # If documents are not requested, strip them from response
        if not include_documents and raw.get("success"):
            data = raw.get("data", {})
            if isinstance(data, dict):
                # Aggressively strip bulky fields
                bulky_fields = {
                    "documents", "plans", "appraisal", "listings", "history",
                    "raw_html", "raw_text", "transactions", "permits",
                    "description", "content", "body", "html_content", "text_content",
                    "raw_data", "full_data", "details", "extended_info",
                    "attachments", "files", "images", "photos", "media",
                }
                data = {k: v for k, v in data.items() if k not in bulky_fields}
                
                # Truncate remaining long strings
                for k, v in data.items():
                    if isinstance(v, str) and len(v) > 200:
                        data[k] = v[:200] + "…"
                    elif isinstance(v, (dict, list)):
                        v_str = json.dumps(v, ensure_ascii=False)
                        if len(v_str) > 500:
                            data[k] = f"[{type(v).__name__} with {len(v) if isinstance(v, list) else 'many'} items]"
                
                return {"success": True, "data": data}
        
        return raw

    @mcp.tool(description="Create asset.")
    async def create_asset(
        ctx: Context,
        scope: Optional[Dict[str, Any]] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        street: Optional[str] = None,
        number: Optional[int] = None,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
        radius: Optional[int] = None,
    ) -> Dict[str, Any]:
        data = {}
        if scope:
            data["scope"] = scope
        if address:
            data["address"] = address
        if city:
            data["city"] = city
        if street:
            data["street"] = street
        if number:
            data["number"] = number
        if block:
            data["block"] = block
        if parcel:
            data["parcel"] = parcel
        if radius:
            data["radius"] = radius
        
        return _make_request(ctx, "POST", "/assets", data=data)

    @mcp.tool(description="Sync asset.")
    async def sync_asset(
        ctx: Context,
        asset_id: int,
    ) -> Dict[str, Any]:
        return _make_request(ctx, "POST", f"/assets/{asset_id}/sync")

    @mcp.tool(description="Get asset subresource (transactions/permits/plans/appraisal/listings/documents).")
    async def get_asset_data(
        ctx: Context,
        asset_id: int,
        kind: str,
        fields: Optional[List[str]] = None,
        limit: int = 5,
        compact: bool = True,
    ) -> Dict[str, Any]:
        """
        Get asset subresource data.
        
        Args:
            asset_id: The ID of the asset
            kind: Type of data to retrieve - one of: transactions, permits, plans, appraisal, listings, documents
            fields: Optional list of field names to return
            limit: Maximum number of items to return (default: 10)
            compact: If True, drop bulky nested fields automatically
        
        Returns:
            Dictionary with success status and requested data
        """
        valid_kinds = ["transactions", "permits", "plans", "appraisal", "listings", "documents"]
        if kind not in valid_kinds:
            return {
                "success": False,
                "error": f"Invalid kind '{kind}'. Must be one of: {', '.join(valid_kinds)}"
            }
        
        raw = _make_request(ctx, "GET", f"/assets/{asset_id}/{kind}")
        
        # Special handling for documents: return metadata + chunk ids only
        if kind == "documents":
            if not raw.get("success"):
                return raw
            
            data = raw.get("data", {})
            items = data.get("results") or data.get("data") or []
            if isinstance(data, list):
                items = data
            
            if isinstance(items, list):
                # Return only metadata for documents, not full content
                processed = []
                for doc in items[:limit]:
                    doc_meta = {
                        "id": doc.get("id"),
                        "title": doc.get("title"),
                        "type": doc.get("type"),
                        "created_at": doc.get("created_at"),
                        "updated_at": doc.get("updated_at"),
                        "size": doc.get("size"),
                        "chunk_ids": doc.get("chunk_ids", []),
                    }
                    if fields:
                        doc_meta = {k: v for k, v in doc_meta.items() if k in fields}
                    processed.append(doc_meta)
                
                return {"success": True, "data": processed}
        
        # For other kinds, use standard list processing
        return process_list_result(raw, fields=fields, limit=limit, compact=compact)

    @mcp.tool(description="Generate a PDF report for an asset.")
    async def generate_pdf_report(
        ctx: Context,
        asset_id: int,
        sections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a PDF report for a specific asset.
        
        Args:
            asset_id: The ID of the asset to generate a report for
            sections: Optional list of sections to include in the report.
                     Available sections: summary, permits, plans, planning, environment, comparables, mortgage, appendix.
                     If not provided, all default sections will be included.
        
        Returns:
            Dictionary with success status and report information including:
            - id: Report ID
            - assetId: Asset ID
            - address: Asset address
            - filename: Generated PDF filename
            - createdAt: Report creation timestamp
            - status: Report status
            - pages: Number of pages in the PDF
            - fileSize: PDF file size in bytes
            - sections: List of sections included in the report
            - url: URL to download the PDF report
        """
        data = {"assetId": asset_id}
        if sections:
            data["sections"] = sections
        
        return _make_request(ctx, "POST", "/reports", data=data)
    
    # Assign functions to module namespace for direct access (after registration)
    _assign_to_module(
        list_assets=list_assets,
        get_asset_filters=get_asset_filters,
        get_asset=get_asset,
        create_asset=create_asset,
        sync_asset=sync_asset,
        get_asset_data=get_asset_data,
        generate_pdf_report=generate_pdf_report,
    )


# ============================================================================
# DEAL MANAGEMENT TOOLS
# ============================================================================

def register_deals_tools():
    """Register deal-related tools."""
    
    @mcp.tool(description="List deals.")
    async def list_deals(
        ctx: Context,
        stage: Optional[str] = None,
        deal_lead: Optional[int] = None,
        asset_id: Optional[int] = None,
        updated_after: Optional[str] = None,
        search: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        fields: Optional[List[str]] = None,
        limit: int = 5,
        compact: bool = True,
    ) -> Dict[str, Any]:
        params = {}
        if stage:
            params["stage"] = stage
        if deal_lead:
            params["deal_lead"] = deal_lead
        if asset_id:
            params["asset_id"] = asset_id
        if updated_after:
            params["updated_after"] = updated_after
        if search:
            params["q"] = search
        if page:
            params["page"] = page
        # Clamp page_size to limit and max 20
        params["page_size"] = min(page_size or limit, 20)
        
        raw = _make_request(ctx, "GET", "/deal-workspace/deals", params=params)
        return process_list_result(raw, fields=fields, limit=limit, compact=compact)

    @mcp.tool(description="Get deal.")
    async def get_deal(
        ctx: Context,
        deal_id: int,
    ) -> Dict[str, Any]:
        return _make_request(ctx, "GET", f"/deal-workspace/deals/{deal_id}")

    @mcp.tool(description="Create deal.")
    async def create_deal(
        ctx: Context,
        asset_id: int,
        stage: Optional[str] = None,
        confidentiality_level: Optional[str] = None,
        parties: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        data = {}
        if stage:
            data["stage"] = stage
        if confidentiality_level:
            data["confidentiality_level"] = confidentiality_level
        if parties:
            data["parties"] = parties
        
        return _make_request(ctx, "POST", f"/deal-workspace/deals/{asset_id}", data=data)

    @mcp.tool(description="List negotiations.")
    async def list_negotiations(
        ctx: Context,
        deal_id: Optional[int] = None,
        status: Optional[str] = None,
        fields: Optional[List[str]] = None,
        limit: int = 5,
        compact: bool = True,
    ) -> Dict[str, Any]:
        params = {}
        if deal_id:
            params["deal_id"] = deal_id
        if status:
            params["status"] = status
        
        raw = _make_request(ctx, "GET", "/deal-workspace/negotiations", params=params)
        return process_list_result(raw, fields=fields, limit=limit, compact=compact)

    @mcp.tool(description="Get negotiation.")
    async def get_negotiation(
        ctx: Context,
        negotiation_id: int,
    ) -> Dict[str, Any]:
        return _make_request(ctx, "GET", f"/deal-workspace/negotiations/{negotiation_id}")

    @mcp.tool(description="List offers.")
    async def list_offers(
        ctx: Context,
        negotiation_id: Optional[int] = None,
        status: Optional[str] = None,
        fields: Optional[List[str]] = None,
        limit: int = 5,
        compact: bool = True,
    ) -> Dict[str, Any]:
        params = {}
        if negotiation_id:
            params["negotiation_id"] = negotiation_id
        if status:
            params["status"] = status
        
        raw = _make_request(ctx, "GET", "/deal-workspace/offers", params=params)
        return process_list_result(raw, fields=fields, limit=limit, compact=compact)

    @mcp.tool(description="Get offer.")
    async def get_offer(
        ctx: Context,
        offer_id: int,
    ) -> Dict[str, Any]:
        return _make_request(ctx, "GET", f"/deal-workspace/offers/{offer_id}")
    
    # Assign functions to module namespace for direct access (after registration)
    _assign_to_module(
        list_deals=list_deals,
        create_deal=create_deal,
        get_deal=get_deal,
        list_negotiations=list_negotiations,
        get_negotiation=get_negotiation,
        list_offers=list_offers,
        get_offer=get_offer,
    )


# ============================================================================
# EXPENSE CALCULATION TOOLS
# ============================================================================

def register_cost_tools():
    """Register cost calculation tools."""
    
    @mcp.tool(description="Estimate build cost.")
    async def estimate_build_cost(
        ctx: Context,
        area_m2: float,
        scope: Optional[List[str]] = None,
        region: Optional[str] = None,
        quality: Optional[str] = None,
    ) -> Dict[str, Any]:
        data = {"area_m2": area_m2}
        if scope:
            data["scope"] = scope
        if region:
            data["region"] = region
        if quality:
            data["quality"] = quality
        
        return _make_request(ctx, "POST", "/cost/estimate/build", data=data)

    @mcp.tool(description="Get cost options for construction cost estimation only. Only relevant for land properties (מגרשים) when estimating building costs. Not needed for regular deal expense calculations.")
    async def get_cost_options(
        ctx: Context,
    ) -> Dict[str, Any]:
        return _make_request(ctx, "GET", "/cost/options")

    @mcp.tool(description="Calculate deal expenses including purchase tax, service costs, and construction costs.")
    async def calculate_deal_expenses(
        ctx: Context,
        price: float,
        buyers: Optional[List[Dict[str, Any]]] = None,
        area: Optional[float] = None,
        property_type: Optional[str] = None,
        services: Optional[List[Dict[str, Any]]] = None,
        vat_rate: Optional[float] = None,
        construction_area: Optional[float] = None,
        construction_cost_per_sqm: Optional[float] = None,
        construction_includes_vat: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Calculate complete deal expenses for a property purchase.
        
        Args:
            price: Property price (required)
            buyers: List of buyer dictionaries with sharePct and optional flags (optional).
                If not provided, uses the logged-in user as the default buyer with 100% share:
                - sharePct: Percentage share (0-100)
                - isFirstHome: Boolean (optional)
                - isReplacementHome: Boolean (optional)
                - oleh: Boolean (optional, for new immigrants)
                - disabled: Boolean (optional)
                - bereavedFamily: Boolean (optional)
                - name: String (optional)
            area: Property area in square meters (optional, for price per sqm calculation)
            property_type: "residential" or "land" (default: "residential").
                Building expenses are only calculated for "land" property type.
            services: List of service cost dictionaries with:
                - label: Service label
                - percent: Percentage of price (optional)
                - amount: Fixed amount (optional)
                - includesVat: Boolean indicating if VAT is included
            vat_rate: VAT rate (default: 0.18 for 18%)
            construction_area: Construction area in sqm (for land purchases only)
            construction_cost_per_sqm: Construction cost per sqm (for land purchases only)
            construction_includes_vat: Whether construction cost includes VAT (default: True)
            
        Returns:
            Dictionary with complete expense breakdown including:
            - totalTax: Total purchase tax
            - breakdown: Purchase tax breakdown per buyer
            - serviceTotal: Total service costs
            - serviceBreakdown: Service costs breakdown
            - constructionCost: Construction cost (only for land property type)
            - total: Total cost including all expenses
            - pricePerSqBefore: Price per sqm before expenses
            - pricePerSqAfter: Price per sqm after expenses
        """
        # If no buyers provided, use logged-in user as default buyer with 100% share
        if not buyers:
            user_profile = _get_user_profile(ctx)
            if user_profile:
                # Use user's full name if available, otherwise use email
                first_name = user_profile.get("first_name", "")
                last_name = user_profile.get("last_name", "")
                if first_name or last_name:
                    user_name = f"{first_name} {last_name}".strip()
                else:
                    user_name = user_profile.get("email", "User")
                buyers = [{"name": user_name, "sharePct": 100}]
            else:
                # Fallback if user profile cannot be retrieved
                buyers = [{"name": "User", "sharePct": 100}]
        
        data = {
            "price": price,
            "buyers": buyers,
        }
        if area is not None:
            data["area"] = area
        if property_type:
            data["propertyType"] = property_type
        if services:
            data["services"] = services
        if vat_rate is not None:
            data["vatRate"] = vat_rate
        if construction_area is not None:
            data["constructionArea"] = construction_area
        if construction_cost_per_sqm is not None:
            data["constructionCostPerSqm"] = construction_cost_per_sqm
        if construction_includes_vat is not None:
            data["constructionIncludesVat"] = construction_includes_vat
        
        return _make_request(ctx, "POST", "/deal-expenses/calculate", data=data)
    
    # Assign functions to module namespace for direct access (after registration)
    _assign_to_module(
        estimate_build_cost=estimate_build_cost,
        get_cost_options=get_cost_options,
        calculate_deal_expenses=calculate_deal_expenses,
    )


# ============================================================================
# MORTGAGE CALCULATION TOOLS
# ============================================================================

def register_mortgage_tools():
    """Register mortgage calculation tools."""
    
    @mcp.tool(description="Analyze mortgage.")
    async def analyze_mortgage(
        ctx: Context,
        property_price: float,
        savings_total: float,
        annual_rate_pct: Optional[float | str] = None,
        term_years: Optional[int | str] = None,
        transactions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        # Ensure proper type conversion for parameters that might come as strings
        property_price = float(property_price)
        savings_total = float(savings_total)
        
        data = {
            "property_price": property_price,
            "savings_total": savings_total,
        }
        if annual_rate_pct is not None:
            data["annual_rate_pct"] = float(annual_rate_pct)
        if term_years is not None:
            data["term_years"] = int(term_years)
        if transactions:
            data["transactions"] = transactions
        
        return _make_request(ctx, "POST", "/mortgage-analyze", data=data)
    
    # Assign functions to module namespace for direct access (after registration)
    _assign_to_module(analyze_mortgage=analyze_mortgage)


# ============================================================================
# CRM TOOLS
# ============================================================================

def register_crm_tools():
    """Register CRM-related tools."""
    
    @mcp.tool(description="List contacts.")
    async def list_contacts(
        ctx: Context,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        fields: Optional[List[str]] = None,
        limit: int = 5,
        compact: bool = True,
    ) -> Dict[str, Any]:
        params = {}
        if page:
            params["page"] = page
        # Clamp page_size to limit and max 20
        params["page_size"] = min(page_size or limit, 20)
        
        raw = _make_request(ctx, "GET", "/crm/contacts", params=params)
        result = process_list_result(raw, fields=fields, limit=limit, compact=compact)
        
        # Preserve pagination metadata (count) from paginated responses
        if isinstance(raw, dict) and raw.get("success"):
            data = raw.get("data", {})
            if isinstance(data, dict) and "count" in data:
                result["count"] = data["count"]
        
        return result

    @mcp.tool(description="Get contact.")
    async def get_contact(
        ctx: Context,
        contact_id: int,
    ) -> Dict[str, Any]:
        return _make_request(ctx, "GET", f"/crm/contacts/{contact_id}")

    @mcp.tool(description="Create contact.")
    async def create_contact(
        ctx: Context,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        equity: Optional[float] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        data = {"name": name}
        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        if equity is not None:
            data["equity"] = equity
        if tags:
            data["tags"] = tags
        if notes:
            data["notes"] = notes
        
        return _make_request(ctx, "POST", "/crm/contacts", data=data)

    @mcp.tool(description="Search contacts.")
    async def search_contacts(
        ctx: Context,
        query: str,
        fields: Optional[List[str]] = None,
        limit: int = 5,
        compact: bool = True,
    ) -> Dict[str, Any]:
        raw = _make_request(ctx, "GET", "/crm/contacts/search", params={"q": query})
        return process_list_result(raw, fields=fields, limit=limit, compact=compact)

    @mcp.tool(description="List leads.")
    async def list_leads(
        ctx: Context,
        status: Optional[str] = None,
        contact_id: Optional[int] = None,
        asset_id: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        fields: Optional[List[str]] = None,
        limit: int = 5,
        compact: bool = True,
    ) -> Dict[str, Any]:
        params = {}
        if status:
            params["status"] = status
        if contact_id:
            params["contact"] = contact_id
        if asset_id:
            params["asset_id"] = asset_id
        if page:
            params["page"] = page
        # Clamp page_size to limit and max 20
        params["page_size"] = min(page_size or limit, 20)
        
        raw = _make_request(ctx, "GET", "/crm/leads", params=params)
        return process_list_result(raw, fields=fields, limit=limit, compact=compact)

    @mcp.tool(description="Get lead.")
    async def get_lead(
        ctx: Context,
        lead_id: int,
    ) -> Dict[str, Any]:
        return _make_request(ctx, "GET", f"/crm/leads/{lead_id}")

    @mcp.tool(description="Create lead.")
    async def create_lead(
        ctx: Context,
        contact_id: int,
        asset_id: int,
        status: Optional[str] = None,
        notes: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        data = {
            "contact": contact_id,
            "asset": asset_id,
        }
        if status:
            data["status"] = status
        if notes:
            data["notes"] = notes
        
        return _make_request(ctx, "POST", "/crm/leads", data=data)

    @mcp.tool(description="Update lead status.")
    async def update_lead_status(
        ctx: Context,
        lead_id: int,
        status: str,
    ) -> Dict[str, Any]:
        return _make_request(ctx, "POST", f"/crm/leads/{lead_id}/set_status", data={"status": status})

    @mcp.tool(description="Add lead note.")
    async def add_lead_note(
        ctx: Context,
        lead_id: int,
        text: str,
    ) -> Dict[str, Any]:
        return _make_request(ctx, "POST", f"/crm/leads/{lead_id}/add_note", data={"text": text})

    @mcp.tool(description="List tasks. Status options: 'pending' (open tasks), 'completed', 'cancelled'.")
    async def list_tasks(
        ctx: Context,
        contact_id: Optional[int] = None,
        lead_id: Optional[int] = None,
        status: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        fields: Optional[List[str]] = None,
        limit: int = 5,
        compact: bool = True,
    ) -> Dict[str, Any]:
        params = {}
        if contact_id:
            params["contact"] = contact_id
        if lead_id:
            params["lead"] = lead_id
        if status:
            params["status"] = status
        if page:
            params["page"] = page
        # Clamp page_size to limit and max 20
        params["page_size"] = min(page_size or limit, 20)
        
        raw = _make_request(ctx, "GET", "/crm/tasks", params=params)
        return process_list_result(raw, fields=fields, limit=limit, compact=compact)

    @mcp.tool(description="Create task.")
    async def create_task(
        ctx: Context,
        contact_id: int,
        title: str,
        description: Optional[str] = None,
        due_at: Optional[str] = None,
        lead_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        data = {
            "contact": contact_id,
            "title": title,
        }
        if description:
            data["description"] = description
        if due_at:
            data["due_at"] = due_at
        if lead_id:
            data["lead"] = lead_id
        if status:
            data["status"] = status
        
        return _make_request(ctx, "POST", "/crm/tasks", data=data)

    @mcp.tool(description="Complete task.")
    async def complete_task(
        ctx: Context,
        task_id: int,
    ) -> Dict[str, Any]:
        return _make_request(ctx, "POST", f"/crm/tasks/{task_id}/complete")

    @mcp.tool(description="List meetings.")
    async def list_meetings(
        ctx: Context,
        contact_id: Optional[int] = None,
        status: Optional[str] = None,
        upcoming: Optional[bool] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        fields: Optional[List[str]] = None,
        limit: int = 5,
        compact: bool = True,
    ) -> Dict[str, Any]:
        params = {}
        if contact_id:
            params["contact"] = contact_id
        if status:
            params["status"] = status
        if upcoming:
            params["upcoming"] = "true"
        if page:
            params["page"] = page
        # Clamp page_size to limit and max 20
        params["page_size"] = min(page_size or limit, 20)
        
        raw = _make_request(ctx, "GET", "/crm/meetings", params=params)
        return process_list_result(raw, fields=fields, limit=limit, compact=compact)

    @mcp.tool(description="Create meeting.")
    async def create_meeting(
        ctx: Context,
        contact_id: int,
        scheduled_for: str,
        title: Optional[str] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        data = {
            "contact": contact_id,
            "scheduled_for": scheduled_for,
        }
        if title:
            data["title"] = title
        if location:
            data["location"] = location
        if notes:
            data["notes"] = notes
        if status:
            data["status"] = status
        
        return _make_request(ctx, "POST", "/crm/meetings", data=data)

    @mcp.tool(description="List interactions.")
    async def list_interactions(
        ctx: Context,
        contact_id: Optional[int] = None,
        interaction_type: Optional[str] = None,
        since: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        fields: Optional[List[str]] = None,
        limit: int = 5,
        compact: bool = True,
    ) -> Dict[str, Any]:
        params = {}
        if contact_id:
            params["contact"] = contact_id
        if interaction_type:
            params["type"] = interaction_type
        if since:
            params["since"] = since
        if page:
            params["page"] = page
        # Clamp page_size to limit and max 20
        params["page_size"] = min(page_size or limit, 20)
        
        raw = _make_request(ctx, "GET", "/crm/interactions", params=params)
        return process_list_result(raw, fields=fields, limit=limit, compact=compact)

    @mcp.tool(description="Create interaction.")
    async def create_interaction(
        ctx: Context,
        contact_id: int,
        interaction_type: str,
        occurred_at: str,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        data = {
            "contact": contact_id,
            "interaction_type": interaction_type,
            "occurred_at": occurred_at,
        }
        if notes:
            data["notes"] = notes
        if metadata:
            data["metadata"] = metadata
        
        return _make_request(ctx, "POST", "/crm/interactions", data=data)
    
    # Assign functions to module namespace for direct access (after registration)
    _assign_to_module(
        list_contacts=list_contacts,
        get_contact=get_contact,
        create_contact=create_contact,
        search_contacts=search_contacts,
        list_leads=list_leads,
        get_lead=get_lead,
        create_lead=create_lead,
        update_lead_status=update_lead_status,
        add_lead_note=add_lead_note,
        list_tasks=list_tasks,
        create_task=create_task,
        complete_task=complete_task,
        list_meetings=list_meetings,
        create_meeting=create_meeting,
        list_interactions=list_interactions,
        create_interaction=create_interaction,
    )


# ============================================================================
# EXTERNAL MCP TOOLS REGISTRATION
# ============================================================================

def register_yad2_tools():
    """Register Yad2 real estate search tools."""
    try:
        from yad2.mcp_server import (
            fetch_listings as _yad2_fetch_listings,
            build_search_url as _yad2_build_search_url,
            get_search_parameters_reference as _yad2_get_search_parameters_reference,
            get_all_property_types as _yad2_get_all_property_types,
            fetch_location_autocomplete as _yad2_fetch_location_autocomplete,
        )
        
        @mcp.tool(description="Fetch active listings via Yad2's public map feed API. Supports all Yad2 search parameters.")
        async def yad2_fetch_listings(
            ctx: Context,
            # Price parameters
            maxPrice: Optional[int | str] = None,
            minPrice: Optional[int | str] = None,
            # Location parameters
            topArea: Optional[int | str] = None,
            area: Optional[int | str] = None,
            city: Optional[int | str] = None,
            neighborhood: Optional[int | str] = None,
            street: Optional[str] = None,
            # Property type
            property: Optional[str] = None,
            # Property details
            rooms: Optional[str] = None,
            minRooms: Optional[int | str] = None,
            maxRooms: Optional[int | str] = None,
            floor: Optional[str] = None,
            size: Optional[str] = None,
            minSize: Optional[int | str] = None,
            maxSize: Optional[int | str] = None,
            # Features
            parking: Optional[int | str] = None,
            elevator: Optional[int | str | bool] = None,
            balcony: Optional[int | str | bool] = None,
            renovated: Optional[int | str | bool] = None,
            accessibility: Optional[int | str | bool] = None,
            airCondition: Optional[int | str | bool] = None,
            bars: Optional[int | str | bool] = None,
            shelter: Optional[int | str | bool] = None,
            storage: Optional[int | str | bool] = None,
            terrace: Optional[int | str | bool] = None,
            garden: Optional[int | str | bool] = None,
            pets: Optional[int | str | bool] = None,
            furniture: Optional[int | str | bool] = None,
            # Building details
            buildingFloors: Optional[int | str] = None,
            entranceDate: Optional[str] = None,
            propertyCondition: Optional[str] = None,
            # Search parameters
            page: Optional[int | str] = None,
            order: Optional[str] = None,
            dealType: Optional[str] = None,
            priceOnly: Optional[int | str | bool] = None,
            priceDropped: Optional[int | str | bool] = None,
            saleType: Optional[str] = None,
            exclusive: Optional[int | str | bool] = None,
            publishedDays: Optional[int | str] = None,
            # Advanced filters
            fromFloor: Optional[int | str] = None,
            toFloor: Optional[int | str] = None,
            yearBuilt: Optional[int | str] = None,
            minYear: Optional[int | str] = None,
            maxYear: Optional[int | str] = None,
            # API options
            zoom: Optional[int] = None,
            listing_type: str = "all",
            pull_contacts: bool = False,
        ):
            return await _yad2_fetch_listings(
                ctx,
                maxPrice=maxPrice,
                minPrice=minPrice,
                topArea=topArea,
                area=area,
                city=city,
                neighborhood=neighborhood,
                street=street,
                property=property,
                rooms=rooms,
                minRooms=minRooms,
                maxRooms=maxRooms,
                floor=floor,
                size=size,
                minSize=minSize,
                maxSize=maxSize,
                parking=parking,
                elevator=elevator,
                balcony=balcony,
                renovated=renovated,
                accessibility=accessibility,
                airCondition=airCondition,
                bars=bars,
                shelter=shelter,
                storage=storage,
                terrace=terrace,
                garden=garden,
                pets=pets,
                furniture=furniture,
                buildingFloors=buildingFloors,
                entranceDate=entranceDate,
                propertyCondition=propertyCondition,
                page=page,
                order=order,
                dealType=dealType,
                priceOnly=priceOnly,
                priceDropped=priceDropped,
                saleType=saleType,
                exclusive=exclusive,
                publishedDays=publishedDays,
                fromFloor=fromFloor,
                toFloor=toFloor,
                yearBuilt=yearBuilt,
                minYear=minYear,
                maxYear=maxYear,
                zoom=zoom,
                listing_type=listing_type,
                pull_contacts=pull_contacts,
            )
        
        @mcp.tool(description="Build a Yad2 search URL for the given parameters. Supports all Yad2 search parameters.")
        async def yad2_build_search_url(
            ctx: Context,
            # Price parameters
            maxPrice: Optional[int | str] = None,
            minPrice: Optional[int | str] = None,
            # Location parameters
            topArea: Optional[int | str] = None,
            area: Optional[int | str] = None,
            city: Optional[int | str] = None,
            neighborhood: Optional[int | str] = None,
            street: Optional[str] = None,
            # Property type
            property: Optional[str] = None,
            # Property details
            rooms: Optional[str] = None,
            minRooms: Optional[int | str] = None,
            maxRooms: Optional[int | str] = None,
            floor: Optional[str] = None,
            size: Optional[str] = None,
            minSize: Optional[int | str] = None,
            maxSize: Optional[int | str] = None,
            # Features
            parking: Optional[int | str] = None,
            elevator: Optional[int | str | bool] = None,
            balcony: Optional[int | str | bool] = None,
            renovated: Optional[int | str | bool] = None,
            accessibility: Optional[int | str | bool] = None,
            airCondition: Optional[int | str | bool] = None,
            bars: Optional[int | str | bool] = None,
            shelter: Optional[int | str | bool] = None,
            storage: Optional[int | str | bool] = None,
            terrace: Optional[int | str | bool] = None,
            garden: Optional[int | str | bool] = None,
            pets: Optional[int | str | bool] = None,
            furniture: Optional[int | str | bool] = None,
            # Building details
            buildingFloors: Optional[int | str] = None,
            entranceDate: Optional[str] = None,
            propertyCondition: Optional[str] = None,
            # Search parameters
            page: Optional[int | str] = None,
            order: Optional[str] = None,
            dealType: Optional[str] = None,
            priceOnly: Optional[int | str | bool] = None,
            priceDropped: Optional[int | str | bool] = None,
            saleType: Optional[str] = None,
            exclusive: Optional[int | str | bool] = None,
            publishedDays: Optional[int | str] = None,
            # Advanced filters
            fromFloor: Optional[int | str] = None,
            toFloor: Optional[int | str] = None,
            yearBuilt: Optional[int | str] = None,
            minYear: Optional[int | str] = None,
            maxYear: Optional[int | str] = None,
        ):
            return await _yad2_build_search_url(
                ctx,
                maxPrice=maxPrice,
                minPrice=minPrice,
                topArea=topArea,
                area=area,
                city=city,
                neighborhood=neighborhood,
                street=street,
                property=property,
                rooms=rooms,
                minRooms=minRooms,
                maxRooms=maxRooms,
                floor=floor,
                size=size,
                minSize=minSize,
                maxSize=maxSize,
                parking=parking,
                elevator=elevator,
                balcony=balcony,
                renovated=renovated,
                accessibility=accessibility,
                airCondition=airCondition,
                bars=bars,
                shelter=shelter,
                storage=storage,
                terrace=terrace,
                garden=garden,
                pets=pets,
                furniture=furniture,
                buildingFloors=buildingFloors,
                entranceDate=entranceDate,
                propertyCondition=propertyCondition,
                page=page,
                order=order,
                dealType=dealType,
                priceOnly=priceOnly,
                priceDropped=priceDropped,
                saleType=saleType,
                exclusive=exclusive,
                publishedDays=publishedDays,
                fromFloor=fromFloor,
                toFloor=toFloor,
                yearBuilt=yearBuilt,
                minYear=minYear,
                maxYear=maxYear,
            )
        
        @mcp.tool(description="Get a comprehensive reference of available Yad2 search parameters.")
        async def yad2_get_search_parameters_reference(ctx: Context):
            return await _yad2_get_search_parameters_reference(ctx)
        
        @mcp.tool(description="Get all available Yad2 property type codes with Hebrew and English names.")
        async def yad2_get_all_property_types(ctx: Context):
            return await _yad2_get_all_property_types(ctx)
        
        @mcp.tool(description="Fetch location data from Yad2 address autocomplete API and return prepared search parameters.")
        async def yad2_fetch_location_autocomplete(ctx: Context, search_text: str):
            return await _yad2_fetch_location_autocomplete(ctx, search_text)
        
        logger.info("Yad2 tools registered successfully")
    except ImportError as e:
        logger.warning(f"Failed to register Yad2 tools: {e}")


def register_mavat_tools():
    """Register Mavat planning information tools."""
    try:
        from mavat.mcp_server import (
            search_plans as _mavat_search_plans,
            get_plan_details as _mavat_get_plan_details,
            get_plan_documents as _mavat_get_plan_documents,
            search_by_location as _mavat_search_by_location,
            search_by_block_parcel as _mavat_search_by_block_parcel,
            get_lookup_tables as _mavat_get_lookup_tables,
            get_districts as _mavat_get_districts,
            get_cities as _mavat_get_cities,
            get_streets as _mavat_get_streets,
            search_lookup as _mavat_search_lookup,
            get_plan_summary as _mavat_get_plan_summary,
        )
        
        @mcp.tool(description="Search for plans using various criteria.")
        async def mavat_search_plans(
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
        ):
            return await _mavat_search_plans(
                ctx, query, city, district, plan_area, street,
                block_number, parcel_number, status, limit, page
            )
        
        @mcp.tool(description="Retrieve detailed information for a specific plan.")
        async def mavat_get_plan_details(ctx: Context, plan_id: str):
            return await _mavat_get_plan_details(ctx, plan_id)
        
        @mcp.tool(description="Get documents associated with a specific plan.")
        async def mavat_get_plan_documents(ctx: Context, plan_id: str, entity_name: Optional[str] = None):
            return await _mavat_get_plan_documents(ctx, plan_id, entity_name)
        
        @mcp.tool(description="Search for plans by location criteria.")
        async def mavat_search_by_location(
            ctx: Context,
            city: str,
            district: Optional[str] = None,
            plan_area: Optional[str] = None,
            street: Optional[str] = None,
            limit: int = 20
        ):
            return await _mavat_search_by_location(ctx, city, district, plan_area, street, limit)
        
        @mcp.tool(description="Search for plans by block and parcel numbers.")
        async def mavat_search_by_block_parcel(
            ctx: Context,
            block_number: str,
            parcel_number: str,
            limit: int = 20
        ):
            return await _mavat_search_by_block_parcel(ctx, block_number, parcel_number, limit)
        
        @mcp.tool(description="Get all available lookup tables for districts, cities, streets, etc.")
        async def mavat_get_lookup_tables(ctx: Context, force_refresh: bool = False):
            return await _mavat_get_lookup_tables(ctx, force_refresh)
        
        @mcp.tool(description="Get available districts.")
        async def mavat_get_districts(ctx: Context, force_refresh: bool = False):
            return await _mavat_get_districts(ctx, force_refresh)
        
        @mcp.tool(description="Get available cities.")
        async def mavat_get_cities(ctx: Context, force_refresh: bool = False):
            return await _mavat_get_cities(ctx, force_refresh)
        
        @mcp.tool(description="Get available streets.")
        async def mavat_get_streets(ctx: Context, force_refresh: bool = False):
            return await _mavat_get_streets(ctx, force_refresh)
        
        @mcp.tool(description="Search lookup tables by text.")
        async def mavat_search_lookup(
            ctx: Context,
            search_text: str,
            table_type: Optional[str] = None,
            force_refresh: bool = False
        ):
            return await _mavat_search_lookup(ctx, search_text, table_type, force_refresh)
        
        @mcp.tool(description="Get a comprehensive summary of a plan including details and documents.")
        async def mavat_get_plan_summary(ctx: Context, plan_id: str):
            return await _mavat_get_plan_summary(ctx, plan_id)
        
        logger.info("Mavat tools registered successfully")
    except ImportError as e:
        logger.warning(f"Failed to register Mavat tools: {e}")


def register_govmap_tools():
    """Register GovMap tools."""
    try:
        from govmap.mcp_server import (
            autocomplete as _govmap_autocomplete,
            coordinate_conversion as _govmap_coordinate_conversion,
            get_layers_catalog as _govmap_get_layers_catalog,
            get_search_types as _govmap_get_search_types,
            get_parcel_data as _govmap_get_parcel_data,
            get_parcel_addresses as _govmap_get_parcel_addresses,
            get_addresses_by_block_parcel as _govmap_get_addresses_by_block_parcel,
            get_base_layers as _govmap_get_base_layers,
            entities_by_point as _govmap_entities_by_point,
            get_deals_by_location as _govmap_get_deals_by_location,
        )
        
        @mcp.tool(description="GovMap public autocomplete (no token). Returns raw JSON buckets.")
        async def govmap_autocomplete(ctx: Context, query: str, language: str = "he", max_results: int = 10):
            return await _govmap_autocomplete(ctx, query, language, max_results)
        
        @mcp.tool(description="Convert coordinates between ITM (EPSG:2039) and WGS84 (EPSG:4326).")
        async def govmap_coordinate_conversion(
            ctx: Context,
            x: float,
            y: float,
            from_crs: str = "ITM",
            to_crs: str = "WGS84"
        ):
            return await _govmap_coordinate_conversion(ctx, x, y, from_crs, to_crs)
        
        @mcp.tool(description="Get the layers catalog from GovMap.")
        async def govmap_get_layers_catalog(ctx: Context, language: str = "he"):
            return await _govmap_get_layers_catalog(ctx, language)
        
        @mcp.tool(description="Get search types from GovMap.")
        async def govmap_get_search_types(ctx: Context, language: str = "he"):
            return await _govmap_get_search_types(ctx, language)
        
        @mcp.tool(description="Get parcel data for specific coordinates (EPSG:2039).")
        async def govmap_get_parcel_data(ctx: Context, x: float, y: float):
            return await _govmap_get_parcel_data(ctx, x, y)
        
        @mcp.tool(description="Get detailed address information for a parcel using its objectid.")
        async def govmap_get_parcel_addresses(ctx: Context, objectid: int):
            return await _govmap_get_parcel_addresses(ctx, objectid)
        
        @mcp.tool(description="Get addresses for a given block and parcel using GovMap autocomplete API.")
        async def govmap_get_addresses_by_block_parcel(ctx: Context, block: str, parcel: str):
            return await _govmap_get_addresses_by_block_parcel(ctx, block, parcel)
        
        @mcp.tool(description="Get base layers from GovMap API.")
        async def govmap_get_base_layers(ctx: Context):
            return await _govmap_get_base_layers(ctx)
        
        @mcp.tool(description="Get entities by point with specified layer IDs (EPSG:2039).")
        async def govmap_entities_by_point(
            ctx: Context,
            x: float,
            y: float,
            layer_ids: List[Any],
            tolerance_m: float = 30.0
        ):
            return await _govmap_entities_by_point(ctx, x, y, layer_ids, tolerance_m)
        
        @mcp.tool(description="Get real estate deals for a specific location and radius. Returns standardized Deal objects with address, deal_date, deal_amount, rooms, floor, asset_type, area, neighborhood, parcel information, etc.")
        async def govmap_get_deals_by_location(
            ctx: Context,
            x: float,
            y: float,
            start_date: str = "1998-01",
            end_date: str = "2025-11",
            radius: float = 100.0,
            deal_type: str = "street",
            limit: int = 9,
            offset: int = 0,
        ):
            return await _govmap_get_deals_by_location(
                ctx, x, y, start_date, end_date, radius, deal_type, limit, offset
            )
        
        logger.info("GovMap tools registered successfully")
    except ImportError as e:
        logger.warning(f"Failed to register GovMap tools: {e}")


def register_gov_tools():
    """Register Gov (DataGovIL) tools."""
    try:
        from gov.mcp_server import (
            decisive_appraisal as _gov_decisive_appraisal,
            fetch_nadlan_transactions as _gov_fetch_nadlan_transactions,
            search_rami_plans as _gov_search_rami_plans,
            download_rami_plan_documents as _gov_download_rami_plan_documents,
            get_rami_document_types_info as _gov_get_rami_document_types_info,
        )
        
        @mcp.tool(description="Fetch decisive appraisal decisions from gov.il.")
        async def gov_decisive_appraisal(ctx: Context, block: str = "", plot: str = "", max_pages: int = 1):
            return await _gov_decisive_appraisal(ctx, block, plot, max_pages)
        
        @mcp.tool(description="Fetch real estate transactions from nadlan.gov.il.")
        async def gov_fetch_nadlan_transactions(
            ctx: Context,
            address: Optional[str] = None,
            neighborhood_id: Optional[str] = None,
            limit: int = 20,
        ):
            return await _gov_fetch_nadlan_transactions(ctx, address, neighborhood_id, limit)
        
        @mcp.tool(description="Search for planning documents using RAMI TabaSearch API.")
        async def gov_search_rami_plans(
            ctx: Context,
            plan_number: str = "",
            city: Optional[int] = None,
            block: str = "",
            parcel: str = "",
            statuses: Optional[List[int]] = None,
            plan_types: Optional[List[int]] = None,
            from_status_date: Optional[str] = None,
            to_status_date: Optional[str] = None,
            plan_types_used: bool = False
        ):
            return await _gov_search_rami_plans(
                ctx, plan_number, city, block, parcel, statuses,
                plan_types, from_status_date, to_status_date, plan_types_used
            )
        
        @mcp.tool(description="Download documents for a specific plan.")
        async def gov_download_rami_plan_documents(
            ctx: Context,
            plan_id: int,
            plan_number: str,
            base_dir: str = "rami_plans",
            doc_types: Optional[List[str]] = None,
            overwrite: bool = False
        ):
            return await _gov_download_rami_plan_documents(
                ctx, plan_id, plan_number, base_dir, doc_types, overwrite
            )
        
        @mcp.tool(description="Get information about available document types.")
        async def gov_get_rami_document_types_info(ctx: Context):
            return await _gov_get_rami_document_types_info(ctx)
        
        logger.info("Gov (DataGovIL) tools registered successfully")
    except ImportError as e:
        logger.warning(f"Failed to register Gov tools: {e}")


def register_madlan_tools():
    """Register Madlan real estate search tools."""
    try:
        from madlan.mcp_server import (
            get_addresses as _madlan_get_addresses,
            madlan_search_real_estate as _madlan_search_real_estate,
        )
        
        @mcp.tool(description="Autocomplete addresses and get address details from Madlan.")
        async def madlan_get_addresses(
            ctx: Context,
            text: str,
            completion_types: Optional[List[str]] = None,
        ):
            return await _madlan_get_addresses(ctx, text, completion_types)
        
        @mcp.tool(description="Search for real estate listings on Madlan with optional filters.")
        async def madlan_search_real_estate(
            ctx: Context,
            location_doc_id: Optional[str] = None,
            deal_type: str = "unitBuy",
            min_price: Optional[int | str] = None,
            max_price: Optional[int | str] = None,
            min_rooms: Optional[float | str] = None,
            max_rooms: Optional[float | str] = None,
            min_area: Optional[int | str] = None,
            max_area: Optional[int | str] = None,
            min_floor: Optional[int | str] = None,
            max_floor: Optional[int | str] = None,
            min_baths: Optional[float | str] = None,
            max_baths: Optional[float | str] = None,
            building_class: Optional[str] = None,
            general_condition: Optional[str] = None,
            seller_type: Optional[str] = None,
            amenities: Optional[Dict[str, Any]] = None,
            limit: int | str = 50,
            offset: int | str = 0,
            no_fee: bool = False,
            price_drop: bool = False,
            under_price_estimation: bool = False,
            discounted_projects: bool = False,
            only_immediate: bool = False,
            is_commercial_real_estate: bool = False,
        ):
            return await _madlan_search_real_estate(
                ctx, location_doc_id, deal_type, min_price, max_price,
                min_rooms, max_rooms, min_area, max_area, min_floor,
                max_floor, min_baths, max_baths, building_class,
                general_condition, seller_type, amenities, limit, offset,
                no_fee, price_drop, under_price_estimation, discounted_projects,
                only_immediate, is_commercial_real_estate
            )
        
    except ImportError as e:
        logger.warning(f"Failed to register Madlan tools: {e}")


def register_gis_tools():
    """Register GIS (Tel Aviv) tools."""
    try:
        from gis.mcp_server import (
            geocode_address as _gis_geocode_address,
            get_building_permits as _gis_get_building_permits,
            get_land_use_main as _gis_get_land_use_main,
            get_land_use_detailed as _gis_get_land_use_detailed,
            get_plans_local as _gis_get_plans_local,
            get_plans_citywide as _gis_get_plans_citywide,
            get_parcels as _gis_get_parcels,
            get_blocks as _gis_get_blocks,
            get_dangerous_buildings as _gis_get_dangerous_buildings,
            get_noise_levels as _gis_get_noise_levels,
            get_cell_antennas as _gis_get_cell_antennas,
            get_green_areas as _gis_get_green_areas,
            get_shelters as _gis_get_shelters,
            get_building_privilege_page as _gis_get_building_privilege_page,
            get_affordable_housing_projects as _gis_get_affordable_housing_projects,
            get_bike_paths as _gis_get_bike_paths,
            get_metro_stations as _gis_get_metro_stations,
            get_metro_stations_red as _gis_get_metro_stations_red,
            get_metro_stations_green as _gis_get_metro_stations_green,
            get_metro_stations_purple as _gis_get_metro_stations_purple,
            get_parking_lots as _gis_get_parking_lots,
            get_parking_public as _gis_get_parking_public,
            get_parking_private as _gis_get_parking_private,
            get_soil_contamination as _gis_get_soil_contamination,
            get_schools as _gis_get_schools,
            get_schools_kindergartens as _gis_get_schools_kindergartens,
            get_schools_only as _gis_get_schools_only,
            get_green_amenities as _gis_get_green_amenities,
            get_playgrounds as _gis_get_playgrounds,
            get_dog_parks as _gis_get_dog_parks,
            get_public_gardens as _gis_get_public_gardens,
            get_medical_facilities as _gis_get_medical_facilities,
            get_medical_centers as _gis_get_medical_centers,
            get_health_funds as _gis_get_health_funds,
            get_pharmacies as _gis_get_pharmacies,
            get_community_facilities as _gis_get_community_facilities,
            get_community_centers as _gis_get_community_centers,
            get_youth_entrepreneurship_centers as _gis_get_youth_entrepreneurship_centers,
            get_construction_sites as _gis_get_construction_sites,
            get_tama38_key_areas as _gis_get_tama38_key_areas,
            get_road_works as _gis_get_road_works,
            get_road_works_only as _gis_get_road_works_only,
            get_night_works_public as _gis_get_night_works_public,
        )
        
        # Register all GIS tools with wrappers
        @mcp.tool(description="Return (x,y) EPSG:2039 for a given street and house number.")
        async def gis_geocode_address(ctx: Context, street: str, house_number: int, like: bool = True):
            return await _gis_geocode_address(ctx, street, house_number, like)
        
        @mcp.tool(description="Search for building permits near a point (x,y) in meters. Optionally download PDFs.")
        async def gis_get_building_permits(
            ctx: Context,
            x: float,
            y: float,
            radius: int = 30,
            fields: Optional[List[str]] = None,
            download_pdfs: bool = False,
            save_dir: Optional[str] = "permits",
        ):
            return await _gis_get_building_permits(ctx, x, y, radius, fields, download_pdfs, save_dir)
        
        @mcp.tool(description="Get main land-use categories intersecting point (x,y).")
        async def gis_get_land_use_main(ctx: Context, x: float, y: float):
            return await _gis_get_land_use_main(ctx, x, y)
        
        @mcp.tool(description="Get detailed land-use categories intersecting point (x,y).")
        async def gis_get_land_use_detailed(ctx: Context, x: float, y: float):
            return await _gis_get_land_use_detailed(ctx, x, y)
        
        @mcp.tool(description="Get local/parcel-level plans intersecting point (x,y).")
        async def gis_get_plans_local(ctx: Context, x: float, y: float):
            return await _gis_get_plans_local(ctx, x, y)
        
        @mcp.tool(description="Get city-wide plans intersecting point (x,y).")
        async def gis_get_plans_citywide(ctx: Context, x: float, y: float):
            return await _gis_get_plans_citywide(ctx, x, y)
        
        @mcp.tool(description="Get parcels intersecting point (x,y).")
        async def gis_get_parcels(ctx: Context, x: float, y: float):
            return await _gis_get_parcels(ctx, x, y)
        
        @mcp.tool(description="Get blocks intersecting point (x,y).")
        async def gis_get_blocks(ctx: Context, x: float, y: float):
            return await _gis_get_blocks(ctx, x, y)
        
        @mcp.tool(description="Get dangerous buildings within a radius (meters) from point (x,y).")
        async def gis_get_dangerous_buildings(ctx: Context, x: float, y: float, radius: int = 80):
            return await _gis_get_dangerous_buildings(ctx, x, y, radius)
        
        @mcp.tool(description="Get noise levels intersecting point (x,y).")
        async def gis_get_noise_levels(ctx: Context, x: float, y: float):
            return await _gis_get_noise_levels(ctx, x, y)
        
        @mcp.tool(description="Get existing and under-construction cell antennas near point (x,y).")
        async def gis_get_cell_antennas(ctx: Context, x: float, y: float, radius: int = 120):
            return await _gis_get_cell_antennas(ctx, x, y, radius)
        
        @mcp.tool(description="Get green areas within a radius (meters) from point (x,y).")
        async def gis_get_green_areas(ctx: Context, x: float, y: float, radius: int = 150):
            return await _gis_get_green_areas(ctx, x, y, radius)
        
        @mcp.tool(description="Get shelters within a radius (meters) from point (x,y).")
        async def gis_get_shelters(ctx: Context, x: float, y: float, radius: int = 200):
            return await _gis_get_shelters(ctx, x, y, radius)
        
        @mcp.tool(description="Download the building privilege (\"zchuyot\") page for a location.")
        async def gis_get_building_privilege_page(
            ctx: Context,
            x: float,
            y: float,
            save_dir: Optional[str] = "privilege_pages"
        ):
            return await _gis_get_building_privilege_page(ctx, x, y, save_dir)
        
        @mcp.tool(description="Get affordable housing projects within a radius (meters) from point (x,y).")
        async def gis_get_affordable_housing_projects(ctx: Context, x: float, y: float, radius: int = 500):
            return await _gis_get_affordable_housing_projects(ctx, x, y, radius)
        
        @mcp.tool(description="Get bicycle paths within a radius (meters) from point (x,y).")
        async def gis_get_bike_paths(ctx: Context, x: float, y: float, radius: int = 300):
            return await _gis_get_bike_paths(ctx, x, y, radius)
        
        @mcp.tool(description="Get metro stations (all lines: Red, Green, Purple) within a radius (meters) from point (x,y).")
        async def gis_get_metro_stations(ctx: Context, x: float, y: float, radius: int = 1000):
            return await _gis_get_metro_stations(ctx, x, y, radius)
        
        @mcp.tool(description="Get Red Line metro stations within a radius (meters) from point (x,y).")
        async def gis_get_metro_stations_red(ctx: Context, x: float, y: float, radius: int = 1000):
            return await _gis_get_metro_stations_red(ctx, x, y, radius)
        
        @mcp.tool(description="Get Green Line metro stations within a radius (meters) from point (x,y).")
        async def gis_get_metro_stations_green(ctx: Context, x: float, y: float, radius: int = 1000):
            return await _gis_get_metro_stations_green(ctx, x, y, radius)
        
        @mcp.tool(description="Get Purple Line metro stations within a radius (meters) from point (x,y).")
        async def gis_get_metro_stations_purple(ctx: Context, x: float, y: float, radius: int = 1000):
            return await _gis_get_metro_stations_purple(ctx, x, y, radius)
        
        @mcp.tool(description="Get public and private parking lots within a radius (meters) from point (x,y).")
        async def gis_get_parking_lots(ctx: Context, x: float, y: float, radius: int = 300):
            return await _gis_get_parking_lots(ctx, x, y, radius)
        
        @mcp.tool(description="Get public parking lots within a radius (meters) from point (x,y).")
        async def gis_get_parking_public(ctx: Context, x: float, y: float, radius: int = 300):
            return await _gis_get_parking_public(ctx, x, y, radius)
        
        @mcp.tool(description="Get private parking lots within a radius (meters) from point (x,y).")
        async def gis_get_parking_private(ctx: Context, x: float, y: float, radius: int = 300):
            return await _gis_get_parking_private(ctx, x, y, radius)
        
        @mcp.tool(description="Get soil contamination sites within a radius (meters) from point (x,y).")
        async def gis_get_soil_contamination(ctx: Context, x: float, y: float, radius: int = 200):
            return await _gis_get_soil_contamination(ctx, x, y, radius)
        
        @mcp.tool(description="Get schools and kindergartens within a radius (meters) from point (x,y).")
        async def gis_get_schools(ctx: Context, x: float, y: float, radius: int = 500):
            return await _gis_get_schools(ctx, x, y, radius)
        
        @mcp.tool(description="Get kindergartens within a radius (meters) from point (x,y).")
        async def gis_get_schools_kindergartens(ctx: Context, x: float, y: float, radius: int = 500):
            return await _gis_get_schools_kindergartens(ctx, x, y, radius)
        
        @mcp.tool(description="Get schools (excluding kindergartens) within a radius (meters) from point (x,y).")
        async def gis_get_schools_only(ctx: Context, x: float, y: float, radius: int = 500):
            return await _gis_get_schools_only(ctx, x, y, radius)
        
        @mcp.tool(description="Get green amenities (playgrounds, dog parks, public gardens) within a radius (meters) from point (x,y).")
        async def gis_get_green_amenities(ctx: Context, x: float, y: float, radius: int = 400):
            return await _gis_get_green_amenities(ctx, x, y, radius)
        
        @mcp.tool(description="Get playgrounds within a radius (meters) from point (x,y).")
        async def gis_get_playgrounds(ctx: Context, x: float, y: float, radius: int = 400):
            return await _gis_get_playgrounds(ctx, x, y, radius)
        
        @mcp.tool(description="Get dog parks within a radius (meters) from point (x,y).")
        async def gis_get_dog_parks(ctx: Context, x: float, y: float, radius: int = 400):
            return await _gis_get_dog_parks(ctx, x, y, radius)
        
        @mcp.tool(description="Get public gardens within a radius (meters) from point (x,y).")
        async def gis_get_public_gardens(ctx: Context, x: float, y: float, radius: int = 400):
            return await _gis_get_public_gardens(ctx, x, y, radius)
        
        @mcp.tool(description="Get medical facilities (medical centers, health funds, pharmacies) within a radius (meters) from point (x,y).")
        async def gis_get_medical_facilities(ctx: Context, x: float, y: float, radius: int = 500):
            return await _gis_get_medical_facilities(ctx, x, y, radius)
        
        @mcp.tool(description="Get medical centers within a radius (meters) from point (x,y).")
        async def gis_get_medical_centers(ctx: Context, x: float, y: float, radius: int = 500):
            return await _gis_get_medical_centers(ctx, x, y, radius)
        
        @mcp.tool(description="Get health fund clinics within a radius (meters) from point (x,y).")
        async def gis_get_health_funds(ctx: Context, x: float, y: float, radius: int = 500):
            return await _gis_get_health_funds(ctx, x, y, radius)
        
        @mcp.tool(description="Get pharmacies within a radius (meters) from point (x,y).")
        async def gis_get_pharmacies(ctx: Context, x: float, y: float, radius: int = 500):
            return await _gis_get_pharmacies(ctx, x, y, radius)
        
        @mcp.tool(description="Get community facilities (community centers, youth and entrepreneurship centers) within a radius (meters) from point (x,y).")
        async def gis_get_community_facilities(ctx: Context, x: float, y: float, radius: int = 400):
            return await _gis_get_community_facilities(ctx, x, y, radius)
        
        @mcp.tool(description="Get community centers within a radius (meters) from point (x,y).")
        async def gis_get_community_centers(ctx: Context, x: float, y: float, radius: int = 400):
            return await _gis_get_community_centers(ctx, x, y, radius)
        
        @mcp.tool(description="Get youth and entrepreneurship centers within a radius (meters) from point (x,y).")
        async def gis_get_youth_entrepreneurship_centers(ctx: Context, x: float, y: float, radius: int = 400):
            return await _gis_get_youth_entrepreneurship_centers(ctx, x, y, radius)
        
        @mcp.tool(description="Get construction sites within a radius (meters) from point (x,y).")
        async def gis_get_construction_sites(ctx: Context, x: float, y: float, radius: int = 300):
            return await _gis_get_construction_sites(ctx, x, y, radius)
        
        @mcp.tool(description="Get TAMA 38 policy key areas within a radius (meters) from point (x,y).")
        async def gis_get_tama38_key_areas(ctx: Context, x: float, y: float, radius: int = 500):
            return await _gis_get_tama38_key_areas(ctx, x, y, radius)
        
        @mcp.tool(description="Get road works and night works in public space within a radius (meters) from point (x,y).")
        async def gis_get_road_works(ctx: Context, x: float, y: float, radius: int = 200):
            return await _gis_get_road_works(ctx, x, y, radius)
        
        @mcp.tool(description="Get road works within a radius (meters) from point (x,y).")
        async def gis_get_road_works_only(ctx: Context, x: float, y: float, radius: int = 200):
            return await _gis_get_road_works_only(ctx, x, y, radius)
        
        @mcp.tool(description="Get night works in public space within a radius (meters) from point (x,y).")
        async def gis_get_night_works_public(ctx: Context, x: float, y: float, radius: int = 200):
            return await _gis_get_night_works_public(ctx, x, y, radius)
        
        logger.info("GIS (Tel Aviv) tools registered successfully")
    except ImportError as e:
        logger.warning(f"Failed to register GIS tools: {e}")


def register_handasa_tools():
    """Register Handasa tools."""
    try:
        from handasa.mcp_server import (
            handasa_archive as _handasa_handasa_archive,
            download_handasa_document as _handasa_download_handasa_document,
        )
        
        @mcp.tool(description="Fetch the Handasa permit archive for a given block/parcel.")
        async def handasa_archive(
            ctx: Context,
            block: str,
            parcel: Optional[str] = None,
            page_size: int = 50,
        ):
            return await _handasa_handasa_archive(ctx, block, parcel, page_size)
        
        @mcp.tool(description="Download a document from the Handasa portal.")
        async def handasa_download_document(
            ctx: Context,
            unique_id: str,
            save_to: Optional[str] = None,
            overwrite: bool = False,
            return_content: bool = False,
        ):
            return await _handasa_download_handasa_document(ctx, unique_id, save_to, overwrite, return_content)
        
        logger.info("Handasa tools registered successfully")
    except ImportError as e:
        logger.warning(f"Failed to register Handasa tools: {e}")


# ============================================================================
# FILE READING TOOLS
# ============================================================================

def register_file_reading_tools():
    """Register file reading tools for permits, zchuyot, tabu, etc."""
    
    @mcp.tool(description="Read a file (PDF, image, or text) from the filesystem. Read-only, for uploads/data pipeline only. Supports permits, zchuyot, tabu documents, etc.")
    async def read_file(
        ctx: Context,
        file_path: str,
        max_size_mb: Optional[float] = 10.0,
        max_pages: Optional[int] = 10,
        expand_limits: bool = False,
    ) -> Dict[str, Any]:
        """
        Read a file from the filesystem and extract its content.
        
        This is a read-only tool designed for reading uploaded documents and data pipeline files.
        Supports reading permits, zchuyot (building privilege pages), tabu documents, and other real estate documents.
        
        Args:
            file_path: Path to the file to read (relative to workspace root or absolute path)
            max_size_mb: Maximum file size in MB (default: 10 MB). Can be expanded with expand_limits=True
            max_pages: Maximum number of pages to read for PDFs (default: 10). Can be expanded with expand_limits=True
            expand_limits: If True, allows reading larger files (up to 50 MB, 50 pages). Requires explicit request.
        
        Returns:
            Dictionary with:
            - success: Boolean indicating if read was successful
            - file_path: Path to the file
            - file_size: File size in bytes
            - file_size_mb: File size in MB
            - mime_type: Detected MIME type
            - content: Extracted content (text for PDFs, base64 for images, text for text files)
            - pages: Number of pages (for PDFs)
            - pages_read: Number of pages actually read (may be limited by max_pages)
            - truncated: Boolean indicating if content was truncated due to limits
        """
        import mimetypes
        import base64
        from pathlib import Path
        
        # Allowed file types for security
        ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.json', '.xml', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
        ALLOWED_MIME_TYPES = {
            'application/pdf',
            'text/plain',
            'text/json',
            'application/json',
            'text/xml',
            'application/xml',
            'image/png',
            'image/jpeg',
            'image/gif',
            'image/bmp',
            'image/tiff',
        }
        
        # Expand limits if requested
        if expand_limits:
            max_size_mb = max(max_size_mb or 10.0, 50.0)
            max_pages = max(max_pages or 10, 50)
        else:
            max_size_mb = max_size_mb or 10.0
            max_pages = max_pages or 10
        
        max_size_bytes = int(max_size_mb * 1024 * 1024)
        
        try:
            # Resolve file path
            file_path_obj = Path(file_path)
            if not file_path_obj.is_absolute():
                # Try relative to workspace root
                workspace_root = Path(project_root)
                file_path_obj = workspace_root / file_path_obj
            else:
                file_path_obj = file_path_obj.resolve()
            
            # Security check: ensure file exists and is readable
            if not file_path_obj.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                }
            
            if not file_path_obj.is_file():
                return {
                    "success": False,
                    "error": f"Path is not a file: {file_path}",
                }
            
            # Check file extension
            if file_path_obj.suffix.lower() not in ALLOWED_EXTENSIONS:
                return {
                    "success": False,
                    "error": f"File type not allowed. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}",
                }
            
            # Get file size
            file_size = file_path_obj.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            # Check size limit
            if file_size > max_size_bytes:
                return {
                    "success": False,
                    "error": f"File too large: {file_size_mb:.2f} MB exceeds limit of {max_size_mb:.2f} MB. Use expand_limits=True to read larger files.",
                    "file_size_mb": file_size_mb,
                    "max_size_mb": max_size_mb,
                }
            
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path_obj))
            if not mime_type:
                # Fallback based on extension
                ext = file_path_obj.suffix.lower()
                mime_map = {
                    '.pdf': 'application/pdf',
                    '.txt': 'text/plain',
                    '.json': 'application/json',
                    '.xml': 'text/xml',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.bmp': 'image/bmp',
                    '.tiff': 'image/tiff',
                }
                mime_type = mime_map.get(ext, 'application/octet-stream')
            
            # Check MIME type
            if mime_type not in ALLOWED_MIME_TYPES:
                return {
                    "success": False,
                    "error": f"MIME type not allowed: {mime_type}",
                }
            
            # Read file based on type
            content = None
            pages = None
            pages_read = None
            truncated = False
            
            if mime_type == 'application/pdf':
                # Read PDF
                try:
                    import pdfplumber
                    
                    with pdfplumber.open(str(file_path_obj)) as pdf:
                        total_pages = len(pdf.pages)
                        pages = total_pages
                        pages_to_read = min(total_pages, max_pages)
                        pages_read = pages_to_read
                        truncated = total_pages > max_pages
                        
                        # Extract text from pages
                        text_parts = []
                        for i in range(pages_to_read):
                            page = pdf.pages[i]
                            page_text = page.extract_text()
                            if page_text:
                                text_parts.append(f"--- Page {i + 1} ---\n{page_text}")
                        
                        content = "\n\n".join(text_parts)
                        
                        if truncated:
                            content += f"\n\n[Note: Document has {total_pages} pages, but only first {max_pages} pages were read. Use expand_limits=True to read more pages.]"
                        
                except ImportError:
                    return {
                        "success": False,
                        "error": "pdfplumber library not available. Install with: pip install pdfplumber",
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Error reading PDF: {str(e)}",
                    }
            
            elif mime_type.startswith('image/'):
                # Read image as base64
                try:
                    with open(file_path_obj, 'rb') as f:
                        image_data = f.read()
                        content = base64.b64encode(image_data).decode('utf-8')
                        # Also try to get image dimensions if PIL is available
                        try:
                            from PIL import Image
                            with Image.open(file_path_obj) as img:
                                pages = 1  # Images are single "page"
                                pages_read = 1
                                content = {
                                    "base64": content,
                                    "format": img.format,
                                    "mode": img.mode,
                                    "size": img.size,
                                }
                        except ImportError:
                            # PIL not available, just return base64
                            pages = 1
                            pages_read = 1
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Error reading image: {str(e)}",
                    }
            
            elif mime_type.startswith('text/') or mime_type in ('application/json', 'application/xml'):
                # Read text file
                try:
                    with open(file_path_obj, 'r', encoding='utf-8') as f:
                        content = f.read()
                        pages = 1
                        pages_read = 1
                except UnicodeDecodeError:
                    # Try with different encoding
                    try:
                        with open(file_path_obj, 'r', encoding='latin-1') as f:
                            content = f.read()
                            pages = 1
                            pages_read = 1
                    except Exception as e:
                        return {
                            "success": False,
                            "error": f"Error reading text file: {str(e)}",
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Error reading text file: {str(e)}",
                    }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {mime_type}",
                }
            
            return {
                "success": True,
                "file_path": str(file_path_obj),
                "file_size": file_size,
                "file_size_mb": round(file_size_mb, 2),
                "mime_type": mime_type,
                "content": content,
                "pages": pages,
                "pages_read": pages_read,
                "truncated": truncated,
            }
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error reading file: {str(e)}",
            }
    
    logger.info("File reading tools registered successfully")


# ============================================================================
# TOOL REGISTRATION
# ============================================================================

# Register core tools by default (assets, deals, cost, mortgage, CRM, file reading)
register_assets_tools()
register_deals_tools()
register_cost_tools()
register_mortgage_tools()
register_crm_tools()
register_file_reading_tools()

# Register external MCP tools (optional - can be enabled via environment variable)
# Set ENABLE_EXTERNAL_MCP_TOOLS=true to enable all external tools
if os.getenv("ENABLE_EXTERNAL_MCP_TOOLS", "false").lower() == "true":
    register_yad2_tools()
    register_mavat_tools()
    register_govmap_tools()
    register_gov_tools()
    register_madlan_tools()
    register_gis_tools()
    register_handasa_tools()
    logger.info("All external MCP tools registered")
else:
    logger.info("External MCP tools disabled. Set ENABLE_EXTERNAL_MCP_TOOLS=true to enable.")


if __name__ == "__main__":
    mcp.run()
