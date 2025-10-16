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
import requests
import argparse
import json
import logging
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple



from utils.retry import request_with_retry
from pyproj import Transformer

from gis.parse_zchuyot import parse_html_privilege_page, parse_zchuyot


class ArcGISError(RuntimeError):
    pass

ALL_PERMIT_FIELDS = [
    "oid_permit","request_num","permission_date","permission_num","expiry_date","open_request",
    "building_num","yechidot_diyur","sw_tama_38","sw_tama_38_chadash","sw_tama_38_tosefet",
    "sug_bakasha","tochen_bakasha","finished","occupation","tr_hathalat_bniya","protected",
    "building_stage","koteret","progress","maslul_rishuy","url_hadmaya","ms_klali",
    "heara_teudat_gmar","k_sivug_makor","sivug_makor","request_stage","ms_tik_binyan",
    "addresses","hakala_tosefet_achuz_shetach","hakala_yd_hagdala_achuz","hakala_yd_mevukash",
    "hakala_yd_mutar","hakala_melel","hakala_nimuk","tik_tipul_1","tik_tipul_2","tik_tipul_3",
    "tik_tipul_4","tik_tipul_5","date_import"
]


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
        self._logger.info("ArcGIS request", extra={"method": method, "url": url})
        if method == "POST":
            r = request_with_retry(
                requests.post,
                url,
                data=params,
                headers=self.HDRS,
                timeout=30,
                max_retries=retries + 1,
            )
        else:
            r = request_with_retry(
                requests.get,
                url,
                params=params,
                headers=self.HDRS,
                timeout=30,
                max_retries=retries + 1,
            )
        self._logger.debug("ArcGIS response", extra={"status": r.status_code, "content_type": r.headers.get("Content-Type")})
        data = self._safe_json(r)
        if "_error" in data:
            self._logger.error("ArcGIS _error in payload", extra={"payload": data})
            raise ArcGISError(str(data))
        if "error" in data:
            self._logger.error("ArcGIS error payload", extra={"payload": data.get("error")})
            raise ArcGISError(str(data["error"]))
        return data

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

    def get_addresses_by_block_parcel(self, block: str, parcel: str) -> List[Dict[str, Any]]:
        """
        Returns list of addresses for a given block and parcel.
        Each address includes street name, house number, and coordinates.
        """
        self._logger.info("Looking up addresses by block/parcel", extra={"block": block, "parcel": parcel})
        
        # First, get the coordinates of the block/parcel center
        try:
            # Query parcels layer to get the geometry
            parcel_params = {
                "f": "pjson",
                "where": f"ms_gush = {block} AND ms_chelka = {parcel}",
                "outFields": "ms_gush,ms_chelka",
                "returnGeometry": "true",
                "resultRecordCount": 1,
            }
            parcel_data = self._query(self.L_PARCELS, parcel_params)
            parcel_feats = parcel_data.get("features", [])
            
            if not parcel_feats:
                self._logger.warning("Parcel not found", extra={"block": block, "parcel": parcel})
                return []
            
            # Get the geometry of the parcel
            parcel_geom = parcel_feats[0].get("geometry", {})
            if not parcel_geom:
                self._logger.warning("No geometry found for parcel", extra={"block": block, "parcel": parcel})
                return []
            
            # Query addresses that intersect with this parcel
            address_params = {
                "f": "pjson",
                "where": "1=1",
                "geometry": json.dumps(parcel_geom),
                "geometryType": "esriGeometryPolygon",
                "inSR": 2039,
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "t_rechov,ms_bayit,x,y",
                "returnGeometry": "false",
            }
            
            address_data = self._query(self.L_ADDR, address_params)
            address_feats = address_data.get("features", [])
            
            addresses = []
            for feat in address_feats:
                attrs = feat.get("attributes", {})
                if attrs.get("t_rechov") and attrs.get("ms_bayit"):
                    addresses.append({
                        "street": attrs.get("t_rechov", ""),
                        "house_number": attrs.get("ms_bayit"),
                        "x": float(attrs.get("x", 0)),
                        "y": float(attrs.get("y", 0)),
                    })
            
            self._logger.info("Found addresses for block/parcel", extra={
                "block": block, 
                "parcel": parcel, 
                "count": len(addresses)
            })
            return addresses
            
        except Exception as e:
            self._logger.error("Failed to lookup addresses by block/parcel", extra={
                "block": block, 
                "parcel": parcel, 
                "error": str(e)
            })
            return []

    def get_building_permits(self, x: float, y: float, radius: int = 50,
                             fields: Optional[Iterable[str]] = None,
                             download_pdfs: bool = False,
                             save_dir: Optional[str] = "permits") -> List[Dict[str, Any]]:
        """Spatial search around point (x,y) EPSG:2039. Returns attributes only.
        Args:
            x,y: coordinates (EPSG:2039)
            radius: buffer distance (meters)
            fields: iterable of field names (defaults to ALL_PERMIT_FIELDS)
            download_pdfs: also download linked permit PDFs
            save_dir: destination directory for PDFs
        """
        if fields is None:
            fields = ALL_PERMIT_FIELDS

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
            
            # Get blocks (block) and parcels (parcel) for the location
            blocks = self.get_blocks(x, y)
            parcels = self.get_parcels(x, y)
            
            if not blocks or not parcels:
                self._logger.warning("No blocks or parcels found for location", extra={"x": x, "y": y})
                return None
                
            # Extract block and parcel values
            block = blocks[0].get("ms_gush")
            parcel = parcels[0].get("ms_chelka")
            
            self._logger.info("Extracted values", extra={"block": block, "parcel": parcel, "blocks": blocks, "parcels": parcels})
            
            if not block or not parcel:
                self._logger.warning("Missing block or parcel values", extra={"block": block, "parcel": parcel})
                return None
                
            self._logger.info("Found block and parcel", extra={"block": block, "parcel": parcel})
            
            # Create save directory if it doesn't exist
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
            
            # Initialize result structure
            result = {
                "file_path": None,
                "content_type": None,
                "block": block,
                "parcel": parcel,
                "parcels": [],
                "pdf_data": [],
                "message": f"Building privilege pages for block {block}, parcel {parcel}"
            }

            # Try to download privilege pages
            # First, try the main page to see if it returns a PDF directly or HTML with options
            main_url = f"https://gisn.tel-aviv.gov.il/medamukdam/fr_asp/fr_meda_main.asp?gush={block}&helka={parcel}&iriaMode=internet"
            
            self._logger.info("Checking main privilege page", extra={"url": main_url})
            main_response = requests.get(main_url, headers=self.HDRS, timeout=30, allow_redirects=True)
            main_response.raise_for_status()

            # Check if this is a PDF (single privilege document)
            main_content_type = main_response.headers.get("Content-Type", "").lower()
            if "pdf" in main_content_type or main_response.content.startswith(b'%PDF'):
                self._logger.info("Main page returns PDF directly - single privilege document")
                result["content_type"] = "pdf"

                # Save the PDF
                filename = f"privilege_block_{block}_parcel_{parcel}.pdf"
                dest_path = os.path.join(save_dir, filename)
                result["file_path"] = dest_path


                with open(dest_path, "wb") as fh:
                    fh.write(main_response.content)

                # Parse the PDF
                try:
                    parsed_pdf = parse_zchuyot(dest_path)
                    result["pdf_data"].append({
                        "file_path": dest_path,
                        "data": parsed_pdf,
                        "option": 1
                    })
                    result["message"] += " - downloaded 1 privilege page (main page PDF)"
                    self._logger.info("Successfully downloaded and parsed main page PDF")
                except Exception as e:
                    self._logger.warning(f"Failed to parse main page PDF: {e}")
                    result["message"] += " - downloaded 1 privilege page (parsing failed)"

            elif "html" in main_content_type or "text" in main_content_type:
                # Main page is HTML - check for multiple options
                html_content = main_response.content.decode('utf-8', errors='ignore')
                result["content_type"] = "html"


                # Look for JavaScript variables that might contain option data
                pattern = re.compile(r'OPTION\s+VALUE\s*=\s*["\']?(\d+)["\']?', re.IGNORECASE)
                matches = pattern.findall(html_content)
                if matches:
                    ints = [int(m) for m in matches]
                    try:

                        # Download each privilege page
                        for i in ints:
                            opt_url = f"https://gisn.tel-aviv.gov.il/medamukdam/fr_asp/fr_meda_single.asp?gush={block}&helka={parcel}&opt={i}&status=0&street=0&house=0&"
                            self._logger.info(f"Downloading privilege page {i}", extra={"url": opt_url})

                            try:
                                opt_response = requests.get(opt_url, headers=self.HDRS, timeout=30, allow_redirects=True)
                                opt_response.raise_for_status()

                                # Check if it's a PDF
                                opt_content_type = opt_response.headers.get("Content-Type", "").lower()
                                if "pdf" in opt_content_type or opt_response.content.startswith(b'%PDF'):
                                    filename = f"privilege_block_{block}_parcel_{parcel}_opt_{i}.pdf"
                                    dest_path = os.path.join(save_dir, filename)
                                    result["file_path"] = dest_path

                                    with open(dest_path, "wb") as fh:
                                        fh.write(opt_response.content)

                                    # Parse the PDF
                                    try:
                                        parsed_pdf = parse_zchuyot(dest_path)
                                        result["pdf_data"].append({
                                            "file_path": dest_path,
                                            "data": parsed_pdf,
                                            "option": i
                                        })
                                        self._logger.info(f"Successfully parsed privilege page {i}")
                                    except Exception as e:
                                        self._logger.warning(f"Failed to parse PDF privilege page {i}: {e}")
                                else:
                                    self._logger.warning(f"Privilege page {i} is not a PDF")

                            except Exception as e:
                                self._logger.warning(f"Failed to download privilege page {i}: {e}")

                        result["message"] += f" - found {len(ints)} options, downloaded {len(result['pdf_data'])} PDFs"

                    except Exception as e:
                        self._logger.warning(f"Failed to parse HTML privilege page options: {e}")
                        # Fall back to trying individual options
                        self._try_individual_privilege_options(block, parcel, save_dir, result)
                else:
                    # No options found, try individual options
                    self._try_individual_privilege_options(block, parcel, save_dir, result)
            else:
                # Main page is not HTML or PDF, try individual options
                self._try_individual_privilege_options(block, parcel, save_dir, result)


            return result
            
        except Exception as e:
            self._logger.error(f"Unexpected error in get_building_privilege_page: {e}", exc_info=True)
            return {"success": False, "error": str(e), "message": f"Unexpected error: {e}"}

    def _try_individual_privilege_options(self, block: int, parcel: int, save_dir: str, result: Dict[str, Any]) -> None:
        """Try downloading individual privilege page options (opt=1, opt=2, etc.)"""
        self._logger.info("Trying individual privilege page options", extra={"block": block, "parcel": parcel})
        
        # Try up to 5 options
        consecutive_empty = 0
        max_consecutive_empty = 5  # Don't stop early for now
        
        for opt in range(1, 6):
            opt_url = f"https://gisn.tel-aviv.gov.il/medamukdam/fr_asp/fr_meda_single.asp?gush={block}&helka={parcel}&opt={opt}&status=0&street=0&house=0&"
            
            try:
                self._logger.info(f"Trying privilege page option {opt}", extra={"url": opt_url})
                opt_response = requests.get(opt_url, headers=self.HDRS, timeout=30, allow_redirects=True)
                self._logger.info(f"Response status: {opt_response.status_code}, content-type: {opt_response.headers.get('Content-Type')}, size: {len(opt_response.content)}")
                opt_response.raise_for_status()
                self._logger.info(f"Request successful for option {opt}")
                
                # Check if it's a PDF
                opt_content_type = opt_response.headers.get("Content-Type", "").lower()
                self._logger.info(f"Content type check: '{opt_content_type}', PDF check: {opt_response.content.startswith(b'%PDF')}")
                if "pdf" in opt_content_type or opt_response.content.startswith(b'%PDF'):
                    self._logger.info(f"PDF detected for option {opt}, proceeding with download")
                    try:
                        filename = f"privilege_block_{block}_parcel_{parcel}_opt_{opt}.pdf"
                        dest_path = os.path.join(save_dir, filename)
                        
                        with open(dest_path, "wb") as fh:
                            fh.write(opt_response.content)
                        self._logger.info(f"File saved to {dest_path}")
                    except Exception as e:
                        self._logger.error(f"Failed to save file for option {opt}: {e}")
                        continue
                    
                    # Check if the PDF has meaningful content before parsing
                    try:
                        self._logger.info(f"Starting content check for option {opt}")
                        import pdfplumber
                        with pdfplumber.open(dest_path) as pdf:
                            total_text = ""
                            for page in pdf.pages:
                                text = page.extract_text()
                                if text:
                                    total_text += text
                            
                            # If PDF has less than 50 characters, consider it empty/blank
                            text_length = len(total_text.strip())
                            self._logger.info(f"Privilege page option {opt} has {text_length} characters")
                            if text_length < 50:
                                self._logger.info(f"Privilege page option {opt} appears to be blank ({text_length} chars), skipping")
                                consecutive_empty += 1
                                # Remove the empty file
                                import os
                                if os.path.exists(dest_path):
                                    os.remove(dest_path)
                                continue
                            else:
                                consecutive_empty = 0  # Reset counter for non-empty pages
                                
                    except Exception as e:
                        self._logger.warning(f"Failed to check PDF content for option {opt}: {e}")
                        # Don't skip on content check failure, just continue with parsing
                        consecutive_empty = 0
                    
                    # Parse the PDF if it has content
                    try:
                        self._logger.info(f"Starting PDF parsing for option {opt}")
                        parsed_pdf = parse_zchuyot(dest_path)
                        result["pdf_data"].append({
                            "file_path": dest_path, 
                            "data": parsed_pdf,
                            "option": opt
                        })
                        self._logger.info(f"Successfully downloaded and parsed privilege page option {opt}")
                        
                        # Set the first successful file as the main file path
                        if result["file_path"] is None:
                            result["file_path"] = dest_path
                            result["content_type"] = "pdf"
                            
                    except Exception as e:
                        self._logger.warning(f"Failed to parse PDF privilege page option {opt}: {e}")
                else:
                    self._logger.debug(f"Privilege page option {opt} is not a PDF (content-type: {opt_content_type})")
                    consecutive_empty += 1
                    
            except Exception as e:
                self._logger.debug(f"Failed to download privilege page option {opt}: {e}")
                consecutive_empty += 1
                # If we get a 404 or similar error, we've probably reached the end of available options
                if "404" in str(e) or "Not Found" in str(e):
                    break
            
            # Stop if we've hit too many consecutive empty pages
            if consecutive_empty >= max_consecutive_empty:
                self._logger.info(f"Stopping after {consecutive_empty} consecutive empty pages")
                break
        
        if result["pdf_data"]:
            result["message"] += f" - downloaded {len(result['pdf_data'])} valid privilege pages"
        else:
            result["message"] += " - no valid privilege pages found"

    def get_block_parcel_info(self, x: float, y: float) -> Dict[str, Any]:
        """
        Simple function to get block and parcel information without downloading the privilege page.
        This helps debug issues with the main function.
        """
        try:
            # Get blocks (block) and parcels (parcel) for the location
            blocks = self.get_blocks(x, y)
            parcels = self.get_parcels(x, y)
            
            if not blocks or not parcels:
                return {"error": "No blocks or parcels found", "blocks": blocks, "parcels": parcels}
                
            # Extract block and parcel values
            block = blocks[0].get("ms_gush")
            parcel = parcels[0].get("ms_chelka")
            
            if not block or not parcel:
                return {"error": "Missing block or parcel values", "block": block, "parcel": parcel}
                
            # Construct the privilege page URL
            privilege_url = f"https://gisn.tel-aviv.gov.il/medamukdam/fr_asp/fr_meda_main.asp?block={block}&parcel={parcel}&iriaMode=internet"
            
            return {
                "success": True,
                "block": block,
                "parcel": parcel,
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


    gs = TelAvivGS()
    x, y = gs.get_address_coordinates("רוזוב", 18)
    a = gs.get_plans_local(x, y)
    print(a)
    # print(gs.get_plans_citywide(x, y))
    # Download building privilege page
    # privilege_path = gs.get_building_privilege_page(x, y)
    # print(f"{privilege_path}")
