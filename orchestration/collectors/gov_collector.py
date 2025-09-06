"""Government data collector implementation."""

from typing import Any, Dict, List, Optional

from gov.decisive import fetch_decisive_appraisals
from gov.nadlan.scraper import NadlanDealsScraper

from .base_collector import BaseCollector


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
            "decisive": self._collect_decisive(block, parcel),
            "transactions": self._collect_transactions(address),
        }

    def _collect_decisive(self, block: str, parcel: str) -> List[Dict[str, Any]]:
        """Collect decisive appraisals for a given block/parcel."""
        try:
            return self.decisive_func(block=block, plot=parcel)
        except Exception:
            return []

    def _collect_transactions(self, address: str) -> List[Dict[str, Any]]:
        """Collect transaction history for a given address."""
        try:
            deals = self.deals_client.get_deals_by_address(address)
            return [deal.to_dict() if hasattr(deal, 'to_dict') else dict(deal) for deal in deals]
        except Exception:
            return []

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for government data collection."""
        required_params = ['block', 'parcel', 'address']
        return all(param in kwargs for param in required_params)
