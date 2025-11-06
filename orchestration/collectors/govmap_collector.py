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
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from orchestration.collectors.base_collector import BaseCollector
from govmap.api_client import GovMapClient
from orchestration.location import LocationQuery

logger = logging.getLogger(__name__)


class GovMapCollector(BaseCollector):
    """Collects national-level parcel + nearby layers from GovMap OpenData."""

    def __init__(self, client: Optional[GovMapClient] = None) -> None:
        self.client = client or GovMapClient()



    def collect(
        self,
        location: Optional[LocationQuery] = None,
        **kwargs
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
        if block and parcel and not address:
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
                                        
                                        # Calculate similarity ratio using SequenceMatcher
                                        similarity_ratio = SequenceMatcher(None, original_street, corrected_street_lower).ratio()
                                        
                                        # Only update if there's some similarity or if the original search was very generic
                                        should_update = (
                                            # High similarity ratio (handles spelling variants like "לה גווארדיה" vs "לה גווארדייה")
                                            similarity_ratio >= 0.75 or
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

                    # Get entities by point (schools, parks, parking, metro, etc.)
                    try:
                        entities = self.client.entities_by_point(x, y, radius=500.0)
                        if entities:
                            out["nearby"] = self._process_entities_by_layer(entities)
                            logger.info(f"Found entities from {len(entities)} layers")
                    except Exception as e:
                        logger.warning(f"Failed to get entities by point: {e}")

                else:
                    logger.warning("Could not extract coordinates from autocomplete result")
            else:
                logger.warning("Autocomplete response did not contain results")
        except Exception as e:
            logger.error(f"Failed to process query '{search_query}': {e}")

        return out

    def _process_entities_by_layer(self, entities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Process entities_by_point response and organize by layer type.
        
        Maps GovMap layer IDs to human-readable layer names:
        - 17: בתי ספר (schools)
        - 18: גני ילדים (kindergartens)
        - 20: תחנות אוטובוס (bus stations)
        - 151: תחנות קווי מטרו (metro stations)
        - 160: קווי מטרו (metro lines)
        - 394: חניונים (parking lots)
        - 400: מתקני ספורט (sports facilities)
        - 407: תחנות רכבת (train stations)
        - 417: מקלטים (shelters)
        - 388: מסעדות (restaurants)
        - 150: אתרי רשות הטבע והגנים (nature and parks authority sites)
        - 215699: פארקים עירוניים (urban parks)
        - 200723: התחדשות עירונית (urban renewal)
        """
        layer_name_map = {
            "17": "schools",
            "18": "kindergartens",
            "20": "bus_stations",
            "151": "metro_stations",
            "160": "metro_lines",
            "394": "parking_lots",
            "400": "sports_facilities",
            "407": "train_stations",
            "417": "shelters",
            "388": "restaurants",
            "150": "nature_parks",
            "215699": "urban_parks",
            "200723": "urban_renewal",
            "16": "real_estate_transactions",  # This is already handled separately
        }
        
        organized = {}
        
        for layer_data in entities:
            layer_name = layer_data.get("name", "")
            caption = layer_data.get("caption", "")
            entities_list = layer_data.get("entities", [])
            
            # Try to match by layer name or caption
            layer_key = None
            for layer_id, key in layer_name_map.items():
                if layer_id in layer_name or layer_id in caption:
                    layer_key = key
                    break
            
            # If no match, use a sanitized version of the name
            if not layer_key:
                layer_key = layer_name.lower().replace(" ", "_").replace("-", "_") if layer_name else "unknown"
            
            # Process entities to extract relevant fields
            processed_entities = []
            for entity in entities_list:
                processed_entity = {
                    "objectId": entity.get("objectId"),
                    "centroid": entity.get("centroid"),
                    "fields": self._extract_entity_fields(entity.get("fields", [])),
                }
                processed_entities.append(processed_entity)
            
            if processed_entities:
                organized[layer_key] = {
                    "layer_name": layer_name,
                    "caption": caption,
                    "entities": processed_entities,
                    "count": len(processed_entities),
                }
        
        return organized

    def _extract_entity_fields(self, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract entity fields into a structured dictionary."""
        extracted = {}
        for field in fields:
            field_name = field.get("fieldName", "")
            field_value = field.get("fieldValue", "")
            if field_name and field_value:
                # Use English field names when available, otherwise use Hebrew
                extracted[field_name] = field_value
        
        return extracted

    def validate_parameters(self, **kwargs) -> bool:
        """Validate that a non-empty location is provided."""

        location = kwargs.get("location")
        return isinstance(location, LocationQuery) and not location.is_empty()


if __name__ == "__main__":
    from orchestration.location import LocationQuery

    collector = GovMapCollector()
    result = collector.collect(LocationQuery(street="אבן גבירול", house_number=59, city="תל אביב-יפו"))
    print("result:", result)
