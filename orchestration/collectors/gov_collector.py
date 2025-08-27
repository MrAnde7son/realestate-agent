"""Government data collector implementation."""

from typing import List, Optional, Dict, Any
from .base_collector import BaseCollector
from gov.decisive import fetch_decisive_appraisals
from gov.nadlan.scraper import NadlanDealsScraper


class GovCollector(BaseCollector):
    """Collector for gov.il decisive appraisals and transaction history."""

    def __init__(
        self,
        deals_client: Optional[NadlanDealsScraper] = None,
        decisive_func=fetch_decisive_appraisals,
    ) -> None:
        self.deals_client = deals_client or NadlanDealsScraper()
        self.decisive_func = decisive_func

    def collect(self, block: str, parcel: str, address: str) -> Dict[str, Any]:
        """Collect government data for a given block/parcel and address."""
        return {
            "decisive": self.collect_decisive(block, parcel),
            "transactions": self.collect_transactions(address),
        }

    def collect_decisive(self, block: str, parcel: str) -> List[Dict[str, Any]]:
        """Collect decisive appraisals for a given block/parcel."""
        try:
            return self.decisive_func(block=block, plot=parcel)
        except Exception:
            return []

    def collect_transactions(self, address: str) -> List[Dict[str, Any]]:
        """Collect transaction history for a given address."""
        try:
            return self.deals_client.fetch_deals(address)
        except Exception:
            return []

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for government data collection."""
        required_params = ['block', 'parcel', 'address']
        return all(param in kwargs for param in required_params)
