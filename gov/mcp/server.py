# server.py
import asyncio
from typing import Any, Dict, List, Optional

from fastmcp import Context, FastMCP

from ..decisive import fetch_decisive_appraisals
from ..nadlan import NadlanDealsScraper
from ..rami.rami_client import RamiClient

# Create an MCP server
mcp = FastMCP("DataGovIL", dependencies=["requests", "pandas"])

# Persistent RAMI client for this server process
_rami_client: Optional[RamiClient] = None

def _get_rami_client() -> RamiClient:
    global _rami_client
    if _rami_client is None:
        _rami_client = RamiClient()
    return _rami_client


@mcp.tool()
async def decisive_appraisal(ctx: Context, block: str = "", plot: str = "", max_pages: int = 1):
    """Fetch decisive appraisal decisions from gov.il."""
    try:
        await ctx.info("Fetching decisive appraisal decisions...")
    except Exception:
        pass
    return fetch_decisive_appraisals(block, plot, max_pages=max_pages)


@mcp.tool()
async def fetch_nadlan_transactions(
    ctx: Context,
    address: Optional[str] = None,
    neighborhood_id: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """Fetch real estate transactions from nadlan.gov.il.

    This tool can fetch transactions by address (using autocomplete) or directly by neighborhood ID.
    
    Examples:
        
        # Fetch deals by address (automatically finds neighborhood ID)
        result = await fetch_nadlan_transactions(
            ctx=ctx,
            address="רמת החייל"
        )
        
        # Fetch deals by neighborhood ID directly
        result = await fetch_nadlan_transactions(
            ctx=ctx,
            neighborhood_id="65210036"
        )
    
    Args:
        address: Free-text address or neighborhood name (will use autocomplete to find neighborhood ID)
        neighborhood_id: Numeric neighborhood ID from nadlan.gov.il (use this if you know the ID)
        limit: Maximum number of deals to return (default: 20)
        
    Returns:
        Dict with transaction data
        
    Raises:
        RuntimeError: If the query fails or no data is found
    """
    await ctx.info("Fetching nadlan transactions...")
    
    try:
        scraper = NadlanDealsScraper()
        
        if address:
            # Use address search (automatically finds neighborhood ID)
            await ctx.info(f"Searching for address: {address}")
            deals = await asyncio.to_thread(scraper.get_deals_by_address, address)
            
            # Apply limit
            if limit > 0:
                deals = deals[:limit]
            
            deals_data = [deal.to_dict() for deal in deals]
            await ctx.info(f"Successfully found {len(deals)} deals for address: {address}")
            
            return {
                "query_type": "address",
                "address": address,
                "deals_count": len(deals),
                "deals": deals_data,
                "source": "nadlan.gov.il"
            }
            
        elif neighborhood_id:
            # Use neighborhood ID directly
            await ctx.info(f"Fetching deals for neighborhood ID: {neighborhood_id}")
            deals = await asyncio.to_thread(scraper.get_deals_by_neighborhood_id, neighborhood_id)
            
            # Apply limit
            if limit > 0:
                deals = deals[:limit]
            
            deals_data = [deal.to_dict() for deal in deals]
            await ctx.info(f"Successfully found {len(deals)} deals for neighborhood ID: {neighborhood_id}")
            
            return {
                "query_type": "neighborhood",
                "neighborhood_id": neighborhood_id,
                "deals_count": len(deals),
                "deals": deals_data,
                "source": "nadlan.gov.il"
            }
            
        else:
            raise ValueError("Either 'address' or 'neighborhood_id' must be provided")
                
    except Exception as e:
        await ctx.info(f"Error fetching transactions: {str(e)}")
        raise RuntimeError(f"Failed to fetch nadlan transactions: {e}")


@mcp.tool()
async def search_rami_plans(
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
) -> Dict[str, Any]:
    """Search for planning documents using RAMI TabaSearch API.
    
    Args:
        plan_number: Plan number to search for
        city: City code (e.g., 5000 for Tel Aviv area)
        block: block (block) number
        parcel: parcel (plot) number
        statuses: List of status codes to filter by
        plan_types: List of plan type codes to filter by
        from_status_date: Start date for status filter (YYYY-MM-DD)
        to_status_date: End date for status filter (YYYY-MM-DD)
        plan_types_used: Whether plan types filter is being used
        
    Returns:
        Dict with plan count and list of plans found
    """
    client = _get_rami_client()
    
    search_params = {
        "planNumber": plan_number,
        "city": city,
        "block": block,
        "parcel": parcel,
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
        await ctx.warning(f"Error searching RAMI plans: {str(e)}")
        return {
            "total_records": 0,
            "plans": [],
            "error": str(e),
            "search_params": search_params
        }


@mcp.tool()
async def download_rami_plan_documents(
    ctx: Context,
    plan_id: int,
    plan_number: str,
    base_dir: str = "rami_plans",
    doc_types: Optional[List[str]] = None,
    overwrite: bool = False
) -> Dict[str, Any]:
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
    client = _get_rami_client()
    
    await ctx.info(f"Downloading documents for plan {plan_number} (ID: {plan_id})")
    
    try:
        result = client.download_plan_documents(
            plan_id=plan_id,
            plan_number=plan_number,
            base_dir=base_dir,
            doc_types=doc_types,
            overwrite=overwrite
        )
        
        await ctx.info(f"Download completed: {result}")
        return result
        
    except Exception as e:
        await ctx.warning(f"Error downloading plan documents: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "plan_id": plan_id,
            "plan_number": plan_number
        }


@mcp.tool()
async def get_rami_document_types_info(ctx: Context) -> Dict[str, Any]:
    """Get information about available document types.
    
    Returns:
        Dict with document type descriptions
    """
    await ctx.info("Getting RAMI document types information")
    
    return {
        "document_types": {
            "takanon": "תקנון - Planning regulations and bylaws",
            "tasrit": "תשריט - Plan drawings and maps", 
            "nispach": "נספח - Attachments and supplementary documents",
            "mmg": "ממ\"ג - Municipal master plan documents"
        },
        "description": "Available document types for download from RAMI planning system"
    }


if __name__ == "__main__":
    mcp.run()
