"""GIS data collector for Bat Yam."""

import logging
from typing import Any, Dict, Optional

from gis.batyam_gis_client import BatYamGIS
from orchestration.location import LocationQuery, ensure_location_query
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class BatYamGISCollector(BaseCollector):
    """Collector for Bat Yam GIS data."""

    def __init__(self, client: Optional[BatYamGIS] = None) -> None:
        self.client = client or BatYamGIS()

    def collect(
        self,
        location: Optional[LocationQuery] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Collect GIS data for a given location with coordinates or block/parcel."""
        query = ensure_location_query(location)
        
        # Use coordinates if available, otherwise raise error
        # (Geocoding should be done via GovMap first)
        x = query.x_itm
        y = query.y_itm
        
        if not x or not y:
            raise ValueError(
                "BatYamGISCollector requires coordinates (x_itm, y_itm). "
                "Please geocode the address first using GovMap or another service."
            )
        
        data = {
            "blocks": self.client.get_blocks(x, y),
            "parcels": self.client.get_parcels(x, y),
            "permits": self.client.get_building_permits(x, y),
            "rights": self.client.get_land_use_main(x, y),
            "shelters": self.client.get_shelters(x, y),
            "green": self.client.get_green_areas(x, y),
            "noise": self.client.get_noise_levels(x, y),
            "antennas": self.client.get_cell_antennas(x, y),
            "land_use_detailed": self.client.get_land_use_detailed(x, y),
            "dangerous": self.client.get_dangerous_buildings(x, y),
            "local_plans": self.client.get_plans_local(x, y),
            "city_plans": self.client.get_plans_citywide(x, y),
            "metro_stations": self.client.get_metro_stations(x, y),
            "parking_lots": self.client.get_parking_lots(x, y),
            "schools": self.client.get_schools(x, y),
            "construction_sites": self.client.get_construction_sites(x, y),
            "affordable_housing": self.client.get_affordable_housing_projects(x, y),
            "bike_paths": self.client.get_bike_paths(x, y),
            "soil_contamination": self.client.get_soil_contamination(x, y),
            "green_amenities": self.client.get_green_amenities(x, y),
            "medical_facilities": self.client.get_medical_facilities(x, y),
            "community_facilities": self.client.get_community_facilities(x, y),
            "dog_parks": self.client.get_dog_parks(x, y),
            "public_gardens": self.client.get_public_gardens(x, y),
            "playgrounds": self.client.get_playgrounds(x, y),
            "medical_centers": self.client.get_medical_centers(x, y),
            "health_funds": self.client.get_health_funds(x, y),
            "pharmacies": self.client.get_pharmacies(x, y),
            "tama38_key_areas": self.client.get_tama38_key_areas(x, y),
            "road_works": self.client.get_road_works(x, y),
        }
        
        # Extract block/parcel from results
        block, parcel = self._extract_block_parcel(data)
        data.update({
            "block": block,
            "parcel": parcel,
            "x": x,
            "y": y,
        })
        return data

    def _extract_block_parcel(self, data: Dict[str, Any]) -> tuple[str, str]:
        """Extract block and parcel numbers from GIS data."""
        block = ""
        blocks = data.get("blocks", [])
        if blocks and isinstance(blocks, list) and len(blocks) > 0:
            block_data = blocks[0]
            if isinstance(block_data, dict):
                # Try common field names for block
                block = block_data.get("גוש") or block_data.get("gush") or block_data.get("ms_gush") or ""
                if block and not isinstance(block, str):
                    block = str(block)
        
        parcel = ""
        parcels = data.get("parcels", [])
        if parcels and isinstance(parcels, list) and len(parcels) > 0:
            parcel_data = parcels[0]
            if isinstance(parcel_data, dict):
                # Try common field names for parcel
                parcel = parcel_data.get("חלקה") or parcel_data.get("chelka") or parcel_data.get("ms_chelka") or ""
                if parcel and not isinstance(parcel, str):
                    parcel = str(parcel)
        
        block = block.strip() if block else ""
        parcel = parcel.strip() if parcel else ""
        
        return block, parcel

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for GIS collection."""
        location = ensure_location_query(kwargs.get("location"))
        return bool(location.x_itm and location.y_itm)

