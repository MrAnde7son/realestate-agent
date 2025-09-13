"""Rami data collector implementation."""

from typing import Any, Dict, List, Optional

from gov.rami.rami_client import RamiClient

from .base_collector import BaseCollector


class RamiCollector(BaseCollector):
    """Collector for RAMI plans data."""

    def __init__(self, client: Optional[RamiClient] = None) -> None:
        self.client = client or RamiClient()

    def collect(self, gush: str, chelka: str) -> List[Dict[str, Any]]:
        """Collect RAMI plans for a given gush (block) and chelka (parcel)."""
        try:
            # Create search parameters using the same logic as the test
            search_params = self.client.create_search_params(gush=gush, chelka=chelka)
            
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
        required_params = ['gush', 'chelka']
        return all(param in kwargs for param in required_params)
