"""Government data collector implementation."""

import logging
from typing import Any, Dict, List, Optional

from gov.decisive import DecisiveAppraisalClient, DecisiveAppraisal
from gov.nadlan.scraper import NadlanDealsScraper

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class GovCollector(BaseCollector):
    """Collector for gov.il decisive appraisals and transaction history."""

    def __init__(
        self,
        deals_client: Optional[NadlanDealsScraper] = None,
        decisive_client: Optional[DecisiveAppraisalClient] = None,
    ) -> None:
        # Use longer timeout for more reliable results
        self.deals_client = deals_client or NadlanDealsScraper(timeout=120.0)
        self.decisive_client = decisive_client or DecisiveAppraisalClient(timeout=120.0)

    def collect(self, block: str, parcel: str, address: str) -> Dict[str, Any]:
        """Collect government data for a given block/parcel and address."""
        return {
            "decisive": self._collect_decisive(block, parcel),
            "transactions": self._collect_transactions(address),
        }

    def _collect_decisive(self, block: str, parcel: str) -> List[Dict[str, Any]]:
        """Collect decisive appraisals for a given block/parcel."""
        try:
            appraisals = self.decisive_client.fetch_appraisals(block=block, plot=parcel)
            return [appraisal.to_dict() for appraisal in appraisals]
        except Exception as e:
            logger.error(f"Error collecting decisive appraisals: {e}")
            return []

    def _collect_transactions(self, address: str) -> List[Dict[str, Any]]:
        """Collect transaction history for a given address."""
        try:
            logger.info(f"Fetching Nadlan transactions for: {address}")
            # Fallback to address approach
            deals = self.deals_client.get_deals_by_address(address)
            logger.info(f"Found {len(deals)} transactions via address")
            return [deal.to_dict() if hasattr(deal, 'to_dict') else dict(deal) for deal in deals]
        except Exception as e:
            logger.error(f"Nadlan transaction fetch failed: {e}")
            return []

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for government data collection."""
        required_params = ['block', 'parcel', 'address']
        return all(param in kwargs for param in required_params)
