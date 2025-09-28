# -*- coding: utf-8 -*-
"""
GovMap collector that plugs into your existing orchestration layer.

Usage
-----
from orchestration.collectors.govmap_collector import GovMapCollector
from orchestration.location import LocationQuery

collector = GovMapCollector()
result = collector.collect(LocationQuery(street="רוזוב", house_number=14, city="תל אביב"))
print("Address:", result["address"])
if "x" in result and "y" in result:
    print(f"Coordinates: x={result['x']}, y={result['y']}")
    print("Parcel data:", result["api_data"].get("parcel", "Not available"))
"""
import logging
from typing import Any, Dict, Optional, Tuple

from orchestration.collectors.base_collector import BaseCollector
from govmap.api_client import GovMapClient, GovMapAuthError
from orchestration.location import LocationQuery, ensure_location_query

logger = logging.getLogger(__name__)


class GovMapCollector(BaseCollector):
    """Collects national-level parcel + nearby layers from GovMap OpenData."""

    def __init__(self, client: Optional[GovMapClient] = None) -> None:
        self.client = client or GovMapClient()



    def collect(
        self,
        location: Optional[LocationQuery] = None,
    ) -> Dict[str, Any]:
        """Collect data from GovMap using address autocomplete and parcel data.

        Parameters
        ----------
        location : Optional[LocationQuery]
            Structured address information. When ``None`` an empty query is
            assumed.
        """

        query = ensure_location_query(location)
        address = query.formatted or query.street or query.city

        out: Dict[str, Any] = {
            "address": address,
            "api_data": {},
        }

        try:
            # Get autocomplete results for the address
            autocomplete_result = self.client.autocomplete(address)
            out["api_data"]["autocomplete"] = autocomplete_result

            # Extract coordinates from the first result
            results = autocomplete_result.get("results") if isinstance(autocomplete_result, dict) else None
            if results:
                coords = self.client.extract_coordinates_from_shapes(results[0])
                if coords:
                    x, y = coords
                    out["x"] = x
                    out["y"] = y

                    # Get parcel data using the extracted coordinates
                    try:
                        parcel_data = self.client.get_parcel_data(x, y)
                        out["api_data"]["parcel"] = parcel_data
                    except Exception as e:
                        logger.warning(f"Failed to get parcel data: {e}")
                else:
                    logger.warning("Could not extract coordinates from autocomplete result")
            else:
                logger.warning("Autocomplete response did not contain results")

        except Exception as e:
            logger.error(f"Failed to process address '{address}': {e}")


    def validate_parameters(self, **kwargs) -> bool:
        """Validate that a non-empty location is provided."""

        location = kwargs.get("location")
        return isinstance(location, LocationQuery) and not location.is_empty()


if __name__ == "__main__":
    from orchestration.location import LocationQuery

    collector = GovMapCollector()
    result = collector.collect(LocationQuery(street="רוזוב", house_number=14, city="תל אביב"))
    print("Address:", result["address"])
    if "x" in result and "y" in result:
        print(f"Coordinates: x={result['x']}, y={result['y']}")
        print("Parcel data:", result["api_data"].get("parcel", "Not available"))
    else:
        print("Could not extract coordinates from address")
