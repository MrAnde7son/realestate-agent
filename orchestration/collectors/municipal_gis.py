"""Composable municipal GIS adapter layer for multi-city coverage.

This module introduces a lightweight OOP abstraction for municipal GIS data
collection. Each adapter declares the cities it supports and exposes a common
``collect`` signature so the orchestration layer can route requests to the
right data source (deep municipal GIS vs. national GovMap fallback).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional

from orchestration.collectors.gis_collector import GISCollector
from orchestration.collectors.herzliya_gis_collector import HerzliyaGISCollector
from orchestration.collectors.batyam_gis_collector import BatYamGISCollector
from orchestration.collectors.ramat_gan_gis_collector import RamatGanGISCollector
from orchestration.collectors.base_collector import BaseCollector
from orchestration.location import LocationQuery, ensure_location_query

logger = logging.getLogger(__name__)


class MunicipalGisAdapter(ABC):
    """Abstract base class for municipal GIS adapters."""

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
    def collect(self, location: LocationQuery) -> Dict:
        """Collect GIS data for the given location."""


class TelAvivMunicipalGisAdapter(MunicipalGisAdapter):
    """Adapter that delegates to the Tel Aviv municipal GIS collector."""

    supported_cities = ["תל אביב", "תל אביב - יפו", "תל אביב-יפו", "tel aviv", "tel aviv-yafo", "tel aviv yafo"]

    def __init__(self, collector: Optional[GISCollector] = None) -> None:
        super().__init__()
        self.collector = collector

    def collect(self, location: LocationQuery) -> Dict:
        collector = self.collector or GISCollector()
        return collector.collect(location)


class HerzliyaMunicipalGisAdapter(MunicipalGisAdapter):
    """Adapter that delegates to the Herzliya municipal GIS collector."""

    supported_cities = ["הרצליה", "הרצלייה", "herzliya", "hertzeliya", "hertzliya"]

    def __init__(self, collector: Optional[HerzliyaGISCollector] = None) -> None:
        super().__init__()
        self.collector = collector

    def collect(self, location: LocationQuery) -> Dict:
        collector = self.collector or HerzliyaGISCollector()
        return collector.collect(location)


class BatYamMunicipalGisAdapter(MunicipalGisAdapter):
    """Adapter that delegates to the Bat Yam municipal GIS collector."""

    supported_cities = ["בת ים", "bat yam", "batyam"]

    def __init__(self, collector: Optional[BatYamGISCollector] = None) -> None:
        super().__init__()
        self.collector = collector

    def collect(self, location: LocationQuery) -> Dict:
        collector = self.collector or BatYamGISCollector()
        return collector.collect(location)


class RamatGanMunicipalGisAdapter(MunicipalGisAdapter):
    """Adapter that delegates to the Ramat Gan municipal GIS collector."""

    supported_cities = ["רמת גן", "ramat gan", "ramatgan"]

    def __init__(self, collector: Optional[RamatGanGISCollector] = None) -> None:
        super().__init__()
        self.collector = collector

    def collect(self, location: LocationQuery) -> Dict:
        collector = self.collector or RamatGanGISCollector()
        return collector.collect(location)


class MultiCityGISCollector(BaseCollector):
    """Routes GIS collection to the best adapter for the given city."""

    def __init__(
        self,
        adapters: Optional[List[MunicipalGisAdapter]] = None,
    ) -> None:
        # Default adapters for all supported cities
        if adapters is None:
            self.adapters = [
                TelAvivMunicipalGisAdapter(),
                HerzliyaMunicipalGisAdapter(),
                BatYamMunicipalGisAdapter(),
                RamatGanMunicipalGisAdapter(),
            ]
        else:
            self.adapters = adapters

    def collect(self, location: Optional[LocationQuery] = None, **kwargs) -> Dict:
        query = ensure_location_query(location)
        adapter = self._select_adapter(query.city)
        logger.info("Using %s for municipal GIS collection", adapter.__class__.__name__)
        return adapter.collect(query)

    def _select_adapter(self, city: Optional[str]) -> MunicipalGisAdapter:
        normalized_city = (city or "").strip()

        if not normalized_city:
            raise ValueError("City must be provided when no default city is configured")

        for adapter in self.adapters:
            if adapter.supports(normalized_city):
                return adapter

        available = ", ".join({c for adapter in self.adapters for c in adapter.supported_cities}) or "none"
        raise ValueError(
            f"No municipal GIS adapter available for city '{normalized_city}'. "
            f"Supported cities: {available}"
        )
