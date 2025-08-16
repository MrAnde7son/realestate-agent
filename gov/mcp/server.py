# server.py
from fastmcp import FastMCP, Context
import requests
from typing import Any, Dict, Optional

from .constants import (
    CKAN_BASE_URL,
    USER_AGENT,
    DEFAULT_TIMEOUT,
    SEARCH_TIMEOUT,
    get_popular_tags,
    get_tag_suggestions,
    get_tags_by_category,
    search_tags,
)
from .decisive import fetch_decisive_appraisals
from .transactions import RealEstateTransactions

# Create an MCP server
mcp = FastMCP("DataGovIL", dependencies=["requests"])

HEADERS = {"User-Agent": USER_AGENT}


def _request(method: str, endpoint: str, *, params=None, timeout: int = DEFAULT_TIMEOUT):
    """Helper to call the CKAN API with default headers and timeouts."""
    url = f"{CKAN_BASE_URL}/{endpoint}"
    response = requests.request(method, url, params=params, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.json()


@mcp.tool()
async def status_show(ctx: Context):
    """Get the CKAN version and a list of installed extensions."""
    await ctx.info("Fetching CKAN status...")
    return _request("post", "status_show")


@mcp.tool()
async def license_list(ctx: Context):
    """Get the list of licenses available for datasets on the site."""
    await ctx.info("Fetching license list...")
    return _request("get", "license_list")


@mcp.tool()
async def package_list(ctx: Context):
    """Get a list of all package IDs (datasets)."""
    await ctx.info("Fetching package list...")
    return _request("get", "package_list")


@mcp.tool()
async def package_search(ctx: Context, q: str = "", fq: str = "",
                         sort: str = "", rows: int = 20, start: int = 0,
                         include_private: bool = False):

    """Find packages (datasets) matching query terms."""
    await ctx.info("Searching for packages...")
    params = {
        "q": q,
        "fq": fq,
        "sort": sort,
        "rows": rows,
        "start": start,
        "include_private": include_private
    }
    return _request("get", "package_search", params=params, timeout=SEARCH_TIMEOUT)


@mcp.tool()
async def package_show(ctx: Context, id: str):
    """Get metadata about one specific package (dataset)."""
    await ctx.info(f"Fetching metadata for package: {id}")
    params = {"id": id}
    return _request("get", "package_show", params=params)


@mcp.tool()
async def organization_list(ctx: Context, all_fields: bool = False):
    """Get names of all organizations or full details when all_fields=True."""
    await ctx.info("Fetching organization list...")
    params = {"all_fields": all_fields}
    return _request("get", "organization_list", params=params)


@mcp.tool()
async def organization_show(ctx: Context, id: str):
    """Get details of a specific organization."""
    await ctx.info(f"Fetching details for organization: {id}")
    params = {"id": id}
    return _request("get", "organization_show", params=params)


@mcp.tool()
async def tag_list(ctx: Context):
    """Get the list of tags available for datasets."""
    await ctx.info("Fetching tag list...")
    return _request("get", "tag_list")


@mcp.tool()
async def tag_show(ctx: Context, id: str):
    """Get details for a specific tag."""
    await ctx.info(f"Fetching details for tag: {id}")
    params = {"id": id}
    return _request("get", "tag_show", params=params)


@mcp.tool()
async def tag_search(ctx: Context, query: str = "", limit: int = 10, offset: int = 0):
    """Search for tags matching query terms."""
    await ctx.info("Searching for tags...")
    params = {"q": query, "limit": limit, "offset": offset}
    return _request("get", "tag_search", params=params, timeout=SEARCH_TIMEOUT)


@mcp.tool()
async def tags_by_category(ctx: Context, category: str):
    """Return tag objects for a given category."""
    await ctx.info(f"Getting tags for category: {category}")
    return get_tags_by_category(category)


@mcp.tool()
async def local_tag_search(ctx: Context, keyword: str):
    """Search local tag metadata for a keyword."""
    await ctx.info(f"Searching tags locally for: {keyword}")
    return search_tags(keyword)


@mcp.tool()
async def popular_tags(ctx: Context, limit: int = 10):
    """Return popular tags from local metadata."""
    await ctx.info("Fetching popular tags from local metadata")
    return get_popular_tags(limit)


@mcp.tool()
async def tag_suggestions(ctx: Context, theme: str):
    """Return tag suggestions for a given theme."""
    await ctx.info(f"Fetching tag suggestions for theme: {theme}")
    return get_tag_suggestions(theme)


@mcp.tool()
async def decisive_appraisal(ctx: Context, block: str = "", plot: str = "", max_pages: int = 1):
    """Fetch decisive appraisal decisions from gov.il."""
    try:
        await ctx.info("Fetching decisive appraisal decisions...")
    except Exception:
        pass
    return fetch_decisive_appraisals(block, plot, max_pages=max_pages)


@mcp.tool()
async def resource_search(ctx: Context, query: str = "", order_by: str = "",
                          offset: int = 0, limit: int = 100):
    """Find resources based on their field values."""
    await ctx.info("Searching for resources...")
    params = {
        "query": query,
        "order_by": order_by,
        "offset": offset,
        "limit": limit
    }
    return _request("get", "resource_search", params=params, timeout=SEARCH_TIMEOUT)


@mcp.tool()
async def datastore_search(ctx: Context, resource_id: str, q: str = "",
                           distinct: bool = False, plain: bool = True,
                           limit: int = 100, offset: int = 0, fields: str = "",
                           sort: str = "", include_total: bool = True,
                           records_format: str = "objects"):
    """Search a datastore resource."""
    await ctx.info(f"Searching datastore for resource: {resource_id}")
    params = {
        "resource_id": resource_id,
        "q": q,
        "distinct": distinct,
        "plain": plain,
        "limit": limit,
        "offset": offset,
        "fields": fields,
        "sort": sort,
        "include_total": include_total,
        "records_format": records_format
    }
    return _request("get", "datastore_search", params=params, timeout=SEARCH_TIMEOUT)


@mcp.tool()
def fetch_data(dataset_name: str, limit: int = 100, offset: int = 0):
    """Fetch data from public API based on a dataset name query"""
    def find_resource_id(name):
        params = {"id": name}
        data = _request("get", "package_show", params=params)
        resources = data.get("result", {}).get("resources", [])
        if resources:
            return resources[0].get("id")
        return None

    resource_id = find_resource_id(dataset_name)
    if not resource_id:
        return {"error": f"No dataset found matching '{dataset_name}'"}

    params = {"resource_id": resource_id, "limit": limit, "offset": offset}
    data = _request("get", "datastore_search", params=params, timeout=SEARCH_TIMEOUT)

    if data.get("success"):
        return data["result"]["records"]
    raise Exception(data.get("error", "Unknown error occurred"))


@mcp.tool()
async def fetch_comparable_transactions(
    ctx: Context,
    x: float, 
    y: float,
    street: str,
    house: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    target_area: Optional[float] = None,
    limit: int = 2000,
    top: int = 20,
) -> Dict[str, Any]:
    """Fetch comparable Tel-Aviv real-estate transactions from data.gov.il.

    Locates the active real-estate transactions dataset on data.gov.il 
    and returns basic statistics along with the top-N comparable transactions.
    
    Example:
        # Fetch comparables for הגולן 1, תל אביב (Block 6638, Plot 96)
        # First get coordinates using Tel Aviv GIS: x=184320.94, y=668548.65 (EPSG:2039)
        
        result = await fetch_comparable_transactions(
            ctx=ctx,
            x=184320.94, y=668548.65,
            street="הגולן",
            house=1,
            date_from="2020-01-01",  # Optional: filter by date range
            date_to="2025-12-31",
            target_area=80.0,        # Optional: filter by similar area (±20%)
            top=15                   # Top 15 closest comparables
        )
        
        # Expected output for הגולן 1 area:
        # Based on government data (Ministry of Housing public housing purchases):
        # - Recent transactions (2023-2025): ₪2.1-2.6M for 3-4 room apartments
        # - Price per sqm: ~₪27,000-33,000
        # - Block 6638 has decisive appraiser decisions available
    
    Args:
        x: X coordinate in EPSG:2039
        y: Y coordinate in EPSG:2039
        street: Street name for reference
        house: House number for reference
        date_from: Start date filter (YYYY-MM-DD), optional
        date_to: End date filter (YYYY-MM-DD), optional  
        target_area: Filter by apartment area ±20% tolerance, optional
        limit: Max records to fetch from data.gov.il (default: 2000)
        top: Number of top comparable transactions to return (default: 20)
        
    Returns:
        Dict with 'stats' (median/avg prices) and 'comps' (comparable transactions)
        
    Raises:
        RuntimeError: If no transaction dataset found on data.gov.il
    """
    await ctx.info(f"Fetching comparable transactions for {street} {house}")
    
    # Use the transactions module to handle all the business logic
    transactions = RealEstateTransactions()
    
    try:
        result = transactions.fetch_comparable_transactions(
            x=x, y=y, street=street, house=house,
            date_from=date_from, date_to=date_to, target_area=target_area,
            limit=limit, top=top
        )
        
        stats = result["stats"]
        comps_count = len(result["comps"])
        await ctx.info(f"Successfully found {comps_count} comparable transactions")
        await ctx.info(f"Median price per sqm: ₪{stats.get('median_price_sqm', 0):,.0f}")
        
        return result
        
    except Exception as e:
        await ctx.info(f"Error fetching transactions: {str(e)}")
        raise


if __name__ == "__main__":
    # This code only runs when the file is executed directly
    mcp.run()
