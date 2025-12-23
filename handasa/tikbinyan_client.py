# -*- coding: utf-8 -*-
"""
Generic client for municipal tikbinyan (building files) portals.
Supports Bat Yam, Herzliya, and Ramat Gan.
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"


def _normalize_label(value: Optional[str]) -> str:
    """Normalize Hebrew text labels."""
    if not value:
        return ""
    text = str(value).replace("\xa0", " ").replace("\u200f", "").strip()
    text = re.sub(r"[()\[\],/]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class TikbinyanClient(ABC):
    """Base client for municipal tikbinyan (building files) portals."""

    def __init__(
        self,
        base_url: str,
        session: Optional[requests.Session] = None,
        timeout: float = 60.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        """Initialize the tikbinyan client.
        
        Args:
            base_url: Base URL for the tikbinyan portal (e.g., https://batyam.complot.co.il)
            session: Optional requests session
            timeout: Request timeout in seconds
            user_agent: User agent string
        """
        self.base_url = base_url.rstrip("/")
        self.tikbinyan_url = f"{self.base_url}/tikbinyan"
        self.session = session or requests.Session()
        self.timeout = timeout
        self.session.headers.setdefault("User-Agent", user_agent)
        # API base URL for the shared backend
        self.api_base = "https://handasi.complot.co.il/wsComplotPublicData/ComplotPublicData.asmx"

    @abstractmethod
    def get_site_id(self) -> str:
        """Get the site_id for this city (used in API calls).
        
        Returns:
            Site ID string (e.g., "81" for Bat Yam)
        """
        pass

    def get_cities(self) -> List[Dict[str, Any]]:
        """Get list of cities/municipalities.
        
        Returns:
            List of cities with label, value (site_id), and k fields
        """
        try:
            response = self.session.post(
                f"{self.api_base}/GetYeshuvim",
                json={"site_id": self.get_site_id()},
                headers={
                    "Content-Type": "application/json; charset=UTF-8",
                    "Origin": self.base_url,
                    "Referer": self.tikbinyan_url + "/",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            # Response format: {"d": [{"label": "בת ים", "v": "6200", "k": ""}, ...]}
            return data.get("d", [])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch cities: {e}")
            return []

    def get_streets(self, site_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of streets for the city.
        
        Args:
            site_id: Optional site_id (defaults to self.get_site_id())
            
        Returns:
            List of streets with label, value (street_id), and k (site_id) fields
        """
        if site_id is None:
            site_id = self.get_site_id()
        
        try:
            response = self.session.post(
                f"{self.api_base}/GetStreets",
                json={"site_id": site_id},
                headers={
                    "Content-Type": "application/json; charset=UTF-8",
                    "Origin": self.base_url,
                    "Referer": self.tikbinyan_url + "/",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            # Response format: {"d": [{"label": "הצפירה", "v": "320", "k": "6200"}, ...]}
            return data.get("d", [])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch streets: {e}")
            return []

    def _find_street_id(self, street_name: str, site_id: Optional[str] = None) -> Optional[str]:
        """Find street ID by street name.
        
        Args:
            street_name: Street name to search for
            site_id: Optional site_id
            
        Returns:
            Street ID if found, None otherwise
        """
        streets = self.get_streets(site_id)
        normalized_search = _normalize_label(street_name).lower()
        
        for street in streets:
            label = street.get("label", "")
            normalized_label = _normalize_label(label).lower()
            if normalized_search in normalized_label or normalized_label in normalized_search:
                return street.get("v")
        
        return None

    def _parse_address(self, address: str) -> tuple[Optional[str], Optional[int]]:
        """Parse address string to extract street name and house number.
        
        Args:
            address: Address string (e.g., "הצפירה 8" or "הצפירה")
            
        Returns:
            Tuple of (street_name, house_number)
        """
        if not address:
            return None, None
        
        # Try to extract house number (last number in the string)
        parts = address.strip().split()
        street_parts = []
        house_number = None
        
        for part in parts:
            # Check if part is a number
            try:
                num = int(part)
                if house_number is None:  # Take the first number found
                    house_number = num
            except ValueError:
                street_parts.append(part)
        
        street_name = " ".join(street_parts) if street_parts else address
        return street_name.strip() if street_name else None, house_number
    
    def _get_city_code(self) -> Optional[str]:
        """Get the city code (c parameter) from GetYeshuvim.
        
        Returns:
            City code string (the "v" field from GetYeshuvim response) or None
        """
        cities = self.get_cities()
        if cities:
            # Return the first city's value (v field) which is the city code
            return cities[0].get("v")
        return None
    
    def _fix_response_encoding(self, response: requests.Response) -> None:
        """Fix response encoding to handle UTF-8-SIG (UTF-8 with BOM) correctly.
        
        The server sends UTF-8-SIG but requests may detect it as ISO-8859-1,
        causing Hebrew text to appear as gibberish.
        """
        if response.apparent_encoding:
            response.encoding = response.apparent_encoding
        else:
            response.encoding = 'utf-8-sig'  # UTF-8 with BOM
    
    def _parse_buildings_table(self, html: str) -> List[Dict[str, Any]]:
        """Parse HTML table response to extract building information.
        
        Args:
            html: HTML response from GetTikimByAddress
            
        Returns:
            List of building dictionaries
        """
        import re
        
        buildings = []
        seen_ids = set()
        
        # The actual format from the API: javascript:getBuilding(3802)
        # Also look for building IDs in table rows
        building_id_patterns = [
            r'javascript:getBuilding\((\d+)\)',  # javascript:getBuilding(3802)
            r'href=["\']javascript:getBuilding\((\d+)\)["\']',  # In href attribute
            r'<td>\s*<a[^>]*>(\d+)</a>\s*</td>',  # Building ID in table cell
            r'building[_-]?id["\']?\s*[:=]\s*["\']?(\d+)',
            r'tik[_-]?id["\']?\s*[:=]\s*["\']?(\d+)',
            r'#building/(\d+)',
            r'building/(\d+)',
            r't=(\d+)',
        ]
        
        for pattern in building_id_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                building_id = str(match).strip()
                if building_id and building_id not in seen_ids:
                    seen_ids.add(building_id)
                    buildings.append({
                        "id": building_id,
                        "v": building_id,
                        "building_id": building_id,
                        "t": building_id,  # 't' is also used for building ID
                    })
        
        # Also try to parse as JSON if it's embedded
        json_pattern = r'\{[^{}]*"building[_-]?id"[^{}]*\}'
        json_matches = re.findall(json_pattern, html, re.IGNORECASE)
        for match in json_matches:
            try:
                import json
                data = json.loads(match)
                bid = data.get("building_id") or data.get("id") or data.get("v") or data.get("t")
                if bid and str(bid) not in seen_ids:
                    seen_ids.add(str(bid))
                    buildings.append(data)
            except (json.JSONDecodeError, ValueError):
                continue
        
        logger.debug(f"Parsed {len(buildings)} buildings from HTML: {buildings}")
        return buildings

    def _get_gush_file(self, block: str, parcel: Optional[str] = None) -> Optional[requests.Response]:
        """Get gush (block) file information using GetGushFile endpoint.
        
        Args:
            block: Block number (גוש)
            parcel: Parcel number (חלקה), optional
            
        Returns:
            Response object if successful, None otherwise
        """
        site_id = self.get_site_id()
        endpoint = "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"
        params = {
            "appname": "cixpa",
            "prgname": "GetGushFile",
            "siteid": site_id,
            "g": block,
            "arguments": "siteid,g",
        }
        
        if parcel:
            params["h"] = parcel
            params["arguments"] = "siteid,g,h"
        
        try:
            logger.info(f"Calling GetGushFile with params: {params}")
            response = self.session.get(
                endpoint,
                params=params,
                headers={
                    "Origin": self.base_url,
                    "Referer": f"{self.base_url}/gush2/",
                },
                timeout=self.timeout,
            )
            
            if response.status_code == 200:
                self._fix_response_encoding(response)
                logger.debug(f"Successfully fetched gush file for block={block}, parcel={parcel}")
                return response
            else:
                logger.warning(f"Failed to fetch gush file: HTTP {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch gush file: {e}", exc_info=True)
        
        return None

    def _parse_gush_file_response(self, html: str, block: str, parcel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse GetGushFile HTML response to extract building information.
        
        Args:
            html: HTML response from GetGushFile
            block: Block number (גוש)
            parcel: Parcel number (חלקה), optional
            
        Returns:
            List of building info and permit documents
        """
        import re
        
        documents = []
        
        # Extract building IDs from the HTML
        # Look for javascript:getBuilding(ID) patterns
        building_ids = set()
        building_patterns = [
            r'javascript:getBuilding\((\d+)\)',
            r'href=["\']javascript:getBuilding\((\d+)\)["\']',
            r'#building/(\d+)',
            r'building/(\d+)',
            r't=(\d+)',
        ]
        
        for pattern in building_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                building_id = str(match).strip()
                if building_id:
                    building_ids.add(building_id)
        
        logger.debug(f"Found {len(building_ids)} building IDs in gush file: {building_ids}")
        
        # For each building ID found, get full building info
        for building_id in building_ids:
            try:
                building_docs = self._get_by_building_id(building_id)
                documents.extend(building_docs)
            except Exception as e:
                logger.warning(f"Failed to get building info for {building_id}: {e}")
        
        # Also try to extract any request/permit information directly from the HTML
        # Look for request IDs: javascript:getRequest(ID)
        request_pattern = r'javascript:getRequest\((\d+)\)'
        request_ids = re.findall(request_pattern, html)
        
        if request_ids:
            logger.debug(f"Found {len(request_ids)} request IDs in gush file")
            # Extract request information from HTML tables
            for req_id in set(request_ids):
                # Try to find the row containing this request
                row_pattern = rf'<tr[^>]*>.*?<a[^>]*href=["\']javascript:getRequest\({req_id}\)["\'][^>]*>.*?</tr>'
                row_match = re.search(row_pattern, html, re.DOTALL | re.IGNORECASE)
                
                if row_match:
                    row_html = row_match.group(0)
                    cell_pattern = r'<td[^>]*>(.*?)</td>'
                    cells = re.findall(cell_pattern, row_html, re.DOTALL | re.IGNORECASE)
                    
                    if len(cells) >= 3:
                        import html as html_module
                        cell_texts = []
                        for cell in cells:
                            text = re.sub(r'<[^>]+>', '', cell)
                            text = html_module.unescape(text)
                            text = re.sub(r'\s+', ' ', text).strip()
                            if isinstance(text, bytes):
                                text = text.decode('utf-8', errors='ignore')
                            cell_texts.append(text)
                        
                        date = None
                        description = None
                        category = None
                        
                        if len(cell_texts) >= 3:
                            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', cell_texts[2])
                            if date_match:
                                date = date_match.group(1)
                        
                        if len(cell_texts) >= 4:
                            description = cell_texts[3] if cell_texts[3] else None
                        
                        if len(cell_texts) >= 5:
                            category = cell_texts[4] if cell_texts[4] else None
                        
                        document = {
                            "request_num": req_id,
                            "external_id": req_id,
                            "document_date": date,
                            "title": description or f"Request {req_id}",
                            "document_type": description or f"Request {req_id}",
                            "status": category or "",
                            "meta": {
                                "block": block,
                                "parcel": parcel,
                                "category": category,
                            },
                        }
                        # Get source name by removing "Client" suffix if present
                        source_name = self.__class__.__name__.replace("Client", "")
                        documents.append(self._normalize_document(document, source_name))
        
        if documents:
            logger.info(f"Successfully parsed {len(documents)} documents from gush file for block={block}, parcel={parcel}")
        else:
            logger.warning(f"No documents found in gush file for block={block}, parcel={parcel}")
        
        return documents

    def _get_unified_file(self, block: str, parcel: Optional[str] = None) -> Optional[requests.Response]:
        """Get unified file information using GetUnifiedFile endpoint.
        
        Args:
            block: Block number (גוש)
            parcel: Parcel number (חלקה), optional
            
        Returns:
            Response object if successful, None otherwise
        """
        site_id = self.get_site_id()
        endpoint = "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"
        params = {
            "appname": "cixpa",
            "prgname": "GetUnifiedFile",
            "siteid": site_id,
            "g": block,
            "arguments": "siteid,g",
        }
        
        if parcel:
            params["h"] = parcel
            params["arguments"] = "siteid,g,h"
        
        try:
            logger.info(f"Calling GetUnifiedFile with params: {params}")
            response = self.session.get(
                endpoint,
                params=params,
                headers={
                    "Origin": self.base_url,
                    "Referer": f"{self.base_url}/gush2/",
                },
                timeout=self.timeout,
            )
            
            if response.status_code == 200:
                self._fix_response_encoding(response)
                logger.debug(f"Successfully fetched unified file for block={block}, parcel={parcel}")
                return response
            else:
                logger.warning(f"Failed to fetch unified file: HTTP {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch unified file: {e}", exc_info=True)
        
        return None

    def _parse_unified_file_response(self, html: str, block: str, parcel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse GetUnifiedFile HTML response to extract building information.
        
        Args:
            html: HTML response from GetUnifiedFile
            block: Block number (גוש)
            parcel: Parcel number (חלקה), optional
            
        Returns:
            List of building info and permit documents
        """
        import re
        
        documents = []
        
        # Extract building IDs from the HTML
        # Look for javascript:getBuilding(ID) patterns
        building_ids = set()
        building_patterns = [
            r'javascript:getBuilding\((\d+)\)',
            r'href=["\']javascript:getBuilding\((\d+)\)["\']',
            r'#building/(\d+)',
            r'building/(\d+)',
            r't=(\d+)',
        ]
        
        for pattern in building_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                building_id = str(match).strip()
                if building_id:
                    building_ids.add(building_id)
        
        logger.debug(f"Found {len(building_ids)} building IDs in unified file: {building_ids}")
        
        # For each building ID found, get full building info
        for building_id in building_ids:
            try:
                building_docs = self._get_by_building_id(building_id)
                documents.extend(building_docs)
            except Exception as e:
                logger.warning(f"Failed to get building info for {building_id}: {e}")
        
        # Also try to extract any request/permit information directly from the HTML
        # Look for request IDs: javascript:getRequest(ID)
        request_pattern = r'javascript:getRequest\((\d+)\)'
        request_ids = re.findall(request_pattern, html)
        
        if request_ids:
            logger.debug(f"Found {len(request_ids)} request IDs in unified file")
            # Extract request information from HTML tables
            for req_id in set(request_ids):
                # Try to find the row containing this request
                row_pattern = rf'<tr[^>]*>.*?<a[^>]*href=["\']javascript:getRequest\({req_id}\)["\'][^>]*>.*?</tr>'
                row_match = re.search(row_pattern, html, re.DOTALL | re.IGNORECASE)
                
                if row_match:
                    row_html = row_match.group(0)
                    cell_pattern = r'<td[^>]*>(.*?)</td>'
                    cells = re.findall(cell_pattern, row_html, re.DOTALL | re.IGNORECASE)
                    
                    if len(cells) >= 3:
                        import html as html_module
                        cell_texts = []
                        for cell in cells:
                            text = re.sub(r'<[^>]+>', '', cell)
                            text = html_module.unescape(text)
                            text = re.sub(r'\s+', ' ', text).strip()
                            if isinstance(text, bytes):
                                text = text.decode('utf-8', errors='ignore')
                            cell_texts.append(text)
                        
                        date = None
                        description = None
                        category = None
                        
                        if len(cell_texts) >= 3:
                            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', cell_texts[2])
                            if date_match:
                                date = date_match.group(1)
                        
                        if len(cell_texts) >= 4:
                            description = cell_texts[3] if cell_texts[3] else None
                        
                        if len(cell_texts) >= 5:
                            category = cell_texts[4] if cell_texts[4] else None
                        
                        document = {
                            "request_num": req_id,
                            "external_id": req_id,
                            "document_date": date,
                            "title": description or f"Request {req_id}",
                            "document_type": description or f"Request {req_id}",
                            "status": category or "",
                            "meta": {
                                "block": block,
                                "parcel": parcel,
                                "category": category,
                                "source_type": "unified_file",
                            },
                        }
                        # Get source name by removing "Client" suffix if present
                        source_name = self.__class__.__name__.replace("Client", "")
                        documents.append(self._normalize_document(document, source_name))
        
        if documents:
            logger.info(f"Successfully parsed {len(documents)} documents from unified file for block={block}, parcel={parcel}")
        else:
            logger.warning(f"No documents found in unified file for block={block}, parcel={parcel}")
        
        return documents

    @abstractmethod
    def get_building_info(
        self,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
        address: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get building information and permits.
        
        Args:
            block: Block number (גוש)
            parcel: Parcel number (חלקה)
            address: Street address
            
        Returns:
            List of building info and permit documents
        """
        pass

    def _normalize_document(
        self,
        row: Dict[str, Any],
        source_name: str,
    ) -> Dict[str, Any]:
        """Normalize a document row to a standard format.
        
        Args:
            row: Raw document data
            source_name: Name of the source (e.g., "BatYamTikbinyan")
            
        Returns:
            Normalized document dictionary
        """
        document_type = row.get("document_type") or row.get("type") or row.get("title") or ""
        status = row.get("status") or row.get("stage") or ""
        permit_num = row.get("permit_num") or row.get("permission_num") or row.get("permit_number")
        request_num = row.get("request_num") or row.get("request_number")
        document_date = row.get("document_date") or row.get("date") or row.get("issue_date")
        building_id = row.get("building_id") or row.get("building_number")
        
        external_id = (
            row.get("external_id")
            or row.get("unique_id")
            or row.get("id")
            or permit_num
            or request_num
            or building_id
        )
        
        external_url = row.get("external_url") or row.get("url") or row.get("link")
        if not external_url and external_id:
            external_url = f"{self.tikbinyan_url}/#building/{external_id}"
        
        # Classify document type - pass the full row so we can check for request_num/permission_num
        classified_type = self._classify_document_type(document_type, row)
        
        normalized = {
            "title": document_type,
            "status": status,
            "permission_num": permit_num,
            "request_num": request_num,
            "external_id": str(external_id) if external_id else None,
            "external_url": external_url,
            "document_date": document_date,
            "building_id": building_id,
            "source": source_name,
            "document_type": classified_type,
            "document_category": self._classify_document_category(classified_type),
            "meta": row,
        }
        
        return normalized

    @staticmethod
    def _classify_document_type(descriptor: Optional[str], row: Optional[Dict[str, Any]] = None) -> str:
        """Classify document type from descriptor and optional row data."""
        # If we have a request_num or permission_num, it's likely a permit
        if row:
            if row.get("request_num") or row.get("permission_num") or row.get("permit_num"):
                # Check if it's a specific permit type
                descriptor_to_check = descriptor or ""
                normalized = _normalize_label(descriptor_to_check)
                normalized_lower = normalized.lower()
                
                if "מילולי" in normalized_lower or "verbal" in normalized_lower:
                    return "permit_verbal"
                if "תכנית" in normalized_lower or "plan" in normalized_lower:
                    return "permit_plan"
                # Default to permit if we have request/permit number
                return "permit"
        
        if not descriptor:
            return "other"
        
        normalized = _normalize_label(descriptor)
        normalized_lower = normalized.lower()
        
        # Permit keywords
        if any(keyword in normalized_lower for keyword in ["היתר", "permit", "בקשה", "request"]):
            if "מילולי" in normalized_lower or "verbal" in normalized_lower:
                return "permit_verbal"
            if "תכנית" in normalized_lower or "plan" in normalized_lower:
                return "permit_plan"
            return "permit"
        
        # Plan keywords
        if any(keyword in normalized_lower for keyword in ["תשריט", "תכנית", "plan"]):
            if "בית משותף" in normalized_lower or "condo" in normalized_lower:
                return "condo_plan"
            return "plan"
        
        # Drawing keywords
        if any(keyword in normalized_lower for keyword in ["מפת מדידה", "technical", "drawing"]):
            return "technical_drawing"
        
        if any(keyword in normalized_lower for keyword in ["תכנית אדריכלית", "architectural"]):
            return "architectural_drawing"
        
        return "other"

    @staticmethod
    def _classify_document_category(doc_type: str) -> str:
        """Classify document category from document type."""
        if doc_type in {"permit", "permit_verbal", "permit_plan", "permit_construction", "permit_renovation"}:
            return "permit"
        if doc_type == "plan":
            return "plan"
        if doc_type in {"condo_plan", "architectural_drawing", "technical_drawing", "blueprint"}:
            return "drawing"
        return "document"


class BatYamTikbinyanClient(TikbinyanClient):
    """Client for Bat Yam tikbinyan portal."""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        timeout: float = 60.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        super().__init__(
            base_url="https://batyam.complot.co.il",
            session=session,
            timeout=timeout,
            user_agent=user_agent,
        )

    def get_site_id(self) -> str:
        """Get the site_id for Bat Yam."""
        return "81"

    def get_building_info(
        self,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
        address: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get building information from Bat Yam tikbinyan portal."""
        
        # Try block/parcel
        if block:
            return self._get_by_block_parcel(block, parcel)
        
        # Try address
        if address:
            return self._get_by_address(address)
        
        raise ValueError("Must provide building_id, block, or address")

    def _get_by_building_id(self, building_id: str) -> List[Dict[str, Any]]:
        """Get building info by building ID."""
        site_id = self.get_site_id()
        
        # Use the actual endpoint that the website uses: GetTikFile
        endpoint = "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"
        params = {
            "appname": "cixpa",
            "prgname": "GetTikFile",
            "siteid": site_id,
            "t": building_id,
            "arguments": "siteid,t",
        }
        
        try:
            response = self.session.get(
                endpoint,
                params=params,
                headers={
                    "Origin": self.base_url,
                    "Referer": self.tikbinyan_url + "/",
                },
                timeout=self.timeout,
            )
            
            if response.status_code == 200:
                logger.debug(f"Successfully fetched building {building_id} page")
                # Fix encoding to handle Hebrew text correctly
                self._fix_response_encoding(response)
                # The response is HTML, parse it
                return self._parse_building_page(response.text, building_id)
            else:
                logger.warning(f"Failed to fetch building {building_id}: HTTP {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch building {building_id} from Bat Yam: {e}", exc_info=True)
        
        return []

    def _get_by_block_parcel(self, block: str, parcel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get building info by block and parcel."""
        if not parcel:
            logger.warning("Parcel number is required for block/parcel search in Bat Yam")
            return []
        
        all_documents = []
        seen_ids = set()
        
        # Try GetGushFile endpoint
        gush_response = self._get_gush_file(block, parcel)
        if gush_response:
            gush_docs = self._parse_gush_file_response(gush_response.text, block, parcel)
            for doc in gush_docs:
                doc_id = doc.get("external_id") or doc.get("request_num") or doc.get("permission_num")
                if doc_id and doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_documents.append(doc)
        
        # Try GetUnifiedFile endpoint
        unified_response = self._get_unified_file(block, parcel)
        if unified_response:
            unified_docs = self._parse_unified_file_response(unified_response.text, block, parcel)
            for doc in unified_docs:
                doc_id = doc.get("external_id") or doc.get("request_num") or doc.get("permission_num")
                if doc_id and doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_documents.append(doc)
        
        return all_documents

    def _get_by_address(self, address: str) -> List[Dict[str, Any]]:
        """Get building info by address."""
        # Parse address to extract street name and house number
        street_name, house_number = self._parse_address(address)
        
        if not street_name:
            logger.warning(f"Could not parse street name from address: {address}")
            return []
        
        # Find street ID
        street_id = self._find_street_id(street_name)
        if not street_id:
            logger.warning(f"Street '{street_name}' not found in Bat Yam")
            return []
        
        logger.info(f"Found street '{street_name}' with ID: {street_id}")
        
        # Now we need to search for buildings by street and house number
        # This endpoint might need to be discovered, but let's try common patterns
        return self._search_buildings_by_street(street_id, house_number)
    
    def _search_buildings_by_street(self, street_id: str, house_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for buildings by street ID and optional house number.
        
        Args:
            street_id: Street ID from GetStreets
            house_number: Optional house number
            
        Returns:
            List of building info and permit documents
        """
        site_id = self.get_site_id()
        city_code = self._get_city_code()
        
        if not city_code:
            logger.warning("Could not determine city code for building search")
            return []
        
        # Use the actual endpoint that the website uses
        endpoint = "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"
        params = {
            "appname": "cixpa",
            "prgname": "GetTikimByAddress",
            "siteid": site_id,
            "c": city_code,
            "s": street_id,
            "l": "true",
            "arguments": "siteid,c,s,h,l",
        }
        if house_number:
            params["h"] = str(house_number)
        
        try:
            logger.info(f"Calling GetTikimByAddress with params: {params}")
            response = self.session.get(
                endpoint,
                params=params,
                headers={
                    "Origin": self.base_url,
                    "Referer": self.tikbinyan_url + "/",
                },
                timeout=self.timeout,
            )
            
            logger.info(f"Response status: {response.status_code}, URL: {response.url}")
            
            if response.status_code == 200:
                # Fix encoding to handle Hebrew text correctly
                self._fix_response_encoding(response)
                
                # Log response details for debugging
                content_type = response.headers.get('Content-Type', 'unknown')
                logger.debug(f"Response Content-Type: {content_type}")
                logger.debug(f"Response encoding: {response.encoding}")
                logger.debug(f"Response length: {len(response.text)} chars")
                logger.debug(f"Response preview (first 1000 chars):\n{response.text[:1000]}")
                
                # The response might be HTML or JSON, try to parse it
                try:
                    # Try JSON first
                    data = response.json()
                    logger.debug(f"Parsed as JSON, type: {type(data)}")
                    if isinstance(data, dict):
                        logger.debug(f"JSON keys: {list(data.keys())}")
                        buildings = data.get("d", [])
                    elif isinstance(data, list):
                        buildings = data
                    else:
                        buildings = []
                    logger.debug(f"Extracted {len(buildings)} buildings from JSON")
                except ValueError as e:
                    # Not JSON, try parsing HTML table
                    logger.debug(f"Not JSON (error: {e}), trying HTML parsing")
                    buildings = self._parse_buildings_table(response.text)
                    logger.debug(f"Extracted {len(buildings)} buildings from HTML")
                
                if buildings:
                    logger.info(f"Found {len(buildings)} buildings for street {street_id}, house {house_number}")
                    logger.debug(f"Buildings data: {buildings}")
                    # Process each building
                    all_documents = []
                    for building in buildings:
                        # Extract building ID from various possible formats
                        building_id = None
                        if isinstance(building, dict):
                            building_id = building.get("v") or building.get("id") or building.get("building_id") or building.get("t")
                            logger.debug(f"Building dict: {building}, extracted ID: {building_id}")
                        elif isinstance(building, str):
                            # Might be just the building ID as a string
                            building_id = building
                            logger.debug(f"Building string: {building}")
                        
                        if building_id:
                            # Get full building info
                            building_docs = self._get_by_building_id(str(building_id))
                            all_documents.extend(building_docs)
                    
                    return all_documents
                else:
                    logger.warning(f"No buildings found in response for street_id={street_id}, house_number={house_number}")
                    logger.debug(f"Full response text:\n{response.text}")
        except requests.RequestException as e:
            logger.error(f"Failed to search buildings: {e}", exc_info=True)
        
        logger.warning(f"Could not find buildings for street_id={street_id}, house_number={house_number}")
        return []

    def _parse_api_response(self, data: Dict[str, Any], building_id: str) -> List[Dict[str, Any]]:
        """Parse API JSON response to extract permit information."""
        documents = []
        
        # Handle different response structures
        if isinstance(data, dict):
            # Check for common response wrappers
            building_data = data.get("building") or data.get("data") or data.get("result") or data
            
            # Extract permits/documents
            permits = building_data.get("permits") or building_data.get("documents") or building_data.get("files") or []
            if not permits and isinstance(building_data, list):
                permits = building_data
            
            for permit in permits if isinstance(permits, list) else [permits]:
                if isinstance(permit, dict):
                    normalized = self._normalize_document(permit, "BatYamTikbinyan")
                    normalized["building_id"] = building_id
                    documents.append(normalized)
        
        return documents

    def _parse_building_page(self, html: str, building_id: str) -> List[Dict[str, Any]]:
        """Parse building page HTML to extract permit information."""
        documents = []
        
        # Try to find JSON data embedded in the page
        import json
        import re
        
        # Look for JSON data in script tags or data attributes
        json_patterns = [
            r'var\s+buildingData\s*=\s*({[^;]+});',
            r'data-building=["\']([^"\']+)["\']',
            r'buildingData\s*[:=]\s*({[^;]+})',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                try:
                    if match.startswith('{'):
                        data = json.loads(match)
                    else:
                        data = json.loads(match.replace("'", '"'))
                    return self._parse_api_response(data, building_id)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        # If no JSON found, parse HTML tables for request/permit data
        # Look for table rows with request IDs: javascript:getRequest(19001550)
        request_pattern = r'javascript:getRequest\((\d+)\)'
        request_ids = re.findall(request_pattern, html)
        
        if request_ids:
            logger.info(f"Found {len(request_ids)} requests/permits in HTML for building {building_id}")
            
            # Extract full row data for each request ID
            # Find the tbody section that contains getRequest (there may be multiple tbody sections)
            tbody_html = html
            all_tbodies = re.findall(r'<tbody[^>]*>(.*?)</tbody>', html, re.DOTALL | re.IGNORECASE)
            for tbody in all_tbodies:
                if 'getRequest' in tbody:
                    tbody_html = tbody
                    logger.debug(f"Found requests tbody with {len(tbody)} chars")
                    break
            
            for req_id in set(request_ids):  # Use set to avoid duplicates
                # Find the row containing this request ID - must be in tbody and have request ID as link text
                # Pattern: <tr> ... <a href="javascript:getRequest(ID)">ID</a> ... </tr>
                row_pattern = rf'<tr[^>]*>.*?<a[^>]*href=["\']javascript:getRequest\({req_id}\)["\'][^>]*>{req_id}</a>.*?</tr>'
                row_match = re.search(row_pattern, tbody_html, re.DOTALL | re.IGNORECASE)
                
                if not row_match:
                    # Fallback: try without requiring ID as link text
                    row_pattern = rf'<tr[^>]*>(.*?<a[^>]*href=["\']javascript:getRequest\({req_id}\)["\'][^>]*>.*?)</tr>'
                    row_match = re.search(row_pattern, tbody_html, re.DOTALL | re.IGNORECASE)
                
                if not row_match:
                    continue
                
                row_html = row_match.group(0)  # Get the full row including <tr> tags
                
                # Extract all table cells in order (only <td> tags, not <th>)
                cell_pattern = r'<td[^>]*>(.*?)</td>'
                cells = re.findall(cell_pattern, row_html, re.DOTALL | re.IGNORECASE)
                
                if len(cells) < 3:
                    # Skip rows that don't have enough cells (likely not a data row)
                    continue
                
                # Clean HTML tags from each cell
                import html as html_module
                cell_texts = []
                for cell in cells:
                    # Remove HTML tags and clean whitespace
                    text = re.sub(r'<[^>]+>', '', cell)
                    # Decode HTML entities (like &nbsp;, &amp;, etc.)
                    text = html_module.unescape(text)
                    # Clean whitespace
                    text = re.sub(r'\s+', ' ', text).strip()
                    # Ensure it's a proper string (not bytes)
                    if isinstance(text, bytes):
                        text = text.decode('utf-8', errors='ignore')
                    cell_texts.append(text)
                
                # Based on the HTML structure from the actual page:
                # Cell 0: icon link (empty or whitespace)
                # Cell 1: request ID link (should contain the request ID)
                # Cell 2: date (DD/MM/YYYY format)
                # Cell 3: description (with class "hidden-on-mobile")
                # Cell 4: category (with class "hidden-on-mobile")
                # Cell 5+: other fields (may be empty)
                
                date = None
                description = None
                category = None
                
                # Verify this is a request row by checking cell 1 contains the request ID
                if req_id not in cell_texts[1]:
                    # This might be the wrong row, skip it
                    continue
                
                if len(cell_texts) >= 3:
                    # Date is in cell 2 (index 2) - format DD/MM/YYYY
                    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', cell_texts[2])
                    if date_match:
                        date = date_match.group(1)
                
                if len(cell_texts) >= 4:
                    # Description is in cell 3 (index 3)
                    description = cell_texts[3] if cell_texts[3] else None
                
                if len(cell_texts) >= 5:
                    # Category is in cell 4 (index 4)
                    category = cell_texts[4] if cell_texts[4] else None
                
                # Create document entry - pass raw data, let _normalize_document classify it
                document = {
                    "request_num": req_id,
                    "external_id": req_id,
                    "document_date": date,
                    "title": description or f"Request {req_id}",
                    "document_type": description or f"Request {req_id}",  # Raw description for classification
                    "building_id": building_id,
                    "status": category or "",  # Store category as status
                    "meta": {
                        "category": category,
                        "all_cells": cell_texts[:6],  # Store first 6 cells for debugging
                    },
                }
                documents.append(self._normalize_document(document, "BatYamTikbinyan"))
            
            if documents:
                logger.info(f"Successfully parsed {len(documents)} documents from HTML for building {building_id}")
                return documents
        
        # If no requests found, log warning
        if not documents:
            logger.warning(f"Could not extract JSON data or parse HTML tables for building page {building_id}")
        
        return documents


class HerzliyaTikbinyanClient(TikbinyanClient):
    """Client for Herzliya tikbinyan portal."""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        timeout: float = 60.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        super().__init__(
            base_url="https://handasa.herzliya.muni.il",
            session=session,
            timeout=timeout,
            user_agent=user_agent,
        )

    def get_site_id(self) -> str:
        """Get the site_id for Herzliya."""
        # This needs to be determined - using a placeholder
        return "82"  # TODO: Verify actual site_id for Herzliya

    def get_building_info(
        self,
        building_id: Optional[str] = None,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
        address: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get building information from Herzliya tikbinyan portal."""
        if building_id:
            return self._get_by_building_id(building_id)
        if block:
            return self._get_by_block_parcel(block, parcel)
        if address:
            return self._get_by_address(address)
        raise ValueError("Must provide building_id, block, or address")

    def _get_by_building_id(self, building_id: str) -> List[Dict[str, Any]]:
        """Get building info by building ID."""
        # Try API endpoints first
        api_base = "https://handasi.complot.co.il/handasi2016"
        endpoints = [
            f"{api_base}/building/getBuilding",
            f"{api_base}/api/building/{building_id}",
            f"{api_base}/building/building-data",
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(
                    endpoint,
                    params={"id": building_id, "buildingId": building_id},
                    timeout=self.timeout,
                )
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return self._parse_api_response(data, building_id)
                    except ValueError:
                        return self._parse_building_page(response.text, building_id)
            except requests.RequestException:
                continue
        
        # Fallback to page
        url = f"{self.tikbinyan_url}/#building/{building_id}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return self._parse_building_page(response.text, building_id)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch building {building_id} from Herzliya: {e}")
            raise

    def _get_by_block_parcel(self, block: str, parcel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get building info by block and parcel."""
        if not parcel:
            logger.warning("Parcel number is required for block/parcel search in Herzliya")
            return []
        
        all_documents = []
        seen_ids = set()
        
        # Try GetGushFile endpoint
        gush_response = self._get_gush_file(block, parcel)
        if gush_response:
            gush_docs = self._parse_gush_file_response(gush_response.text, block, parcel)
            for doc in gush_docs:
                doc_id = doc.get("external_id") or doc.get("request_num") or doc.get("permission_num")
                if doc_id and doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_documents.append(doc)
        
        # Try GetUnifiedFile endpoint
        unified_response = self._get_unified_file(block, parcel)
        if unified_response:
            unified_docs = self._parse_unified_file_response(unified_response.text, block, parcel)
            for doc in unified_docs:
                doc_id = doc.get("external_id") or doc.get("request_num") or doc.get("permission_num")
                if doc_id and doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_documents.append(doc)
        
        return all_documents

    def _get_by_address(self, address: str) -> List[Dict[str, Any]]:
        """Get building info by address."""
        street_name, house_number = self._parse_address(address)
        if not street_name:
            logger.warning(f"Could not parse street name from address: {address}")
            return []
        
        street_id = self._find_street_id(street_name)
        if not street_id:
            logger.warning(f"Street '{street_name}' not found in Herzliya")
            return []
        
        logger.info(f"Found street '{street_name}' with ID: {street_id}")
        return self._search_buildings_by_street(street_id, house_number)
    
    def _search_buildings_by_street(self, street_id: str, house_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for buildings by street ID and optional house number."""
        site_id = self.get_site_id()
        city_code = self._get_city_code()
        
        if not city_code:
            logger.warning("Could not determine city code for building search")
            return []
        
        # Use the actual endpoint that the website uses
        endpoint = "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"
        params = {
            "appname": "cixpa",
            "prgname": "GetTikimByAddress",
            "siteid": site_id,
            "c": city_code,
            "s": street_id,
            "l": "true",
            "arguments": "siteid,c,s,h,l",
        }
        if house_number:
            params["h"] = str(house_number)
        
        try:
            logger.info(f"Calling GetTikimByAddress with params: {params}")
            response = self.session.get(
                endpoint,
                params=params,
                headers={
                    "Origin": self.base_url,
                    "Referer": self.tikbinyan_url + "/",
                },
                timeout=self.timeout,
            )
            
            logger.info(f"Response status: {response.status_code}, URL: {response.url}")
            
            if response.status_code == 200:
                # Fix encoding to handle Hebrew text correctly
                self._fix_response_encoding(response)
                
                # Log response details for debugging
                content_type = response.headers.get('Content-Type', 'unknown')
                logger.debug(f"Response Content-Type: {content_type}")
                logger.debug(f"Response encoding: {response.encoding}")
                logger.debug(f"Response length: {len(response.text)} chars")
                logger.debug(f"Response preview (first 1000 chars):\n{response.text[:1000]}")
                
                # The response might be HTML or JSON, try to parse it
                try:
                    # Try JSON first
                    data = response.json()
                    logger.debug(f"Parsed as JSON, type: {type(data)}")
                    if isinstance(data, dict):
                        logger.debug(f"JSON keys: {list(data.keys())}")
                        buildings = data.get("d", [])
                    elif isinstance(data, list):
                        buildings = data
                    else:
                        buildings = []
                    logger.debug(f"Extracted {len(buildings)} buildings from JSON")
                except ValueError as e:
                    # Not JSON, try parsing HTML table
                    logger.debug(f"Not JSON (error: {e}), trying HTML parsing")
                    buildings = self._parse_buildings_table(response.text)
                    logger.debug(f"Extracted {len(buildings)} buildings from HTML")
                
                if buildings:
                    logger.info(f"Found {len(buildings)} buildings for street {street_id}, house {house_number}")
                    logger.debug(f"Buildings data: {buildings}")
                    # Process each building
                    all_documents = []
                    for building in buildings:
                        # Extract building ID from various possible formats
                        building_id = None
                        if isinstance(building, dict):
                            building_id = building.get("v") or building.get("id") or building.get("building_id") or building.get("t")
                            logger.debug(f"Building dict: {building}, extracted ID: {building_id}")
                        elif isinstance(building, str):
                            # Might be just the building ID as a string
                            building_id = building
                            logger.debug(f"Building string: {building}")
                        
                        if building_id:
                            # Get full building info
                            building_docs = self._get_by_building_id(str(building_id))
                            all_documents.extend(building_docs)
                    
                    return all_documents
                else:
                    logger.warning(f"No buildings found in response for street_id={street_id}, house_number={house_number}")
                    logger.debug(f"Full response text:\n{response.text}")
        except requests.RequestException as e:
            logger.error(f"Failed to search buildings: {e}", exc_info=True)
        
        logger.warning(f"Could not find buildings for street_id={street_id}, house_number={house_number}")
        return []

    def _parse_api_response(self, data: Dict[str, Any], building_id: str) -> List[Dict[str, Any]]:
        """Parse API JSON response to extract permit information."""
        documents = []
        if isinstance(data, dict):
            building_data = data.get("building") or data.get("data") or data.get("result") or data
            permits = building_data.get("permits") or building_data.get("documents") or building_data.get("files") or []
            if not permits and isinstance(building_data, list):
                permits = building_data
            for permit in permits if isinstance(permits, list) else [permits]:
                if isinstance(permit, dict):
                    normalized = self._normalize_document(permit, "HerzliyaTikbinyan")
                    normalized["building_id"] = building_id
                    documents.append(normalized)
        return documents

    def _parse_building_page(self, html: str, building_id: str) -> List[Dict[str, Any]]:
        """Parse building page HTML to extract permit information."""
        documents = []
        import json
        import re
        json_patterns = [
            r'var\s+buildingData\s*=\s*({[^;]+});',
            r'data-building=["\']([^"\']+)["\']',
            r'buildingData\s*[:=]\s*({[^;]+})',
        ]
        for pattern in json_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match if match.startswith('{') else match.replace("'", '"'))
                    return self._parse_api_response(data, building_id)
                except (json.JSONDecodeError, ValueError):
                    continue
        logger.warning(f"Could not extract JSON data from building page for {building_id}")
        return documents


class RamatGanTikbinyanClient(TikbinyanClient):
    """Client for Ramat Gan tikbinyan portal."""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        timeout: float = 60.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        super().__init__(
            base_url="https://handasa.ramat-gan.muni.il",
            session=session,
            timeout=timeout,
            user_agent=user_agent,
        )

    def get_site_id(self) -> str:
        """Get the site_id for Ramat Gan."""
        # This needs to be determined - using a placeholder
        return "83"  # TODO: Verify actual site_id for Ramat Gan

    def get_building_info(
        self,
        building_id: Optional[str] = None,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
        address: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get building information from Ramat Gan tikbinyan portal."""
        if building_id:
            return self._get_by_building_id(building_id)
        if block:
            return self._get_by_block_parcel(block, parcel)
        if address:
            return self._get_by_address(address)
        raise ValueError("Must provide building_id, block, or address")

    def _get_by_building_id(self, building_id: str) -> List[Dict[str, Any]]:
        """Get building info by building ID."""
        api_base = "https://handasi.complot.co.il/handasi2016"
        endpoints = [
            f"{api_base}/building/getBuilding",
            f"{api_base}/api/building/{building_id}",
            f"{api_base}/building/building-data",
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(
                    endpoint,
                    params={"id": building_id, "buildingId": building_id},
                    timeout=self.timeout,
                )
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return self._parse_api_response(data, building_id)
                    except ValueError:
                        return self._parse_building_page(response.text, building_id)
            except requests.RequestException:
                continue
        
        url = f"{self.tikbinyan_url}/#building/{building_id}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return self._parse_building_page(response.text, building_id)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch building {building_id} from Ramat Gan: {e}")
            raise

    def _get_by_block_parcel(self, block: str, parcel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get building info by block and parcel."""
        if not parcel:
            logger.warning("Parcel number is required for block/parcel search in Ramat Gan")
            return []
        
        all_documents = []
        seen_ids = set()
        
        # Try GetGushFile endpoint
        gush_response = self._get_gush_file(block, parcel)
        if gush_response:
            gush_docs = self._parse_gush_file_response(gush_response.text, block, parcel)
            for doc in gush_docs:
                doc_id = doc.get("external_id") or doc.get("request_num") or doc.get("permission_num")
                if doc_id and doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_documents.append(doc)
        
        # Try GetUnifiedFile endpoint
        unified_response = self._get_unified_file(block, parcel)
        if unified_response:
            unified_docs = self._parse_unified_file_response(unified_response.text, block, parcel)
            for doc in unified_docs:
                doc_id = doc.get("external_id") or doc.get("request_num") or doc.get("permission_num")
                if doc_id and doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_documents.append(doc)
        
        return all_documents

    def _get_by_address(self, address: str) -> List[Dict[str, Any]]:
        """Get building info by address."""
        street_name, house_number = self._parse_address(address)
        if not street_name:
            logger.warning(f"Could not parse street name from address: {address}")
            return []
        
        street_id = self._find_street_id(street_name)
        if not street_id:
            logger.warning(f"Street '{street_name}' not found in Ramat Gan")
            return []
        
        logger.info(f"Found street '{street_name}' with ID: {street_id}")
        return self._search_buildings_by_street(street_id, house_number)
    
    def _search_buildings_by_street(self, street_id: str, house_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for buildings by street ID and optional house number."""
        site_id = self.get_site_id()
        city_code = self._get_city_code()
        
        if not city_code:
            logger.warning("Could not determine city code for building search")
            return []
        
        # Use the actual endpoint that the website uses
        endpoint = "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"
        params = {
            "appname": "cixpa",
            "prgname": "GetTikimByAddress",
            "siteid": site_id,
            "c": city_code,
            "s": street_id,
            "l": "true",
            "arguments": "siteid,c,s,h,l",
        }
        if house_number:
            params["h"] = str(house_number)
        
        try:
            logger.info(f"Calling GetTikimByAddress with params: {params}")
            response = self.session.get(
                endpoint,
                params=params,
                headers={
                    "Origin": self.base_url,
                    "Referer": self.tikbinyan_url + "/",
                },
                timeout=self.timeout,
            )
            
            logger.info(f"Response status: {response.status_code}, URL: {response.url}")
            
            if response.status_code == 200:
                # Fix encoding to handle Hebrew text correctly
                self._fix_response_encoding(response)
                
                # Log response details for debugging
                content_type = response.headers.get('Content-Type', 'unknown')
                logger.debug(f"Response Content-Type: {content_type}")
                logger.debug(f"Response encoding: {response.encoding}")
                logger.debug(f"Response length: {len(response.text)} chars")
                logger.debug(f"Response preview (first 1000 chars):\n{response.text[:1000]}")
                
                # The response might be HTML or JSON, try to parse it
                try:
                    # Try JSON first
                    data = response.json()
                    logger.debug(f"Parsed as JSON, type: {type(data)}")
                    if isinstance(data, dict):
                        logger.debug(f"JSON keys: {list(data.keys())}")
                        buildings = data.get("d", [])
                    elif isinstance(data, list):
                        buildings = data
                    else:
                        buildings = []
                    logger.debug(f"Extracted {len(buildings)} buildings from JSON")
                except ValueError as e:
                    # Not JSON, try parsing HTML table
                    logger.debug(f"Not JSON (error: {e}), trying HTML parsing")
                    buildings = self._parse_buildings_table(response.text)
                    logger.debug(f"Extracted {len(buildings)} buildings from HTML")
                
                if buildings:
                    logger.info(f"Found {len(buildings)} buildings for street {street_id}, house {house_number}")
                    logger.debug(f"Buildings data: {buildings}")
                    # Process each building
                    all_documents = []
                    for building in buildings:
                        # Extract building ID from various possible formats
                        building_id = None
                        if isinstance(building, dict):
                            building_id = building.get("v") or building.get("id") or building.get("building_id") or building.get("t")
                            logger.debug(f"Building dict: {building}, extracted ID: {building_id}")
                        elif isinstance(building, str):
                            # Might be just the building ID as a string
                            building_id = building
                            logger.debug(f"Building string: {building}")
                        
                        if building_id:
                            # Get full building info
                            building_docs = self._get_by_building_id(str(building_id))
                            all_documents.extend(building_docs)
                    
                    return all_documents
                else:
                    logger.warning(f"No buildings found in response for street_id={street_id}, house_number={house_number}")
                    logger.debug(f"Full response text:\n{response.text}")
        except requests.RequestException as e:
            logger.error(f"Failed to search buildings: {e}", exc_info=True)
        
        logger.warning(f"Could not find buildings for street_id={street_id}, house_number={house_number}")
        return []

    def _parse_api_response(self, data: Dict[str, Any], building_id: str) -> List[Dict[str, Any]]:
        """Parse API JSON response to extract permit information."""
        documents = []
        if isinstance(data, dict):
            building_data = data.get("building") or data.get("data") or data.get("result") or data
            permits = building_data.get("permits") or building_data.get("documents") or building_data.get("files") or []
            if not permits and isinstance(building_data, list):
                permits = building_data
            for permit in permits if isinstance(permits, list) else [permits]:
                if isinstance(permit, dict):
                    normalized = self._normalize_document(permit, "RamatGanTikbinyan")
                    normalized["building_id"] = building_id
                    documents.append(normalized)
        return documents

    def _parse_building_page(self, html: str, building_id: str) -> List[Dict[str, Any]]:
        """Parse building page HTML to extract permit information."""
        documents = []
        import json
        import re
        json_patterns = [
            r'var\s+buildingData\s*=\s*({[^;]+});',
            r'data-building=["\']([^"\']+)["\']',
            r'buildingData\s*[:=]\s*({[^;]+})',
        ]
        for pattern in json_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match if match.startswith('{') else match.replace("'", '"'))
                    return self._parse_api_response(data, building_id)
                except (json.JSONDecodeError, ValueError):
                    continue
        logger.warning(f"Could not extract JSON data from building page for {building_id}")
        return documents


__all__ = [
    "TikbinyanClient",
    "BatYamTikbinyanClient",
    "HerzliyaTikbinyanClient",
    "RamatGanTikbinyanClient",
]

