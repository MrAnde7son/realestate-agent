# Mavat MCP Server

A FastMCP-based Model Context Protocol server for integrating with the Mavat planning information system (`mavat.iplan.gov.il`).

## Overview

The Mavat MCP server provides tools for searching and retrieving planning information from Israel's national planning database. It uses Playwright to automate browser interactions and extract data from the Mavat portal.

## Features

- **Plan Search**: Free-text search across planning documents
- **Plan Details**: Retrieve comprehensive information about specific plans
- **Document Access**: Get documents associated with plans
- **GIS Layers**: Access geographic information system layers
- **Comprehensive Summaries**: Get all plan information in one call

## Installation

### Prerequisites

- Python 3.8+
- Playwright browser automation

### Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```bash
   playwright install
   ```

## Available Tools

### 1. `search_plans`

Search for plans matching a free-text query.

**Parameters:**
- `query` (str): Search term (e.g., "רמת החייל")
- `limit` (int, optional): Maximum results (default: 20)
- `headless` (bool, optional): Run browser in headless mode (default: True)

**Returns:**
- List of matching plans with metadata
- Search statistics and source information

**Example:**
```python
result = await search_plans(ctx, "רמת החייל", limit=10)
```

### 2. `get_plan_details`

Retrieve detailed information for a specific plan.

**Parameters:**
- `plan_id` (str): Unique plan identifier
- `headless` (bool, optional): Run browser in headless mode (default: True)

**Returns:**
- Complete plan information
- Status, authority, jurisdiction, and metadata

**Example:**
```python
result = await get_plan_details(ctx, "12345")
```

### 3. `get_plan_documents`

Get documents associated with a specific plan.

**Parameters:**
- `plan_id` (str): Unique plan identifier
- `headless` (bool, optional): Run browser in headless mode (default: True)

**Returns:**
- List of available documents
- Document metadata and access information

**Example:**
```python
result = await get_plan_documents(ctx, "12345")
```

### 4. `get_plan_gis_layers`

Get GIS layers associated with a specific plan.

**Parameters:**
- `plan_id` (str): Unique plan identifier
- `headless` (bool, optional): Run browser in headless mode (default: True)

**Returns:**
- List of available GIS layers
- Geographic data and metadata

**Example:**
```python
result = await get_plan_gis_layers(ctx, "12345")
```

### 5. `get_plan_summary`

Get a comprehensive summary including details, documents, and GIS layers.

**Parameters:**
- `plan_id` (str): Unique plan identifier
- `headless` (bool, optional): Run browser in headless mode (default: True)

**Returns:**
- Complete plan summary
- All available information in structured format

**Example:**
```python
result = await get_plan_summary(ctx, "12345")
```

## Usage Examples

### Basic Plan Search

```python
from mavat.mcp.server import search_plans

# Search for plans in a specific area
result = await search_plans(ctx, "רמת החייל", limit=5)

if result["success"]:
    for plan in result["plans"]:
        print(f"Plan: {plan['title']} (ID: {plan['plan_id']})")
        print(f"Status: {plan['status']}")
```

### Get Complete Plan Information

```python
from mavat.mcp.server import get_plan_summary

# Get comprehensive plan information
summary = await get_plan_summary(ctx, "12345")

if summary["success"]:
    details = summary["summary"]["details"]
    documents = summary["summary"]["documents"]
    gis_layers = summary["summary"]["gis_layers"]
    
    print(f"Plan: {details['plan_name']}")
    print(f"Documents: {len(documents)}")
    print(f"GIS Layers: {len(gis_layers)}")
```

## Error Handling

The server provides comprehensive error handling:

- **Playwright Not Installed**: Clear instructions for installation
- **Runtime Errors**: Detailed error messages with context
- **Network Issues**: Graceful fallbacks and retry logic
- **Invalid Inputs**: Validation and helpful error messages

## Configuration

### Headless Mode

By default, the browser runs in headless mode for production use. Set `headless=False` for debugging:

```python
# Debug mode - shows browser window
result = await search_plans(ctx, "query", headless=False)
```

### Rate Limiting

The server includes built-in delays to respect the target website's resources:

- Search operations: 1-2 second delays
- Plan detail retrieval: 2-3 second delays
- Document access: 1-2 second delays

## Testing

Run the test suite:

```bash
# Run all Mavat tests
pytest tests/mavat/

# Run specific test file
pytest tests/mavat/test_mcp_server.py

# Run with coverage
pytest tests/mavat/ --cov=mavat --cov-report=html
```

## Development

### Adding New Tools

1. Create the tool function with proper async signature
2. Add `@mcp.tool()` decorator
3. Include comprehensive error handling
4. Add tests in `tests/mavat/test_mcp_server.py`
5. Update this README

### Testing New Features

1. Create unit tests with mocked dependencies
2. Add integration tests for real functionality
3. Ensure proper error handling coverage
4. Test with and without Playwright

## Troubleshooting

### Common Issues

1. **Playwright Not Installed**
   - Install: `pip install playwright && playwright install`
   - Verify browser binaries are available

2. **Browser Launch Failures**
   - Check system dependencies (X11, etc.)
   - Try running with `headless=False` for debugging

3. **Network Timeouts**
   - Increase timeout values in scraper
   - Check network connectivity to mavat.iplan.gov.il

4. **Import Errors**
   - Verify Python path includes mavat package
   - Check all dependencies are installed

### Debug Mode

Enable debug mode for troubleshooting:

```python
# Show browser window and detailed logging
result = await search_plans(ctx, "query", headless=False)
```

## License

This project is part of the realestate-agent toolkit. See the main project LICENSE for details.

## Contributing

1. Follow the existing code style and patterns
2. Add comprehensive tests for new functionality
3. Update documentation for new features
4. Ensure error handling follows established patterns
5. Test with both Playwright available and unavailable scenarios

