# -*- coding: utf-8 -*-
"""
Base class for proxy-based municipal GIS clients (Herzliya, Bat Yam, Ramat Gan).
These cities use the v5.gis-net.co.il proxy service instead of direct ArcGIS REST API.
"""

from __future__ import annotations
import requests
import json
import logging
from typing import Any, Dict, List, Tuple
from abc import ABC, abstractmethod

from utils.retry import request_with_retry


class ArcGISError(RuntimeError):
    pass


class ProxyGISClient(ABC):
    """Base class for proxy-based municipal GIS clients."""
    
    PROXY_BASE = "https://v5.gis-net.co.il/proxy/proxy.ashx"
    
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with default headers."""
        self._session.headers.update({
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        })
    
    @abstractmethod
    def get_service_url(self) -> str:
        """Return the ArcGIS service URL for this city."""
        pass
    
    @abstractmethod
    def get_referer(self) -> str:
        """Return the referer URL for this city."""
        pass
    
    @abstractmethod
    def get_cookies(self) -> Dict[str, str]:
        """Return the cookies needed for authentication."""
        pass
    
    @abstractmethod
    def get_layer_id_for_blocks(self) -> int:
        """Return the layer ID for blocks (גושים)."""
        pass
    
    @abstractmethod
    def get_layer_id_for_parcels(self) -> int:
        """Return the layer ID for parcels (חלקות)."""
        pass
    
    def _safe_json(self, r: requests.Response) -> Dict[str, Any]:
        """Safely parse JSON response."""
        ct = (r.headers.get("Content-Type") or "").lower()
        text = r.text
        if "json" in ct or text.lstrip().startswith(("{", "[")):
            try:
                return r.json()
            except Exception as e:
                try:
                    return json.loads(text)
                except Exception:
                    raise ArcGISError(f"JSON parse error: {e}; body[:200]={text[:200]}")
        error_preview = text[:500] if len(text) > 500 else text
        raise ArcGISError(f"Non-JSON response ({r.status_code}, {ct}); body[:500]={error_preview}")
    
    def _identify(self, x: float, y: float, layer_id: int, tolerance: int = 9) -> Dict[str, Any]:
        """Perform an identify operation at the given coordinates."""
        import uuid
        service_url = self.get_service_url()
        identify_path = f"{service_url}/identify"
        
        # Build query parameters - matching the format from actual network requests
        from urllib.parse import urlencode
        params_dict = {
            "f": "json",
            "tolerance": str(tolerance),
            "returnGeometry": "true",
            "returnFieldName": "false",
            "returnUnformattedValues": "false",
            "imageDisplay": "1688,873,96",
            "geometry": json.dumps({"x": x, "y": y}),
            "geometryType": "esriGeometryPoint",
            "sr": "2039",
            "layers": f"all:{layer_id}",
            "guid": str(uuid.uuid4()),  # Add GUID like successful requests
        }
        
        # Construct URL: PROXY_BASE?SERVICE_URL/identify?PARAMS
        # The proxy expects: proxy.ashx?http://arcgis.../identify?f=json&tolerance=9&...
        # So we append the service URL directly, then the encoded params
        params_string = urlencode(params_dict)
        proxy_url = f"{self.PROXY_BASE}?{identify_path}?{params_string}"
        
        headers = {
            "referer": self.get_referer(),
        }
        cookies = self.get_cookies()
        
        self._logger.debug(f"Identify request: {proxy_url[:100]}...")
        
        try:
            response = request_with_retry(
                self._session.get,
                proxy_url,
                headers=headers,
                cookies=cookies,
                timeout=60,
                max_retries=3,
            )
            data = self._safe_json(response)
            
            if "error" in data:
                self._logger.error("ArcGIS error in response", extra={"error": data.get("error")})
                raise ArcGISError(str(data.get("error")))
            
            return data
        except requests.RequestException as e:
            self._logger.error(f"Request failed: {e}")
            raise ArcGISError(f"Request failed: {e}")
    
    def _query(self, layer_id: int, where: str, return_geometry: bool = True, out_fields: str = "*", method: str = "GET") -> Dict[str, Any]:
        """Perform a query operation on a specific layer.
        
        Args:
            layer_id: Layer ID to query
            where: WHERE clause for the query
            return_geometry: Whether to return geometry
            out_fields: Fields to return
            method: HTTP method to use ("GET" or "POST")
        """
        import uuid
        service_url = self.get_service_url()
        query_path = f"{service_url}/{layer_id}/query"
        
        # Build query parameters - matching the format from actual network requests
        params_dict = {
            "f": "json",
            "where": where,
            "returnGeometry": "true" if return_geometry else "false",
            "spatialRel": "esriSpatialRelIntersects",  # Required even for non-spatial queries
            "outFields": out_fields,
            "guid": str(uuid.uuid4()),  # Generate a GUID like the actual requests
        }
        
        headers = {
            "referer": self.get_referer(),
        }
        cookies = self.get_cookies()
        
        if method.upper() == "POST":
            # For POST, use the proxy URL without params, send data in body
            proxy_url = f"{self.PROXY_BASE}?{query_path}"
            self._logger.debug(f"Query POST request: {proxy_url[:150]}...")
            
            try:
                response = request_with_retry(
                    self._session.post,
                    proxy_url,
                    data=params_dict,
                    headers=headers,
                    cookies=cookies,
                    timeout=60,
                    max_retries=3,
                )
            except requests.RequestException as e:
                self._logger.error(f"POST request failed: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_text = e.response.text[:500]
                        self._logger.error(f"Response body: {error_text}")
                    except Exception:
                        pass
                raise ArcGISError(f"Request failed: {e}")
        else:
            # For GET, construct URL with params
            from urllib.parse import urlencode
            params_string = urlencode(params_dict)
            proxy_url = f"{self.PROXY_BASE}?{query_path}?{params_string}"
            self._logger.debug(f"Query GET request: {proxy_url[:150]}...")
            
            try:
                response = request_with_retry(
                    self._session.get,
                    proxy_url,
                    headers=headers,
                    cookies=cookies,
                    timeout=60,
                    max_retries=3,
                )
            except requests.RequestException as e:
                self._logger.error(f"GET request failed: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_text = e.response.text[:500]
                        self._logger.error(f"Response body: {error_text}")
                    except Exception:
                        pass
                raise ArcGISError(f"Request failed: {e}")
        
        data = self._safe_json(response)
        
        if "error" in data:
            self._logger.error("ArcGIS error in response", extra={"error": data.get("error")})
            raise ArcGISError(str(data.get("error")))
        
        return data
    
    def get_blocks(self, x: float, y: float) -> List[Dict[str, Any]]:
        """Get blocks (גושים) at the given coordinates."""
        layer_id = self.get_layer_id_for_blocks()
        try:
            data = self._identify(x, y, layer_id)
            results = data.get("results", [])
            
            blocks = []
            for result in results:
                attrs = result.get("attributes", {})
                if attrs:
                    blocks.append(attrs)
            
            return blocks
        except ArcGISError as e:
            # If identify fails, log warning and return empty list
            # This allows the collector to continue with other data
            self._logger.warning(f"Failed to get blocks via identify: {e}")
            return []
    
    def get_parcels(self, x: float, y: float) -> List[Dict[str, Any]]:
        """Get parcels (חלקות) at the given coordinates."""
        layer_id = self.get_layer_id_for_parcels()
        try:
            data = self._identify(x, y, layer_id)
            results = data.get("results", [])
            
            parcels = []
            for result in results:
                attrs = result.get("attributes", {})
                if attrs:
                    parcels.append(attrs)
            
            return parcels
        except ArcGISError as e:
            # If identify fails, log warning and return empty list
            # This allows the collector to continue with other data
            self._logger.warning(f"Failed to get parcels via identify: {e}")
            return []
    
    def get_address_coordinates(self, street: str, house_number: int, like: bool = True) -> Tuple[float, float]:
        """
        Get coordinates for an address.
        
        Note: This is a placeholder implementation. These cities may not have
        a direct geocoding API like Tel Aviv. You may need to use GovMap or
        another geocoding service as a fallback.
        """
        raise NotImplementedError(
            f"Address geocoding not yet implemented for {self.__class__.__name__}. "
            "Consider using GovMap or another geocoding service."
        )
    
    def get_addresses_by_block_parcel(self, block: str, parcel: str) -> List[Dict[str, Any]]:
        """
        Get addresses for a block/parcel.
        
        Note: This may not be available for all cities.
        """
        raise NotImplementedError(
            f"Block/parcel address lookup not yet implemented for {self.__class__.__name__}"
        )
    
    # Placeholder methods that return empty lists for now
    # These can be implemented later if the cities support these layers
    
    def get_building_permits(self, x: float, y: float, radius: int = 50, **kwargs) -> List[Dict[str, Any]]:
        """Get building permits (placeholder - returns empty list)."""
        self._logger.warning(f"Building permits not yet implemented for {self.__class__.__name__}")
        return []
    
    def get_land_use_main(self, x: float, y: float) -> List[Dict[str, Any]]:
        """Get main land use (placeholder - returns empty list)."""
        return []
    
    def get_land_use_detailed(self, x: float, y: float) -> List[Dict[str, Any]]:
        """Get detailed land use (placeholder - returns empty list)."""
        return []
    
    def get_plans_local(self, x: float, y: float) -> List[Dict[str, Any]]:
        """Get local plans (placeholder - returns empty list)."""
        return []
    
    def get_plans_citywide(self, x: float, y: float) -> List[Dict[str, Any]]:
        """Get citywide plans (placeholder - returns empty list)."""
        return []
    
    def get_shelters(self, x: float, y: float, radius: int = 200) -> List[Dict[str, Any]]:
        """Get shelters (placeholder - returns empty list)."""
        return []
    
    def get_green_areas(self, x: float, y: float, radius: int = 150) -> List[Dict[str, Any]]:
        """Get green areas (placeholder - returns empty list)."""
        return []
    
    def get_noise_levels(self, x: float, y: float) -> List[Dict[str, Any]]:
        """Get noise levels (placeholder - returns empty list)."""
        return []
    
    def get_cell_antennas(self, x: float, y: float, radius: int = 120) -> List[Dict[str, Any]]:
        """Get cell antennas (placeholder - returns empty list)."""
        return []
    
    def get_dangerous_buildings(self, x: float, y: float, radius: int = 80) -> List[Dict[str, Any]]:
        """Get dangerous buildings (placeholder - returns empty list)."""
        return []
    
    def get_metro_stations(self, x: float, y: float, radius: int = 1000) -> List[Dict[str, Any]]:
        """Get metro stations (placeholder - returns empty list)."""
        return []
    
    def get_parking_lots(self, x: float, y: float, radius: int = 300) -> List[Dict[str, Any]]:
        """Get parking lots (placeholder - returns empty list)."""
        return []
    
    def get_schools(self, x: float, y: float, radius: int = 500) -> List[Dict[str, Any]]:
        """Get schools (placeholder - returns empty list)."""
        return []
    
    def get_construction_sites(self, x: float, y: float, radius: int = 300) -> List[Dict[str, Any]]:
        """Get construction sites (placeholder - returns empty list)."""
        return []
    
    def get_affordable_housing_projects(self, x: float, y: float, radius: int = 500) -> List[Dict[str, Any]]:
        """Get affordable housing projects (placeholder - returns empty list)."""
        return []
    
    def get_bike_paths(self, x: float, y: float, radius: int = 300) -> List[Dict[str, Any]]:
        """Get bike paths (placeholder - returns empty list)."""
        return []
    
    def get_soil_contamination(self, x: float, y: float, radius: int = 200) -> List[Dict[str, Any]]:
        """Get soil contamination (placeholder - returns empty list)."""
        return []
    
    def get_green_amenities(self, x: float, y: float, radius: int = 400) -> List[Dict[str, Any]]:
        """Get green amenities (placeholder - returns empty list)."""
        return []
    
    def get_medical_facilities(self, x: float, y: float, radius: int = 500) -> List[Dict[str, Any]]:
        """Get medical facilities (placeholder - returns empty list)."""
        return []
    
    def get_community_facilities(self, x: float, y: float, radius: int = 400) -> List[Dict[str, Any]]:
        """Get community facilities (placeholder - returns empty list)."""
        return []
    
    def get_dog_parks(self, x: float, y: float, radius: int = 400) -> List[Dict[str, Any]]:
        """Get dog parks (placeholder - returns empty list)."""
        return []
    
    def get_public_gardens(self, x: float, y: float, radius: int = 400) -> List[Dict[str, Any]]:
        """Get public gardens (placeholder - returns empty list)."""
        return []
    
    def get_playgrounds(self, x: float, y: float, radius: int = 400) -> List[Dict[str, Any]]:
        """Get playgrounds (placeholder - returns empty list)."""
        return []
    
    def get_medical_centers(self, x: float, y: float, radius: int = 500) -> List[Dict[str, Any]]:
        """Get medical centers (placeholder - returns empty list)."""
        return []
    
    def get_health_funds(self, x: float, y: float, radius: int = 500) -> List[Dict[str, Any]]:
        """Get health funds (placeholder - returns empty list)."""
        return []
    
    def get_pharmacies(self, x: float, y: float, radius: int = 500) -> List[Dict[str, Any]]:
        """Get pharmacies (placeholder - returns empty list)."""
        return []
    
    def get_tama38_key_areas(self, x: float, y: float, radius: int = 500) -> List[Dict[str, Any]]:
        """Get TAMA 38 key areas (placeholder - returns empty list)."""
        return []
    
    def get_road_works(self, x: float, y: float, radius: int = 200) -> List[Dict[str, Any]]:
        """Get road works (placeholder - returns empty list)."""
        return []

