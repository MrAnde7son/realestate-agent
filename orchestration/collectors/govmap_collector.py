# -*- coding: utf-8 -*-
"""
GovMap collector that plugs into your existing orchestration layer.

Usage
-----
from govmap import GovMapClient
from orchestration.collectors.govmap_collector import GovMapCollector

collector = GovMapCollector(GovMapClient())
# Example (re-using TelAvivGS geocoder if available):
# x,y = TelAvivGS().get_address_coordinates("רוזוב", 14)
# data = collector.collect(x=x, y=y)
"""
from typing import Any, Dict, Optional

from .base_collector import BaseCollector
from govmap.api_client import GovMapClient


class GovMapCollector(BaseCollector):
    """Collects national-level parcel + nearby layers from GovMap OpenData."""

    def __init__(self, client: Optional[GovMapClient] = None) -> None:
        self.client = client or GovMapClient()

    def autocomplete(self, query: str) -> Dict[str, Any]:
        """Get autocomplete results for an address query.
        
        Parameters
        ----------
        query : Address query string
        
        Returns
        -------
        Dict containing autocomplete results
        """
        return self.client.autocomplete(query)

    def collect(
        self,
        *,
        x: float,
        y: float,
    ) -> Dict[str, Any]:
        """Collect data from GovMap using the new API endpoints.

        Parameters
        ----------
        x, y : EPSG:2039 coordinates of the target point.
        """
        out: Dict[str, Any] = {
            "x": x,
            "y": y,
            "api_data": {},
        }

        # Collect data from all new API endpoints
        try:
            # Get parcel data from new API
            parcel_api_data = self.client.get_parcel_data(x, y)
            out["api_data"]["parcel"] = parcel_api_data
        except Exception as e:
            # Log but don't fail the entire collection
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to get parcel data from new API: {e}")

        try:
            # Get layers catalog
            layers_catalog = self.client.get_layers_catalog()
            out["api_data"]["layers_catalog"] = layers_catalog
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to get layers catalog: {e}")

        try:
            # Get search types
            search_types = self.client.get_search_types()
            out["api_data"]["search_types"] = search_types
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to get search types: {e}")

        try:
            # Get base layers
            base_layers = self.client.get_base_layers()
            out["api_data"]["base_layers"] = base_layers
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to get base layers: {e}")

        return out

    def validate_parameters(self, **kwargs) -> bool:
        return isinstance(kwargs.get("x"), (int, float)) and isinstance(kwargs.get("y"), (int, float))
