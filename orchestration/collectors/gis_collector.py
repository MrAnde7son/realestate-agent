"""GIS data collector implementation."""

from typing import List, Optional, Dict, Any, Tuple
from .base_collector import BaseCollector
from gis.gis_client import TelAvivGS


class GISCollector(BaseCollector):
    """Collector for Tel-Aviv GIS data."""

    def __init__(self, client: Optional[TelAvivGS] = None) -> None:
        self.client = client or TelAvivGS()

    def collect(self, x: float, y: float) -> Dict[str, Any]:
        """Collect GIS data for a given coordinate pair."""
        return {
            "blocks": self.client.get_blocks(x, y),
            "parcels": self.client.get_parcels(x, y),
            "permits": self.client.get_building_permits(x, y),
            "rights": self.client.get_land_use_main(x, y),
            "shelters": self.client.get_shelters(x, y),
            "green": self.client.get_green_areas(x, y),
            "noise": self.client.get_noise_levels(x, y),
        }

    def geocode(self, address: str, house_number: int) -> Tuple[float, float]:
        """Geocode an address to coordinates."""
        return self.client.get_address_coordinates(address, house_number)

    def extract_block_parcel(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """Extract block and parcel numbers from GIS data."""
        block = data.get("blocks", [{}])[0].get("ms_gush", "")
        parcel = data.get("parcels", [{}])[0].get("ms_chelka", "")
        return block, parcel

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for GIS collection."""
        if 'x' in kwargs and 'y' in kwargs:
            return isinstance(kwargs['x'], (int, float)) and isinstance(kwargs['y'], (int, float))
        elif 'address' in kwargs and 'house_number' in kwargs:
            return isinstance(kwargs['address'], str) and isinstance(kwargs['house_number'], int)
        return False
