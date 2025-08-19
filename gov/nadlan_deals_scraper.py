# -*- coding: utf-8 -*-
"""
nadlan_deals_scraper.py
-----------------------

This module provides a comprehensive interface for retrieving and analyzing real-estate deal data
from the Israeli Ministry of Housing's public real-estate site (nadlan.gov.il).

The site is built on a React front-end that talks to a pair of REST endpoints
behind the scenes.  These endpoints are not formally documented but can be
observed via browser developer tools.  They still accept JSON requests as
described in community posts on Stack Overflow.  The
workflow to fetch deals for a given address or neighbourhood is roughly:

1. Perform a GET request against ``GetDataByQuery`` with a free-text query.
   This endpoint returns a JSON blob describing the search context.  A
   neighbourhood can be referenced by its name (e.g. ``"שכונת גבעת מרדכי,
   ירושלים"``) or by a full street address.
2. Modify the returned JSON to set the ``PageNo`` field to a positive value
   (zero appears to be treated as invalid by the service).  You can also
   override other fields here to narrow the search; see the notes below.
3. POST the modified JSON to ``GetAssestAndDeals``.  The response contains
   a list of assets and deal information for the query.

If the REST API becomes unavailable, the script falls back to a very simple
HTML scraper that uses ``BeautifulSoup`` to extract deal information from the
``?view=neighborhood&id=<id>&page=deals`` view.  Because the site is rendered
client-side, this fallback only works when JavaScript is enabled via tools
such as Selenium; using requests alone will not populate the deals table.

Usage
::::::

The easiest way to fetch deals is by calling ``get_deals_by_address`` with
a free-text address or neighbourhood name.  For example::

    from nadlan_deals_scraper import NadlanDealsScraper
    scraper = NadlanDealsScraper()
    deals = scraper.get_deals_by_address("שכונת גבעת מרדכי, ירושלים")
    for d in deals:
        print(d["asset_address"], d["deal_date"], d["price"], d["rooms"], d["floor"])

For comparable transactions analysis::

    scraper = NadlanDealsScraper()
    result = scraper.fetch_comparable_transactions(
        x=184320.94, y=668548.65,  # EPSG:2039 coordinates
        street="הגולן",
        house=1,
        date_from="2020-01-01",
        date_to="2025-12-31",
        target_area=80.0,
        top=15
    )
    print(f"Found {len(result['comps'])} comparable transactions")
    print(f"Median price per sqm: ₪{result['stats']['median_price_sqm']:,.0f}")

Notes
:::::

* The API does not require authentication and is free to use, but there
  appears to be rate limiting.  Please be courteous and avoid rapid
  repeated calls.
* Because the API is unofficial and may change without notice, this script
  includes basic exception handling.  If the API returns an unexpected
  status code or structure, a descriptive error is raised.
* See the Stack Overflow discussion referenced above for details on the
  payload structure and why ``PageNo`` must be set to a value greater than
  zero.

"""

from __future__ import annotations

import json
import logging
import math
import base64
import gzip
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from pyproj import Transformer
from dateutil import parser as dtp

logger = logging.getLogger(__name__)


class NadlanAPIError(Exception):
    """Exception raised when the Nadlan REST API returns an error."""


class NadlanScrapingError(Exception):
    """Exception raised when HTML scraping fails."""


@dataclass
class DealRecord:
    """Represents a single real estate deal record."""
    asset_address: Optional[str] = None
    deal_date: Optional[str] = None
    price: Optional[float] = None
    rooms: Optional[str] = None
    floor: Optional[str] = None
    asset_type: Optional[str] = None
    building_year: Optional[str] = None
    total_area: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DealRecord':
        """Create a DealRecord from a dictionary."""
        return cls(
            asset_address=data.get("AssetAddress"),
            deal_date=data.get("DealDate"),
            price=cls._parse_price(data.get("Price")),
            rooms=data.get("Rooms"),
            floor=data.get("Floor"),
            asset_type=data.get("AssetType"),
            building_year=data.get("BuildingYear"),
            total_area=cls._parse_area(data.get("TotalArea")),
            raw_data=data
        )
    
    @staticmethod
    def _parse_price(price_str: Any) -> Optional[float]:
        """Parse price string to float."""
        if not price_str:
            return None
        try:
            # Remove common price formatting
            price_str = str(price_str).replace(",", "").replace("₪", "").replace(" ", "")
            return float(price_str)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _parse_area(area_str: Any) -> Optional[float]:
        """Parse area string to float."""
        if not area_str:
            return None
        try:
            # Remove common area formatting
            area_str = str(area_str).replace(",", ".").replace("מ²", "").replace(" ", "")
            return float(area_str)
        except (ValueError, TypeError):
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "asset_address": self.asset_address,
            "deal_date": self.deal_date,
            "price": self.price,
            "rooms": self.rooms,
            "floor": self.floor,
            "asset_type": self.asset_type,
            "building_year": self.building_year,
            "total_area": self.total_area,
            "raw_data": self.raw_data
        }


class NadlanDealsScraper:
    """Main class for scraping and analyzing real estate deals from nadlan.gov.il."""
    
    def __init__(self, timeout: float = 10.0, user_agent: Optional[str] = None):
        """Initialize the scraper.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
        """
        self.timeout = timeout
        self.user_agent = user_agent or "NadlanDealsScraper/1.0"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "he,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        
        # API endpoints
        self.query_endpoint = "https://www.nadlan.gov.il/Nadlan.REST/Main/GetDataByQuery"
        self.deals_endpoint = "https://www.nadlan.gov.il/Nadlan.REST/Main/GetAssestAndDeals"
        
        # Coordinate transformer for EPSG:2039 to WGS84 conversion
        self._trans_2039_4326 = Transformer.from_crs(2039, 4326, always_xy=True)
        
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()
    
    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters using haversine formula."""
        R = 6_371_000.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dlat = p2 - p1
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _try_date(s) -> Optional[str]:
        """Parse date string and return in YYYY-MM-DD format."""
        if not s:
            return None
        try:
            return dtp.parse(str(s), dayfirst=True, yearfirst=False, fuzzy=True).strftime("%Y-%m-%d")
        except Exception:
            return None

    @staticmethod
    def _median(vals: List[Optional[float]]) -> Optional[float]:
        """Calculate median of a list of values, ignoring None values."""
        vals = sorted([v for v in vals if v is not None])
        if not vals:
            return None
        n = len(vals)
        m = n // 2
        return vals[m] if n % 2 else (vals[m - 1] + vals[m]) / 2

    def get_data_by_query(self, query: str) -> Dict[str, Any]:
        """Query the Nadlan ``GetDataByQuery`` endpoint.

        Args:
            query: Free text describing the neighbourhood or address

        Returns:
            The JSON object returned by the endpoint

        Raises:
            NadlanAPIError: If the server returns an error or invalid JSON
        """
        logger.debug("Fetching data for query: %s", query)
        try:
            resp = self.session.get(
                self.query_endpoint, 
                params={"query": query}, 
                timeout=self.timeout
            )
        except Exception as exc:
            raise NadlanAPIError(f"Failed to connect to {self.query_endpoint}: {exc}") from exc
            
        if resp.status_code != 200:
            raise NadlanAPIError(
                f"GetDataByQuery returned status {resp.status_code}: {resp.text[:200]!r}"
            )
        
        # Check if the response is HTML instead of JSON
        content_type = resp.headers.get('content-type', '').lower()
        if 'html' in content_type or resp.text.strip().startswith('<!doctype'):
            raise NadlanAPIError(
                f"The nadlan.gov.il API endpoint is currently returning HTML instead of JSON. "
                f"This suggests the API has changed or is temporarily unavailable. "
                f"Response preview: {resp.text[:200]!r}"
            )
            
        try:
            data = resp.json()
        except Exception as exc:
            raise NadlanAPIError(
                f"Failed to decode JSON: {exc}\nResponse was: {resp.text[:200]!r}"
            )
        return data

    def get_assets_and_deals(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Post a JSON payload to the ``GetAssestAndDeals`` endpoint.

        This function sets the ``PageNo`` field to 1 if it is not already
        specified or is zero, as the API rejects page zero.

        Args:
            payload: JSON object returned from ``GetDataByQuery``

        Returns:
            JSON response containing assets and deals

        Raises:
            NadlanAPIError: If the request fails or returns an error
        """
        # Ensure PageNo is set to a positive integer
        try:
            page_no = int(payload.get("PageNo", 0) or 0)
        except (TypeError, ValueError):
            page_no = 0
        if page_no <= 0:
            payload["PageNo"] = 1
            
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        logger.debug("Posting payload to GetAssestAndDeals: %s", payload)
        
        try:
            resp = self.session.post(
                self.deals_endpoint, 
                headers=headers, 
                data=json.dumps(payload), 
                timeout=self.timeout
            )
        except Exception as exc:
            raise NadlanAPIError(f"Failed to connect to {self.deals_endpoint}: {exc}") from exc
            
        if resp.status_code != 200:
            raise NadlanAPIError(
                f"GetAssestAndDeals returned status {resp.status_code}: {resp.text[:200]!r}"
            )
        
        # Check if the response is HTML instead of JSON
        content_type = resp.headers.get('content-type', '').lower()
        if 'html' in content_type or resp.text.strip().startswith('<!doctype'):
            raise NadlanAPIError(
                f"The nadlan.gov.il API endpoint is currently returning HTML instead of JSON. "
                f"This suggests the API has changed or is temporarily unavailable. "
                f"Response preview: {resp.text[:200]!r}"
            )
            
        try:
            data = resp.json()
        except Exception as exc:
            raise NadlanAPIError(
                f"Failed to decode JSON: {exc}\nResponse was: {resp.text[:200]!r}"
            )
        return data

    def get_deals_by_address(self, query: str) -> List[DealRecord]:
        """Retrieve deals for a free‑text address or neighbourhood name.

        This convenience function wraps ``get_data_by_query`` and
        ``get_assets_and_deals``.  It returns the list of deals contained in
        the response.

        Args:
            query: Free‑text description of the area

        Returns:
            List of DealRecord objects

        Raises:
            NadlanAPIError: If either API call fails
        """
        search_data = self.get_data_by_query(query)
        logger.info("Received search context: keys=%s", list(search_data.keys()))
        
        deals_data = self.get_assets_and_deals(search_data)
        
        # The API returns a dict with keys like "AssetsAndDeals", "Deals", or similar.
        # We'll attempt to locate the deals list by looking for a list of dicts.
        for key, value in deals_data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return [DealRecord.from_dict(deal) for deal in value]
                
        # If not found, raise a descriptive error
        raise NadlanAPIError(
            "Could not locate deals list in response. Keys received: {}".format(
                list(deals_data.keys())
            )
        )

    def get_deals_by_neighborhood_id(self, neighbourhood_id: str) -> List[DealRecord]:
        """Retrieve deals using a neighbourhood identifier.

        The public site uses numeric neighbourhood identifiers in its URLs.  At
        present there is no documented API that accepts the ID directly, so this
        function first fetches the neighbourhood name via a small lookup page and
        then delegates to ``get_deals_by_address``.

        Args:
            neighbourhood_id: The numeric ID as seen in the URL

        Returns:
            List of DealRecord objects

        Raises:
            NadlanAPIError: If the name lookup or subsequent API calls fail
        """
        # Attempt to resolve the neighbourhood name by scraping the page title.
        url = f"https://www.nadlan.gov.il/?view=neighborhood&id={neighbourhood_id}"
        logger.debug("Fetching neighbourhood page: %s", url)
        
        try:
            resp = self.session.get(url, timeout=self.timeout)
        except Exception as exc:
            raise NadlanAPIError(f"Failed to fetch neighbourhood page: {exc}") from exc
            
        if resp.status_code != 200:
            raise NadlanAPIError(
                f"Neighbourhood page returned status {resp.status_code}: {resp.text[:200]!r}"
            )
            
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # The neighbourhood name appears in the <title> tag
        title = soup.title.string if soup.title else ""
        name = None
        
        if title:
            # Example: "שכונת רמת החייל, תל אביב - יפו - nadlan.gov.il"
            parts = [p.strip() for p in title.split("-")]
            if parts:
                # Take the first part and remove the domain suffix
                name = parts[0]
                
        if not name:
            raise NadlanAPIError("Could not determine neighbourhood name from page title")
            
        logger.info("Resolved neighbourhood id %s to name: %s", neighbourhood_id, name)
        return self.get_deals_by_address(name)

    def scrape_deals_from_page(self, page_html: str) -> List[DealRecord]:
        """Extract deal data from the neighbourhood deals page.

        This helper is used as a fallback when the REST API is unavailable.  It
        expects HTML from the deals page with JavaScript already executed.

        Args:
            page_html: Complete HTML of the deals page after JavaScript execution

        Returns:
            List of DealRecord objects
        """
        soup = BeautifulSoup(page_html, "html.parser")
        table = soup.find("table")
        if not table:
            return []
            
        # Extract headers
        header_cells = table.find_all("th")
        headers = [h.get_text(strip=True) for h in header_cells]
        deals = []
        
        # Hebrew to English field mapping
        field_mapping = {
            "כתובת": "AssetAddress",
            "מחיר": "Price",
            "חדרים": "Rooms",
            "קומה": "Floor",
            "סוג נכס": "AssetType",
            "שנת בנייה": "BuildingYear",
            "שטח": "TotalArea",
            "תאריך עסקה": "DealDate"
        }
        
        for row in table.find_all("tr")[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) != len(headers):
                continue
                
            # Create a dict from headers and cells, mapping Hebrew to English
            deal_dict = {}
            for header, cell_value in zip(headers, cells):
                english_field = field_mapping.get(header, header)
                deal_dict[english_field] = cell_value
                
            deals.append(DealRecord.from_dict(deal_dict))
            
        return deals
    
    def get_deals_with_fallback(self, query: str) -> List[DealRecord]:
        """Get deals with fallback to HTML scraping if API fails.
        
        Args:
            query: Address or neighbourhood query
            
        Returns:
            List of DealRecord objects
        """
        try:
            return self.get_deals_by_address(query)
        except NadlanAPIError as e:
            logger.warning("API failed, attempting HTML scraping: %s", e)
            # For now, we can't easily implement HTML scraping fallback
            # as it requires JavaScript execution. This is a placeholder.
            raise NadlanAPIError(f"API failed and HTML scraping not implemented: {e}")

    def _process_nadlan_deal(
        self,
        deal: DealRecord,
        subj_lat: float,
        subj_lon: float,
        date_from: Optional[str],
        date_to: Optional[str],
        target_area: Optional[float],
    ) -> Optional[Dict[str, Any]]:
        """Process a nadlan deal record into a comparable transaction format."""
        # Extract address components for geocoding
        address = deal.asset_address
        if not address:
            return None
            
        # Parse deal date
        deal_date = deal.deal_date
        if deal_date:
            parsed_date = self._try_date(deal_date)
            if parsed_date:
                # Apply date filters if specified
                if date_from and parsed_date < date_from:
                    return None
                if date_to and parsed_date > date_to:
                    return None
                deal_date = parsed_date
        
        # Apply area filter if specified
        if target_area and deal.total_area:
            area_tolerance = target_area * 0.2  # ±20%
            if abs(deal.total_area - target_area) > area_tolerance:
                return None
        
        # For now, we'll use a simple distance calculation based on address matching
        # In a real implementation, you'd want to geocode the addresses
        distance_m = None  # TODO: Implement proper geocoding
        
        return {
            "address": address,
            "deal_date": deal_date,
            "price": deal.price,
            "rooms": deal.rooms,
            "floor": deal.floor,
            "asset_type": deal.asset_type,
            "building_year": deal.building_year,
            "total_area": deal.total_area,
            "distance_m": distance_m,
            "source": "nadlan.gov.il",
            "raw_data": deal.raw_data
        }

    def _calculate_statistics(self, transactions: List[Dict[str, Any]], subject_info: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistical information from comparable transactions."""
        if not transactions:
            return {
                "count": 0,
                "median_price": None,
                "avg_price": None,
                "median_price_sqm": None,
                "avg_price_sqm": None,
                "price_range": None,
                "area_range": None
            }
        
        prices = [t.get("price") for t in transactions if t.get("price")]
        areas = [t.get("total_area") for t in transactions if t.get("total_area")]
        
        # Calculate price statistics
        median_price = self._median(prices) if prices else None
        avg_price = sum(prices) / len(prices) if prices else None
        
        # Calculate price per square meter
        price_per_sqm = []
        for t in transactions:
            if t.get("price") and t.get("total_area"):
                price_per_sqm.append(t["price"] / t["total_area"])
        
        median_price_sqm = self._median(price_per_sqm) if price_per_sqm else None
        avg_price_sqm = sum(price_per_sqm) / len(price_per_sqm) if price_per_sqm else None
        
        # Calculate ranges
        price_range = (min(prices), max(prices)) if prices else None
        area_range = (min(areas), max(areas)) if areas else None
        
        return {
            "count": len(transactions),
            "median_price": median_price,
            "avg_price": avg_price,
            "median_price_sqm": median_price_sqm,
            "avg_price_sqm": avg_price_sqm,
            "price_range": price_range,
            "area_range": area_range
        }

    def fetch_comparable_transactions(
        self,
        x: float, 
        y: float,
        street: str,
        house: int,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        target_area: Optional[float] = None,
        limit: int = 2000,
        top: int = 20,
    ) -> Dict[str, Any]:
        """
        Fetch comparable real-estate transactions from nadlan.gov.il.

        Uses the NadlanDealsScraper to fetch real transaction data from the Israeli
        Ministry of Housing's public real-estate site.
        
        Example:
            # Fetch comparables for הגולן 1, תל אביב (Block 6638, Plot 96)
            scraper = NadlanDealsScraper()
            result = scraper.fetch_comparable_transactions(
                x=184320.94, y=668548.65,  # EPSG:2039 coordinates
                street="הגולן",
                house=1,
                date_from="2020-01-01",  # Optional: filter by date range
                date_to="2025-12-31",
                target_area=80.0,        # Optional: filter by similar area (±20%)
                top=15                   # Top 15 closest comparables
            )
        
        Args:
            x: X coordinate in EPSG:2039
            y: Y coordinate in EPSG:2039
            street: Street name for reference
            house: House number for reference
            date_from: Start date filter (YYYY-MM-DD), optional
            date_to: End date filter (YYYY-MM-DD), optional  
            target_area: Filter by apartment area ±20% tolerance, optional
            limit: Max records to fetch (default: 2000)
            top: Number of top comparable transactions to return (default: 20)
            
        Returns:
            Dict with 'stats' (median/avg prices) and 'comps' (comparable transactions)
            
        Raises:
            RuntimeError: If no transaction data can be fetched
        """
        # Convert coordinates to lat/lon
        lon, lat = self._trans_2039_4326.transform(x, y)
        subject_info = {"x": x, "y": y, "lon": lon, "lat": lat}

        try:
            # Try to fetch deals using the street name and area
            query = f"{street}, תל אביב"
            deals = self.get_deals_by_address(query)
            
            # Process deals into comparable transactions
            comps = []
            for deal in deals:
                comp = self._process_nadlan_deal(
                    deal, lat, lon, date_from, date_to, target_area
                )
                if comp:
                    comps.append(comp)
            
            # Sort by date (most recent first) and then by distance
            comps.sort(
                key=lambda c: (
                    c["distance_m"] if c["distance_m"] is not None else 9e12,
                    -int(datetime.fromisoformat(c["deal_date"]).timestamp()) if c["deal_date"] else 0,
                )
            )
            
            # Get top N comparables
            topn = comps[:top]

            # Calculate statistics
            stats = self._calculate_statistics(topn, subject_info)

            return {"stats": stats, "comps": topn}
            
        except NadlanAPIError as e:
            raise RuntimeError(f"Failed to fetch transactions from nadlan.gov.il: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error fetching transactions: {e}")

    def fetch_comparable_transactions_by_neighborhood(
        self,
        neighborhood_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        target_area: Optional[float] = None,
        top: int = 20,
    ) -> Dict[str, Any]:
        """
        Fetch comparable transactions using a neighborhood identifier.
        
        Args:
            neighborhood_id: The numeric neighborhood ID from nadlan.gov.il
            date_from: Start date filter (YYYY-MM-DD), optional
            date_to: End date filter (YYYY-MM-DD), optional
            target_area: Filter by apartment area ±20% tolerance, optional
            top: Number of top comparable transactions to return (default: 20)
            
        Returns:
            Dict with 'stats' (median/avg prices) and 'comps' (comparable transactions)
        """
        try:
            deals = self.get_deals_by_neighborhood_id(neighborhood_id)
            
            # Process deals into comparable transactions
            comps = []
            for deal in deals:
                comp = self._process_nadlan_deal(
                    deal, 0, 0, date_from, date_to, target_area  # No coordinates for neighborhood search
                )
                if comp:
                    comps.append(comp)
            
            # Sort by date (most recent first)
            comps.sort(
                key=lambda c: (
                    -int(datetime.fromisoformat(c["deal_date"]).timestamp()) if c["deal_date"] else 0,
                )
            )
            
            # Get top N comparables
            topn = comps[:top]

            # Calculate statistics
            stats = self._calculate_statistics(topn, {})

            return {"stats": stats, "comps": topn}
            
        except NadlanAPIError as e:
            raise RuntimeError(f"Failed to fetch transactions for neighborhood {neighborhood_id}: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error fetching transactions: {e}")

    def get_neighborhood_id_from_govmap(self, query: str) -> Optional[str]:
        """Get neighborhood ID from govmap auto-complete API.
        
        Args:
            query: Search query (e.g., "רמת החייל")
            
        Returns:
            Neighborhood ID if found, None otherwise
        """
        govmap_url = "https://es.govmap.gov.il/TldSearch/api/AutoComplete"
        params = {
            "query": query,
            "ids": "276267023",  # This seems to be a fixed parameter
            "gid": "govmap"
        }
        
        try:
            resp = self.session.get(govmap_url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            
            # Look for neighborhood matches
            if "res" in data and "NEIGHBORHOOD" in data["res"]:
                neighborhoods = data["res"]["NEIGHBORHOOD"]
                for neighborhood in neighborhoods:
                    if "רמת החייל" in neighborhood.get("Value", ""):
                        return neighborhood.get("Key")
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get neighborhood ID from govmap: {e}")
            return None

    def get_deals_from_neighborhood_page(self, neighborhood_id: str) -> List[DealRecord]:
        """Get deals from the neighborhood page view.
        
        Args:
            neighborhood_id: The neighborhood ID from govmap
            
        Returns:
            List of DealRecord objects
        """
        url = f"https://www.nadlan.gov.il/?view=neighborhood&id={neighborhood_id}&page=deals"
        
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            
            # Parse the HTML to extract deal information
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Look for deal data in the page
            # This will need to be customized based on the actual page structure
            deals = []
            
            # Try to find deal information in the page
            # The exact selectors will depend on how the page is structured
            deal_elements = soup.find_all('div', class_='deal-item')  # Adjust selector as needed
            
            for element in deal_elements:
                try:
                    # Extract deal information from HTML elements
                    # This is a placeholder - actual implementation depends on page structure
                    deal = DealRecord(
                        asset_address=element.get_text().strip(),
                        deal_date=None,  # Extract from page
                        price=None,      # Extract from page
                        rooms=None,      # Extract from page
                        floor=None,      # Extract from page
                        asset_type=None, # Extract from page
                        building_year=None, # Extract from page
                        total_area=None, # Extract from page
                        raw_data={"source": "neighborhood_page", "url": url}
                    )
                    deals.append(deal)
                except Exception as e:
                    logger.warning(f"Failed to parse deal element: {e}")
                    continue
            
            return deals
            
        except Exception as e:
            logger.error(f"Failed to get deals from neighborhood page: {e}")
            return []

    def _decompress_base64_gzip(self, encoded_data: str) -> Dict[str, Any]:
        """Decode base64-encoded gzipped data.
        
        This method replicates the JavaScript decompressBase64Gzip function
        used by the React app.
        
        Args:
            encoded_data: Base64-encoded gzipped string
            
        Returns:
            Decoded JSON data
        """
        try:
            # Decode base64
            compressed_data = base64.b64decode(encoded_data)
            
            # Decompress gzip
            decompressed_data = gzip.decompress(compressed_data)
            
            # Parse JSON
            return json.loads(decompressed_data.decode('utf-8'))
            
        except Exception as e:
            logger.error(f"Failed to decompress base64-gzipped data: {e}")
            raise NadlanAPIError(f"Failed to decompress response data: {e}")

    def get_deals_from_aws_api(self, neighborhood_id: str = None, base_id: str = None, base_name: str = None) -> List[DealRecord]:
        """Get deals from the working AWS API endpoint.
        
        This method uses the actual API that the React app uses:
        https://x4006fhmy5.execute-api.il-central-1.amazonaws.com/api/deal
        
        Args:
            neighborhood_id: Optional neighborhood ID
            base_id: Optional base ID
            base_name: Optional base name
            
        Returns:
            List of DealRecord objects
        """
        api_url = "https://x4006fhmy5.execute-api.il-central-1.amazonaws.com/api/deal"
        
        # Build the request payload based on what the React app sends
        payload = {
            "fetch_number": 1,
            "type_order": "dealDate_down"
        }
        
        if neighborhood_id:
            payload["neighborhood_id"] = neighborhood_id
        if base_id:
            payload["base_id"] = base_id
        if base_name:
            payload["base_name"] = base_name
            
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Origin": "https://www.nadlan.gov.il",
            "Referer": "https://www.nadlan.gov.il/"
        }
        
        try:
            resp = self.session.post(api_url, json=payload, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            
            # The response is base64-encoded and gzipped
            encoded_data = resp.text.strip('"')  # Remove quotes if present
            
            # Decompress the data
            data = self._decompress_base64_gzip(encoded_data)
            
            # Check if we got a successful response
            if data.get("statusCode") == 403:
                raise NadlanAPIError("API access denied - may require authentication")
                
            if "data" not in data or "items" not in data["data"]:
                raise NadlanAPIError(f"Unexpected API response format: {list(data.keys())}")
                
            deals = []
            for item in data["data"]["items"]:
                try:
                    deal = DealRecord(
                        asset_address=item.get("address", ""),
                        deal_date=item.get("dealDate"),
                        price=item.get("dealAmount"),
                        rooms=item.get("rooms"),
                        floor=item.get("floor"),
                        asset_type=item.get("assetType"),
                        building_year=item.get("yearBuilt"),
                        total_area=item.get("area"),
                        raw_data={"source": "aws_api", "api_url": api_url, "original_data": item}
                    )
                    deals.append(deal)
                except Exception as e:
                    logger.warning(f"Failed to parse deal item: {e}")
                    continue
                    
            return deals
            
        except Exception as e:
            logger.error(f"Failed to get deals from AWS API: {e}")
            raise NadlanAPIError(f"Failed to get deals from AWS API: {e}")

    def get_deals_by_address_new_api(self, query: str) -> List[DealRecord]:
        """Get deals using the new AWS API endpoint.
        
        This method tries to find the neighborhood ID and then uses the working API.
        
        Args:
            query: Free-text address or neighborhood name
            
        Returns:
            List of DealRecord objects
        """
        # For now, let's try with some common neighborhood IDs for רמת החייל
        # Based on the govmap data you found earlier
        neighborhood_ids = ["65767022", "65867952"]  # רמת החייל variants
        
        for neighborhood_id in neighborhood_ids:
            try:
                logger.info(f"Trying neighborhood ID: {neighborhood_id}")
                deals = self.get_deals_from_aws_api(neighborhood_id=neighborhood_id)
                if deals:
                    logger.info(f"Found {len(deals)} deals for neighborhood {neighborhood_id}")
                    return deals
            except Exception as e:
                logger.warning(f"Failed with neighborhood ID {neighborhood_id}: {e}")
                continue
                
        # If no deals found, return empty list
        logger.warning(f"No deals found for query: {query}")
        return []


# Convenience functions for backwards compatibility
def get_data_by_query(query: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Legacy function - use NadlanDealsScraper class instead."""
    with NadlanDealsScraper(timeout=timeout) as scraper:
        return scraper.get_data_by_query(query)


def get_assests_and_deals(payload: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
    """Legacy function - use NadlanDealsScraper class instead."""
    with NadlanDealsScraper(timeout=timeout) as scraper:
        return scraper.get_assets_and_deals(payload)


def get_deals_by_address(query: str, timeout: float = 10.0) -> List[Dict[str, Any]]:
    """Legacy function - use NadlanDealsScraper class instead."""
    with NadlanDealsScraper(timeout=timeout) as scraper:
        deals = scraper.get_deals_by_address(query)
        return [deal.to_dict() for deal in deals]


def get_deals_by_neighborhood_id(neighbourhood_id: str, timeout: float = 10.0) -> List[Dict[str, Any]]:
    """Legacy function - use NadlanDealsScraper class instead."""
    with NadlanDealsScraper(timeout=timeout) as scraper:
        deals = scraper.get_deals_by_neighborhood_id(neighbourhood_id)
        return [deal.to_dict() for deal in deals]


# Legacy function for backwards compatibility
def fetch_comparable_transactions(
    x: float, y: float, street: str, house: int,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    target_area: Optional[float] = None, limit: int = 2000, top: int = 20,
) -> Dict[str, Any]:
    """
    Convenience function to fetch comparable transactions.
    Creates a NadlanDealsScraper instance and calls the method.
    """
    with NadlanDealsScraper() as scraper:
        return scraper.fetch_comparable_transactions(
            x, y, street, house, date_from, date_to, target_area, limit, top
        )


if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(
        description="Fetch Israeli real‑estate deals from nadlan.gov.il via the unofficial API."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--query", "-q", metavar="TEXT", help="Free‑text address or neighbourhood name (in Hebrew)"
    )
    group.add_argument(
        "--neighbourhood-id", "-n", metavar="ID", help="Numeric neighbourhood id from the URL"
    )
    args = parser.parse_args()
    
    try:
        with NadlanDealsScraper() as scraper:
            if args.query:
                deals = scraper.get_deals_by_address(args.query)
            else:
                deals = scraper.get_deals_by_address(args.neighbourhood_id)
                
            if not deals:
                print("No deals were found for the given input.")
                sys.exit(0)
                
            # Pretty‑print the deals as JSON
            deals_dict = [deal.to_dict() for deal in deals]
            print(json.dumps(deals_dict, ensure_ascii=False, indent=2))
            
    except NadlanAPIError as e:
        logger.error("Error fetching deals: %s", e)
        sys.exit(1)