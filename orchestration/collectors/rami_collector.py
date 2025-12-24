"""Rami data collector implementation."""

from typing import Any, Dict, List, Optional

from gov.rami.rami_client import RamiClient

from orchestration.collectors.base_collector import BaseCollector
from orchestration.location import LocationQuery, ensure_location_query


class RamiCollector(BaseCollector):
    """Collector for RAMI plans data."""

    def __init__(self, client: Optional[RamiClient] = None) -> None:
        self.client = client or RamiClient()

    def collect(
        self, location: Optional[LocationQuery] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """Collect RAMI plans for a given block (block) and parcel (parcel)."""
        query = ensure_location_query(location)
        block = query.block
        if not block:
            raise ValueError("RamiCollector requires a block number")
        try:
            # Block search is enough for rami to cover larger area
            search_params = self.client.create_search_params(block=str(block))

            # Fetch plans using the same method as the test
            plans = self.client.fetch_plans(search_params)
            enriched_plans: List[Dict[str, Any]] = []

            for plan in plans:
                documents = self.client.extract_document_urls(plan)
                enriched_plans.append(
                    {
                        "planNumber": plan.get("planNumber", ""),
                        "planId": plan.get("planId", ""),
                        "status": plan.get("status", ""),
                        "title": plan.get("mahut", ""),
                        "documents": documents,
                        "raw": plan,
                    }
                )

            return enriched_plans
        except Exception:
            return []

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for RAMI data collection."""
        query = ensure_location_query(kwargs.get("location"))
        return bool(query.block)


if __name__ == "__main__":
    client = RamiCollector()
    plans = client.collect(LocationQuery(block=6336))
    print(plans)
