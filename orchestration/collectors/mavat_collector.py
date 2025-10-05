"""Mavat data collector implementation."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from orchestration.collectors.base_collector import BaseCollector
from mavat.scrapers.mavat_selenium_client import MavatSeleniumClient


class MavatCollector(BaseCollector):
    """Wrapper around :class:`MavatSeleniumClient` providing a stable API."""

    def __init__(self, client: Optional[MavatSeleniumClient] = None) -> None:
        self.client = client or MavatSeleniumClient()
        self.logger = logging.getLogger(__name__)

    def collect(self, block: str, parcel: Optional[str] = None, city: Optional[str] = None) -> List[Dict[str, Any]]:
        """Collect Mavat plans for a given block/parcel.
        
        This method implements the base collect interface and provides
        planning data from the Mavat system.
        
        Parameters
        ----------
        block: str
            Block number for cadastral search.
        parcel: str
            Parcel number for cadastral search.
        city: str, optional
            City name for additional context.
            
        Returns
        -------
        List[Dict[str, Any]]
            A list of plan summaries in consistent format.
        """
        try:
            # Search by block and parcel using Selenium client
            with self.client as client:
                plans = client.search_plans(block=block, parcel=parcel, city=city)
                
                # Convert to consistent format
                formatted_plans = []
                for plan in plans:
                    formatted_plans.append({
                        "plan_id": plan.plan_id,
                        "title": plan.title,
                        "status": plan.status,
                        "authority": plan.authority,
                        "entity_number": plan.entity_number,
                        "approval_date": plan.approval_date,
                        "status_date": plan.status_date,
                        "raw": plan.raw
                    })
                
                return formatted_plans
        except Exception:
            return []


    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for Mavat collection."""
        required_params = ['block', 'parcel']
        return all(param in kwargs for param in required_params)

if __name__ == '__main__':
    collector = MavatCollector()
    result = collector.collect(block=6336, city="תמא")
    print(result)