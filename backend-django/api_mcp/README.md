# Real Estate API MCP Server

FastMCP-based Model Context Protocol server for the Real Estate API integration with LLMs.

## Overview

This MCP server provides tools for accessing:
- **Assets**: Property assets and their enriched data
- **Deal Expenses**: Deals, negotiations, and offers with financial information
- **Expense Calculation**: Building construction cost estimation
- **Mortgage Calculation**: Mortgage affordability analysis
- **CRM**: Contacts, leads, tasks, meetings, and interactions

## Installation

```bash
pip install fastmcp requests
```

## Configuration

Set the following environment variables:

- `REALESTATE_API_URL`: Base URL for the API (default: `http://127.0.0.1:8000/api`)
- `REALESTATE_API_TOKEN`: Optional JWT token for authenticated requests

## Usage

Run the server:

```bash
python backend-django/mcp_server.py
```

Or use with an MCP client:

```python
from fastmcp import FastMCP
from backend_django.mcp.server import mcp

# The server is already configured with all tools
```

## Available Tools

### Assets (10 tools)

- `list_assets`: List all assets with filtering and pagination
- `get_asset`: Get detailed information for a specific asset
- `create_asset`: Create a new asset
- `sync_asset`: Trigger synchronization for an asset
- `get_asset_transactions`: Get transactions for an asset
- `get_asset_permits`: Get permits for an asset
- `get_asset_plans`: Get plans for an asset
- `get_asset_appraisal`: Get appraisal analysis for an asset
- `get_asset_listings`: Get listings for an asset
- `get_asset_documents`: Get documents for an asset

### Deal Expenses (8 tools)

- `list_deals`: List all deals with optional filtering
- `get_deal`: Get deal details
- `create_deal`: Create a new deal for an asset
- `list_negotiations`: List negotiations, optionally filtered by deal
- `get_negotiation`: Get negotiation details
- `list_offers`: List offers, optionally filtered by negotiation
- `get_offer`: Get offer details including financial information

### Expense Calculation (2 tools)

- `estimate_build_cost`: Estimate building construction costs using Dekel-style calculations
- `get_cost_options`: Get available options for cost estimation (regions, qualities, scopes)

### Mortgage Calculation (1 tool)

- `analyze_mortgage`: Analyze mortgage affordability and payment scenarios

### CRM (16 tools)

- `list_contacts`: List all contacts
- `get_contact`: Get contact details
- `create_contact`: Create a new contact
- `search_contacts`: Search contacts by name, email, phone, or tags
- `list_leads`: List all leads with optional filtering
- `get_lead`: Get lead details
- `create_lead`: Create a new lead
- `update_lead_status`: Update lead status
- `add_lead_note`: Add a note to a lead
- `list_tasks`: List all tasks with optional filtering
- `create_task`: Create a new task
- `complete_task`: Mark a task as completed
- `list_meetings`: List all meetings with optional filtering
- `create_meeting`: Create a new meeting
- `list_interactions`: List all interactions with optional filtering
- `create_interaction`: Create a new interaction

## Example Usage

### List Assets

```python
result = await list_assets(
    ctx=ctx,
    city="תל אביב",
    max_price=5000000,
    page=1
)
```

### Analyze Mortgage

```python
result = await analyze_mortgage(
    ctx=ctx,
    property_price=4500000,
    savings_total=900000,
    annual_rate_pct=4.5,
    term_years=25
)
```

### Estimate Build Cost

```python
result = await estimate_build_cost(
    ctx=ctx,
    area_m2=100,
    scope=["shell", "finish"],
    region="CENTER",
    quality="standard"
)
```

### Get Cost Options

```python
result = await get_cost_options(ctx=ctx)
```

### Create a Deal

```python
result = await create_deal(
    ctx=ctx,
    asset_id=123,
    stage="discovery",
    parties=[
        {
            "user_id": 1,
            "role": "buyer",
            "side": "buyer"
        }
    ]
)
```

### Create a Contact

```python
result = await create_contact(
    ctx=ctx,
    name="John Doe",
    email="john@example.com",
    phone="050-1234567",
    equity=1000000,
    tags=["investor", "buyer"]
)
```

## Error Handling

All tools return a dictionary with:
- `success`: Boolean indicating if the request was successful
- `data`: Response data (if successful)
- `error`: Error message (if unsuccessful)
- `status_code`: HTTP status code (if available)

## Authentication

If `REALESTATE_API_TOKEN` is set, all requests will include an `Authorization: Bearer <token>` header. Otherwise, requests will be made without authentication (which may work for public endpoints but will fail for protected ones).

## Rate Limiting

The server respects API rate limits. If you encounter rate limiting errors, wait before retrying requests.

