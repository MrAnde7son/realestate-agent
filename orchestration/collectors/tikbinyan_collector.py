"""Collectors for municipal tikbinyan (building files) portals."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from handasa.tikbinyan_client import (
    BatYamTikbinyanClient,
    HerzliyaTikbinyanClient,
    RamatGanTikbinyanClient,
    TikbinyanClient,
)

from orchestration.collectors.base_collector import BaseCollector
from orchestration.location import LocationQuery, ensure_location_query

logger = logging.getLogger(__name__)


class TikbinyanCollector(BaseCollector):
    """Base collector for tikbinyan portals."""

    def __init__(self, client: TikbinyanClient) -> None:
        """Initialize the collector with a tikbinyan client."""
        self.client = client

    def collect(
        self,
        location: Optional[LocationQuery] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Collect building info and permits from tikbinyan portal.
        
        Args:
            location: Location query with block, parcel, or building_id
            **kwargs: Additional parameters (building_id, address, etc.)
            
        Returns:
            List of building info and permit documents
        """
        query = ensure_location_query(location)
        
        # Try building_id first (from kwargs only, as LocationQuery doesn't have building_id)
        building_id = kwargs.get("building_id")
        
        # Try block/parcel
        block = query.block
        parcel = query.parcel
        
        # Try address
        address = kwargs.get("address")
        if not address and query.street:
            address_parts = [query.street]
            if query.house_number:
                address_parts.append(str(query.house_number))
            address = " ".join(address_parts)
        
        try:
            return self.client.get_building_info(
                building_id=building_id,
                block=str(block) if block else None,
                parcel=str(parcel) if parcel else None,
                address=address,
            )
        except Exception as e:
            logger.exception(
                "Failed to fetch tikbinyan data for building_id=%s block=%s parcel=%s address=%s",
                building_id,
                block,
                parcel,
                address,
            )
            raise

    def validate_parameters(self, **kwargs) -> bool:
        """Validate parameters for collection."""
        location = ensure_location_query(kwargs.get("location"))
        building_id = kwargs.get("building_id")
        block = location.block
        address = kwargs.get("address") or location.street
        
        return bool(building_id or block or address)


class BatYamTikbinyanCollector(TikbinyanCollector):
    """Collector for Bat Yam tikbinyan portal."""

    def __init__(self, client: Optional[BatYamTikbinyanClient] = None) -> None:
        super().__init__(client or BatYamTikbinyanClient())


class HerzliyaTikbinyanCollector(TikbinyanCollector):
    """Collector for Herzliya tikbinyan portal."""

    def __init__(self, client: Optional[HerzliyaTikbinyanClient] = None) -> None:
        super().__init__(client or HerzliyaTikbinyanClient())


class RamatGanTikbinyanCollector(TikbinyanCollector):
    """Collector for Ramat Gan tikbinyan portal."""

    def __init__(self, client: Optional[RamatGanTikbinyanClient] = None) -> None:
        super().__init__(client or RamatGanTikbinyanClient())


__all__ = [
    "TikbinyanCollector",
    "BatYamTikbinyanCollector",
    "HerzliyaTikbinyanCollector",
    "RamatGanTikbinyanCollector",
]


if __name__ == "__main__":
    # Example usage
    collector = BatYamTikbinyanCollector()
    result = collector.collect(location=LocationQuery(building_id="3802"))
    print(result)

