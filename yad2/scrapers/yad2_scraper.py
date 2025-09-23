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
    from urlparse import urljoin

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
        self.api_base_url = "https://www.yad2.co.il/api"
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
                return {
                    'search_text': search_text,
                    'hoods': data.get('hoods', []),
                    'cities': data.get('cities', []),
                    'areas': data.get('areas', []),
                    'top_areas': data.get('topAreas', []),
                    'streets': data.get('streets', [])
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
            
            # Extract property details using working selector
            desc_lines = listing_element.select("span.item-data-content_itemInfoLine__AeoPP")
            if len(desc_lines) > 1:
                values = desc_lines[1].get_text(strip=True).split(' • ')
                if len(values) >= 1:
                    listing.rooms = URLUtils.extract_number(values[0])
                if len(values) >= 2:
                    listing.floor = values[1].strip()
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
    search_params = {
            "property": "1",        # Apartment
            "maxPrice": 5000000,    # 5M NIS
            "city": "5000",         # Tel Aviv
            "max_pages": 2
        }
    scraper = Yad2Scraper(search_params)
    scraper.scrape_all_pages(max_pages=10)
    scraper.save_to_json()