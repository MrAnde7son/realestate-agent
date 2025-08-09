import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import requests

DEFAULT_BASE_URL = "https://gisn.tel-aviv.gov.il/arcgis/rest/services"

logger = logging.getLogger(__name__)


def normalize_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    url = url.strip()
    if url.startswith('/'):
        return 'https://gisn.tel-aviv.gov.il' + url
    return url


def safe_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)


class TelAvivGISClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, session: Optional[requests.Session] = None) -> None:
        self.base_url = base_url.rstrip('/')
        self.session = session or requests.Session()

    def _get(self, path: str, params: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        logger.info("HTTP GET", extra={"url": url, "params": params})
        resp = self.session.get(url, params=params, timeout=timeout)
        logger.debug("HTTP response", extra={"status": resp.status_code, "content_type": resp.headers.get("Content-Type")})
        resp.raise_for_status()
        payload = resp.json()
        return payload

    def geocode_address(self, where_clause: str) -> Optional[Dict[str, float]]:
        params = {
            "f": "pjson",
            "where": where_clause,
            "outFields": "x,y",
            "returnGeometry": "false",
        }
        payload = self._get("IView2RekaHeb/MapServer/0/query", params)
        features = payload.get("features", [])
        if not features:
            logger.warning("No address features found", extra={"where": where_clause})
            return None
        attrs = features[0].get("attributes", {})
        x = attrs.get("x")
        y = attrs.get("y")
        logger.info("Geocoded address", extra={"x": x, "y": y})
        if x is None or y is None:
            return None
        return {"x": x, "y": y}

    def query_permits(
        self,
        permit_where: str = "1=1",
        point_xy: Optional[Dict[str, float]] = None,
        distance_meters: int = 2000,
        out_fields: str = "request_num,permission_num,building_stage,url_hadmaya,addresses,permission_date",
        return_geometry: bool = False,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "f": "pjson",
            "where": permit_where,
            "geometryType": "esriGeometryPoint",
            "inSR": 2039,
            "spatialRel": "esriSpatialRelIntersects",
            "distance": distance_meters,
            "units": "esriSRUnit_Meter",
            "outFields": out_fields,
            "returnGeometry": str(return_geometry).lower(),
        }
        if point_xy is not None:
            params["geometry"] = json.dumps(point_xy)
        payload = self._get("IView2/MapServer/772/query", params)
        features = payload.get("features", [])
        logger.info("Received permits", extra={"count": len(features)})
        return features


def download_permit_pdfs(features: List[Dict[str, Any]], save_dir: str = "permits") -> List[str]:
    os.makedirs(save_dir, exist_ok=True)
    saved_paths: List[str] = []
    for feature in features:
        attrs = feature.get("attributes", {})
        url = normalize_url(attrs.get("url_hadmaya"))
        if not url:
            logger.debug("Skipping feature without url_hadmaya", extra={"attrs": attrs})
            continue
        perm_num = attrs.get('permission_num')
        req_num = attrs.get('request_num')
        base = str(perm_num or req_num or 'permit')
        filename = safe_filename(base) + '.pdf'
        dest_path = os.path.join(save_dir, filename)
        try:
            logger.info("Downloading permit PDF", extra={"url": url, "dest": dest_path})
            resp = requests.get(url, timeout=30, allow_redirects=True)
            resp.raise_for_status()
            with open(dest_path, 'wb') as fh:
                fh.write(resp.content)
            saved_paths.append(dest_path)
            logger.info("Saved PDF", extra={"path": dest_path, "bytes": len(resp.content)})
        except Exception as e:
            logger.error("Failed to download PDF", extra={"url": url, "error": str(e)})
    return saved_paths


def query_tel_aviv_permits(
    address_where: Optional[str] = "t_rechov LIKE '%הגולן%' AND ms_bayit = 1",
    permit_where: str = "1=1",
    distance_meters: int = 2000,
    save_dir: Optional[str] = "permits",
) -> List[Dict[str, Any]]:
    """
    High-level helper: optionally geocode an address WHERE, then query permits, and
    optionally download PDFs if save_dir is provided.
    """
    # Set logging level from env if configured
    log_level = os.getenv("LOG_LEVEL")
    if log_level:
        logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))

    client = TelAvivGISClient()
    point_xy: Optional[Dict[str, float]] = None
    if address_where:
        logger.info("Geocoding address via WHERE", extra={"where": address_where})
        geo = client.geocode_address(address_where)
        if geo is None:
            logger.warning("Address geocoding returned no coordinates; proceeding without geometry filter")
        else:
            point_xy = {"x": geo["x"], "y": geo["y"]}

    features = client.query_permits(
        permit_where=permit_where,
        point_xy=point_xy,
        distance_meters=distance_meters,
    )

    if save_dir:
        download_permit_pdfs(features, save_dir=save_dir)

    return features 