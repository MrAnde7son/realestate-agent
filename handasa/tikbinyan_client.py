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

    @abstractmethod
    def get_building_info(
        self,
        building_id: Optional[str] = None,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
        address: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get building information and permits.
        
        Args:
            building_id: Building ID (מספר תיק בניין)
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
            "document_type": self._classify_document_type(document_type),
            "document_category": self._classify_document_category(document_type),
            "meta": row,
        }
        
        return normalized

    @staticmethod
    def _classify_document_type(descriptor: Optional[str]) -> str:
        """Classify document type from descriptor."""
        if not descriptor:
            return "other"
        
        normalized = _normalize_label(descriptor)
        normalized_lower = normalized.lower()
        
        # Permit keywords
        if any(keyword in normalized_lower for keyword in ["היתר", "permit"]):
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
        building_id: Optional[str] = None,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
        address: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get building information from Bat Yam tikbinyan portal."""
        # Try building ID first
        if building_id:
            return self._get_by_building_id(building_id)
        
        # Try block/parcel
        if block:
            return self._get_by_block_parcel(block, parcel)
        
        # Try address
        if address:
            return self._get_by_address(address)
        
        raise ValueError("Must provide building_id, block, or address")

    def _get_by_building_id(self, building_id: str) -> List[Dict[str, Any]]:
        """Get building info by building ID."""
        # The portal uses handasi.complot.co.il as shared backend
        # Try to call the API endpoint directly
        api_base = "https://handasi.complot.co.il/handasi2016"
        
        # Try different possible API endpoints
        endpoints = [
            f"{api_base}/building/getBuilding",
            f"{api_base}/api/building/{building_id}",
            f"{api_base}/building/building-data",
        ]
        
        for endpoint in endpoints:
            try:
                # Try GET first
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
                        # Not JSON, try parsing HTML
                        return self._parse_building_page(response.text, building_id)
            except requests.RequestException:
                continue
        
        # Fallback: fetch the page and parse
        url = f"{self.tikbinyan_url}/#building/{building_id}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return self._parse_building_page(response.text, building_id)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch building {building_id} from Bat Yam: {e}")
            raise

    def _get_by_block_parcel(self, block: str, parcel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get building info by block and parcel."""
        # Implementation depends on actual API structure
        # This is a placeholder that needs to be adapted
        logger.warning("Block/parcel search not yet fully implemented for Bat Yam")
        return []

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
        # Try different possible endpoints for building search
        endpoints = [
            f"{self.api_base}/GetBuildings",
            f"{self.api_base}/SearchBuildings",
            f"{self.api_base}/GetBuildingsByStreet",
        ]
        
        site_id = self.get_site_id()
        
        for endpoint in endpoints:
            try:
                # Try with street_id and house_number
                payload = {
                    "site_id": site_id,
                    "street_id": street_id,
                }
                if house_number:
                    payload["house_number"] = house_number
                
                response = self.session.post(
                    endpoint,
                    json=payload,
                    headers={
                        "Content-Type": "application/json; charset=UTF-8",
                        "Origin": self.base_url,
                        "Referer": self.tikbinyan_url + "/",
                    },
                    timeout=self.timeout,
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        buildings = data.get("d", []) if isinstance(data, dict) else []
                        if buildings:
                            logger.info(f"Found {len(buildings)} buildings for street {street_id}")
                            # Process each building
                            all_documents = []
                            for building in buildings:
                                building_id = building.get("v") or building.get("id") or building.get("building_id")
                                if building_id:
                                    # Get full building info
                                    building_docs = self._get_by_building_id(str(building_id))
                                    all_documents.extend(building_docs)
                            return all_documents
                    except (ValueError, KeyError):
                        continue
            except requests.RequestException:
                continue
        
        # If no API endpoint works, return empty list
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
        
        # If no JSON found, return empty list (will need HTML parsing if needed)
        logger.warning(f"Could not extract JSON data from building page for {building_id}")
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
        logger.warning("Block/parcel search not yet fully implemented for Herzliya")
        return []

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
        endpoints = [
            f"{self.api_base}/GetBuildings",
            f"{self.api_base}/SearchBuildings",
            f"{self.api_base}/GetBuildingsByStreet",
        ]
        
        site_id = self.get_site_id()
        
        for endpoint in endpoints:
            try:
                payload = {"site_id": site_id, "street_id": street_id}
                if house_number:
                    payload["house_number"] = house_number
                
                response = self.session.post(
                    endpoint,
                    json=payload,
                    headers={
                        "Content-Type": "application/json; charset=UTF-8",
                        "Origin": self.base_url,
                        "Referer": self.tikbinyan_url + "/",
                    },
                    timeout=self.timeout,
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        buildings = data.get("d", []) if isinstance(data, dict) else []
                        if buildings:
                            all_documents = []
                            for building in buildings:
                                building_id = building.get("v") or building.get("id") or building.get("building_id")
                                if building_id:
                                    building_docs = self._get_by_building_id(str(building_id))
                                    all_documents.extend(building_docs)
                            return all_documents
                    except (ValueError, KeyError):
                        continue
            except requests.RequestException:
                continue
        
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
        logger.warning("Block/parcel search not yet fully implemented for Ramat Gan")
        return []

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
        endpoints = [
            f"{self.api_base}/GetBuildings",
            f"{self.api_base}/SearchBuildings",
            f"{self.api_base}/GetBuildingsByStreet",
        ]
        
        site_id = self.get_site_id()
        
        for endpoint in endpoints:
            try:
                payload = {"site_id": site_id, "street_id": street_id}
                if house_number:
                    payload["house_number"] = house_number
                
                response = self.session.post(
                    endpoint,
                    json=payload,
                    headers={
                        "Content-Type": "application/json; charset=UTF-8",
                        "Origin": self.base_url,
                        "Referer": self.tikbinyan_url + "/",
                    },
                    timeout=self.timeout,
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        buildings = data.get("d", []) if isinstance(data, dict) else []
                        if buildings:
                            all_documents = []
                            for building in buildings:
                                building_id = building.get("v") or building.get("id") or building.get("building_id")
                                if building_id:
                                    building_docs = self._get_by_building_id(str(building_id))
                                    all_documents.extend(building_docs)
                            return all_documents
                    except (ValueError, KeyError):
                        continue
            except requests.RequestException:
                continue
        
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

