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
from govmap.api_client import GovMapClient
from orchestration.location import LocationQuery, ensure_location_query

logger = logging.getLogger(__name__)


class GovMapCollector(BaseCollector):
    """Collects national-level parcel + nearby layers from GovMap OpenData."""

    def __init__(self, client: Optional[GovMapClient] = None) -> None:
        self.client = client or GovMapClient()



    def collect(
        self,
        location: Optional[LocationQuery] = None,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Collect data from GovMap using address autocomplete and parcel data.

        Parameters
        ----------
        location : Optional[LocationQuery]
            Structured address information. When ``None`` an empty query is
            assumed.
        block : Optional[str]
            Block number for block/parcel-only queries
        parcel : Optional[str]
            Parcel number for block/parcel-only queries
        """

        query = ensure_location_query(location)
        address = query.formatted or query.street or query.city

        # Determine search query based on input
        if block and parcel and block.strip() and parcel.strip() and not address:
            # Block/parcel-only query
            search_query = f"גוש {block} חלקה {parcel}"
            logger.info(f"Processing block/parcel-only query in GovMap: {block}/{parcel}")
            out: Dict[str, Any] = {
                "address": search_query,
                "api_data": {},
                "block": block,
                "parcel": parcel,
            }
        else:
            # Address-based query
            search_query = address
            out: Dict[str, Any] = {
                "address": search_query,
                "api_data": {},
            }

        try:
            # Get autocomplete results
            autocomplete_result = self.client.autocomplete(search_query)
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
                        
                        # If we have parcel data with objectid, get detailed addresses
                        if parcel_data and parcel_data.get("properties", {}).get("objectid"):
                            objectid = parcel_data["properties"]["objectid"]
                            logger.info(f"Getting detailed addresses for parcel objectid: {objectid}")
                            
                            try:
                                addresses = self.client.get_parcel_addresses(objectid)
                                if addresses:
                                    out["addresses"] = addresses
                                    logger.info(f"Found {len(addresses)} detailed addresses")
                                    
                                    # Update the main address with the first detailed address
                                    first_addr = addresses[0]
                                    if first_addr.get("street") and first_addr.get("city"):
                                        detailed_address = f"{first_addr['street']}"
                                        if first_addr.get("house_number"):
                                            detailed_address += f" {first_addr['house_number']}"
                                        detailed_address += f", {first_addr['city']}"
                                        out["address"] = detailed_address
                                        logger.info(f"Updated address to: {detailed_address}")
                                else:
                                    logger.warning(f"No detailed addresses found for objectid {objectid}")
                            except Exception as e:
                                logger.warning(f"Failed to get detailed addresses for objectid {objectid}: {e}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to get parcel data: {e}")

                else:
                    logger.warning("Could not extract coordinates from autocomplete result")
            else:
                logger.warning("Autocomplete response did not contain results")
        except Exception as e:
            logger.error(f"Failed to process query '{search_query}': {e}")

        return out

    def validate_parameters(self, **kwargs) -> bool:
        """Validate that a non-empty location is provided."""

        location = kwargs.get("location")
        return isinstance(location, LocationQuery) and not location.is_empty()


if __name__ == "__main__":
    from orchestration.location import LocationQuery

    collector = GovMapCollector()
    result = collector.collect(block="7793", parcel="102")
    print("Address:", result["address"])
    print("result:", result)

