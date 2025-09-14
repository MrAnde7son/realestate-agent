"""Rami data collector implementation."""

from typing import Any, Dict, List, Optional

from .rami_client import RamiClient

from orchestration.collectors.base_collector import BaseCollector


class RamiCollector(BaseCollector):
    """Collector for RAMI plans data."""

    def __init__(self, client: Optional[RamiClient] = None) -> None:
        self.client = client or RamiClient()

    def collect(self, block: str, parcel: str) -> List[Dict[str, Any]]:
        """Collect RAMI plans for a given block (block) and parcel (parcel)."""
        try:
            # Create search parameters using the same logic as the test
            search_params = self.client.create_search_params(block=block, parcel=parcel)
            
            # Fetch plans using the same method as the test
            plans_df = self.client.fetch_plans(search_params)
            
            # Convert DataFrame to list of dictionaries
            formatted_plans = []
            for _, plan_row in plans_df.iterrows():
                plan = plan_row.to_dict()
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
