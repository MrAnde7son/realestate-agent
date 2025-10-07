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
from bs4 import BeautifulSoup
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin  # type: ignore

from ..core import Yad2SearchParameters, Yad2ParameterReference, RealEstateListing, URLUtils

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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
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
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Check if we got a CAPTCHA page
                    if self.is_captcha_page(soup):
                        logger.warning("CAPTCHA page detected on attempt {}".format(attempt + 1))
                        if attempt < retries - 1:
                            # Wait longer before retrying
                            wait_time = delay * (attempt + 1) * 2
                            logger.info("Waiting {} seconds before retry...".format(wait_time))
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error("CAPTCHA page received on final attempt")
                            return None
                    
                    return soup
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
    
    def is_captcha_page(self, soup):
        """
        Check if the page is a CAPTCHA page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            bool: True if CAPTCHA page detected
        """
        if not soup:
            return False
            
        # Check for common CAPTCHA indicators
        title = soup.find('title')
        if title and 'captcha' in title.get_text().lower():
            return True
            
        # Check for ShieldSquare CAPTCHA
        if soup.find(text=lambda text: text and 'shieldsquare' in text.lower()):
            return True
            
        # Check for common CAPTCHA elements
        captcha_indicators = [
            'captcha',
            'challenge',
            'verification',
            'robot',
            'bot detection'
        ]
        
        page_text = soup.get_text().lower()
        for indicator in captcha_indicators:
            if indicator in page_text:
                return True
                
        return False
    
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
            
            # Extract price using multiple possible selectors
            price_elem = (
                listing_element.select_one('[data-testid="price"]') or
                listing_element.select_one('.feed-item-price_price__ygoeF') or
                listing_element.select_one('.yad1-listing-data-content_priceBox__trQtc')
            )
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Only process if it looks like a real price (contains numbers and currency symbols)
                if price_text and any(char in price_text for char in ['₪', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ',']):
                    listing.price = URLUtils.clean_price(price_text)
            
            # Extract title/address using multiple possible selectors
            title_elem = (
                listing_element.select_one("span.item-data-content_heading__tphH4") or
                listing_element.select_one(".yad1-listing-data-content_heading__Gc3bF") or
                listing_element.select_one("h2[data-nagish='content-section-title'] span")
            )
            if title_elem:
                listing.title = title_elem.get_text(strip=True)
                listing.address = title_elem.get_text(strip=True)
            
            # Extract property details using multiple possible selectors
            desc_lines = (
                listing_element.select("span.item-data-content_itemInfoLine__AeoPP") or
                listing_element.select(".yad1-listing-data-content_itemInfoLine__eufuS")
            )
            
            if len(desc_lines) > 1:
                # Try to extract rooms, floor, size from the second line
                second_line = desc_lines[1].get_text(strip=True)
                if '•' in second_line:
                    values = second_line.split(' • ')
                    if len(values) >= 1:
                        listing.rooms = URLUtils.extract_number(values[0])
                    if len(values) >= 2:
                        listing.floor = values[1].strip()
                    if len(values) >= 3:
                        listing.size = URLUtils.extract_number(values[2])
                else:
                    # Try to extract rooms from the text directly
                    listing.rooms = URLUtils.extract_number(second_line)
            
            # Extract URL using multiple possible selectors
            link_elem = (
                listing_element.find('a', href=True) or
                listing_element.select_one('a[data-nagish="feed-item-layout-link"]') or
                listing_element.select_one('a[data-nagish="king-of-the-har-link"]')
            )
            if link_elem:
                listing.url = urljoin(self.base_url, link_elem['href'])
                listing.listing_id = URLUtils.extract_listing_id(listing.url)
            
            return listing
            
        except Exception as e:
            logger.error("Error extracting listing info: {}".format(e))
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
        
        listings = []
        
        # Try multiple selectors to catch different types of listings
        selectors_to_try = [
            "a.item-layout_itemLink__CZZ7w",  # Original selector
            "li[data-testid='platinum-item']",  # Platinum listings
            "li[data-testid='yad1-listing-basic']",  # Yad1 listings
            "li[data-testid='king-item']",  # King/agency listings
        ]
        
        for selector in selectors_to_try:
            items = soup.select(selector)
            if items:
                logger.debug("Found {} items using selector: {}".format(len(items), selector))
                
                for item in items:
                    # Find the parent card container or use the item itself
                    card = item.find_parent("div", class_="card_cardBox__KLi9I") or item
                    listing = self.extract_listing_info(card)
                    if listing and listing.title:  # Only add if we got meaningful data
                        listings.append(listing)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_listings = []
        for listing in listings:
            if listing.url and listing.url not in seen_urls:
                seen_urls.add(listing.url)
                unique_listings.append(listing)
        
        logger.info("Found {} unique listings on page {}".format(len(unique_listings), page))
        return unique_listings
    
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
    search_params = {
            "property": "1",        # Apartment
            "maxPrice": 5000000,    # 5M NIS
            "city": "5000",         # Tel Aviv
            "max_pages": 2
        }
    scraper = Yad2Scraper(search_params)
    scraper.scrape_all_pages(max_pages=10)
    scraper.save_to_json()