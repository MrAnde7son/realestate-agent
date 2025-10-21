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

        block = location.block
        parcel = location.parcel
        address = location.formatted or location.street or location.city

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
                logger.info(f"GovMap autocomplete returned {len(results)} results for '{search_query}'")
                
                # Log the first few results for debugging
                for i, result in enumerate(results[:3]):
                    result_text = result.get("text", "N/A")
                    result_type = result.get("type", "N/A")
                    logger.info(f"  Result {i+1}: '{result_text}' (type: {result_type})")
                
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
                                    
                                    # Validate that the corrected address is actually related to the original search
                                    first_addr = addresses[0]
                                    if first_addr.get("street") and first_addr.get("city"):
                                        corrected_street = first_addr["street"]
                                        corrected_city = first_addr["city"]
                                        corrected_number = first_addr.get("house_number")
                                        
                                        # Check if the corrected address is similar to the original search
                                        original_street = location.street.lower() if location.street else ""
                                        corrected_street_lower = corrected_street.lower()
                                        
                                        # Only update if there's some similarity or if the original search was very generic
                                        should_update = (
                                            # Street names are similar (contains or is contained)
                                            original_street in corrected_street_lower or 
                                            corrected_street_lower in original_street or
                                            # Original search was very short/generic
                                            len(original_street) <= 3 or
                                            # Street names share common words
                                            any(word in corrected_street_lower for word in original_street.split() if len(word) > 2)
                                        )
                                        
                                        if should_update:
                                            detailed_address = f"{corrected_street}"
                                            if corrected_number:
                                                detailed_address += f" {corrected_number}"
                                            detailed_address += f", {corrected_city}"
                                            out["address"] = detailed_address
                                            logger.info(f"✅ Updated address to: {detailed_address} (similarity validated)")
                                        else:
                                            logger.warning(f"⚠️ Corrected address '{corrected_street}' is too different from original '{original_street}', keeping original")
                                            logger.info(f"Original: '{search_query}' -> Corrected: '{corrected_street}' (rejected)")
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
