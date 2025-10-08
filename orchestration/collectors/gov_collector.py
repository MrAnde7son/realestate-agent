"""Government data collector implementation."""

import logging
from typing import Any, Dict, List, Optional

from gov.decisive import DecisiveAppraisalClient
from gov.nadlan.scraper_selenium import NadlanDealsScraper

from orchestration.collectors.base_collector import BaseCollector
from orchestration.location import LocationQuery, ensure_location_query

logger = logging.getLogger(__name__)


class GovCollector(BaseCollector):
    """Collector for gov.il decisive appraisals and transaction history."""

    def __init__(
        self,
        deals_client: Optional[NadlanDealsScraper] = None,
        decisive_client: Optional[DecisiveAppraisalClient] = None,
        max_age_days: int = 365,
        use_cache: bool = True,
    ) -> None:
        # Use optimized scraper with caching and date filtering for performance
        self.deals_client = deals_client or NadlanDealsScraper(
            timeout=120.0, 
            max_age_days=max_age_days,
            use_cache=use_cache
        )
        self.decisive_client = decisive_client or DecisiveAppraisalClient(timeout=120.0)
        self.max_age_days = max_age_days
        self.use_cache = use_cache

    def collect(
        self,
        block: str,
        parcel: Optional[str] = None,
        location: Optional[LocationQuery] = None,
        max_age_days: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Collect government data for a given block/parcel and location.

        Args:
            block: Block number for decisive appraisals
            parcel: Parcel number (optional)
            location: Location query for transaction history
            max_age_days: Override default max age for transactions (optional)
            force_refresh: Force refresh even if cache is available (optional)
        """

        query = ensure_location_query(location)
        address = query.formatted or query.street or query.city

        return {
            "decisive": self._collect_decisive(block, parcel),
            "transactions": self._collect_transactions(address, max_age_days, force_refresh),
        }

    def _collect_decisive(self, block: str, parcel: str) -> List[Dict[str, Any]]:
        """Collect decisive appraisals for a given block/parcel."""
        try:
            # Block search is enough for decisive appraisals to cover larger area
            appraisals = self.decisive_client.fetch_appraisals(block=block)
            return [appraisal.to_dict() for appraisal in appraisals]
        except Exception as e:
            logger.error(f"Error collecting decisive appraisals: {e}")
            return []

    def _collect_transactions(self, address: str, max_age_days: Optional[int] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Collect transaction history for a given address with optional date filtering and caching."""
        try:
            logger.info(f"Fetching Nadlan transactions for: {address}")
            # Use optimized scraper with caching, API fallback, and date filtering
            deals = self.deals_client.get_deals_by_address(address, max_age_days=max_age_days, force_refresh=force_refresh)
            logger.info(f"Found {len(deals)} transactions via optimized scraper")
            return [deal.to_dict() if hasattr(deal, 'to_dict') else dict(deal) for deal in deals]
        except Exception as e:
            logger.error(f"Nadlan transaction fetch failed: {e}")
            return []

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for government data collection."""

        location = kwargs.get("location")
        return (
            bool(kwargs.get('block'))
            and isinstance(location, LocationQuery)
            and not location.is_empty()
        )

if __name__ == "__main__":
    # Example with fully optimized collector
    print("Testing optimized Nadlan transaction collection...")
    
    # Create collector with optimizations enabled
    collector = GovCollector(
        max_age_days=180,  # Only fetch deals from last 180 days
        use_cache=True,   # Enable caching for better performance
    )
    
    # Test the optimized collection
    result = collector.collect(
        block="6336", 
        location=LocationQuery("תל אביב-יפו", "רוזוב", 4),
        max_age_days=180  # Override to 180 days for this specific request
    )
    
    print(f"Found {len(result['transactions'])} recent transactions")
    print(f"Found {len(result['decisive'])} decisive appraisals")
    
    # Test cache performance - second call should be much faster
    print("\nTesting cache performance...")
    import time
    start_time = time.time()
    result2 = collector.collect(
        block="6336", 
        location=LocationQuery("תל אביב-יפו", "רוזוב", 4)
    )
    cache_time = time.time() - start_time
    print(result2)