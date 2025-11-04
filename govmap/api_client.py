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
* Keep layers configurable via constructor args (no environment variables).
"""
from enum import Enum
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List

import requests
from pyproj import Transformer
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Default endpoints (no env usage)
DEFAULT_WMS = "https://open.govmap.gov.il/geoserver/opendata/wms"
DEFAULT_WFS = "https://open.govmap.gov.il/geoserver/opendata/ows"

# Reusable transformers
_TO_WGS84 = Transformer.from_crs(2039, 4326, always_xy=True)
_FROM_WGS84 = Transformer.from_crs(4326, 2039, always_xy=True)

# 16 עסקאות נדל"ן
# 20 תחנות אוטובוס
# 407 תחנות רכבת
# 160 קווי מטרו
# 151 תחנות קווי מטרו
# 200723 התחדשות עירונית
# 400 מתקני ספורט
# 388 מסעדות
# 394 חניונים
# 150 אתרי רשות הטבע והגנים
# 417 מקלטים
# 17 בתי ספר
# 18 גני ילדים
# 215699 פארקים עירוניים
ENVIRONMENTAL_LAYER_IDS = [
    400, 394, 386, 150, 384, 305, 417, 20, 17, 15, 21, 16, 18, 407, 151, 160, 200723, 215699, 178, 388
]

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


class GovMapAuthError(GovMapError):
    """Raised when GovMap endpoints require authenticated access."""

    pass


class DealType(Enum):
    STREET = "street"
    NEIGHBORHOOD = "neighborhood"
    SETTLEMENT = "settlement"

class GovMapClient:
    """Thin client for GovMap OpenData and public endpoints."""

    def __init__(
        self,
        wms_url: str = DEFAULT_WMS,
        wfs_url: str = DEFAULT_WFS,
        session: Optional[requests.Session] = None,
        timeout: int = 30,
        api_token: Optional[str] = None,
        user_token: Optional[str] = None,
        domain: Optional[str] = None,
        auth_token: Optional[str] = None,  # pre-existing session token if you have it
    ) -> None:
        self.wms_url = wms_url.rstrip("?")
        self.wfs_url = wfs_url.rstrip("?")
        self.autocomplete_url = "https://www.govmap.gov.il/api/search-service/autocomplete"
        self.layers_catalog_url = "https://www.govmap.gov.il/api/layers-catalog/catalog"
        self.search_types_url = "https://www.govmap.gov.il/api/search-service/getTypes"
        self.parcel_search_url = "https://www.govmap.gov.il/api/layers-catalog/apps/parcel-search/address"
        self.base_layers_url = "https://www.govmap.gov.il/api/layers-catalog/baseLayers?language=he"
        self.entities_by_point_url = "https://www.govmap.gov.il/api/layers-catalog/entitiesByPoint"
        self.deals_url = "https://www.govmap.gov.il/api/real-estate/deals/{x},{y}/{radius}"
        self.specific_deals_url = "https://www.govmap.gov.il/api/real-estate/{deal_type}-deals/{polygon_id}?limit={limit}&offset={offset}&startDate={startDate}&endDate={endDate}"


        self.http = session or requests.Session()
        self.timeout = timeout
        self.http.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        })

        # Disable SSL warnings (you can set self.http.verify=True if you want strict TLS)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.http.mount('https://', requests.adapters.HTTPAdapter())
        self.http.verify = False

        # Auth state (no env usage)
        self.auth_data: Dict[str, str] = {}
        if api_token:
            self.auth_data["api_token"] = api_token
        if user_token:
            self.auth_data["user_token"] = user_token
        if domain:
            self.auth_data["domain"] = domain
        if auth_token:
            self.auth_data["token"] = auth_token

    # ----------------------------- Search -----------------------------
    def autocomplete(self, query: str, language: str = "he", max_results: int = 10) -> Dict[str, Any]:
        """Call the public autocomplete endpoint (no token required).
        Returns the raw JSON response from the new GovMap API.
        """
        # Create an isolated session for this request (keeps retries independent)
        session = requests.Session()
        session.verify = False

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update({
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
            "Content-Type": "application/json",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        })

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
        except Exception as e:
            logger.error(f"GovMap autocomplete failed: {e}")
            raise GovMapError(f"Autocomplete failed: {e}")

    @staticmethod
    def extract_coordinates_from_shapes(result: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """Extract ITM coordinates from autocomplete response."""
        if "shape" in result and isinstance(result["shape"], str):
            shape = result["shape"]
            # "POINT(3877998.167083787 3778264.858683848)"
            if shape.startswith("POINT("):
                coords_str = shape[6:-1]  # Remove "POINT(" and ")"
                parts = coords_str.split()
                if len(parts) >= 2:
                    try:
                        x = float(parts[0]); y = float(parts[1])
                        return x, y
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Failed to parse coordinates from shape '{shape}': {e}")
        return None

    def get_layers_catalog(self, language: str = "he") -> Dict[str, Any]:
        """Get the layers catalog from GovMap."""
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
        """Get search types from GovMap."""
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
        """Get parcel data for specific coordinates."""
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        coord_string = f"({x}%20{y})"
        url = f"{self.parcel_search_url}/{coord_string}"

        for attempt in range(3):
            try:
                r = self.http.get(url, headers=headers, timeout=self.timeout, verify=False)
                if r.status_code == 200:
                    return r.json()
                elif r.status_code == 500:
                    if attempt < 2:
                        import time; time.sleep(2 ** attempt)
                        logger.warning(f"GovMap parcel search HTTP 500, retrying attempt {attempt + 2}/3 for ({x}, {y})")
                        continue
                    raise GovMapError(f"Parcel search HTTP {r.status_code}")
                else:
                    logger.warning(f"GovMap parcel search returned HTTP {r.status_code} for ({x}, {y})")
                    raise GovMapError(f"Parcel search HTTP {r.status_code}")
            except Exception as e:
                if attempt < 2:
                    import time; time.sleep(2 ** attempt)
                    logger.warning(f"GovMap parcel search failed, retrying attempt {attempt + 2}/3 for ({x}, {y}): {e}")
                    continue
                logger.warning(f"GovMap parcel search failed after 3 attempts for ({x}, {y}): {e}")
                raise GovMapError(f"Parcel search failed: {e}")

        raise GovMapError("Parcel search failed after all retry attempts")

    def get_parcel_addresses(self, objectid: int) -> List[Dict[str, Any]]:
        """Get detailed address information for a parcel using its objectid."""
        logger.info(f"Getting parcel addresses for objectid: {objectid}")
        
        try:
            url = f"https://www.govmap.gov.il/api/layers-catalog/apps/address-search/parcel/{objectid}"
            r = self.http.get(url, timeout=self.timeout, verify=False)
            
            if r.status_code != 200:
                logger.warning(f"Parcel address API returned HTTP {r.status_code}")
                return []
            
            data = r.json()
            if not isinstance(data, list) or not data:
                logger.warning(f"No address data found for objectid {objectid}")
                return []
            
            addresses = []
            for feature in data:
                if feature.get("type") == "Feature":
                    props = feature.get("properties", {})
                    geometry = feature.get("geometry", {})
                    
                    # Extract coordinates from geometry
                    coords = None
                    if geometry.get("type") == "MultiPolygon":
                        # Get centroid of the first polygon
                        coords_list = geometry.get("coordinates", [[]])
                        if coords_list and coords_list[0] and coords_list[0][0]:
                            # Calculate centroid
                            polygon_coords = coords_list[0][0]
                            if polygon_coords:
                                x_sum = sum(coord[0] for coord in polygon_coords)
                                y_sum = sum(coord[1] for coord in polygon_coords)
                                coords = (x_sum / len(polygon_coords), y_sum / len(polygon_coords))
                    
                    address = {
                        "street": props.get("str_name", ""),
                        "house_number": props.get("house_num"),
                        "city": props.get("setl_name", ""),
                        "locality": props.get("locality_name", ""),
                        "objectid": props.get("address_objectid"),
                        "x": coords[0] if coords else None,
                        "y": coords[1] if coords else None,
                    }
                    
                    addresses.append(address)
            
            logger.info(f"Found {len(addresses)} addresses for objectid {objectid}")
            return addresses
            
        except Exception as e:
            logger.error(f"Failed to get parcel addresses for objectid {objectid}: {e}")
            return []

    def get_addresses_by_block_parcel(self, block: str, parcel: str) -> List[Dict[str, Any]]:
        """Get addresses for a given block and parcel using GovMap autocomplete API."""
        logger.info(f"Looking up addresses by block/parcel in GovMap: {block}/{parcel}")
        
        try:
            # Search for the specific parcel using autocomplete
            parcel_query = f"גוש {block} חלקה {parcel}"
            logger.info(f"Searching for parcel: {parcel_query}")
            
            parcel_result = self.autocomplete(parcel_query, max_results=50)
            parcel_results = parcel_result.get("results", [])
            
            if not parcel_results:
                logger.warning(f"Parcel not found in GovMap autocomplete: {parcel_query}")
                return []
            
            # Find the exact parcel match
            target_parcel = None
            for result in parcel_results:
                if result.get("type") == "parcel" and result.get("text") == parcel_query:
                    target_parcel = result
                    break
            
            if not target_parcel:
                logger.warning(f"Exact parcel match not found for {parcel_query}")
                return []
            
            # Extract coordinates from the parcel
            parcel_coords = self.extract_coordinates_from_shapes(target_parcel)
            if not parcel_coords:
                logger.warning(f"Could not extract coordinates from parcel {parcel_query}")
                return []
            
            parcel_x, parcel_y = parcel_coords
            logger.info(f"Found parcel {parcel_query} at coordinates: {parcel_x}, {parcel_y}")
            
            # Now search for addresses in the same area using the block
            # Use the block number to find nearby addresses
            address_query = f"גוש {block}"
            logger.info(f"Searching for addresses near block: {address_query}")
            
            address_result = self.autocomplete(address_query, max_results=100)
            address_results = address_result.get("results", [])
            
            addresses = []
            for result in address_results:
                result_type = result.get("type", "")
                result_text = result.get("text", "")
                
                # Look for address-related results (streets, settlements, etc.)
                if result_type in ["address", "settlement", "poi"] and result_text:
                    coords = self.extract_coordinates_from_shapes(result)
                    if coords:
                        addr_x, addr_y = coords
                        # Check if the address is reasonably close to our parcel
                        distance = ((addr_x - parcel_x) ** 2 + (addr_y - parcel_y) ** 2) ** 0.5
                        if distance < 2000:  # Within 2km
                            # Parse the address text
                            street_name = result_text
                            
                            # Try to extract house number if present
                            house_number = None
                            if " " in result_text:
                                parts = result_text.split()
                                for part in parts:
                                    if part.isdigit():
                                        house_number = int(part)
                                        break
                            
                            addresses.append({
                                "street": street_name,
                                "house_number": house_number,
                                "city": "",  # Will be extracted from context
                                "x": addr_x,
                                "y": addr_y,
                            })
            
            # If we found addresses, return them
            if addresses:
                logger.info(f"Found {len(addresses)} addresses for block {block}, parcel {parcel}")
                return addresses
            
            # If no specific addresses found, create a generic one based on the parcel
            logger.info("No specific addresses found, creating generic address from parcel location")
            addresses.append({
                "street": f"גוש {block} חלקה {parcel}",
                "house_number": None,
                "city": "",
                "x": parcel_x,
                "y": parcel_y,
            })
            
            logger.info(f"Created generic address for block {block}, parcel {parcel}")
            return addresses
            
        except Exception as e:
            logger.error(f"Failed to lookup addresses by block/parcel in GovMap: {e}")
            return []

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

    # ----------------------------- Utils -----------------------------
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
            block = int(values[0]); parcel = int(values[1])
            return block, parcel
        except (TypeError, ValueError):
            logger.debug("Failed to parse block/parcel from SearchAndLocate values: %s", values)
            return None

    def entities_by_point(
        self,
        x_itm: float,
        y_itm: float,
        layer_ids: list[str] | list[int] = ENVIRONMENTAL_LAYER_IDS,
        radius: float = 100.0,
    ):
        layers = [{"layerId": str(lid)} for lid in layer_ids]

        payload = {
            "point": [float(x_itm), float(y_itm)],
            "layers": layers,
            "tolerance": float(radius),
        }

        r = self.http.post(self.entities_by_point_url, json=payload, timeout=self.timeout, verify=False)
        if r.status_code != 200:
            raise GovMapError(f"entitiesByPoint HTTP {r.status_code}")
        json_resp = r.json()
        if json_resp and json_resp.get("data"):
            return json_resp["data"]
        return []

    # ----------------------------- Deals -----------------------------
    def get_deals_by_location(
        self,
        x: float,
        y: float,
        start_date: str = "1998-01",
        end_date: str = "2025-11",
        radius: float = 100.0,
        deal_type: DealType = DealType.STREET,
        limit: int = 9,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get deals for a specific location and radius with detailed deal information.
        
        This method fetches deals for a location and automatically retrieves detailed
        deal data for each polygon_id found.
        
        Parameters
        ----------
        x : float
            ITM X coordinate
        y : float
            ITM Y coordinate
        radius : float
            Radius in meters to search for deals
        deal_type : str
            Type of deals: "street", "neighborhood", or "settlement" (default: "street")
        limit : int
            Maximum number of deals to return per polygon (default: 9)
        offset : int
            Offset for pagination (default: 0)
        start_date : Optional[str]
            Start date in format "YYYY-MM" (e.g., "1998-01")
        end_date : Optional[str]
            End date in format "YYYY-MM" (e.g., "2025-11")
            
        Returns
        -------
        List[Dict[str, Any]]
            List of enriched deal entries. Each entry contains:
            - Original polygon data (dealscount, settlementNameHeb, polygon_id, objectid, etc.)
            - Detailed deal data (deals array with dealAmount, dealDate, assetArea, etc.)
        """
        try:
            url = self.deals_url.format(x=x, y=y, radius=radius)
            
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
                "Content-Type": "application/json",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }
            
            r = self.http.get(url, headers=headers, timeout=self.timeout, verify=False)
            if r.status_code != 200:
                raise GovMapError(f"Get deals by location HTTP {r.status_code}")
            
            response = r.json()
            deals_list = []
            if isinstance(response, list):
                deals_list = response
            elif isinstance(response, dict) and "data" in response:
                deals_list = response["data"]
            
            # Enrich each deal with detailed data
            enriched_deals = []
            for deal in deals_list:
                polygon_id = deal.get("polygon_id")
                if polygon_id:
                    try:
                        details = self._get_deal_details(
                            polygon_id=polygon_id,
                            start_date=start_date,
                            end_date=end_date,
                            deal_type=deal_type,
                            limit=limit,
                            offset=offset,
                        )
                        # Merge detailed deal data into the deal entry
                        deal["deals"] = details.get("data", [])
                        deal["totalCount"] = details.get("totalCount")
                        deal["limit"] = details.get("limit")
                        deal["offset"] = details.get("offset")
                    except Exception as e:
                        logger.warning(f"Failed to get deal details for polygon_id {polygon_id}: {e}")
                        # Keep the deal entry even if details fetch fails
                        deal["deals"] = []
                        deal["totalCount"] = "0"
                
                enriched_deals.append(deal)
            
            return enriched_deals
            
        except Exception as e:
            logger.error(f"Failed to get deals by location for ({x}, {y}) with radius {radius}: {e}")
            raise GovMapError(f"Get deals by location failed: {e}")

    def _get_deal_details(
        self,
        polygon_id: str,
        start_date: str = "1998-01",
        end_date: str = "2025-11",
        deal_type: DealType = DealType.STREET,
        limit: int = 9,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get detailed deal data for a specific polygon_id (protected method).
        
        This method is called internally by get_deals_by_location to fetch detailed
        deal information for each polygon_id.
        
        Parameters
        ----------
        polygon_id : str
            Polygon ID (e.g., "7228-50")
        deal_type : DealType
            Type of deals: "street", "neighborhood", or "settlement" (default: "street")
        limit : int
            Maximum number of deals to return (default: 9)
        offset : int
            Offset for pagination (default: 0)
        start_date : Optional[str]
            Start date in format "YYYY-MM" (e.g., "1998-01")
        end_date : Optional[str]
            End date in format "YYYY-MM" (e.g., "2025-11")
            
        Returns
        -------
        Dict[str, Any]
            Response containing totalCount, data (list of deals), limit, and offset.
            Each deal in data contains: objectid, dealAmount, dealDate, assetArea, 
            propertyTypeDescription, dealNatureDescription, etc.
        """
        try:
            url = self.specific_deals_url.format(
                deal_type=deal_type.value,
                polygon_id=polygon_id,
                limit=limit,
                offset=offset,
                startDate=start_date,
                endDate=end_date,
            )
            
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
                "Content-Type": "application/json",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }
            
            r = self.http.get(url, headers=headers, timeout=self.timeout, verify=False)
            if r.status_code != 200:
                raise GovMapError(f"Get deal details HTTP {r.status_code}")
            
            return r.json()
            
        except Exception as e:
            logger.error(f"Failed to get deal details for polygon_id {polygon_id}: {e}")
            raise GovMapError(f"Get deal details failed: {e}")


if __name__ == "__main__":
    api_client = GovMapClient()
    result = api_client.autocomplete("רוזוב 14 תל אביב")
    catalog = api_client.get_layers_catalog().get('catalog', [])
    if result.get("results"):
        first = result["results"][0]
        coords = api_client.extract_coordinates_from_shapes(first)
        if coords:
            x, y = coords
            # entities = api_client.entities_by_point(x, y, radius=1000.0)
            # print(entities)
            deals = api_client.get_deals_by_location(x, y)
            print(deals)


