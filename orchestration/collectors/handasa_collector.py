from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from handasa.client import HandasaClient

from orchestration.collectors.base_collector import BaseCollector
from orchestration.location import LocationQuery, ensure_location_query

logger = logging.getLogger(__name__)


class HandasaCollector(BaseCollector):
    """Collector that wraps :class:`HandasaClient` for pipeline usage."""

    def __init__(self, client: Optional[HandasaClient] = None) -> None:
        self.client = client or HandasaClient()

    def collect(
        self, location: Optional[LocationQuery] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        query = ensure_location_query(location)
        block = query.block
        parcel = query.parcel
        if not block:
            raise ValueError("HandasaCollector requires a block number")
        try:
            return self.client.get_archive(str(block), str(parcel))
        except Exception:
            logger.exception(
                "Failed to fetch Handasa archive for block %s parcel %s", block, parcel
            )
            raise

    def validate_parameters(self, **kwargs) -> bool:
        location = ensure_location_query(
            kwargs.get("location"),
        )
        block = location.block
        return bool(block)


__all__ = ["HandasaCollector"]


if __name__ == "__main__":
    collector = HandasaCollector()
    result = collector.collect(LocationQuery(block=6952, parcel=127))
    print(result)
