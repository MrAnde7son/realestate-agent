"""GIS data collector implementation."""

import logging
from typing import Any, Dict, Optional, Tuple

from gis.gis_client import TelAvivGS

from orchestration.location import LocationQuery, ensure_location_query

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class GISCollector(BaseCollector):
    """Collector for Tel-Aviv GIS data."""

    def __init__(self, client: Optional[TelAvivGS] = None) -> None:
        self.client = client or TelAvivGS()

    def collect(
        self,
        location: Optional[LocationQuery] = None,
    ) -> Dict[str, Any]:
        """Geocode and collect GIS data for a given address."""

        query = ensure_location_query(location)
        street = query.street
        city = query.city
        search_street = (street or query.formatted or "").strip()
        number = query.house_number or 0

        if not search_street:
            raise ValueError("GISCollector requires at least a street name")

        x, y = self._geocode(search_street, number, city)
        data = {
            "blocks": self.client.get_blocks(x, y),
            "parcels": self.client.get_parcels(x, y),
            "permits": self.client.get_building_permits(x, y),
            "rights": self.client.get_land_use_main(x, y),
            "shelters": self.client.get_shelters(x, y),
            "green": self.client.get_green_areas(x, y),
            "noise": self.client.get_noise_levels(x, y),
            "antennas": self.client.get_cell_antennas(x, y),
        }
        block, parcel = self._extract_block_parcel(data)
        data.update({"block": block, "parcel": parcel, "x": x, "y": y})
        return data

    def _geocode(self, street: str, house_number: int, city: str = "") -> Tuple[float, float]:
        """Geocode an address to coordinates with fallback strategies."""
        # Try the original address first with like=True (same as MCP server)
        try:
            return self.client.get_address_coordinates(street, house_number, like=True)
        except Exception as e:
            logger.warning(f"Primary geocoding failed: {e}")

        # Try with reversed street name (common issue with Hebrew addresses)
        if ' ' in street:
            parts = street.split()
            if len(parts) == 2:
                reversed_address = f"{parts[1]} {parts[0]}"
                try:
                    logger.info(f"Trying reversed address: {reversed_address}")
                    return self.client.get_address_coordinates(reversed_address, house_number, like=True)
                except Exception as e2:
                    logger.warning(f"Reversed geocoding failed: {e2}")

        # Try appending city if provided and not already part of the street string
        if city and city not in street:
            try:
                combined = f"{street} {city}".strip()
                logger.info(f"Trying geocoding with city context: {combined}")
                return self.client.get_address_coordinates(combined, house_number, like=True)
            except Exception as e3:
                logger.warning(f"City-aware geocoding failed: {e3}")

        # If all else fails, raise the original error
        raise Exception(f"All geocoding attempts failed for {street} {house_number}")

    def _extract_block_parcel(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """Extract block and parcel numbers from GIS data."""
        block = data.get("blocks", [{}])[0].get("ms_gush", "")
        parcel = data.get("parcels", [{}])[0].get("ms_chelka", "")
        return block, parcel


    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for GIS collection."""

        location = kwargs.get("location")
        return (
            isinstance(location, LocationQuery)
            and bool(location.street)
            and location.house_number is not None
        )
