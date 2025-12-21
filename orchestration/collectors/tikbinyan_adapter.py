"""Composable tikbinyan adapter layer for multi-city coverage.

This module introduces a lightweight OOP abstraction for municipal tikbinyan
(building files) data collection. Each adapter declares the cities it supports
and exposes a common ``collect`` signature so the orchestration layer can route
requests to the right data source.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional

from handasa.tikbinyan_client import (
    BatYamTikbinyanClient,
    HerzliyaTikbinyanClient,
    RamatGanTikbinyanClient,
    TikbinyanClient,
)

from orchestration.collectors.base_collector import BaseCollector
from orchestration.location import LocationQuery, ensure_location_query

logger = logging.getLogger(__name__)


class TikbinyanAdapter(ABC):
    """Abstract base class for tikbinyan adapters."""

    supported_cities: Iterable[str] = ()

    def __init__(self, aliases: Optional[Iterable[str]] = None) -> None:
        self._aliases = {self._normalize(city) for city in (aliases or [])}

    def supports(self, city: str) -> bool:
        """Return True if the adapter supports the provided city name.
        
        Checks exact matches first, then checks if city name contains any
        of the supported city names for broader support of variations.
        """
        normalized = self._normalize(city)
        supported = {self._normalize(name) for name in self.supported_cities}
        
        # First check exact match
        if normalized in supported or normalized in self._aliases:
            return True
        
        # Then check if city name contains any of the supported city names
        for supported_city in supported:
            if supported_city in normalized:
                return True
        
        return False

    @staticmethod
    def _normalize(city: str) -> str:
        return (city or "").strip().casefold()

    @abstractmethod
    def collect(self, location: LocationQuery, **kwargs) -> List[Dict]:
        """Collect tikbinyan data for the given location."""


class BatYamTikbinyanAdapter(TikbinyanAdapter):
    """Adapter that delegates to the Bat Yam tikbinyan collector."""

    supported_cities = ["בת ים", "bat yam", "batyam"]

    def __init__(self, client: Optional[BatYamTikbinyanClient] = None) -> None:
        super().__init__()
        self.client = client or BatYamTikbinyanClient()

    def collect(self, location: LocationQuery, **kwargs) -> List[Dict]:
        """Collect tikbinyan data for Bat Yam."""
        block = str(location.block) if location.block else None
        parcel = str(location.parcel) if location.parcel else None
        
        address = kwargs.get("address")
        if not address and location.street:
            address_parts = [location.street]
            if location.house_number:
                address_parts.append(str(location.house_number))
            address = " ".join(address_parts)
        
        return self.client.get_building_info(
            block=block,
            parcel=parcel,
            address=address,
        )


class HerzliyaTikbinyanAdapter(TikbinyanAdapter):
    """Adapter that delegates to the Herzliya tikbinyan collector."""

    supported_cities = ["הרצליה", "herzliya", "hertzeliya", "hertzliya"]

    def __init__(self, client: Optional[HerzliyaTikbinyanClient] = None) -> None:
        super().__init__()
        self.client = client or HerzliyaTikbinyanClient()

    def collect(self, location: LocationQuery, **kwargs) -> List[Dict]:
        """Collect tikbinyan data for Herzliya."""
        block = str(location.block) if location.block else None
        parcel = str(location.parcel) if location.parcel else None
        
        address = kwargs.get("address")
        if not address and location.street:
            address_parts = [location.street]
            if location.house_number:
                address_parts.append(str(location.house_number))
            address = " ".join(address_parts)
        
        return self.client.get_building_info(
            block=block,
            parcel=parcel,
            address=address,
        )


class RamatGanTikbinyanAdapter(TikbinyanAdapter):
    """Adapter that delegates to the Ramat Gan tikbinyan collector."""

    supported_cities = ["רמת גן", "ramat gan", "ramatgan", "ramat-gan"]

    def __init__(self, client: Optional[RamatGanTikbinyanClient] = None) -> None:
        super().__init__()
        self.client = client or RamatGanTikbinyanClient()

    def collect(self, location: LocationQuery, **kwargs) -> List[Dict]:
        """Collect tikbinyan data for Ramat Gan."""
        block = str(location.block) if location.block else None
        parcel = str(location.parcel) if location.parcel else None
        
        address = kwargs.get("address")
        if not address and location.street:
            address_parts = [location.street]
            if location.house_number:
                address_parts.append(str(location.house_number))
            address = " ".join(address_parts)
        
        return self.client.get_building_info(
            block=block,
            parcel=parcel,
            address=address,
        )


class MultiCityTikbinyanCollector(BaseCollector):
    """Routes tikbinyan collection to the best adapter for the given city."""

    def __init__(
        self,
        adapters: Optional[List[TikbinyanAdapter]] = None,
    ) -> None:
        # Default adapters for all supported cities
        if adapters is None:
            self.adapters = [
                BatYamTikbinyanAdapter(),
                HerzliyaTikbinyanAdapter(),
                RamatGanTikbinyanAdapter(),
            ]
        else:
            self.adapters = adapters

    def collect(
        self,
        location: Optional[LocationQuery] = None,
        **kwargs
    ) -> List[Dict]:
        """Collect tikbinyan data for the given location."""
        query = ensure_location_query(location)
        adapter = self._select_adapter(query.city)
        logger.info("Using %s for tikbinyan collection", adapter.__class__.__name__)
        return adapter.collect(query, **kwargs)

    def _select_adapter(self, city: Optional[str]) -> TikbinyanAdapter:
        """Select the appropriate adapter for the given city."""
        normalized_city = (city or "").strip()

        if not normalized_city:
            raise ValueError("City must be provided for tikbinyan collection")

        for adapter in self.adapters:
            if adapter.supports(normalized_city):
                return adapter

        available = ", ".join({c for adapter in self.adapters for c in adapter.supported_cities}) or "none"
        raise ValueError(
            f"No tikbinyan adapter available for city '{normalized_city}'. "
            f"Supported cities: {available}"
        )

    def validate_parameters(self, **kwargs) -> bool:
        """Validate parameters for collection."""
        location = ensure_location_query(kwargs.get("location"))
        block = location.block
        address = kwargs.get("address") or location.street
        
        return bool(block or address)


__all__ = [
    "TikbinyanAdapter",
    "BatYamTikbinyanAdapter",
    "HerzliyaTikbinyanAdapter",
    "RamatGanTikbinyanAdapter",
    "MultiCityTikbinyanCollector",
]

if __name__ == "__main__":
    adapter = MultiCityTikbinyanCollector()
    result = adapter.collect(location=LocationQuery(city="בת ים", street="הצפירה", house_number=8))
    print(result)