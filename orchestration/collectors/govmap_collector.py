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
from govmap.api_client import GovMapClient, GovMapAuthError

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

        # Use SearchAndLocate to enrich the address with block/parcel identifiers.
        # Planning data retrieval lives in the dedicated RAMI collector, so we stop
        # here to avoid duplicating that integration in multiple collectors.
        try:
            locate_result = self.client.search_and_locate_address(address)
            out["api_data"]["search_and_locate"] = locate_result

            block_parcel = self.client.extract_block_parcel(locate_result)
            if block_parcel:
                block, parcel = block_parcel
                out["block"] = block
                out["parcel"] = parcel
            else:
                logger.warning("SearchAndLocate response missing block/parcel values")
        except GovMapAuthError as locate_error:
            logger.warning(
                "SearchAndLocate enrichment skipped due to authentication error: %s",
                locate_error,
            )
        except Exception as locate_error:
            logger.warning(f"SearchAndLocate enrichment failed: {locate_error}")

        return out


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