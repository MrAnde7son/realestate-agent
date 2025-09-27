# -*- coding: utf-8 -*-
"""
GovMap API client (tokenless endpoints + OpenData WMS/WFS)

This client avoids the tokened JS SDK and focuses on:
- Autocomplete/search (public endpoint)
- OpenData GeoServer (WMS/WFS) for layers that are publicly exposed

Notes
-----
* Coordinate system: most GovMap layers use EPSG:2039 (ITM). We expose helpers
  to convert to/from WGS84.
* WFS querying uses CQL filters. Geometry field names vary by layer ("the_geom", "geom").
  We allow providing candidate names to try.
* Keep layers configurable via env or function args (don't hardcode).
"""
import os
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests
from pyproj import Transformer
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

DEFAULT_WMS = os.getenv("GOVMAP_WMS_URL", "https://open.govmap.gov.il/geoserver/opendata/wms")
DEFAULT_WFS = os.getenv("GOVMAP_WFS_URL", "https://open.govmap.gov.il/geoserver/opendata/ows")
DEFAULT_AUTOCOMPLETE = os.getenv(
    "GOVMAP_AUTOCOMPLETE_URL",
    "https://www.govmap.gov.il/api/search-service/autocomplete",
)

# Reusable transformers
_TO_WGS84 = Transformer.from_crs(2039, 4326, always_xy=True)
_FROM_WGS84 = Transformer.from_crs(4326, 2039, always_xy=True)


def itm_to_wgs84(x: float, y: float) -> Tuple[float, float]:
    lon, lat = _TO_WGS84.transform(x, y)
    return float(lon), float(lat)


def wgs84_to_itm(lon: float, lat: float) -> Tuple[float, float]:
    x, y = _FROM_WGS84.transform(lon, lat)
    return float(x), float(y)


@dataclass
class WMSFeatureInfo:
    layer: str
    attributes: Dict[str, Any]


class GovMapError(RuntimeError):
    pass


class GovMapClient:
    """Thin client for GovMap OpenData and public endpoints."""

    def __init__(
        self,
        wms_url: str = DEFAULT_WMS,
        wfs_url: str = DEFAULT_WFS,
        autocomplete_url: str = DEFAULT_AUTOCOMPLETE,
        session: Optional[requests.Session] = None,
        timeout: int = 30,
    ) -> None:
        self.wms_url = wms_url.rstrip("?")
        self.wfs_url = wfs_url.rstrip("?")
        self.autocomplete_url = autocomplete_url
        self.layers_catalog_url = "https://www.govmap.gov.il/api/layers-catalog/catalog"
        self.search_types_url = "https://www.govmap.gov.il/api/search-service/getTypes"
        self.parcel_search_url = "https://www.govmap.gov.il/api/layers-catalog/apps/parcel-search/address"
        self.base_layers_url = "https://www.govmap.gov.il/api/layers-catalog/baseLayers?language=he"
        self.search_and_locate_url = "https://ags.govmap.gov.il/Api/Controllers/GovmapApi/SearchAndLocate"
        self.http = session or requests.Session()
        self.timeout = timeout
        self.http.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        })
        
        
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Configure the session with SSL settings
        self.http.mount('https://', requests.adapters.HTTPAdapter())
        self.http.verify = False

    # ----------------------------- Search -----------------------------
    def autocomplete(self, query: str, language: str = "he", max_results: int = 10) -> Dict[str, Any]:
        """Call the public autocomplete endpoint (no token required).
        Returns the raw JSON response from the new GovMap API.
        """
       
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Create a new session with SSL configuration for this request
        session = requests.Session()
        session.verify = False
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers for the new API
        session.headers.update({
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
            "Content-Type": "application/json",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        })
        
        # Prepare JSON body for the new API
        payload = {
            "searchText": query,
            "language": language,
            "isAccurate": False,
            "maxResults": max_results
        }
        
        try:
            r = session.post(self.autocomplete_url, json=payload, timeout=self.timeout, verify=False)
            if r.status_code != 200:
                raise GovMapError(f"Autocomplete HTTP {r.status_code}")
            return r.json()
        except Exception as ssl_e:
            if "SSL" in str(ssl_e) or "ssl" in str(ssl_e).lower():
                logger.warning(f"SSL error with GovMap autocomplete, trying with different SSL settings: {ssl_e}")
                # Try with even more permissive SSL settings
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                ssl_context.set_ciphers('DEFAULT@SECLEVEL=0')
                
                # Create a new session with the custom SSL context
                session = requests.Session()
                session.verify = False
                session.headers.update({
                    "Accept": "application/json",
                    "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
                    "Content-Type": "application/json",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
                })
                
                r = session.post(self.autocomplete_url, json=payload, timeout=self.timeout, verify=False)
                if r.status_code != 200:
                    raise GovMapError(f"Autocomplete HTTP {r.status_code}")
                return r.json()
            else:
                # Re-raise if it's not an SSL error
                raise
        except Exception as e:
            logger.error(f"GovMap autocomplete failed: {e}")
            raise GovMapError(f"Autocomplete failed: {e}")

    @staticmethod
    def extract_coordinates_from_shapes(result: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """Extract ITM coordinates from autocomplete response."""
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
                        return x, y
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Failed to parse coordinates from shape '{shape}': {e}")
        return None

    def get_layers_catalog(self, language: str = "he") -> Dict[str, Any]:
        """Get the layers catalog from GovMap.
        
        Args:
            language: Language code (default: "he")
            
        Returns:
            Dictionary containing the layers catalog data
        """
        try:
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }
            
            params = {"lang": language}
            r = self.http.get(self.layers_catalog_url, params=params, headers=headers, timeout=self.timeout, verify=False)
            if r.status_code != 200:
                raise GovMapError(f"Layers catalog HTTP {r.status_code}")
            return r.json()
        except Exception as e:
            logger.error(f"GovMap layers catalog failed: {e}")
            raise GovMapError(f"Layers catalog failed: {e}")

    def get_search_types(self, language: str = "he") -> Dict[str, Any]:
        """Get search types from GovMap.
        
        Args:
            language: Language code (default: "he")
            
        Returns:
            Dictionary containing the search types data
        """
        try:
            headers = {
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
                "Content-Type": "application/json",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }
            
            payload = {"language": language}
            r = self.http.post(self.search_types_url, json=payload, headers=headers, timeout=self.timeout, verify=False)
            if r.status_code != 200:
                raise GovMapError(f"Search types HTTP {r.status_code}")
            return r.json()
        except Exception as e:
            logger.error(f"GovMap search types failed: {e}")
            raise GovMapError(f"Search types failed: {e}")

    def get_parcel_data(self, x: float, y: float) -> Dict[str, Any]:
        """Get parcel data for specific coordinates.
        
        Args:
            x: X coordinate (ITM)
            y: Y coordinate (ITM)
            
        Returns:
            Dictionary containing parcel data
        """
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        
        # Format coordinates as in the URL pattern
        coord_string = f"({x}%20{y})"
        url = f"{self.parcel_search_url}/{coord_string}"
        
        # Try up to 3 times with exponential backoff
        for attempt in range(3):
            try:
                r = self.http.get(url, headers=headers, timeout=self.timeout, verify=False)
                if r.status_code == 200:
                    return r.json()
                elif r.status_code == 500:
                    # Server error - retry with backoff
                    if attempt < 2:  # Don't retry on last attempt
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
                        logger.warning(f"GovMap parcel search HTTP 500, retrying attempt {attempt + 2}/3 for coordinates ({x}, {y})")
                        continue
                    else:
                        logger.warning(f"GovMap parcel search failed after 3 attempts with HTTP 500 for coordinates ({x}, {y})")
                        raise GovMapError(f"Parcel search HTTP {r.status_code}")
                else:
                    # Other HTTP errors - don't retry
                    logger.warning(f"GovMap parcel search returned HTTP {r.status_code} for coordinates ({x}, {y})")
                    raise GovMapError(f"Parcel search HTTP {r.status_code}")
            except Exception as e:
                if attempt < 2:  # Don't retry on last attempt
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
                    logger.warning(f"GovMap parcel search failed, retrying attempt {attempt + 2}/3 for coordinates ({x}, {y}): {e}")
                    continue
                else:
                    logger.warning(f"GovMap parcel search failed after 3 attempts for coordinates ({x}, {y}): {e}")
                    raise GovMapError(f"Parcel search failed: {e}")
        
        # This should never be reached, but just in case
        raise GovMapError("Parcel search failed after all retry attempts")


    def get_base_layers(self) -> Dict[str, Any]:
        """Get base layers from GovMap API."""
        try:
            r = self.http.get(self.base_layers_url, timeout=self.timeout)
            if r.status_code != 200:
                raise GovMapError(f"Base layers HTTP {r.status_code}")
            return r.json()
        except Exception as e:
            logger.error(f"GovMap base layers failed: {e}")
            raise GovMapError(f"Base layers failed: {e}")

    # ----------------------------- Address insights -----------------------------
    def search_and_locate_address(self, address: str, search_type: int = 0) -> Dict[str, Any]:
        """Use the GovMap SearchAndLocate API to resolve an address."""

        payload = {"type": search_type, "address": address}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            response = self.http.post(
                self.search_and_locate_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
                verify=False,
            )
            if response.status_code != 200:
                raise GovMapError(f"SearchAndLocate HTTP {response.status_code}")
            return response.json()
        except Exception as e:
            logger.error(f"GovMap SearchAndLocate failed: {e}")
            raise GovMapError(f"SearchAndLocate failed: {e}")

    @staticmethod
    def extract_block_parcel(search_response: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Extract block/parcel identifiers from a SearchAndLocate response."""

        data = search_response.get("data") if isinstance(search_response, dict) else None
        if not data:
            return None

        first_entry = data[0]
        values = first_entry.get("Values") if isinstance(first_entry, dict) else None
        if not values or len(values) < 2:
            return None

        try:
            block = int(values[0])
            parcel = int(values[1])
            return block, parcel
        except (TypeError, ValueError):
            logger.debug("Failed to parse block/parcel from SearchAndLocate values: %s", values)
            return None

if __name__ == "__main__":
    api_client = GovMapClient()
    result = api_client.autocomplete("רוזוב 14 תל אביב")
    print(result)
    if result.get("results"):
        first = result["results"][0]
        x,y = api_client.extract_coordinates_from_shapes(first)
        print(f"Coordinates: {x}, {y}")
        parcel = api_client.get_parcel_data(x, y)
        print("Parcel data:", parcel)