"""Government data collector implementation."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from gov.decisive import DecisiveAppraisalClient
from gov.nadlan.scraper_selenium import NadlanDealsScraper
from govmap.api_client import GovMapClient

from orchestration.collectors.base_collector import BaseCollector
from orchestration.location import LocationQuery, ensure_location_query

logger = logging.getLogger(__name__)


class GovCollector(BaseCollector):
    """Collector for gov.il decisive appraisals and transaction history."""

    def __init__(
        self,
        deals_client: Optional[NadlanDealsScraper] = None,
        decisive_client: Optional[DecisiveAppraisalClient] = None,
        govmap_client: Optional[GovMapClient] = None,
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
        self.govmap_client = govmap_client or GovMapClient()
        self.max_age_days = max_age_days
        self.use_cache = use_cache

    def collect(
        self,
        location: Optional[LocationQuery] = None,
        max_age_days: Optional[int] = None,
        force_refresh: bool = False,
        x_itm: Optional[float] = None,
        y_itm: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Collect government data for a given block/parcel and location.

        Args:
            location: Location query for transaction history
            max_age_days: Override default max age for transactions (optional)
            force_refresh: Force refresh even if cache is available (optional)
            x_itm: ITM X coordinate for GovMap deals lookup (optional)
            y_itm: ITM Y coordinate for GovMap deals lookup (optional)
        """

        query = ensure_location_query(location)
        block = query.block
        parcel = query.parcel
        address = query.formatted or query.street or query.city

        # Collect Nadlan transactions
        nadlan_transactions = self._collect_transactions(address, max_age_days, force_refresh)
        
        # Collect GovMap deals if coordinates are available
        govmap_transactions = []
        if x_itm is not None and y_itm is not None:
            govmap_transactions = self._collect_govmap_deals(x_itm, y_itm, max_age_days)
        
        # Merge and deduplicate transactions (prefer Nadlan when duplicates exist)
        all_transactions = self._merge_and_deduplicate_transactions(
            nadlan_transactions, 
            govmap_transactions
        )

        return {
            "decisive": self._collect_decisive(block, parcel),
            "transactions": all_transactions,
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

    def _collect_govmap_deals(self, x_itm: float, y_itm: float, max_age_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Collect GovMap deals by location (returns Deal objects converted to dicts)."""
        try:
            logger.info(f"Fetching GovMap deals for location: ({x_itm}, {y_itm})")
            
            # Calculate date range if max_age_days is provided
            start_date = "1998-01"  # Default start date
            end_date = datetime.now().strftime("%Y-%m")  # Current month
            
            if max_age_days:
                from datetime import timedelta
                cutoff_date = datetime.now() - timedelta(days=max_age_days)
                start_date = cutoff_date.strftime("%Y-%m")
            
            # Fetch deals from GovMap (returns Deal objects)
            deal_objects = self.govmap_client.get_deals_by_location(
                x=x_itm,
                y=y_itm,
                radius=100.0,  # 100 meter radius
                start_date=start_date,
                end_date=end_date,
                limit=100,  # Get more deals per polygon
                offset=0,
            )
            
            # Convert Deal objects to dicts for deduplication and processing
            transactions = []
            for deal_obj in deal_objects:
                if hasattr(deal_obj, 'to_dict'):
                    # Deal object - convert to dict
                    transaction_dict = deal_obj.to_dict()
                    # Add source identifier
                    transaction_dict['source'] = 'govmap'
                    # Add raw data if available
                    if hasattr(deal_obj, 'raw') and deal_obj.raw:
                        transaction_dict['raw'] = deal_obj.raw
                    transactions.append(transaction_dict)
                elif isinstance(deal_obj, dict):
                    # Already a dict (fallback case)
                    transaction_dict = deal_obj.copy()
                    transaction_dict['source'] = 'govmap'
                    transactions.append(transaction_dict)
            
            logger.info(f"Found {len(transactions)} GovMap transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"GovMap deals fetch failed: {e}")
            return []

    def _merge_and_deduplicate_transactions(
        self, 
        nadlan_transactions: List[Dict[str, Any]], 
        govmap_transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge transactions from Nadlan and GovMap, removing duplicates.
        
        Deduplication strategy:
        Uses normalized date + amount + area + location (gush/parcel) to identify duplicates.
        Prefers Nadlan data when duplicates are found (more complete).
        
        Handles both Nadlan and GovMap field names:
        - Nadlan: parcel_block, parcel_parcel, parcel_sub_parcel
        - GovMap: gush_num, parcel_num, sub_parcel_num
        
        Args:
            nadlan_transactions: List of transactions from Nadlan
            govmap_transactions: List of transactions from GovMap
            
        Returns:
            Merged and deduplicated list of transactions
        """
        # Track seen transactions by unique key
        seen_keys = set()
        merged_transactions = []
        
        # First, add all Nadlan transactions (preferred source)
        for transaction in nadlan_transactions:
            # Normalize date for Nadlan transactions if not already normalized
            if "deal_date_normalized" not in transaction and transaction.get("deal_date"):
                try:
                    # Try DD/MM/YYYY format (Nadlan)
                    date_obj = datetime.strptime(transaction["deal_date"], "%d/%m/%Y")
                    transaction["deal_date_normalized"] = date_obj.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    pass
            
            unique_key = self._generate_transaction_key(transaction)
            if unique_key and unique_key not in seen_keys:
                seen_keys.add(unique_key)
                # Ensure source is set
                if "source" not in transaction:
                    transaction["source"] = "nadlan"
                merged_transactions.append(transaction)
            elif unique_key:
                logger.debug(f"Skipping duplicate Nadlan transaction: {unique_key}")
        
        # Then, add GovMap transactions that are not duplicates
        for transaction in govmap_transactions:
            unique_key = self._generate_transaction_key(transaction)
            if unique_key and unique_key not in seen_keys:
                seen_keys.add(unique_key)
                merged_transactions.append(transaction)
                logger.debug(f"Added GovMap transaction: {unique_key}")
            elif unique_key:
                logger.debug(f"Skipping duplicate GovMap transaction: {unique_key}")
        
        logger.info(
            f"Merged transactions: {len(nadlan_transactions)} Nadlan + "
            f"{len(govmap_transactions)} GovMap -> {len(merged_transactions)} unique"
        )
        
        return merged_transactions

    def _generate_transaction_key(self, transaction: Dict[str, Any]) -> Optional[str]:
        """Generate a unique key for a transaction to identify duplicates.
        
        Strategy: 
            Use normalized date + amount + area + location
        
        Handles both Nadlan and GovMap field names:
        - Nadlan: parcel_block, parcel_parcel, parcel_sub_parcel
        - GovMap: gush_num, parcel_num, sub_parcel_num
        
        Returns:
            Unique key string or None if insufficient data
        """
        # Normalize date for comparison
        deal_date = transaction.get("deal_date_normalized")
        if not deal_date:
            deal_date = transaction.get("deal_date")
            if deal_date:
                # Try to normalize date format
                try:
                    # Try DD/MM/YYYY format (Nadlan)
                    date_obj = datetime.strptime(deal_date, "%d/%m/%Y")
                    deal_date = date_obj.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    # Try YYYY-MM-DD format
                    try:
                        date_obj = datetime.strptime(deal_date, "%Y-%m-%d")
                        deal_date = date_obj.strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        deal_date = None
        
        deal_amount = transaction.get("deal_amount")
        area = transaction.get("area")
        
        # Get location information - handle both Nadlan and GovMap field names
        # Nadlan uses: parcel_block, parcel_parcel, parcel_sub_parcel
        # GovMap uses: gush_num, parcel_num, sub_parcel_num
        block = transaction.get("parcel_block") or transaction.get("gush_num")
        parcel = transaction.get("parcel_parcel") or transaction.get("parcel_num")
        sub_parcel = transaction.get("parcel_sub_parcel") or transaction.get("sub_parcel_num")
        
        # If we have date, amount, and location, create a key
        if deal_date and deal_amount is not None:
            # Round amount to nearest 1000 for fuzzy matching
            amount_rounded = round(deal_amount / 1000) * 1000 if deal_amount else None
            
            # Prefer location-based key if available (most reliable)
            if block and parcel:
                # Use location-based key (gush + parcel)
                if sub_parcel:
                    return f"date:{deal_date}|amount:{amount_rounded}|gush:{block}|parcel:{parcel}|sub:{sub_parcel}"
                else:
                    return f"date:{deal_date}|amount:{amount_rounded}|gush:{block}|parcel:{parcel}"
            elif area is not None:
                # Use area-based key (round to nearest 5 sqm)
                area_rounded = round(area / 5) * 5
                return f"date:{deal_date}|amount:{amount_rounded}|area:{area_rounded}"
            else:
                # Use basic date + amount key (least reliable)
                return f"date:{deal_date}|amount:{amount_rounded}"
        
        # If we have insufficient data, return None
        logger.debug(
            f"Cannot generate unique key for transaction: date={deal_date}, "
            f"amount={deal_amount}, area={area}, block={block}, parcel={parcel}"
        )
        return None

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for government data collection."""

        location = ensure_location_query(kwargs.get("location"))
        return bool(location.block)

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
        location=LocationQuery("תל אביב-יפו", "רוזוב", 4)
    )
    cache_time = time.time() - start_time
    print(result2)
