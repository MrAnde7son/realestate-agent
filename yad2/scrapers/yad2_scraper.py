#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 Scraper

Enhanced Yad2 scraper with dynamic parameter support and comprehensive data extraction.
"""
import logging
import requests
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from yad2.core.models import Contact

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from yad2.core import Yad2SearchParameters, Yad2ParameterReference, RealEstateListing, URLUtils

logger = logging.getLogger(__name__)

class Yad2Scraper:
    """Enhanced Yad2 scraper with dynamic parameter support."""
    
    def __init__(self, search_params=None, headers=None):
        """
        Initialize the scraper.
        
        Args:
            search_params: Yad2SearchParameters object or dict of parameters
            headers: Custom headers for requests
        """
        self.base_url = "https://www.yad2.co.il"
        self.api_base_url = "https://gw.yad2.co.il"
        self.search_endpoint = "/realestate/forsale"
        
        # Default headers to mimic a real browser
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)... Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        }
        # Initialize search parameters
        if isinstance(search_params, dict):
            self.search_params = Yad2SearchParameters(**search_params)
        elif isinstance(search_params, Yad2SearchParameters):
            self.search_params = search_params
        else:
            self.search_params = Yad2SearchParameters()
        
        self.listings = []
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Parameter reference for validation
        self.param_reference = Yad2ParameterReference()

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------
    def fetch_map_listings(self, zoom: Optional[int] = None, pull_contacts = False, **overrides) -> List[RealEstateListing]:
        """
        Fetch active listings via Yad2's public map feed API.

        Args:
            zoom: Optional zoom level (defaults to 15).
            **overrides: Explicit parameters (city, neighborhood, property, etc.)

        Returns:
            List of :class:`RealEstateListing` instances.
        """
        try:
            url = f"{self.api_base_url}/realestate-feed/forsale/map"
            active = self.search_params.get_active_parameters()

            allowed_params = {
                "topArea",
                "area",
                "city",
                "neighborhood",
                "street",
                "property",
                "dealType",
                "priceOnly",
                "exclusive",
                "minPrice",
                "maxPrice",
                "rooms",
                "minRooms",
                "maxRooms",
                "minSize",
                "maxSize",
            }

            params: Dict[str, Any] = {}

            def _choose_value(key: str) -> Optional[Any]:
                if key in overrides and overrides[key] is not None:
                    return overrides[key]
                return active.get(key)

            for key in allowed_params:
                value = _choose_value(key)
                if value is None:
                    continue
                if key == "property" and isinstance(value, (list, tuple, set)):
                    params[key] = ",".join(str(v) for v in value if v is not None)
                else:
                    params[key] = value

            zoom_value = overrides.get("zoom")
            if zoom_value is None:
                zoom_value = zoom if zoom is not None else active.get("zoom")
            params["zoom"] = zoom_value if zoom_value is not None else 15

            logger.info("Fetching map listings with params: %s", params)
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code != 200:
                logger.warning("Failed to fetch map listings: %s", response.status_code)
                return []

            try:
                payload = response.json()
            except json.JSONDecodeError:
                logger.error("Failed to decode map listings response as JSON")
                return []

            listings: List[RealEstateListing] = []

            result = payload.get("data")
            for marker in result.get("markers", []) or []:
                listing = self._convert_map_marker(marker, marker_type="yad2")
                if listing:
                    listings.append(listing)

            for marker in result.get("yad1Markers", []) or []:
                listing = self._convert_map_marker(marker, marker_type="yad1")
                if listing:
                    listings.append(listing)

            for marker in result.get("agencyPromotions", []) or []:
                listing = self._convert_map_marker(marker, marker_type="yad2")
                if listing:
                    listings.append(listing)

            logger.info("Fetched %s listings from Yad2 map endpoint", len(listings))

            if pull_contacts:
                for listing in listings:
                    if listing.url and not listing.contact_info:
                        try:
                            contact_info = self.fetch_contact_info(listing.url)
                        except Exception as e:
                            logger.error("Failed to fetch contact info for listing: %s", listing.url)
                            contact_info = None
                        listing.contact_info = contact_info
                        time.sleep(0.5)  # Be polite
            self.listings = listings
            return listings
        except Exception as exc:
            logger.error("Error fetching map listings: %s", exc)
            return []

    def fetch_contact_info(self, listing_url: str) -> Optional[Contact]:
        token = listing_url.split("/")[-1]
        url = f"{self.api_base_url}/realestate-item/{token}/customer"
        response = self.session.get(url, timeout=30)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch contact details: {response.status_code}")

        payload = response.json()

        result = payload.get("data")


        return Contact(**result)


    def get_property_types(self):
        """Get all property type codes with names."""
        return self.param_reference.get_property_types()

    def get_property_type_by_code(self, code):
        """Get property type name by code."""
        if not code:
            return None
        return self.get_property_types().get(int(code))
    
    def fetch_location_autocomplete(self, search_text: str) -> dict:
        """Fetch location data from Yad2 address autocomplete API."""
        try:
            url = f"{self.api_base_url}/address-autocomplete/realestate/v2"
            params = {'text': search_text}

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                hoods = data.get("hoods", [])
                cities = data.get("cities", [])
                areas = data.get("areas", [])
                top_areas = data.get("topAreas", [])
                streets = data.get("streets", [])

                # Backfill missing lists from streets
                if streets:
                    # Cities
                    if not cities:
                        city_ids = {s.get("cityId") for s in streets if s.get("cityId")}
                        cities = [{"cityId": cid} for cid in city_ids]

                    # Areas
                    if not areas:
                        area_ids = {s.get("areaId") for s in streets if s.get("areaId")}
                        areas = [{"areaId": aid} for aid in area_ids]

                    # Top areas
                    if not top_areas:
                        top_area_ids = {s.get("topAreaId") for s in streets if s.get("topAreaId")}
                        top_areas = [{"topAreaId": tid} for tid in top_area_ids]

                return {
                    "search_text": search_text,
                    "hoods": hoods,
                    "cities": cities,
                    "areas": areas,
                    "top_areas": top_areas,
                    "streets": streets,
                }
            else:
                logger.warning(f"Failed to fetch location data: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching location data: {e}")
            return None
    
    def fetch_latest_deals(
        self,
        limit: int = 8,
        page: int = 1,
        sort_by: str = "saleDate",
        order: str = "desc",
        city: int = None,
        neighborhood: int = None,
        coords="10.0,10.0",
        max_pages: int = 1
    ):
        """
        Fetch completed deal records from Yad2's latest-deals endpoint.

        Example request (Tel Aviv, Bavli)::

            https://gw.yad2.co.il/latest-deals-completed/?limit=8&page=1&sortBy=distance&order=asc&topArea=2&area=1&city=5000&neighborhood=484&coords=32.082830000000,34.791321000000

        Args:
            limit: Number of results per page.
            page: Result page to request (starting page when ``max_pages`` > 1).
            sort_by: Sorting field supported by the API (e.g. ``distance``).
            order: Sort order (``asc`` or ``desc``).
            top_area: Optional top area identifier.
            area: Optional area identifier.
            city: Optional city identifier.
            neighborhood: Optional neighborhood identifier.
            coords: Latitude/longitude pair as string ``"lat,long"`` or tuple.
            max_pages: Number of pages to fetch. Set to ``None`` to exhaust all pages.

        Returns:
            List of :class:`RealEstateListing` objects.
        """
        try:
            url = f"{self.api_base_url}/latest-deals-completed/"
            params = {
                "limit": limit,
                "sortBy": sort_by,
                "order": order,
                "coords": coords,
            }

            active = self.search_params.get_active_parameters()

            def _choose(value, fallback_key):
                return value if value is not None else active.get(fallback_key)

            city_val = _choose(city, "city")
            hood_val = _choose(neighborhood, "neighborhood")

            if city_val is not None:
                params["city"] = city_val
            if hood_val is not None:
                params["neighborhood"] = hood_val

            coords_val = coords if coords is not None else active.get("coords")
            if isinstance(coords_val, (list, tuple)) and len(coords_val) == 2:
                coords_val = "{:.6f},{:.6f}".format(float(coords_val[0]), float(coords_val[1]))
            if coords_val:
                params["coords"] = coords_val

            collected_results = []
            pagination_info = {}
            page_to_fetch = max(page, 1)
            pages_fetched = 0

            while True:
                params["page"] = page_to_fetch
                logger.info(f"Fetching latest deals (page {page_to_fetch}): {params}")
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code != 200:
                    logger.warning("Failed to fetch latest deals (page {}): {}".format(
                        page_to_fetch, response.status_code))
                    break

                data = response.json()
                data = data.get("data", [])
                page_results = data.get("results", [])
                pagination_info = data.get("pagination", {}) or {}

                if not page_results:
                    break

                converted = [self._convert_latest_deal_to_listing(entry) for entry in page_results]
                collected_results.extend(converted)

                pages_fetched += 1

                total_pages = pagination_info.get("totalPages")
                current_page = pagination_info.get("page", page_to_fetch)

                if max_pages is not None and pages_fetched >= max_pages:
                    break
                if total_pages is not None and current_page >= total_pages:
                    break

                page_to_fetch = current_page + 1

            return collected_results
        except Exception as e:
            logger.error("Error fetching latest deals: {}".format(e))
            return []

    def _convert_map_marker(self, marker: Dict[str, Any], marker_type: str = "yad2") -> Optional[RealEstateListing]:
        """Convert a map marker response entry into a :class:`RealEstateListing`."""

        if not marker:
            return None

        try:
            listing = RealEstateListing()

            address = marker.get("address") or {}
            city = self._extract_nested_text(address, "city")
            neighborhood = self._extract_nested_text(address, "neighborhood")
            street = self._extract_nested_text(address, "street")

            house = address.get("house") or {}
            house_number = house.get("number")
            if house_number is not None:
                listing.floor = house.get("floor")
            elif house.get("floor") is not None:
                listing.floor = house.get("floor")

            parts = []
            if street:
                if house_number is not None:
                    parts.append(f"{street} {house_number}")
                else:
                    parts.append(street)
            if neighborhood:
                parts.append(neighborhood)
            if city:
                parts.append(city)

            listing.address = ", ".join([part for part in parts if part])
            if neighborhood:
                listing.meta["neighborhood"] = neighborhood
            if city:
                listing.meta["city"] = city
            if street:
                listing.meta["street"] = street

            coords = address.get("coords") or marker.get("coords")
            if isinstance(coords, dict):
                lon = coords.get("lon")
                lat = coords.get("lat")
            elif isinstance(coords, (list, tuple)) and len(coords) >= 2:
                lon, lat = coords[0], coords[1]
            else:
                lon = lat = None
            try:
                if lon is not None and lat is not None:
                    listing.coordinates = (float(lon), float(lat))
            except (TypeError, ValueError):
                listing.coordinates = None

            additional = marker.get("additionalDetails") or {}
            property_details = additional.get("property") or {}
            listing.property_type = property_details.get("text") or property_details.get("name") or marker.get("propertyType")
            listing.rooms = additional.get("roomsCount") or marker.get("rooms")
            listing.total_size = additional.get("squareMeter") or marker.get("size")

            metadata = marker.get("metaData") or {}
            if listing.size is None:
                listing.size = metadata.get("squareMeterBuild")

            cover_image = metadata.get("coverImage")
            if cover_image:
                listing.images.append(cover_image)
            for image in metadata.get("images") or []:
                if image and image not in listing.images:
                    listing.images.append(image)

            video = metadata.get("video")
            if video:
                listing.video = video

            price = marker.get("price")
            if price in (0, "0", 0.0):
                price = None
            listing.price = price

            token = marker.get("token")
            order_id = marker.get("orderId") or marker.get("listingId")
            if token:
                listing.url = f"{self.base_url}/item/{token}"
                listing.listing_id = str(order_id or token)
            elif order_id is not None:
                listing.listing_id = str(order_id)
            else:
                listing.listing_id = None

            title_parts = []
            if listing.property_type:
                title_parts.append(listing.property_type)
            if listing.address:
                title_parts.append(listing.address)
            if not title_parts and listing.listing_id:
                title_parts.append(str(listing.listing_id))
            listing.title = " - ".join(title_parts) if title_parts else None

            tags = marker.get("tags") or []
            if tags:
                listing.features["tags"] = [tag.get("name") for tag in tags if tag.get("name")]

            customer = marker.get("customer") or {}
            has_agency = bool(customer.get("agencyName"))
            ad_type_raw = marker.get("adType")
            ad_type = ad_type_raw.lower() if isinstance(ad_type_raw, str) else None

            seller_type: Optional[str] = None
            if has_agency:
                seller_type = "broker"
            elif ad_type in {"private"}:
                seller_type = "private"
            elif ad_type in {"commercial", "agency", "broker"}:
                seller_type = "broker"
            elif ad_type:
                seller_type = ad_type

            if has_agency:
                listing.features["agency"] = {
                    "name": customer.get("agencyName"),
                    "logo": customer.get("agencyLogo"),
                }

            if seller_type:
                listing.features["seller_type"] = seller_type
                listing.meta["seller_type"] = seller_type

            video_url = metadata.get("video")
            if video_url:
                listing.meta["video"] = video_url

            listing.meta.update({
                "source": "yad2_map",
                "marker_type": marker_type,
                "token": token,
                "order_id": order_id,
                "ad_type": marker.get("adType"),
                "category_id": marker.get("categoryId"),
                "subcategory_id": marker.get("subcategoryId"),
                "customer": customer or None,
                "raw": marker,
            })

            if marker_type == "yad1":
                listing.meta["project_id"] = marker.get("projectId")

            return listing
        except Exception as exc:
            logger.debug("Failed to convert map marker: %s", exc)
            return None

    @staticmethod
    def _extract_nested_text(container: Dict[str, Any], key: str) -> Optional[str]:
        """Helper to safely extract nested 'text' values."""
        if not container:
            return None
        value = container.get(key)
        if isinstance(value, dict):
            return value.get("text") or value.get("name")
        if isinstance(value, str):
            return value
        return None
    
    def _convert_latest_deal_to_listing(self, deal_entry):
        """Convert a latest-deal payload entry into a RealEstateListing."""
        listing = RealEstateListing()
        
        address = deal_entry.get("address") or {}
        street = (address.get("street") or {}).get("text") or (address.get("street") or {}).get("name")
        house_number = address.get("houseNumber")
        neighborhood = (address.get("neighborhood") or {}).get("text")
        city = (address.get("city") or {}).get("text")

        street_line_parts = [part for part in [street, str(house_number) if house_number else None] if part]
        street_line = " ".join(street_line_parts) if street_line_parts else None

        address_parts = [part for part in [street_line, neighborhood, city] if part]
        listing.address = ", ".join(address_parts) if address_parts else None
        if neighborhood:
            listing.meta["neighborhood"] = neighborhood
        if city:
            listing.meta["city"] = city
        if street:
            listing.meta["street"] = street

        listing.property_type = deal_entry.get("propertyType")
        listing.title = listing.property_type or listing.address
        if listing.title and listing.address and listing.title != listing.address:
            listing.title = "{} - {}".format(listing.title, listing.address)
        elif listing.address:
            listing.title = listing.address

        listing.price = deal_entry.get("price")
        listing.rooms = deal_entry.get("rooms")
        listing.floor = deal_entry.get("floor")
        listing.size = deal_entry.get("buildingMR")
        listing.date_posted = deal_entry.get("saleDate")

        # Preserve supporting data for downstream consumers.
        listing.meta.update({
            "source": "yad2_latest_deals",
            "sale_date": deal_entry.get("saleDate"),
            "number_of_floors": deal_entry.get("numberOfFloors"),
            "build_year": deal_entry.get("buildYear"),
            "address_master_id": address.get("addressMasterId"),
            "raw": deal_entry,
        })

        return listing
    
    def set_search_parameters(self, **kwargs):
        """Set or update search parameters."""
        for key, value in kwargs.items():
            try:
                self.search_params.set_parameter(key, value)
            except ValueError as e:
                logger.warning("Warning: {}".format(e))
    
    def build_search_url(self, page=1):
        """Build the search URL with current parameters."""
        # Set page parameter
        self.search_params.set_parameter('page', page)
        
        # Build URL with all parameters
        base_url = self.base_url + self.search_endpoint
        return self.search_params.build_url(base_url)
    
    def fetch_page(self, url, retries=3, delay=1):
        """
        Fetch a page with retry logic.
        
        Args:
            url: URL to fetch
            retries: Number of retry attempts
            delay: Delay between retries in seconds
        
        Returns:
            BeautifulSoup object or None if failed
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return BeautifulSoup(response.content, 'html.parser')
                elif response.status_code == 429:  # Rate limited
                    logger.warning("Rate limited, waiting {} seconds...".format(delay * (attempt + 1)))
                    time.sleep(delay * (attempt + 1))
                else:
                    logger.warning("Failed to fetch page: {}".format(response.status_code))
                    
            except requests.exceptions.RequestException as e:
                logger.error("Error fetching page (attempt {}): {}".format(attempt + 1, e))
                if attempt < retries - 1:
                    time.sleep(delay)
        
        return None
    
    def extract_listing_info(self, listing_element):
        """
        Extract information from a listing element using working selectors.
        
        Args:
            listing_element: BeautifulSoup element containing listing data
            
        Returns:
            RealEstateListing object or None
        """
        try:
            listing = RealEstateListing()
            
            # Extract price using working selector
            price_elem = listing_element.select_one('[data-testid="price"]')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                listing.price = URLUtils.clean_price(price_text)
            
            # Extract title/address using working selector
            title_elem = listing_element.select_one("span.item-data-content_heading__tphH4")
            if title_elem:
                listing.title = title_elem.get_text(strip=True)
                listing.address = title_elem.get_text(strip=True)
            
            # Extract property type from title or content
            # Look for property type patterns in the title/content
            property_type = self._extract_property_type(listing_element)
            if property_type:
                listing.property_type = property_type
            
            # Extract property details using working selector
            desc_lines = listing_element.select("span.item-data-content_itemInfoLine__AeoPP")
            if len(desc_lines) > 1:
                values = desc_lines[1].get_text(strip=True).split(' • ')
                if len(values) >= 1:
                    listing.rooms = URLUtils.extract_number(values[0])
                if len(values) >= 2:
                    listing.floor = URLUtils.parse_floor(values[1].strip())
                if len(values) >= 3:
                    listing.size = URLUtils.extract_number(values[2])
            
            # Extract URL
            link_elem = listing_element.find('a', href=True)
            if link_elem:
                listing.url = urljoin(self.base_url, link_elem['href'])
                listing.listing_id = URLUtils.extract_listing_id(listing.url)
            
            return listing
            
        except Exception as e:
            logger.error("Error extracting listing info: {}".format(e))
            return None
    
    def _extract_property_type(self, listing_element):
        """
        Extract property type from listing element.
        
        Args:
            listing_element: BeautifulSoup element containing listing data
            
        Returns:
            Property type string or None
        """
        try:
            # Get all text content from the listing element
            text_content = listing_element.get_text()
            
            # Define property type patterns to look for
            property_patterns = [
                r'בית פרטי/?\s*קוטג',
                r'בית פרטי',
                r'דירה',
                r'פנטהאוס',
                r'קוטג',
                r'וילה',
                r'בית דו משפחתי',
                r'דופלקס',
                r'טריפלקס',
                r'סטודיו',
                r'דירת גן',
                r'דירה עם גינה'
            ]
            
            # Look for property type patterns in the text
            import re
            for pattern in property_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    property_type = match.group(0).strip()
                    
                    # Clean up the property type
                    if '/' in property_type:
                        # Handle cases like "בית פרטי/ קוטג" - take the first part
                        property_type = property_type.split('/')[0].strip()
                    
                    # Map to standard property type names
                    property_type_mapping = {
                        'בית פרטי': 'בית פרטי',
                        'קוטג': 'קוטג',
                        'וילה': 'קוטג',  # Villa maps to cottage
                        'דירה': 'דירה',
                        'פנטהאוס': 'פנטהאוס',
                        'בית דו משפחתי': 'בית דו משפחתי',
                        'דופלקס': 'דופלקס',
                        'טריפלקס': 'טריפלקס',
                        'סטודיו': 'סטודיו',
                        'דירת גן': 'דירת גן',
                        'דירה עם גינה': 'דירה עם גינה'
                    }
                    
                    return property_type_mapping.get(property_type, property_type)
            
            return None
            
        except Exception as e:
            logger.error("Error extracting property type: {}".format(e))
            return None
    
    def scrape_page(self, page=1):
        """
        Scrape a single page of listings.
        
        Args:
            page: Page number to scrape
            
        Returns:
            List of RealEstateListing objects
        """
        url = self.build_search_url(page)
        logger.info("Scraping page {} from: {}".format(page, url))
        
        soup = self.fetch_page(url)
        if not soup:
            logger.error("Failed to fetch page {}".format(page))
            return []
        
        # Use the working selector from utils
        items = soup.select("a.item-layout_itemLink__CZZ7w")
        if not items:
            logger.info("No listings found on page {} - trying fallback extraction".format(page))
            return []
        
        logger.debug("Found {} listings using working selector".format(len(items)))
        
        listings = []
        for item in items:
            # Find the parent card container
            card = item.find_parent("div", class_="card_cardBox__KLi9I")
            if card:
                listing = self.extract_listing_info(card)
                if listing and listing.title:  # Only add if we got meaningful data
                    listings.append(listing)
        
        return listings
    
    def scrape_all_pages(self, max_pages=10, delay=2):
        """
        Scrape multiple pages of listings.
        
        Args:
            max_pages: Maximum number of pages to scrape
            delay: Delay between page requests in seconds
            
        Returns:
            List of all RealEstateListing objects
        """
        all_listings = []
        
        for page in range(1, max_pages + 1):
            try:
                listings = self.scrape_page(page)
                
                if not listings:
                    logger.info("No more listings found on page {}".format(page))
                    break
                
                all_listings.extend(listings)
                logger.info("Page {}: Found {} listings (Total: {})".format(
                    page, len(listings), len(all_listings)))
                
                # Add delay between requests to be respectful
                if page < max_pages:
                    time.sleep(delay)
                    
            except KeyboardInterrupt:
                logger.debug("Scraping interrupted by user")
                break
            except Exception as e:
                logger.error("Error scraping page {}: {}".format(page, e))
                continue
        
        self.listings = all_listings
        return all_listings
    
    def get_search_summary(self):
        """Get a summary of the current search parameters."""
        active_params = self.search_params.get_active_parameters()
        
        summary = {
            'search_url': self.build_search_url(1),
            'parameters': active_params,
            'parameter_descriptions': {}
        }
        
        # Add human-readable descriptions for parameters
        for param, value in active_params.items():
            info = self.param_reference.get_parameter_info(param)
            summary['parameter_descriptions'][param] = {
                'value': value,
                'description': info['description']
            }
            
            # Add property type names if applicable
            if param == 'property' and value:
                prop_types = str(value).split(',')
                type_names = []
                for prop_id in prop_types:
                    try:
                        type_name = self.param_reference.get_property_types().get(int(prop_id.strip()))
                        if type_name:
                            type_names.append(type_name)
                    except (ValueError, TypeError):
                        pass
                if type_names:
                    summary['parameter_descriptions'][param]['type_names'] = type_names
        
        return summary
    
    def save_to_json(self, filename=None):
        """Save listings to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = "yad2_listings_{}.json".format(timestamp)
        
        data = {
            'search_summary': self.get_search_summary(),
            'scrape_time': datetime.now().isoformat(),
            'total_listings': len(self.listings),
            'listings': [listing.to_dict() for listing in self.listings]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info("Saved {} listings to {}".format(len(self.listings), filename))
        return filename
    
    @classmethod
    def from_url(cls, url, **kwargs):
        """
        Create scraper from existing Yad2 URL.
        
        Args:
            url: Yad2 URL with parameters
            **kwargs: Additional scraper options
            
        Returns:
            Yad2Scraper instance
        """
        params_dict = URLUtils.extract_url_parameters(url)
        return cls(search_params=params_dict, **kwargs) 


if __name__ == "__main__":
    search_params =  { 'city': 5000, 'neighborhood': 203, "topArea": 2, "area": 1, "zoom": 15}
    scraper = Yad2Scraper(search_params)
    deals = scraper.fetch_map_listings(pull_contacts=True)
    print(deals)
