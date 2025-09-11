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
import math
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from pyproj import Transformer

logger = logging.getLogger(__name__)

DEFAULT_WMS = os.getenv("GOVMAP_WMS_URL", "https://open.govmap.gov.il/geoserver/opendata/wms")
DEFAULT_WFS = os.getenv("GOVMAP_WFS_URL", "https://open.govmap.gov.il/geoserver/opendata/ows")
DEFAULT_AUTOCOMPLETE = os.getenv(
    "GOVMAP_AUTOCOMPLETE_URL",
    "https://es.govmap.gov.il/TldSearch/api/AutoComplete",
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
        self.http = session or requests.Session()
        self.timeout = timeout
        self.http.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        })

    # ----------------------------- Search -----------------------------
    def autocomplete(self, query: str, ids: str = "276267023", gid: str = "govmap") -> Dict[str, Any]:
        """Call the public autocomplete endpoint (no token required).
        Returns the raw JSON (contains categories like NEIGHBORHOOD/STREET/BUILDING/etc.).
        """
        params = {"query": query, "ids": ids, "gid": gid}
        r = self.http.get(self.autocomplete_url, params=params, timeout=self.timeout, verify=False)
        if r.status_code != 200:
            raise GovMapError(f"Autocomplete HTTP {r.status_code}")
        return r.json()

    # ------------------------------ WMS -------------------------------
    def wms_getfeatureinfo(
        self,
        *,
        layer: str,
        x: float,
        y: float,
        info_format: str = "application/json",
        buffer_m: int = 5,
        srs: str = "EPSG:2039",
    ) -> List[WMSFeatureInfo]:
        """GetFeatureInfo around a point by synthesizing a tiny bbox around (x,y).
        Works well when WFS is not available for a layer.
        """
        size = 256  # px
        half = buffer_m
        minx, miny = x - half, y - half
        maxx, maxy = x + half, y + half
        bbox = f"{minx},{miny},{maxx},{maxy}"

        params = {
            "service": "WMS",
            "version": "1.1.1",
            "request": "GetFeatureInfo",
            "layers": layer,
            "query_layers": layer,
            "srs": srs,
            "bbox": bbox,
            "width": size,
            "height": size,
            "info_format": info_format,
            # click at center
            "x": size // 2,
            "y": size // 2,
        }
        r = self.http.get(self.wms_url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            raise GovMapError(f"WMS GetFeatureInfo HTTP {r.status_code}: {r.text[:200]}")
        data = r.json() if info_format.endswith("json") else {"features": []}
        out: List[WMSFeatureInfo] = []
        for f in data.get("features", []):
            attrs = f.get("properties") or f.get("attributes") or {}
            out.append(WMSFeatureInfo(layer=layer, attributes=attrs))
        return out

    # ------------------------------ WFS -------------------------------
    def wfs_get_features(
        self,
        *,
        layer: str,
        max_features: int = 50,
        cql_filter: Optional[str] = None,
        srs: str = "EPSG:2039",
        output_format: str = "application/json",
    ) -> Dict[str, Any]:
        params = {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": layer,
            "srsName": srs,
            "maxFeatures": max_features,
            "outputFormat": output_format,
        }
        if cql_filter:
            params["CQL_FILTER"] = cql_filter
        r = self.http.get(self.wfs_url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            raise GovMapError(f"WFS GetFeature HTTP {r.status_code}: {r.text[:200]}")
        return r.json()

    # ------------------------- Higher-level ---------------------------
    def get_parcel_at_point(
        self,
        x: float,
        y: float,
        *,
        layer: str = "opendata:PARCEL_ALL",  # allow override if naming differs
        geom_fields: Iterable[str] = ("the_geom", "geom"),
    ) -> Optional[Dict[str, Any]]:
        """Return the parcel feature that intersects (x,y) (EPSG:2039)."""
        # Try WFS first with CQL INTERSECTS
        for gf in geom_fields:
            try:
                cql = f"INTERSECTS({gf},POINT({x} {y}))"
                data = self.wfs_get_features(layer=layer, max_features=1, cql_filter=cql)
                feats = data.get("features", [])
                if feats:
                    return feats[0]
            except Exception as e:
                logger.debug("WFS INTERSECTS failed", extra={"geom_field": gf, "err": str(e)})
        # Fallback to WMS GetFeatureInfo
        try:
            info = self.wms_getfeatureinfo(layer=layer, x=x, y=y)
            if info:
                return {"type": "Feature", "properties": info[0].attributes}
        except Exception as e:
            logger.debug("WMS GetFeatureInfo fallback failed", extra={"err": str(e)})
        return None
