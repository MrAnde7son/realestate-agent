# server.py
from fastmcp import FastMCP, Context
import requests
from typing import Any, Dict, Optional

from ..constants import (
    CKAN_BASE_URL,
    USER_AGENT,
    DEFAULT_TIMEOUT,
    SEARCH_TIMEOUT,
    get_popular_tags,
    get_tag_suggestions,
    get_tags_by_category,
    search_tags,
)
from ..decisive import fetch_decisive_appraisals
from ..nadlan_deals_scraper import NadlanDealsScraper

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
    return _request("get", "tag_show", params={"id": id})


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
async def fetch_nadlan_transactions(
    ctx: Context,
    query_type: str = "address",
    address: Optional[str] = None,
    neighborhood_id: Optional[str] = None,
    x: Optional[float] = None,
    y: Optional[float] = None,
    street: Optional[str] = None,
    house: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    target_area: Optional[float] = None,
    top: int = 20,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Fetch real estate transactions from nadlan.gov.il.

    This unified tool can fetch transactions by address, neighborhood ID, or coordinates,
    and optionally analyze them for comparable transactions with statistical analysis.
    
    Examples:
        
        # Fetch deals by address
        result = await fetch_nadlan_transactions(
            ctx=ctx,
            query_type="address",
            address="שכונת רמת החייל, תל אביב"
        )
        
        # Fetch deals by neighborhood ID
        result = await fetch_nadlan_transactions(
            ctx=ctx,
            query_type="neighborhood",
            neighborhood_id="65210036"
        )
        
        # Fetch comparable transactions with analysis
        result = await fetch_nadlan_transactions(
            ctx=ctx,
            query_type="comparable",
            x=184320.94, y=668548.65,  # EPSG:2039 coordinates
            street="הגולן", house=1,
            date_from="2020-01-01",
            date_to="2025-12-31",
            target_area=80.0,
            top=15
        )
    
    Args:
        query_type: Type of query - "address", "neighborhood", or "comparable"
        address: Free-text address or neighborhood name (for address queries)
        neighborhood_id: Numeric neighborhood ID from nadlan.gov.il (for neighborhood queries)
        x: X coordinate in EPSG:2039 (for comparable queries)
        y: Y coordinate in EPSG:2039 (for comparable queries)
        street: Street name for reference (for comparable queries)
        house: House number for reference (for comparable queries)
        date_from: Start date filter (YYYY-MM-DD), optional
        date_to: End date filter (YYYY-MM-DD), optional
        target_area: Filter by apartment area ±20% tolerance, optional
        top: Number of top transactions to return (default: 20)
        timeout: Request timeout in seconds (default: 10.0)
        
    Returns:
        Dict with transaction data and optional statistics
        
    Raises:
        RuntimeError: If the query fails or no data is found
    """
    await ctx.info(f"Fetching nadlan transactions with query type: {query_type}")
    
    try:
        with NadlanDealsScraper(timeout=timeout) as scraper:
            if query_type == "address":
                if not address:
                    raise ValueError("Address is required for address queries")
                
                deals = scraper.get_deals_by_address(address)
                deals_data = [deal.to_dict() for deal in deals]
                
                await ctx.info(f"Successfully found {len(deals)} deals for address: {address}")
                return {
                    "query_type": "address",
                    "address": address,
                    "deals_count": len(deals),
                    "deals": deals_data
                }
                
            elif query_type == "neighborhood":
                if not neighborhood_id:
                    raise ValueError("Neighborhood ID is required for neighborhood queries")
                
                deals = scraper.get_deals_by_neighborhood_id(neighborhood_id)
                deals_data = [deal.to_dict() for deal in deals]
                
                await ctx.info(f"Successfully found {len(deals)} deals for neighborhood ID: {neighborhood_id}")
                return {
                    "query_type": "neighborhood",
                    "neighborhood_id": neighborhood_id,
                    "deals_count": len(deals),
                    "deals": deals_data
                }
                
            elif query_type == "comparable":
                if not all([x, y, street, house]):
                    raise ValueError("Coordinates (x, y), street, and house are required for comparable queries")
                
                result = scraper.fetch_comparable_transactions(
                    x=x, y=y, street=street, house=house,
                    date_from=date_from, date_to=date_to,
                    target_area=target_area, top=top
                )
                
                stats = result["stats"]
                comps_count = len(result["comps"])
                await ctx.info(f"Successfully found {comps_count} comparable transactions")
                
                if stats.get("median_price_sqm"):
                    await ctx.info(f"Median price per sqm: ₪{stats.get('median_price_sqm', 0):,.0f}")
                
                return {
                    "query_type": "comparable",
                    "coordinates": {"x": x, "y": y},
                    "location": {"street": street, "house": house},
                    "filters": {
                        "date_from": date_from,
                        "date_to": date_to,
                        "target_area": target_area
                    },
                    "stats": stats,
                    "comparable_transactions": result["comps"]
                }
                
            else:
                raise ValueError(f"Invalid query_type: {query_type}. Must be 'address', 'neighborhood', or 'comparable'")
                
    except Exception as e:
        await ctx.info(f"Error fetching transactions: {str(e)}")
        raise RuntimeError(f"Failed to fetch nadlan transactions: {e}")


if __name__ == "__main__":
    # This code only runs when the file is executed directly
    mcp.run()
