"""GIS data collector implementation."""

from typing import Any, Dict, Optional, Tuple

from gis.gis_client import TelAvivGS

from .base_collector import BaseCollector


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
        }
        block, parcel = self._extract_block_parcel(data)
        data.update({"block": block, "parcel": parcel, "x": x, "y": y})
        return data

    def _geocode(self, address: str, house_number: int) -> Tuple[float, float]:
        """Geocode an address to coordinates."""
        return self.client.get_address_coordinates(address, house_number)

    def _extract_block_parcel(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """Extract block and parcel numbers from GIS data."""
        block = data.get("blocks", [{}])[0].get("ms_gush", "")
        parcel = data.get("parcels", [{}])[0].get("ms_chelka", "")
        return block, parcel

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for GIS collection."""
        return isinstance(kwargs.get('address'), str) and isinstance(kwargs.get('house_number'), int)
