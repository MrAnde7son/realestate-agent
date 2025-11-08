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
- get_asset_data: Get asset subresource (transactions/permits/plans/appraisal/listings/documents)

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

Usage Examples:
1. List assets: list_assets(city="תל אביב", page=1)
2. Get asset: get_asset(asset_id=123)
3. Get asset transactions: get_asset_data(asset_id=123, kind="transactions")
4. Analyze mortgage: analyze_mortgage(property_price=4500000, savings_total=900000)
5. List contacts: list_contacts()
6. Create deal: create_deal(asset_id=123, stage="discovery")
7. Calculate deal expenses: calculate_deal_expenses(price=3000000, buyers=[{"sharePct": 100, "isFirstHome": True}], area=100)
"""

import json
import logging
import os
import sys
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
        return {k: item.get(k) for k in keep if k in item}
    
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
        max_price: Optional[int | str] = None,
        min_price: Optional[int | str] = None,
        rooms: Optional[int | str] = None,
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
        
        params = {}
        if city:
            params["city"] = city
        price_max_int = _to_int(max_price)
        if price_max_int is not None:
            params["priceMax"] = price_max_int
        price_min_int = _to_int(min_price)
        if price_min_int is not None:
            params["priceMin"] = price_min_int
        rooms_int = _to_int(rooms)
        if rooms_int is not None:
            params["rooms"] = rooms_int
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

    @mcp.tool(description="Get cost options.")
    async def get_cost_options(
        ctx: Context,
    ) -> Dict[str, Any]:
        return _make_request(ctx, "GET", "/cost/options")

    @mcp.tool(description="Calculate deal expenses including purchase tax, service costs, and construction costs.")
    async def calculate_deal_expenses(
        ctx: Context,
        price: float,
        buyers: List[Dict[str, Any]],
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
            buyers: List of buyer dictionaries with sharePct and optional flags:
                - sharePct: Percentage share (0-100)
                - isFirstHome: Boolean (optional)
                - isReplacementHome: Boolean (optional)
                - oleh: Boolean (optional, for new immigrants)
                - disabled: Boolean (optional)
                - bereavedFamily: Boolean (optional)
                - name: String (optional)
            area: Property area in square meters (optional, for price per sqm calculation)
            property_type: "residential" or "land" (default: "residential")
            services: List of service cost dictionaries with:
                - label: Service label
                - percent: Percentage of price (optional)
                - amount: Fixed amount (optional)
                - includesVat: Boolean indicating if VAT is included
            vat_rate: VAT rate (default: 0.18 for 18%)
            construction_area: Construction area in sqm (for land purchases)
            construction_cost_per_sqm: Construction cost per sqm (for land purchases)
            construction_includes_vat: Whether construction cost includes VAT (default: True)
            
        Returns:
            Dictionary with complete expense breakdown including:
            - totalTax: Total purchase tax
            - breakdown: Purchase tax breakdown per buyer
            - serviceTotal: Total service costs
            - serviceBreakdown: Service costs breakdown
            - constructionCost: Construction cost (for land)
            - total: Total cost including all expenses
            - pricePerSqBefore: Price per sqm before expenses
            - pricePerSqAfter: Price per sqm after expenses
        """
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

    @mcp.tool(description="List tasks.")
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


# ============================================================================
# TOOL REGISTRATION
# ============================================================================

# Register core tools by default (assets, deals, cost, mortgage, CRM)
register_assets_tools()
register_deals_tools()
register_cost_tools()
register_mortgage_tools()
register_crm_tools()


if __name__ == "__main__":
    mcp.run()
