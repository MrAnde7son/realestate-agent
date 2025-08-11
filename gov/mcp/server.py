# server.py
from fastmcp import FastMCP, Context
import requests

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


if __name__ == "__main__":
    # This code only runs when the file is executed directly
    mcp.run()
