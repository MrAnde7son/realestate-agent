# server.py
import asyncio
from fastmcp import FastMCP, Context
from typing import Any, Dict, Optional
from ..decisive import fetch_decisive_appraisals
from ..nadlan import NadlanDealsScraper

# Create an MCP server
mcp = FastMCP("DataGovIL", dependencies=["requests"])


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


if __name__ == "__main__":
    # This code only runs when the file is executed directly
    mcp.run()
