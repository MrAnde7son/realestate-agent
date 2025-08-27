"""Rami data collector implementation."""

from typing import Any, Dict, List, Optional

from rami.rami_client import RamiClient

from .base_collector import BaseCollector


class RamiCollector(BaseCollector):
    """Collector for RAMI plans data."""

    def __init__(self, client: Optional[RamiClient] = None) -> None:
        self.client = client or RamiClient()

    def collect(self, block: str, parcel: str) -> List[Dict[str, Any]]:
        """Collect RAMI plans for a given block/parcel."""
        try:
            # Search for plans by block and parcel
            plans = self.client.search_plans(block=block, parcel=parcel)
            
            # Convert to consistent format
            formatted_plans = []
            for plan in plans:
                formatted_plans.append({
                    "planNumber": plan.get("planNumber", ""),
                    "planId": plan.get("planId", ""),
                    "title": plan.get("title", ""),
                    "status": plan.get("status", ""),
                    "raw": plan
                })
            
            return formatted_plans
        except Exception:
            return []

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for RAMI data collection."""
        required_params = ['block', 'parcel']
        return all(param in kwargs for param in required_params)
