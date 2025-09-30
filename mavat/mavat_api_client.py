#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mavat API Client

This module provides a client for the Mavat REST API, replacing the browser-based
scraper with direct HTTP requests for better performance and reliability.

API Endpoints:
- Search: https://mavat.iplan.gov.il/rest/api/sv3/Search
- Attachments: https://mavat.iplan.gov.il/rest/api/Attacments/
- Lookup Tables: https://mavat.iplan.gov.il/rest/api/Luts/4-5-6-7-8-9-10-11-39-48-52-53
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '', '..'))
from utils.retry import request_with_retry


@dataclass
class MavatSearchHit:
    """Represents a single search hit returned by Mavat API."""
    plan_id: str
    title: Optional[str] = None
    status: Optional[str] = None
    authority: Optional[str] = None
    jurisdiction: Optional[str] = None
    entity_number: Optional[str] = None
    entity_name: Optional[str] = None
    approval_date: Optional[str] = None
    status_date: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


@dataclass
class MavatPlan:
    """Represents basic details about a plan from the API."""
    plan_id: str
    plan_name: Optional[str] = None
    status: Optional[str] = None
    authority: Optional[str] = None
    jurisdiction: Optional[str] = None
    last_update: Optional[str] = None
    entity_number: Optional[str] = None
    approval_date: Optional[str] = None
    status_date: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


@dataclass
class MavatAttachment:
    """Represents a document attachment from the API."""
    filename: str
    file_type: Optional[str] = None
    size: Optional[int] = None
    url: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


@dataclass
class MavatLookupItem:
    """Represents an item from the lookup tables."""
    code: str
    description: str
    raw: Optional[Dict[str, Any]] = None


class MavatAPIClient:
    """Client for the Mavat REST API."""
    
    BASE_URL = "https://mavat.iplan.gov.il/rest/api"
    SEARCH_URL = f"{BASE_URL}/sv3/Search"
    ATTACHMENTS_URL = f"{BASE_URL}/Attacments/"
    LOOKUP_URL = f"{BASE_URL}/Luts/4-5-6-7-8-9-10-11-39-48-52-53"
    
    def __init__(self, session: Optional[requests.Session] = None):
        """Initialize the API client.
        
        Args:
            session: Optional requests session for connection pooling
        """
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://mavat.iplan.gov.il",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Referer": "https://mavat.iplan.gov.il/SV3?searchEntity=0&searchType=0&entityType=0&searchMethod=2",
        })
        
        # Set credentials to include cookies
        self.session.cookies.update({})
        
        # Cache for lookup tables
        self._lookup_cache = {}
        self._token = None
    
    def _get_auth_token(self) -> str:
        """Get authentication token from Mavat API.
        
        Based on HAR file analysis, tokens are generated via POST requests to the search API.
        However, the API requires captcha validation, so we'll return a placeholder token
        and let the search method handle the captcha error properly.
        
        Returns:
            Authentication token string (empty if captcha is required)
        """
        if self._token:
            return self._token
            
        # Use the working token from the fetch request
        # This token appears to be valid and bypasses captcha validation
        self._token = ""
        return self._token
    
    def is_api_accessible(self) -> bool:
        """Check if the Mavat API is accessible without captcha.
        
        Returns:
            True if API is accessible, False if captcha is required
        """
        try:
            # Try to access lookup tables which don't require captcha
            response = self.session.get(self.LOOKUP_URL, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_lookup_tables(self, force_refresh: bool = False) -> Dict[str, List[MavatLookupItem]]:
        """Get all available lookup tables for districts, cities, streets, etc.
        
        Args:
            force_refresh: Whether to force refresh the cache
            
        Returns:
            Dictionary containing lookup tables by type
        """
        if not force_refresh and self._lookup_cache:
            return self._lookup_cache
        
        try:
            response = request_with_retry(self.session.get, self.LOOKUP_URL, timeout=30)
            
            data = response.json()
            lookup_tables = {}
            
            # Process lookup data
            for table_type, table_data in data.items():
                if isinstance(table_data, list):
                    items = []
                    for entry in table_data:
                        if isinstance(entry, dict):
                            lookup_item = MavatLookupItem(
                                code=str(entry.get("CODE", "")),
                                description=entry.get("DESCRIPTION", ""),
                                raw=entry
                            )
                            items.append(lookup_item)
                    
                    lookup_tables[table_type] = items
            
            self._lookup_cache = lookup_tables
            return lookup_tables
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch lookup tables: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response from lookup tables: {e}")
    
    def get_districts(self, force_refresh: bool = False) -> List[MavatLookupItem]:
        """Get available districts.
        
        Args:
            force_refresh: Whether to force refresh the cache
            
        Returns:
            List of district lookup items
        """
        lookup_tables = self.get_lookup_tables(force_refresh)
        return lookup_tables.get("District", [])
    
    def get_cities(self, force_refresh: bool = False) -> List[MavatLookupItem]:
        """Get available cities.
        
        Args:
            force_refresh: Whether to force refresh the cache
            
        Returns:
            List of city lookup items
        """
        lookup_tables = self.get_lookup_tables(force_refresh)
        return lookup_tables.get("CityCounty", [])
    
    def get_plan_areas(self, force_refresh: bool = False) -> List[MavatLookupItem]:
        """Get available plan areas.
        
        Args:
            force_refresh: Whether to force refresh the cache
            
        Returns:
            List of plan area lookup items
        """
        lookup_tables = self.get_lookup_tables(force_refresh)
        return lookup_tables.get("PlanArea", [])
    
    def get_streets(self, force_refresh: bool = False) -> List[MavatLookupItem]:
        """Get available streets.
        
        Args:
            force_refresh: Whether to force refresh the cache
            
        Returns:
            List of street lookup items
        """
        lookup_tables = self.get_lookup_tables(force_refresh)
        return lookup_tables.get("Street", [])
    
    def get_authorities(self, force_refresh: bool = False) -> List[MavatLookupItem]:
        """Get available authorities.
        
        Args:
            force_refresh: Whether to force refresh the cache
            
        Returns:
            List of authority lookup items
        """
        lookup_tables = self.get_lookup_tables(force_refresh)
        return lookup_tables.get("Committies", [])
    
    def get_plan_types(self, force_refresh: bool = False) -> List[MavatLookupItem]:
        """Get available plan types.
        
        Args:
            force_refresh: Whether to force refresh the cache
            
        Returns:
            List of plan type lookup items
        """
        lookup_tables = self.get_lookup_tables(force_refresh)
        return lookup_tables.get("EntityTypes", [])
    
    def get_statuses(self, force_refresh: bool = False) -> List[MavatLookupItem]:
        """Get available plan statuses.
        
        Args:
            force_refresh: Whether to force refresh the cache
            
        Returns:
            List of status lookup items
        """
        lookup_tables = self.get_lookup_tables(force_refresh)
        return lookup_tables.get("UnifiedStatus", [])
    
    def search_lookup_by_text(
        self, 
        search_text: str, 
        table_type: Optional[str] = None,
        force_refresh: bool = False
    ) -> List[MavatLookupItem]:
        """Search lookup tables by text.
        
        Args:
            search_text: Text to search for
            table_type: Specific table type to search (optional)
            force_refresh: Whether to force refresh the cache
            
        Returns:
            List of matching lookup items
        """
        if table_type:
            tables = {table_type: self.get_lookup_tables(force_refresh).get(table_type, [])}
        else:
            tables = self.get_lookup_tables(force_refresh)
        
        results = []
        search_text_lower = search_text.lower()
        
        for table_name, items in tables.items():
            for item in items:
                if search_text_lower in item.description.lower():
                    results.append(item)
        
        return results
    
    def search_plans(
        self,
        query: Optional[str] = None,
        city: Optional[str] = None,
        district: Optional[str] = None,
        plan_area: Optional[str] = None,
        street: Optional[str] = None,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
        block_number: Optional[str] = None,
        parcel_number: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
        token: Optional[str] = None
    ) -> List[MavatSearchHit]:
        """Search for plans using the Mavat API.
        
        Args:
            query: Free text search query
            city: City name or code
            district: District name or code
            plan_area: Plan area name or code
            street: Street name or code
            block_number: Block number for search
            parcel_number: Parcel number for search
            status: Plan status filter
            limit: Maximum results per page
            page: Page number for pagination
            
        Returns:
            List of MavatSearchHit objects
        """
        city_code = -1
        district_code = -1
        plan_area_code = -1
        jurst_area_code = -1
        city_description = city or ""

        # Try to get proper codes from lookup tables if city is provided
        if city:
            try:
                cities = self.get_cities()
                for city_item in cities:
                    if city.lower() in city_item.description.lower():
                        city_code = int(float(city_item.code))
                        city_description = city_item.description
                        # Extract district and plan area codes from raw data
                        raw_data = city_item.raw or {}
                        district_code = int(float(raw_data.get('DISTRICT_CODE', -1)))
                        plan_area_code = int(float(raw_data.get('PLAN_AREA_CODE', -1)))
                        jurst_area_code = int(float(raw_data.get('JURST_AREA_CODE', -1)))
                        break
            except Exception:
                pass

        search_params = {
            "searchEntity": 1,
            "plNumber": "",
            "plName": query or "",
            "blockNumber": block or block_number or "",
            "toBlockNumber": block or block_number or "",
            "parcelNumber": parcel or parcel_number or "",
            "toParcelNumber": parcel or parcel_number or "",
            "modelCity": {
                "DISTRICT_CODE": district_code,
                "PLAN_AREA_CODE": plan_area_code,
                "JURST_AREA_CODE": jurst_area_code,
                "CODE": city_code,
                "DESCRIPTION": city_description
            },
            "intStreetCode": {
                "DESCRIPTION": street or "",
                "CODE": -1
            },
            "intPlanArea": {
                "DISTRICT_CODE": district_code,
                "CODE": plan_area_code,
                "DESCRIPTION": city_description
            },
            "intDistrict": {
                "CODE": district_code,
                "DESCRIPTION": city_description,
                "DISTRICT_LOCAL": 1
            },
            "intLevelOfAuthority": {
                "ENTITY_TYPE_CODE": 1,
                "DESCRIPTION": "הכל",
                "CODE": -1,
                "IS_MAVAT": 0
            },
            "intSubTypeCode": {
                "ENTITY_TYPE_CODE": 1,
                "CODE": -1,
                "DESCRIPTION": "",
                "IS_MAVAT": 0
            },
            "internetStatus": {
                "DESCRIPTION": status or "",
                "CODE": "-1"
            },
            "area": "",
            "residentialUnit": "",
            "meter": "",
            "dateLastStatusDate": None,
            "dateFromMeetingDate": None,
            "dateToMeetingDate": None,
            "dateFromApproval": None,
            "dateToApproval": None,
            "fromResult": (page - 1) * limit + 1,
            "toResult": page * limit,
            "_page": page,
            "token": token or self._get_auth_token()  # Use provided token or get from website
        }
        
        try:
            response = self.session.post(
                self.SEARCH_URL,
                json=search_params,
                timeout=30
            )
            
            # Enhanced error handling for 401
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    if "CaptchaNotValid" in str(error_data):
                        raise RuntimeError(error_data)
                    else:
                        raise RuntimeError(f"Authentication failed (401): {error_data}")
                except json.JSONDecodeError:
                    raise RuntimeError(f"Authentication failed (401): {response.text[:200]}")
            
            response.raise_for_status()
            
            data = response.json()
            hits = []
            
            # Process search results
            for item in data:
                if item.get("type") == "1" and item.get("result", {}).get("dtResults"):
                    for result in item["result"]["dtResults"]:
                        hit = MavatSearchHit(
                            plan_id=str(result.get("PLAN_ID", "")),
                            title=result.get("ENTITY_NAME"),
                            status=result.get("INTERNET_SHORT_STATUS"),
                            authority=result.get("AUTH_NAME"),
                            jurisdiction=result.get("ENTITY_LOCATION"),
                            entity_number=result.get("ENTITY_NUMBER"),
                            entity_name=result.get("ENTITY_NAME"),
                            approval_date=result.get("APP_DATE"),
                            status_date=result.get("INTERNET_STATUS_DATE"),
                            raw=result
                        )
                        hits.append(hit)
                        
                        if len(hits) >= limit:
                            break
            
            return hits[:limit]
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response: {e}")
    
    def get_plan_details(self, plan_id: str) -> MavatPlan:
        """Get detailed information for a specific plan.
        
        Args:
            plan_id: The unique identifier of the plan
            
        Returns:
            MavatPlan object with plan details
        """
        # For now, we'll use the search API to get plan details
        # In the future, we could implement a dedicated plan details endpoint
        try:
            # Search for the specific plan ID
            hits = self.search_plans(query=plan_id, limit=1)
            
            if not hits:
                raise RuntimeError(f"Plan {plan_id} not found")
            
            hit = hits[0]
            
            # Convert search hit to plan details
            plan = MavatPlan(
                plan_id=hit.plan_id,
                plan_name=hit.entity_name,
                status=hit.status,
                authority=hit.authority,
                jurisdiction=hit.jurisdiction,
                last_update=hit.status_date,
                entity_number=hit.entity_number,
                approval_date=hit.approval_date,
                status_date=hit.status_date,
                raw=hit.raw
            )
            
            return plan
            
        except Exception as e:
            raise RuntimeError(f"Failed to get plan details: {e}")
    
    def get_plan_attachments(self, plan_id: str, entity_name: str) -> List[MavatAttachment]:
        """Get attachments for a specific plan.
        
        Args:
            plan_id: The unique identifier of the plan
            entity_name: The entity name for constructing the attachment URL
            
        Returns:
            List of MavatAttachment objects
        """
        try:
            # Construct attachment URL
            # The API uses a specific format for attachment URLs
            encoded_name = quote(entity_name, safe='')
            attachment_url = f"{self.ATTACHMENTS_URL}?eid={plan_id}&fn={encoded_name}"
            
            # For now, return a basic attachment object
            # In a full implementation, we'd parse the actual attachment data
            attachment = MavatAttachment(
                filename=entity_name,
                url=attachment_url,
                raw={"url": attachment_url}
            )
            
            return [attachment]
            
        except Exception as e:
            raise RuntimeError(f"Failed to get plan attachments: {e}")

    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()


if __name__ == "__main__":
    client = MavatAPIClient()
    print(client.search_plans(block_number="6638", parcel_number="96"))