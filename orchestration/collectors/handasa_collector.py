from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from handasa.client import HandasaClient

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class HandasaCollector(BaseCollector):
    """Collector that wraps :class:`HandasaClient` for pipeline usage."""

    def __init__(self, client: Optional[HandasaClient] = None) -> None:
        self.client = client or HandasaClient()

    def collect(self, block: str, parcel: Optional[str] = None) -> List[Dict[str, Any]]:
        if not block:
            raise ValueError("HandasaCollector requires a block number")

        try:
            return self.client.get_permits(block, parcel)
        except Exception:
            logger.exception("Failed to fetch Handasa permits for block %s parcel %s", block, parcel)
            raise

    def validate_parameters(self, **kwargs) -> bool:
        block = kwargs.get("block")
        return bool(str(block or "").strip())


__all__ = ["HandasaCollector"]
