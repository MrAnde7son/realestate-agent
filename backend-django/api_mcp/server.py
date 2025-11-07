#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real Estate API FastMCP Server

FastMCP-based Model Context Protocol server for the Real Estate API integration with LLMs.
Provides tools for accessing assets, deal expenses, expense calculations, mortgage calculations, and CRM functionality.

Available Tools:

ASSETS:
- list_assets: List all assets with filtering and pagination
- get_asset: Get detailed information for a specific asset
- create_asset: Create a new asset
- sync_asset: Trigger synchronization for an asset
- get_asset_transactions: Get transactions for an asset
- get_asset_permits: Get permits for an asset
- get_asset_plans: Get plans for an asset
- get_asset_appraisal: Get appraisal analysis for an asset
- get_asset_listings: Get listings for an asset
- get_asset_documents: Get documents for an asset

DEAL EXPENSES:
- list_deals: List all deals
- get_deal: Get deal details
- create_deal: Create a new deal
- list_negotiations: List negotiations for a deal
- get_negotiation: Get negotiation details
- list_offers: List offers for a negotiation
- get_offer: Get offer details

EXPENSE CALCULATION:
- estimate_build_cost: Estimate building construction costs
- get_cost_options: Get available options for cost estimation

MORTGAGE CALCULATION:
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
3. Analyze mortgage: analyze_mortgage(property_price=4500000, savings_total=900000)
4. List contacts: list_contacts()
5. Create deal: create_deal(asset_id=123, stage="discovery")
"""

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
mcp = FastMCP("RealEstateAPI", dependencies=["requests"])

# Module-level state
_api_base_url: Optional[str] = None
_api_token: Optional[str] = None

logger = logging.getLogger(__name__)

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

    url = f"{_get_api_base_url()}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    token = _get_api_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
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
        
        response.raise_for_status()
        
        # Handle empty responses
        if response.status_code == 204 or not response.content:
            return {"success": True, "data": None}
        
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
        }


# ============================================================================
# ASSETS TOOLS
# ============================================================================

@mcp.tool()
async def list_assets(
    ctx: Context,
    city: Optional[str] = None,
    max_price: Optional[int] = None,
    min_price: Optional[int] = None,
    rooms: Optional[int] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Dict[str, Any]:
    """List all assets with optional filtering and pagination.
    
    Args:
        city: City name or code to filter by
        max_price: Maximum price filter
        min_price: Minimum price filter
        rooms: Number of rooms filter
        page: Page number for pagination
        page_size: Number of items per page
    
    Returns:
        Dictionary with success status and list of assets
    """
    params = {}
    if city:
        params["city"] = city
    if max_price:
        params["max_price"] = max_price
    if min_price:
        params["min_price"] = min_price
    if rooms:
        params["rooms"] = rooms
    if page:
        params["page"] = page
    if page_size:
        params["page_size"] = page_size
    
    return _make_request(ctx, "GET", "/assets", params=params)


@mcp.tool()
async def get_asset(
    ctx: Context,
    asset_id: int,
    include_documents: bool = False,
) -> Dict[str, Any]:
    """Get detailed information for a specific asset.
    
    Args:
        asset_id: The ID of the asset to retrieve
        include_documents: Whether to include documents in the response
    
    Returns:
        Dictionary with success status and asset details
    """
    params = {}
    if include_documents:
        params["include_documents"] = "true"
    
    return _make_request(ctx, "GET", f"/assets/{asset_id}", params=params)


@mcp.tool()
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
    """Create a new asset and enqueue enrichment pipeline.
    
    Args:
        scope: Scope object with type, value, and city
        address: Full address string
        city: City name
        street: Street name
        number: Street number
        block: Block number
        parcel: Parcel number
        radius: Radius for area-based searches
    
    Returns:
        Dictionary with success status and created asset data
    """
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


@mcp.tool()
async def sync_asset(
    ctx: Context,
    asset_id: int,
) -> Dict[str, Any]:
    """Trigger manual synchronization for an asset.
    
    Args:
        asset_id: The ID of the asset to sync
    
    Returns:
        Dictionary with success status
    """
    return _make_request(ctx, "POST", f"/assets/{asset_id}/sync")


@mcp.tool()
async def get_asset_transactions(
    ctx: Context,
    asset_id: int,
) -> Dict[str, Any]:
    """Get transactions for an asset.
    
    Args:
        asset_id: The ID of the asset
    
    Returns:
        Dictionary with success status and list of transactions
    """
    return _make_request(ctx, "GET", f"/assets/{asset_id}/transactions")


@mcp.tool()
async def get_asset_permits(
    ctx: Context,
    asset_id: int,
) -> Dict[str, Any]:
    """Get permits for an asset.
    
    Args:
        asset_id: The ID of the asset
    
    Returns:
        Dictionary with success status and list of permits
    """
    return _make_request(ctx, "GET", f"/assets/{asset_id}/permits")


@mcp.tool()
async def get_asset_plans(
    ctx: Context,
    asset_id: int,
) -> Dict[str, Any]:
    """Get plans for an asset.
    
    Args:
        asset_id: The ID of the asset
    
    Returns:
        Dictionary with success status and list of plans
    """
    return _make_request(ctx, "GET", f"/assets/{asset_id}/plans")


@mcp.tool()
async def get_asset_appraisal(
    ctx: Context,
    asset_id: int,
) -> Dict[str, Any]:
    """Get appraisal analysis for an asset.
    
    Args:
        asset_id: The ID of the asset
    
    Returns:
        Dictionary with success status and appraisal data
    """
    return _make_request(ctx, "GET", f"/assets/{asset_id}/appraisal")


@mcp.tool()
async def get_asset_listings(
    ctx: Context,
    asset_id: int,
) -> Dict[str, Any]:
    """Get listings for an asset.
    
    Args:
        asset_id: The ID of the asset
    
    Returns:
        Dictionary with success status and list of listings
    """
    return _make_request(ctx, "GET", f"/assets/{asset_id}/listings")


@mcp.tool()
async def get_asset_documents(
    ctx: Context,
    asset_id: int,
) -> Dict[str, Any]:
    """Get documents for an asset.
    
    Args:
        asset_id: The ID of the asset
    
    Returns:
        Dictionary with success status and list of documents
    """
    return _make_request(ctx, "GET", f"/assets/{asset_id}/documents")


# ============================================================================
# DEAL EXPENSES TOOLS
# ============================================================================

@mcp.tool()
async def list_deals(
    ctx: Context,
    stage: Optional[str] = None,
    deal_lead: Optional[int] = None,
    asset_id: Optional[int] = None,
    updated_after: Optional[str] = None,
    search: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Dict[str, Any]:
    """List all deals with optional filtering.
    
    Args:
        stage: Filter by deal stage (discovery, negotiation, legal, financing, closing, abandoned)
        deal_lead: Filter by deal lead user ID
        asset_id: Filter by asset ID
        updated_after: Filter by updated after date (ISO format)
        search: Search in address, city, street, or neighborhood
        page: Page number for pagination
        page_size: Number of items per page
    
    Returns:
        Dictionary with success status and list of deals
    """
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
    if page_size:
        params["page_size"] = page_size
    
    return _make_request(ctx, "GET", "/deal-workspace/deals", params=params)


@mcp.tool()
async def get_deal(
    ctx: Context,
    deal_id: int,
) -> Dict[str, Any]:
    """Get deal details.
    
    Args:
        deal_id: The ID of the deal
    
    Returns:
        Dictionary with success status and deal details
    """
    return _make_request(ctx, "GET", f"/deal-workspace/deals/{deal_id}")


@mcp.tool()
async def create_deal(
    ctx: Context,
    asset_id: int,
    stage: Optional[str] = None,
    confidentiality_level: Optional[str] = None,
    parties: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Create a new deal for an asset.
    
    Args:
        asset_id: The ID of the asset
        stage: Deal stage (default: discovery)
        confidentiality_level: Confidentiality level (standard, restricted, internal)
        parties: List of party roles with user_id, role, side, and optional external_contact
    
    Returns:
        Dictionary with success status and created deal data
    """
    data = {}
    if stage:
        data["stage"] = stage
    if confidentiality_level:
        data["confidentiality_level"] = confidentiality_level
    if parties:
        data["parties"] = parties
    
    return _make_request(ctx, "POST", f"/deal-workspace/deals/{asset_id}", data=data)


@mcp.tool()
async def list_negotiations(
    ctx: Context,
    deal_id: Optional[int] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """List negotiations, optionally filtered by deal.
    
    Args:
        deal_id: Filter by deal ID
        status: Filter by status (open, paused, closed)
    
    Returns:
        Dictionary with success status and list of negotiations
    """
    params = {}
    if deal_id:
        params["deal_id"] = deal_id
    if status:
        params["status"] = status
    
    return _make_request(ctx, "GET", "/deal-workspace/negotiations", params=params)


@mcp.tool()
async def get_negotiation(
    ctx: Context,
    negotiation_id: int,
) -> Dict[str, Any]:
    """Get negotiation details.
    
    Args:
        negotiation_id: The ID of the negotiation
    
    Returns:
        Dictionary with success status and negotiation details
    """
    return _make_request(ctx, "GET", f"/deal-workspace/negotiations/{negotiation_id}")


@mcp.tool()
async def list_offers(
    ctx: Context,
    negotiation_id: Optional[int] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """List offers, optionally filtered by negotiation.
    
    Args:
        negotiation_id: Filter by negotiation ID
        status: Filter by status (active, countered, accepted, withdrawn, expired, rejected)
    
    Returns:
        Dictionary with success status and list of offers
    """
    params = {}
    if negotiation_id:
        params["negotiation_id"] = negotiation_id
    if status:
        params["status"] = status
    
    return _make_request(ctx, "GET", "/deal-workspace/offers", params=params)


@mcp.tool()
async def get_offer(
    ctx: Context,
    offer_id: int,
) -> Dict[str, Any]:
    """Get offer details including financial information.
    
    Args:
        offer_id: The ID of the offer
    
    Returns:
        Dictionary with success status and offer details including amount, financing_type, etc.
    """
    return _make_request(ctx, "GET", f"/deal-workspace/offers/{offer_id}")


# ============================================================================
# EXPENSE CALCULATION TOOLS
# ============================================================================

@mcp.tool()
async def estimate_build_cost(
    ctx: Context,
    area_m2: float,
    scope: Optional[List[str]] = None,
    region: Optional[str] = None,
    quality: Optional[str] = None,
) -> Dict[str, Any]:
    """Estimate building construction costs using Dekel-style calculations.
    
    Args:
        area_m2: Building area in square meters (required)
        scope: List of construction scopes (e.g., ["shell", "finish"])
        region: Region code (TA, CENTER, NORTH, SOUTH)
        quality: Quality level (basic, standard, premium)
    
    Returns:
        Dictionary with success status and cost estimate including:
        - breakdown: Detailed cost breakdown by category
        - totals: Total costs (base, low, high) with and without VAT
        - metadata: Additional metadata about the estimate
    """
    data = {"area_m2": area_m2}
    if scope:
        data["scope"] = scope
    if region:
        data["region"] = region
    if quality:
        data["quality"] = quality
    
    return _make_request(ctx, "POST", "/cost/estimate/build", data=data)


@mcp.tool()
async def get_cost_options(
    ctx: Context,
) -> Dict[str, Any]:
    """Get available options for cost estimation.
    
    Returns:
        Dictionary with success status and available options:
        - regions: List of available region codes
        - qualities: List of available quality levels
        - scopes: List of available construction scopes
    """
    return _make_request(ctx, "GET", "/cost/options")


# ============================================================================
# MORTGAGE CALCULATION TOOLS
# ============================================================================

@mcp.tool()
async def analyze_mortgage(
    ctx: Context,
    property_price: float,
    savings_total: float,
    annual_rate_pct: Optional[float] = None,
    term_years: Optional[int] = None,
    transactions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Analyze mortgage affordability and payment scenarios.
    
    Args:
        property_price: Property price in NIS
        savings_total: Total savings available
        annual_rate_pct: Annual interest rate percentage (default: 4.5)
        term_years: Loan term in years (default: 25)
        transactions: List of transaction objects with date, amount, and type
    
    Returns:
        Dictionary with success status and mortgage analysis including:
        - metrics: median_monthly_income, median_monthly_expense, monthly_surplus_estimate
        - recommendation: recommended_monthly_payment, max_loan_from_payment, 
          max_loan_by_ltv, approved_loan_ceiling, cash_gap_for_purchase
        - notes: Informational notes
    """
    data = {
        "property_price": property_price,
        "savings_total": savings_total,
    }
    if annual_rate_pct is not None:
        data["annual_rate_pct"] = annual_rate_pct
    if term_years is not None:
        data["term_years"] = term_years
    if transactions:
        data["transactions"] = transactions
    
    return _make_request(ctx, "POST", "/mortgage-analyze", data=data)


# ============================================================================
# CRM TOOLS
# ============================================================================

@mcp.tool()
async def list_contacts(
    ctx: Context,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Dict[str, Any]:
    """List all contacts.
    
    Args:
        page: Page number for pagination
        page_size: Number of items per page
    
    Returns:
        Dictionary with success status and list of contacts
    """
    params = {}
    if page:
        params["page"] = page
    if page_size:
        params["page_size"] = page_size
    
    return _make_request(ctx, "GET", "/crm/contacts", params=params)


@mcp.tool()
async def get_contact(
    ctx: Context,
    contact_id: int,
) -> Dict[str, Any]:
    """Get contact details.
    
    Args:
        contact_id: The ID of the contact
    
    Returns:
        Dictionary with success status and contact details
    """
    return _make_request(ctx, "GET", f"/crm/contacts/{contact_id}")


@mcp.tool()
async def create_contact(
    ctx: Context,
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    equity: Optional[float] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new contact.
    
    Args:
        name: Contact name (required)
        email: Contact email
        phone: Contact phone
        equity: Contact equity amount
        tags: List of tags
        notes: Notes about the contact
    
    Returns:
        Dictionary with success status and created contact data
    """
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


@mcp.tool()
async def search_contacts(
    ctx: Context,
    query: str,
) -> Dict[str, Any]:
    """Search contacts by name, email, phone, or tags.
    
    Args:
        query: Search query string
    
    Returns:
        Dictionary with success status and list of matching contacts
    """
    return _make_request(ctx, "GET", "/crm/contacts/search", params={"q": query})


@mcp.tool()
async def list_leads(
    ctx: Context,
    status: Optional[str] = None,
    contact_id: Optional[int] = None,
    asset_id: Optional[int] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Dict[str, Any]:
    """List all leads with optional filtering.
    
    Args:
        status: Filter by lead status
        contact_id: Filter by contact ID
        asset_id: Filter by asset ID
        page: Page number for pagination
        page_size: Number of items per page
    
    Returns:
        Dictionary with success status and list of leads
    """
    params = {}
    if status:
        params["status"] = status
    if contact_id:
        params["contact"] = contact_id
    if asset_id:
        params["asset_id"] = asset_id
    if page:
        params["page"] = page
    if page_size:
        params["page_size"] = page_size
    
    return _make_request(ctx, "GET", "/crm/leads", params=params)


@mcp.tool()
async def get_lead(
    ctx: Context,
    lead_id: int,
) -> Dict[str, Any]:
    """Get lead details.
    
    Args:
        lead_id: The ID of the lead
    
    Returns:
        Dictionary with success status and lead details
    """
    return _make_request(ctx, "GET", f"/crm/leads/{lead_id}")


@mcp.tool()
async def create_lead(
    ctx: Context,
    contact_id: int,
    asset_id: int,
    status: Optional[str] = None,
    notes: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Create a new lead.
    
    Args:
        contact_id: The ID of the contact
        asset_id: The ID of the asset
        status: Initial lead status
        notes: List of note objects with ts and text
    
    Returns:
        Dictionary with success status and created lead data
    """
    data = {
        "contact": contact_id,
        "asset": asset_id,
    }
    if status:
        data["status"] = status
    if notes:
        data["notes"] = notes
    
    return _make_request(ctx, "POST", "/crm/leads", data=data)


@mcp.tool()
async def update_lead_status(
    ctx: Context,
    lead_id: int,
    status: str,
) -> Dict[str, Any]:
    """Update lead status.
    
    Args:
        lead_id: The ID of the lead
        status: New status value
    
    Returns:
        Dictionary with success status and updated lead data
    """
    return _make_request(ctx, "POST", f"/crm/leads/{lead_id}/set_status", data={"status": status})


@mcp.tool()
async def add_lead_note(
    ctx: Context,
    lead_id: int,
    text: str,
) -> Dict[str, Any]:
    """Add a note to a lead.
    
    Args:
        lead_id: The ID of the lead
        text: Note text
    
    Returns:
        Dictionary with success status and updated lead data
    """
    return _make_request(ctx, "POST", f"/crm/leads/{lead_id}/add_note", data={"text": text})


@mcp.tool()
async def list_tasks(
    ctx: Context,
    contact_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    status: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Dict[str, Any]:
    """List all tasks with optional filtering.
    
    Args:
        contact_id: Filter by contact ID
        lead_id: Filter by lead ID
        status: Filter by task status
        page: Page number for pagination
        page_size: Number of items per page
    
    Returns:
        Dictionary with success status and list of tasks
    """
    params = {}
    if contact_id:
        params["contact"] = contact_id
    if lead_id:
        params["lead"] = lead_id
    if status:
        params["status"] = status
    if page:
        params["page"] = page
    if page_size:
        params["page_size"] = page_size
    
    return _make_request(ctx, "GET", "/crm/tasks", params=params)


@mcp.tool()
async def create_task(
    ctx: Context,
    contact_id: int,
    title: str,
    description: Optional[str] = None,
    due_at: Optional[str] = None,
    lead_id: Optional[int] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new task.
    
    Args:
        contact_id: The ID of the contact
        title: Task title (required)
        description: Task description
        due_at: Due date (ISO format)
        lead_id: Associated lead ID
        status: Task status
    
    Returns:
        Dictionary with success status and created task data
    """
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


@mcp.tool()
async def complete_task(
    ctx: Context,
    task_id: int,
) -> Dict[str, Any]:
    """Mark a task as completed.
    
    Args:
        task_id: The ID of the task
    
    Returns:
        Dictionary with success status and updated task data
    """
    return _make_request(ctx, "POST", f"/crm/tasks/{task_id}/complete")


@mcp.tool()
async def list_meetings(
    ctx: Context,
    contact_id: Optional[int] = None,
    status: Optional[str] = None,
    upcoming: Optional[bool] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Dict[str, Any]:
    """List all meetings with optional filtering.
    
    Args:
        contact_id: Filter by contact ID
        status: Filter by meeting status
        upcoming: Filter to show only upcoming meetings
        page: Page number for pagination
        page_size: Number of items per page
    
    Returns:
        Dictionary with success status and list of meetings
    """
    params = {}
    if contact_id:
        params["contact"] = contact_id
    if status:
        params["status"] = status
    if upcoming:
        params["upcoming"] = "true"
    if page:
        params["page"] = page
    if page_size:
        params["page_size"] = page_size
    
    return _make_request(ctx, "GET", "/crm/meetings", params=params)


@mcp.tool()
async def create_meeting(
    ctx: Context,
    contact_id: int,
    scheduled_for: str,
    title: Optional[str] = None,
    location: Optional[str] = None,
    notes: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new meeting.
    
    Args:
        contact_id: The ID of the contact
        scheduled_for: Scheduled date/time (ISO format, required)
        title: Meeting title
        location: Meeting location
        notes: Meeting notes
        status: Meeting status
    
    Returns:
        Dictionary with success status and created meeting data
    """
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


@mcp.tool()
async def list_interactions(
    ctx: Context,
    contact_id: Optional[int] = None,
    interaction_type: Optional[str] = None,
    since: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Dict[str, Any]:
    """List all interactions with optional filtering.
    
    Args:
        contact_id: Filter by contact ID
        interaction_type: Filter by interaction type
        since: Filter interactions since date (ISO format)
        page: Page number for pagination
        page_size: Number of items per page
    
    Returns:
        Dictionary with success status and list of interactions
    """
    params = {}
    if contact_id:
        params["contact"] = contact_id
    if interaction_type:
        params["type"] = interaction_type
    if since:
        params["since"] = since
    if page:
        params["page"] = page
    if page_size:
        params["page_size"] = page_size
    
    return _make_request(ctx, "GET", "/crm/interactions", params=params)


@mcp.tool()
async def create_interaction(
    ctx: Context,
    contact_id: int,
    interaction_type: str,
    occurred_at: str,
    notes: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new interaction.
    
    Args:
        contact_id: The ID of the contact
        interaction_type: Type of interaction (call, email, meeting, note, etc.)
        occurred_at: When the interaction occurred (ISO format, required)
        notes: Interaction notes
        metadata: Additional metadata as dictionary
    
    Returns:
        Dictionary with success status and created interaction data
    """
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


if __name__ == "__main__":
    mcp.run()

