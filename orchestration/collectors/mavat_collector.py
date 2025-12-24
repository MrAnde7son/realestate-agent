"""Mavat data collector implementation."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from orchestration.collectors.base_collector import BaseCollector
from mavat.scrapers.mavat_selenium_client import MavatSeleniumClient
from orchestration.location import LocationQuery, ensure_location_query


class MavatCollector(BaseCollector):
    """Wrapper around :class:`MavatSeleniumClient` providing a stable API."""

    def __init__(self, client: Optional[MavatSeleniumClient] = None) -> None:
        self.client = client or MavatSeleniumClient()
        self.logger = logging.getLogger(__name__)

    def collect(
        self,
        location: Optional[LocationQuery] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Collect Mavat plans for a given block/parcel.

        This method implements the base collect interface and provides
        planning data from the Mavat system.

        Parameters
        ----------
        location: LocationQuery
        limit: int, optional
            Maximum number of plans to return. Defaults to no explicit limit.

        Returns
        -------
        List[Dict[str, Any]]
            A list of plan summaries in consistent format.
        """
        query = ensure_location_query(location)
        block = query.block
        city = query.city
        if not block:
            raise ValueError("MavatCollector requires a block number")

        try:
            # Block search is enough for mavat to cover larger area
            with self.client as client:
                plans = client.search_plans(block=block, city=city, limit=limit)

                # Convert to consistent format
                formatted_plans = []
                for plan in plans:
                    formatted_plans.append(
                        {
                            "plan_id": plan.plan_id,
                            "title": plan.title,
                            "status": plan.status,
                            "authority": plan.authority,
                            "entity_number": plan.entity_number,
                            "approval_date": plan.approval_date,
                            "status_date": plan.status_date,
                        }
                    )

                return formatted_plans
        except Exception:
            return []

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for Mavat collection."""
        query = ensure_location_query(
            kwargs.get("location"),
        )
        block = query.block
        return bool(block)


if __name__ == "__main__":
    collector = MavatCollector()
    result = collector.collect(LocationQuery(block=6336))
    print(result)
