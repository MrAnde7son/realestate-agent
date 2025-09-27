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
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests
from pyproj import Transformer
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Default endpoints (no env usage)
DEFAULT_WMS = "https://open.govmap.gov.il/geoserver/opendata/wms"
DEFAULT_WFS = "https://open.govmap.gov.il/geoserver/opendata/ows"
DEFAULT_AUTOCOMPLETE = "https://www.govmap.gov.il/api/search-service/autocomplete"

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


class GovMapAuthError(GovMapError):
    """Raised when GovMap endpoints require authenticated access."""

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
        *,
        api_token: Optional[str] = None,
        user_token: Optional[str] = None,
        domain: Optional[str] = None,
        auth_token: Optional[str] = None,  # pre-existing session token if you have it
    ) -> None:
        self.wms_url = wms_url.rstrip("?")
        self.wfs_url = wfs_url.rstrip("?")
        self.autocomplete_url = autocomplete_url
        self.layers_catalog_url = "https://www.govmap.gov.il/api/layers-catalog/catalog"
        self.search_types_url = "https://www.govmap.gov.il/api/search-service/getTypes"
        self.parcel_search_url = "https://www.govmap.gov.il/api/layers-catalog/apps/parcel-search/address"
        self.base_layers_url = "https://www.govmap.gov.il/api/layers-catalog/baseLayers?language=he"
        self.search_and_locate_url = "https://ags.govmap.gov.il/Api/Controllers/GovmapApi/SearchAndLocate"
        self.auth_url = "https://ags.govmap.gov.il/Api/Controllers/GovmapApi/Auth"

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
        """
        Resolve an address via GovMap SearchAndLocate with robust auth handling.
        Adds a last-chance unauthenticated attempt (some edges accept it).
        """
        payload = {"type": search_type, "address": address}

        def _attempt_header_auth() -> requests.Response:
            headers = self._build_auth_headers()
            return self.http.post(
                self.search_and_locate_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
                verify=False,
            )

        def _attempt_body_auth() -> requests.Response:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": "https://www.govmap.gov.il",
                "Referer": "https://www.govmap.gov.il/",
                "User-Agent": self.http.headers.get("User-Agent", "Mozilla/5.0"),
            }
            body = {**payload, "auth_data": {k: v for k, v in self.auth_data.items() if v}}
            return self.http.post(
                self.search_and_locate_url,
                json=body,
                headers=headers,
                timeout=self.timeout,
                verify=False,
            )

        # Try header-auth. If bootstrap needed, _build_auth_headers() will call _refresh_auth_token().
        try:
            resp = _attempt_header_auth()
        except Exception as e:
            raise GovMapError(f"SearchAndLocate failed (unauth attempt): {e}")

        try:
            data = resp.json()
        except Exception:
            # Non-JSON is possible on some errors. Expose snippet for debugging.
            snippet = (resp.text or "")[:300].replace("\n", " ")
            raise GovMapError(f"SearchAndLocate returned non-JSON. Payload snippet: {snippet}")

        # Handle tokenExpired in JSON payloads (rare when we got 200)
        if isinstance(data, dict) and data.get("tokenExpired") is True:
            self._refresh_auth_token()
            resp = _attempt_header_auth()
            if resp.status_code != 200:
                resp = _attempt_body_auth()
            if resp.status_code != 200:
                raise GovMapError(f"SearchAndLocate after token refresh failed: HTTP {resp.status_code}")
            data = resp.json()

        return data
    # ----------------------------- Auth helpers -----------------------------
    def _build_auth_headers(self) -> Dict[str, str]:
        """
        Return sanitized auth headers for GovMap private controllers.

        Behavior:
        - If api_token+user_token exist, send them (plus domain/token if present).
        - Else if session token exists, send token only.
        - Else bootstrap by calling _refresh_auth_token() to mint a token, then send token.
        """
        clean = {k: v for k, v in self.auth_data.items() if v}

        if clean.get("api_token") and clean.get("user_token"):
            pass
        elif clean.get("token"):
            clean = {"token": clean["token"]}
        else:
            # Bootstrap token
            self._refresh_auth_token()
            clean = {k: v for k, v in self.auth_data.items() if v}
            if clean.get("api_token") and clean.get("user_token"):
                pass
            elif clean.get("token"):
                clean = {"token": clean["token"]}
            else:
                raise GovMapAuthError("GovMap auth bootstrap failed: no token was obtained.")

        return {
            "auth_data": json.dumps(clean, ensure_ascii=False),
            "Origin": "https://www.govmap.gov.il",
            "Referer": "https://www.govmap.gov.il/",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": self.http.headers.get("User-Agent", "Mozilla/5.0"),
        }

    def _refresh_auth_token(self) -> None:
        """
        Refresh GovMap session token without env vars.

        Steps:
        1) Warm up cookies by GET https://www.govmap.gov.il/
        2) POST to several Auth endpoints with header-auth (auth_data header)
        3) Fallback: POST with body-auth
        4) Fallback: GET (some legacy edges)
        Tolerates non-JSON responses and logs a short snippet for debugging.
        """
        def _extract_token(obj: Any) -> Optional[str]:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(k, str) and k.lower() == "token" and isinstance(v, str) and v.strip():
                        return v.strip()
                for v in obj.values():
                    t = _extract_token(v)
                    if t:
                        return t
            elif isinstance(obj, list):
                for v in obj:
                    t = _extract_token(v)
                    if t:
                        return t
            return None

        # 0) Warm up cookies (important for some edges)
        try:
            self.http.get(
                "https://www.govmap.gov.il/",
                headers={
                    "User-Agent": self.http.headers.get("User-Agent", "Mozilla/5.0"),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": "https://www.govmap.gov.il/",
                },
                timeout=self.timeout,
                verify=False,
            )
        except Exception as _:
            # not fatal; continue
            pass

        # Ensure we always send a domain (anonymous bootstrap often requires domain)
        domain = (self.auth_data.get("domain") or "www.govmap.gov.il").strip()
        self.auth_data["domain"] = domain

        url = "https://ags.govmap.gov.il/Api/Controllers/GovmapApi/Auth"

        base_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://www.govmap.gov.il",
            "Referer": "https://www.govmap.gov.il/",
            "User-Agent": self.http.headers.get("User-Agent", "Mozilla/5.0"),
        }
        clean = {k: v for k, v in self.auth_data.items() if v}
        last_error = None

        try:
            headers1 = {**base_headers, "auth_data": json.dumps(clean or {"domain": domain}, ensure_ascii=False)}
            r = self.http.post(url, json={}, headers=headers1, timeout=self.timeout, verify=False)
            if r.status_code == 200:
                try:
                    data = r.json()
                except Exception:
                    data = None
                if isinstance(data, (dict, list)):
                    token = _extract_token(data)
                    if token:
                        self.auth_data["token"] = token
                        # Persist any returned fields
                        if isinstance(data, dict):
                            for k in ("api_token", "user_token", "domain"):
                                if data.get(k):
                                    self.auth_data[k] = data[k]
                        return
                # Log short snippet for diagnostics
                snippet = (r.text or "")[:300].replace("\n", " ")
                logger.warning(f"GovMap auth (header) returned 200 but no token. Payload snippet: {snippet}")
            elif r.status_code == 401:
                last_error = GovMapAuthError("GovMap authentication rejected credentials (HTTP 401).")
            else:
                last_error = GovMapError(f"GovMap auth HTTP {r.status_code} at {url}")
        except Exception as e:
            last_error = e

        if last_error:
            raise GovMapError(f"GovMap auth did not return a session token. Last error: {last_error}")
        raise GovMapError("GovMap auth did not return a session token.")
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


if __name__ == "__main__":
    api_client = GovMapClient()
    result = api_client.autocomplete("רוזוב 14 תל אביב")
    print(result)
    if result.get("results"):
        first = result["results"][0]
        coords = api_client.extract_coordinates_from_shapes(first)
        if coords:
            x, y = coords
            print(f"Coordinates: {x}, {y}")
            parcel = api_client.get_parcel_data(x, y)
            print("Parcel data:", parcel)
        else:
            print("No coordinates found in autocomplete result.")
