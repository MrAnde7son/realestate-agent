# -*- coding: utf-8 -*-
"""
GovMap collector that plugs into your existing orchestration layer.

Usage
-----
from orchestration.collectors.govmap_collector import GovMapCollector

collector = GovMapCollector()
result = collector.collect(address="רוזוב 14 תל אביב")
print("Address:", result["address"])
if "x" in result and "y" in result:
    print(f"Coordinates: x={result['x']}, y={result['y']}")
    print("Parcel data:", result["api_data"].get("parcel", "Not available"))
"""
import logging
from typing import Any, Dict, Optional, Tuple

from orchestration.collectors.base_collector import BaseCollector
from govmap.api_client import GovMapClient

logger = logging.getLogger(__name__)


class GovMapCollector(BaseCollector):
    """Collects national-level parcel + nearby layers from GovMap OpenData."""

    def __init__(self, client: Optional[GovMapClient] = None) -> None:
        self.client = client or GovMapClient()



    def collect(
        self,
        *,
        address: str,
    ) -> Dict[str, Any]:
        """Collect data from GovMap using address autocomplete and parcel data.

        Parameters
        ----------
        address : Address string to search for (e.g., "רוזוב 14 תל אביב")
        """
        out: Dict[str, Any] = {
            "address": address,
            "api_data": {},
        }

        try:
            # Get autocomplete results for the address
            autocomplete_result = self.client.autocomplete(address)
            out["api_data"]["autocomplete"] = autocomplete_result
            
            # Extract coordinates from the first result
            coords = self._extract_coordinates_from_autocomplete(autocomplete_result)
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
                
        except Exception as e:
            logger.error(f"Failed to process address '{address}': {e}")

        return out

    def _extract_coordinates_from_autocomplete(self, autocomplete_result: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """Extract ITM coordinates from autocomplete response."""
        try:
            if "results" in autocomplete_result:
                results = autocomplete_result.get("results", [])
                if results:
                    result = results[0]  # Get first result
                    if "shape" in result and isinstance(result["shape"], str):
                        shape = result["shape"]
                        # Shape is a POINT string like "POINT(3877998.167083787 3778264.858683848)"
                        if shape.startswith("POINT("):
                            coords_str = shape[6:-1]  # Remove "POINT(" and ")"
                            parts = coords_str.split()
                            if len(parts) >= 2:
                                try:
                                    x = float(parts[0])
                                    y = float(parts[1])
                                    logger.info(f"Extracted coordinates from autocomplete: ({x}, {y})")
                                    return (x, y)
                                except (ValueError, TypeError) as e:
                                    logger.debug(f"Failed to parse coordinates from shape '{shape}': {e}")
            
            logger.warning("No coordinates found in autocomplete response")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting coordinates from autocomplete: {e}")
            return None

    def validate_parameters(self, **kwargs) -> bool:
        """Validate that an address string is provided."""
        address = kwargs.get("address")
        return isinstance(address, str) and bool(address.strip())


if __name__ == "__main__":
    collector = GovMapCollector()
    result = collector.collect(address="רוזוב 14 תל אביב")
    print("Address:", result["address"])
    if "x" in result and "y" in result:
        print(f"Coordinates: x={result['x']}, y={result['y']}")
        print("Parcel data:", result["api_data"].get("parcel", "Not available"))
    else:
        print("Could not extract coordinates from address")