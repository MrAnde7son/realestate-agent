"""GIS data collector implementation."""

import logging
from typing import Any, Dict, Optional, Tuple

from gis.gis_client import TelAvivGS

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class GISCollector(BaseCollector):
    """Collector for Tel-Aviv GIS data."""

    def __init__(self, client: Optional[TelAvivGS] = None) -> None:
        self.client = client or TelAvivGS()

    def collect(self, address: str, house_number: int) -> Dict[str, Any]:
        """Geocode and collect GIS data for a given address."""
        x, y = self._geocode(address, house_number)
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

    def _geocode(self, address: str, house_number: int) -> Tuple[float, float]:
        """Geocode an address to coordinates with fallback strategies."""
        # Try the original address first with like=True (same as MCP server)
        try:
            return self.client.get_address_coordinates(address, house_number, like=True)
        except Exception as e:
            logger.warning(f"Primary geocoding failed: {e}")
            
        # Try with reversed street name (common issue with Hebrew addresses)
        if ' ' in address:
            parts = address.split()
            if len(parts) == 2:
                reversed_address = f"{parts[1]} {parts[0]}"
                try:
                    logger.info(f"Trying reversed address: {reversed_address}")
                    return self.client.get_address_coordinates(reversed_address, house_number, like=True)
                except Exception as e2:
                    logger.warning(f"Reversed geocoding failed: {e2}")
        
        # If all else fails, raise the original error
        raise Exception(f"All geocoding attempts failed for {address} {house_number}")

    def _extract_block_parcel(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """Extract block and parcel numbers from GIS data."""

        blocks = data.get("blocks") or []
        parcels = data.get("parcels") or []

        block_entry = blocks[0] if blocks else {}
        parcel_entry = parcels[0] if parcels else {}

        block = block_entry.get("ms_gush", "") if isinstance(block_entry, dict) else ""
        parcel = parcel_entry.get("ms_chelka", "") if isinstance(parcel_entry, dict) else ""
        return block, parcel

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for GIS collection."""
        return isinstance(kwargs.get('address'), str) and isinstance(kwargs.get('house_number'), int)
