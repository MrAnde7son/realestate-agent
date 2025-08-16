# -*- coding: utf-8 -*-
"""
Thin wrapper around Tel-Aviv IView2 ArcGIS REST for real-estate due diligence.
Focus: address→coords, permits near point, land-use, plans, and a few env layers.

Usage (example):
    from utils.tel_aviv_gs import TelAvivGS
    gs = TelAvivGS()
    x,y = gs.get_address_coordinates('ק"מ', 3)      # EPSG:2039
    permits = gs.get_building_permits(x,y, radius=30)
    for p in permits:
        print(p["permission_num"], p["building_stage"], p["url_hadmaya"])
"""

from __future__ import annotations
import argparse
import json
import os
import re
import time
import logging
import math
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from pyproj import Transformer
from dateutil import parser as dtp

from .parse_zchuyot import parse_zchuyot, parse_html_privilege_page

class ArcGISError(RuntimeError):
    pass

class TelAvivGS:
    BASE = "https://gisn.tel-aviv.gov.il/arcgis/rest/services"
    # Layers
    L_ADDR           = "IView2RekaHeb/MapServer/0"    # כתובות: t_rechov, ms_bayit, x,y,lon,lat
    L_PERMITS        = "IView2/MapServer/772"         # בקשות והיתרי בניה
    L_LAND_USE_MAIN  = "IView2/MapServer/514"         # יעודי קרקע עיקריים
    L_LAND_USE_DET   = "IView2/MapServer/837"         # יעודי קרקע מפורט
    L_PARCELS        = "IView2/MapServer/524"         # חלקות
    L_BLOCKS         = "IView2/MapServer/525"         # גושים
    L_PLANS_LOCAL    = "IView2/MapServer/528"         # תב"עות – מקומיות/מפורטות
    L_PLANS_CITY     = "IView2/MapServer/683"         # תכניות כלל עירוניות
    L_DANGER_BLDG    = "IView2/MapServer/591"         # מבנים מסוכנים
    L_PRESERVE       = "IView2/MapServer/682"         # מבנים לשימור
    L_NOISE          = "IView2/MapServer/786"         # מפלסי רעש
    L_CELL           = "IView2/MapServer/625"         # אנטנות סלולריות קיימות
    L_CELL_WIP       = "IView2/MapServer/953"         # אנטנות בהקמה
    L_GREEN          = "IView2/MapServer/503"         # שטחים ירוקים
    L_SHELTERS       = "IView2/MapServer/592"         # מקלטים

    HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)... Safari/537.36"}

    CKAN = "https://data.gov.il/api/3/action"
    _TRANS_2039_4326 = Transformer.from_crs(2039, 4326, always_xy=True)

    # Module logger
    _logger = logging.getLogger(__name__)

    # ---------- low-level ----------
    def _safe_json(self, r: requests.Response) -> Dict[str, Any]:
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
        raise ArcGISError(f"Non-JSON response ({r.status_code}, {ct}); body[:200]={text[:200]}")

    def _query(self, layer: str, params: Dict[str, Any], method: str = "GET", retries: int = 1) -> Dict[str, Any]:
        url = f"{self.BASE}/{layer}/query"
        for attempt in range(retries + 1):
            try:
                self._logger.info("ArcGIS request", extra={"method": method, "url": url, "attempt": attempt})
                if method == "POST":
                    r = requests.post(url, data=params, headers=self.HDRS, timeout=30)
                else:
                    r = requests.get(url, params=params, headers=self.HDRS, timeout=30)
                self._logger.debug("ArcGIS response", extra={"status": r.status_code, "content_type": r.headers.get("Content-Type")})
                r.raise_for_status()
                data = self._safe_json(r)
                if "_error" in data:
                    self._logger.error("ArcGIS _error in payload", extra={"payload": data})
                    raise ArcGISError(str(data))
                # ArcGIS error payload
                if "error" in data:
                    self._logger.error("ArcGIS error payload", extra={"payload": data.get("error")})
                    raise ArcGISError(str(data["error"]))
                return data
            except (requests.RequestException, ArcGISError) as e:
                if attempt < retries:
                    self._logger.warning("ArcGIS request failed, retrying", extra={"attempt": attempt, "error": str(e)})
                    time.sleep(0.8 * (attempt + 1))
                    continue
                self._logger.error("ArcGIS request failed", extra={"error": str(e)})
                raise

    def get_address_coordinates(self, street: str, house_number: int, like: bool = True) -> Tuple[float, float]:
        """
        Returns (x,y) in EPSG:2039 for the given street & house number.
        """
        self._logger.info("Geocoding address", extra={"street": street, "house_number": house_number, "like": like})
        if like:
            where = f"t_rechov LIKE '%{street}%' AND ms_bayit = {house_number}"
        else:
            where = f"t_rechov = '{street}' AND ms_bayit = {house_number}"
        self._logger.debug("Address WHERE", extra={"where": where})
        params = {
            "f": "pjson",
            "where": where,
            "outFields": "x,y",
            "returnGeometry": "false",
            "resultRecordCount": 1,
        }
        data = self._query(self.L_ADDR, params)
        feats = data.get("features", [])
        if not feats:
            self._logger.warning("Address not found", extra={"where": where})
            raise ArcGISError("Address not found")
        a = feats[0]["attributes"]
        x, y = float(a["x"]), float(a["y"])
        self._logger.info("Geocoded address -> coords", extra={"x": x, "y": y})
        return x, y

    def get_building_permits(self, x: float, y: float, radius: int = 30,
                             fields: Optional[Iterable[str]] = None,
                             download_pdfs: bool = False,
                             save_dir: Optional[str] = "permits") -> List[Dict[str, Any]]:
        """
        Spatial search around point (x,y) EPSG:2039. Returns attributes only.
        """
        if fields is None:
            fields = ["request_num", "permission_num", "building_stage", "url_hadmaya", "addresses", "permission_date"]
        self._logger.info("Querying permits around point", extra={"x": x, "y": y, "radius_m": radius})
        params = {
            "f": "pjson",
            "where": "1=1",
            "geometry": json.dumps({"x": x, "y": y}),
            "geometryType": "esriGeometryPoint",
            "inSR": 2039,
            "spatialRel": "esriSpatialRelIntersects",
            "distance": radius,
            "units": "esriSRUnit_Meter",
            "outFields": ",".join(fields),
            "returnGeometry": "false",
        }
        data = self._query(self.L_PERMITS, params)
        permits = [f.get("attributes", {}) for f in data.get("features", [])]
        self._logger.info("Permits fetched", extra={"count": len(permits)})

        if download_pdfs and save_dir:
            self._logger.info("Downloading permit PDFs", extra={"dir": save_dir})
            os.makedirs(save_dir, exist_ok=True)
            for attrs in permits:
                url = self.normalize_doc_url(attrs.get("url_hadmaya"))
                if not url:
                    self._logger.debug("Skipping permit without url_hadmaya", extra={"attrs": {k: attrs.get(k) for k in ("permission_num","request_num")}})
                    continue
                perm_num = attrs.get("permission_num")
                req_num = attrs.get("request_num")
                base = str(perm_num or req_num or "permit")
                filename = self.safe_filename(base) + ".pdf"
                dest_path = os.path.join(save_dir, filename)
                try:
                    self._logger.debug("Downloading PDF", extra={"url": url, "dest": dest_path})
                    r = requests.get(url, timeout=30, allow_redirects=True)
                    r.raise_for_status()
                    with open(dest_path, "wb") as fh:
                        fh.write(r.content)
                except requests.RequestException as e:
                    self._logger.warning("Failed to download PDF", extra={"url": url, "error": str(e)})
        return permits

    def get_land_use_main(self, x: float, y: float) -> List[Dict[str, Any]]:
        return self._intersects_point(self.L_LAND_USE_MAIN, x, y)

    def get_land_use_detailed(self, x: float, y: float) -> List[Dict[str, Any]]:
        return self._intersects_point(self.L_LAND_USE_DET, x, y)

    def get_plans_local(self, x: float, y: float) -> List[Dict[str, Any]]:
        return self._intersects_point(self.L_PLANS_LOCAL, x, y)

    def get_plans_citywide(self, x: float, y: float) -> List[Dict[str, Any]]:
        return self._intersects_point(self.L_PLANS_CITY, x, y)

    def get_parcels(self, x: float, y: float) -> List[Dict[str, Any]]:
        return self._intersects_point(self.L_PARCELS, x, y)

    def get_blocks(self, x: float, y: float) -> List[Dict[str, Any]]:
        return self._intersects_point(self.L_BLOCKS, x, y)

    def get_dangerous_buildings(self, x: float, y: float, radius: int = 80) -> List[Dict[str, Any]]:
        return self._intersects_point(self.L_DANGER_BLDG, x, y, radius)

    def get_preservation(self, x: float, y: float, radius: int = 80) -> List[Dict[str, Any]]:
        return self._intersects_point(self.L_PRESERVE, x, y, radius)

    def get_noise_levels(self, x: float, y: float) -> List[Dict[str, Any]]:
        return self._intersects_point(self.L_NOISE, x, y)

    def get_cell_antennas(self, x: float, y: float, radius: int = 120) -> List[Dict[str, Any]]:
        out = self._intersects_point(self.L_CELL, x, y, radius)
        out += self._intersects_point(self.L_CELL_WIP, x, y, radius)
        return out

    def get_green_areas(self, x: float, y: float, radius: int = 150) -> List[Dict[str, Any]]:
        return self._intersects_point(self.L_GREEN, x, y, radius)

    def get_shelters(self, x: float, y: float, radius: int = 200) -> List[Dict[str, Any]]:
        return self._intersects_point(self.L_SHELTERS, x, y, radius)

    def get_building_privilege_page(self, x: float, y: float, save_dir: Optional[str] = "privilege_pages") -> Optional[Dict[str, Any]]:
        """
        Downloads building privilege page for a given location and automatically detects content type.
        For HTML pages, extracts all parcels and downloads any linked PDF files for parsing.
        For PDF pages, downloads and parses the file directly.
        
        Args:
            x: X coordinate in EPSG:2039
            y: Y coordinate in EPSG:2039  
            save_dir: Directory to save the privilege page (default: "privilege_pages")
            
        Returns:
            Dictionary with file_path, content_type, and parsed data, or None if failed
        """
        try:
            self._logger.info("Getting building privilege page", extra={"x": x, "y": y})
            
            # Get blocks (gush) and parcels (helka) for the location
            blocks = self.get_blocks(x, y)
            parcels = self.get_parcels(x, y)
            
            if not blocks or not parcels:
                self._logger.warning("No blocks or parcels found for location", extra={"x": x, "y": y})
                return None
                
            # Extract gush and helka values
            gush = blocks[0].get("ms_gush")
            helka = parcels[0].get("ms_chelka")
            
            self._logger.info("Extracted values", extra={"gush": gush, "helka": helka, "blocks": blocks, "parcels": parcels})
            
            if not gush or not helka:
                self._logger.warning("Missing gush or helka values", extra={"gush": gush, "helka": helka})
                return None
                
            self._logger.info("Found gush and helka", extra={"gush": gush, "helka": helka})
            
            # Construct the privilege page URL
            privilege_url = f"https://gisn.tel-aviv.gov.il/medamukdam/fr_asp/fr_meda_main.asp?gush={gush}&helka={helka}&iriaMode=internet"
            
            self._logger.info("Constructed privilege URL", extra={"url": privilege_url, "gush": gush, "helka": helka})
            
            # Create save directory if it doesn't exist
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
            
            self._logger.info(
                "Downloading privilege page", extra={"url": privilege_url, "gush": gush, "helka": helka}
            )            
            r = requests.get(privilege_url, headers=self.HDRS, timeout=30, allow_redirects=True)
            r.raise_for_status()
            
            # Detect content type
            content_type = r.headers.get("Content-Type", "").lower()
            is_pdf = "pdf" in content_type
            is_html = "html" in content_type or "text" in content_type
            
            # Determine file extension
            if is_pdf:
                ext = ".pdf"
                content_type_detected = "pdf"
            elif is_html:
                ext = ".html"
                content_type_detected = "html"
            else:
                # Fallback: check content for PDF magic bytes
                if r.content.startswith(b'%PDF'):
                    ext = ".pdf"
                    content_type_detected = "pdf"
                else:
                    ext = ".html"
                    content_type_detected = "html"
            
            filename = f"privilege_gush_{gush}_helka_{helka}{ext}"
            dest_path = os.path.join(save_dir, filename)

            # Save the content
            with open(dest_path, "wb") as fh:
                fh.write(r.content)
                
            self._logger.info("Privilege page downloaded successfully", extra={"path": dest_path, "type": content_type_detected})
            
            # Initialize result structure
            result = {
                "file_path": dest_path,
                "content_type": content_type_detected,
                "gush": gush,
                "helka": helka,
                "parcels": [],
                "pdf_data": [],
                "message": f"Building privilege page downloaded ({content_type_detected})"
            }

            # Handle HTML content - extract parcels and linked PDFs
            if content_type_detected == "html":
                html_content = r.content.decode('utf-8', errors='ignore')
                try:
                    parsed_parcels = parse_html_privilege_page(html_content)
                    result["parcels"] = parsed_parcels
                    result["message"] += f" with {len(parsed_parcels)} parcels"
                    self._logger.info(f"Parsed {len(parsed_parcels)} parcels from HTML", extra={"parcel_count": len(parsed_parcels)})
                except Exception as e:
                    self._logger.warning(f"Failed to parse HTML parcels: {e}")
                    result["message"] += " (parcel parsing failed)"

                soup = BeautifulSoup(html_content, 'html.parser')
                pdf_links = [
                    self.normalize_doc_url(a['href'])
                    for a in soup.find_all('a', href=True)
                    if a['href'].lower().endswith('.pdf')
                ]
                for idx, pdf_url in enumerate(pdf_links, 1):
                    try:
                        pdf_resp = requests.get(pdf_url, headers=self.HDRS, timeout=30, allow_redirects=True)
                        pdf_resp.raise_for_status()
                        base_name = os.path.basename(pdf_url.split('?')[0]) or f"linked_{idx}.pdf"
                        safe_name = self.safe_filename(base_name)
                        if not safe_name.lower().endswith('.pdf'):
                            safe_name += '.pdf'
                        pdf_path = os.path.join(save_dir, safe_name)
                        with open(pdf_path, 'wb') as fh:
                            fh.write(pdf_resp.content)
                        parsed_pdf = parse_zchuyot(pdf_path)
                        result["pdf_data"].append({"file_path": pdf_path, "data": parsed_pdf})
                    except Exception as e:
                        self._logger.warning(f"Failed to download/parse linked PDF {pdf_url}: {e}")

            # Handle PDF content - parse directly
            elif content_type_detected == "pdf":
                try:
                    parsed_pdf = parse_zchuyot(dest_path)
                    result["pdf_data"].append({"file_path": dest_path, "data": parsed_pdf})
                    result["message"] += " and parsed"
                except Exception as e:
                    self._logger.warning(f"Failed to parse PDF privilege page: {e}")

            return result
            
        except Exception as e:
            self._logger.error(f"Unexpected error in get_building_privilege_page: {e}", exc_info=True)
            return {"success": False, "error": str(e), "message": f"Unexpected error: {e}"}

    def get_gush_helka_info(self, x: float, y: float) -> Dict[str, Any]:
        """
        Simple function to get gush and helka information without downloading the privilege page.
        This helps debug issues with the main function.
        """
        try:
            # Get blocks (gush) and parcels (helka) for the location
            blocks = self.get_blocks(x, y)
            parcels = self.get_parcels(x, y)
            
            if not blocks or not parcels:
                return {"error": "No blocks or parcels found", "blocks": blocks, "parcels": parcels}
                
            # Extract gush and helka values
            gush = blocks[0].get("ms_gush")
            helka = parcels[0].get("ms_chelka")
            
            if not gush or not helka:
                return {"error": "Missing gush or helka values", "gush": gush, "helka": helka}
                
            # Construct the privilege page URL
            privilege_url = f"https://gisn.tel-aviv.gov.il/medamukdam/fr_asp/fr_meda_main.asp?gush={gush}&helka={helka}&iriaMode=internet"
            
            return {
                "success": True,
                "gush": gush,
                "helka": helka,
                "url": privilege_url,
                "blocks": blocks,
                "parcels": parcels
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "message": f"Error: {e}"}

    def _intersects_point(self, layer: str, x: float, y: float, radius: Optional[int] = None,
                          out_fields: str = "*") -> List[Dict[str, Any]]:
        p = {
            "f": "pjson",
            "where": "1=1",
            "geometry": json.dumps({"x": x, "y": y}),
            "geometryType": "esriGeometryPoint",
            "inSR": 2039,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": out_fields,
            "returnGeometry": "false",
        }
        if radius:
            p["distance"] = radius
            p["units"] = "esriSRUnit_Meter"
        self._logger.info("Querying layer intersects point", extra={"layer": layer, "x": x, "y": y, "radius": radius})
        data = self._query(layer, p)
        feats = [f.get("attributes", {}) for f in data.get("features", [])]
        self._logger.debug("Layer features fetched", extra={"layer": layer, "count": len(feats)})
        return feats

    @staticmethod
    def normalize_doc_url(url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        u = url.strip()
        if u.startswith("/"):
            return "https://gisn.tel-aviv.gov.il" + u
        return u

    @staticmethod
    def safe_filename(s: str) -> str:
        return re.sub(r'[\\/*?:"<>|]', "_", s)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--street", required=True)
    ap.add_argument("--num", type=int, required=True)
    ap.add_argument("--radius", type=int, default=30)
    args = ap.parse_args()

    gs = TelAvivGS()
    x, y = gs.get_address_coordinates(args.street, args.num)
    print("2039 coords:", x, y)
    print(gs.get_land_use_main(x, y))
    
    permits = gs.get_building_permits(x, y, args.radius, download_pdfs=True, save_dir="permits")
    print("permits:", len(permits))
    if permits:
        p0 = permits[0]
        print({k: p0.get(k) for k in ("permission_num","building_stage","addresses","url_hadmaya")})
    
    # Download building privilege page
    privilege_path = gs.get_building_privilege_page(x, y)
    if privilege_path:
        print(f"Building privilege page downloaded to: {privilege_path}")
    else:
        print("Could not download building privilege page")
