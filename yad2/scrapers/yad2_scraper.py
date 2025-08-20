#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 Scraper - Core Functionality

Essential Yad2 scraper with clean, focused implementation.
"""

import requests
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from ..core import Yad2SearchParameters, Yad2ParameterReference, RealEstateListing, URLUtils


class Yad2Scraper:
    """Focused Yad2 scraper with essential functionality."""
    
    def __init__(self, search_params=None, headers=None):
        """Initialize the scraper."""
        self.base_url = "https://www.yad2.co.il"
        self.search_endpoint = "/realestate/forsale"
        self.api_base_url = "https://gw.yad2.co.il"
        
        # Default headers to mimic a real browser
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Referer": "https://www.yad2.co.il/"
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
    
    def search_property_types(self, search_term=None):
        """Search property types by name or get all if no search term."""
        all_types = self.get_property_types()
        
        if not search_term:
            return all_types
        
        # Filter by search term
        search_term_lower = search_term.lower()
        return {
            code: name for code, name in all_types.items()
            if search_term_lower in name.lower()
        }
    
    def get_property_type_by_code(self, code):
        """Get property type name by code."""
        if not code:
            return None
        return self.get_property_types().get(int(code))
    
    def fetch_location_data(self, search_text):
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
                print(f"Failed to fetch location data: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching location data: {e}")
            return None
    
    def set_search_parameters(self, **kwargs):
        """Set or update search parameters."""
        for key, value in kwargs.items():
            try:
                self.search_params.set_parameter(key, value)
            except ValueError as e:
                print(f"Warning: {e}")
    
    def build_search_url(self, page=1):
        """Build the search URL with current parameters."""
        self.search_params.set_parameter('page', page)
        base_url = self.base_url + self.search_endpoint
        return self.search_params.build_url(base_url)
    
    def fetch_page(self, url, retries=3, delay=1):
        """Fetch a page with retry logic."""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return BeautifulSoup(response.content, 'html.parser')
                elif response.status_code == 429:  # Rate limited
                    print(f"Rate limited, waiting {delay * (attempt + 1)} seconds...")
                    time.sleep(delay * (attempt + 1))
                else:
                    print(f"Failed to fetch page: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
        
        return None
    
    def extract_listing_info(self, listing_element):
        """Extract information from a listing element."""
        try:
            listing = RealEstateListing()
            
            # Extract price
            price_elem = listing_element.select_one('[data-testid="price"]')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                listing.price = URLUtils.clean_price(price_text)
            
            # Extract title/address
            title_elem = listing_element.select_one("span.item-data-content_heading__tphH4")
            if title_elem:
                listing.title = title_elem.get_text(strip=True)
                listing.address = title_elem.get_text(strip=True)
            
            # Extract property details
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
            print(f"Error extracting listing info: {e}")
            return None
    
    def scrape_page(self, page=1):
        """Scrape a single page of listings."""
        url = self.build_search_url(page)
        print(f"Scraping page {page} from: {url}")
        
        soup = self.fetch_page(url)
        if not soup:
            print(f"Failed to fetch page {page}")
            return []
        
        # Use the working selector
        items = soup.select("a.item-layout_itemLink__CZZ7w")
        if not items:
            print(f"No listings found on page {page}")
            return []
        
        print(f"Found {len(items)} listings")
        
        listings = []
        for item in items:
            card = item.find_parent("div", class_="card_cardBox__KLi9I")
            if card:
                listing = self.extract_listing_info(card)
                if listing and listing.title:
                    listings.append(listing)
        
        return listings
    
    def scrape_all_pages(self, max_pages=10, delay=2):
        """Scrape multiple pages of listings."""
        all_listings = []
        
        for page in range(1, max_pages + 1):
            try:
                listings = self.scrape_page(page)
                
                if not listings:
                    print(f"No more listings found on page {page}")
                    break
                
                all_listings.extend(listings)
                print(f"Page {page}: Found {len(listings)} listings (Total: {len(all_listings)})")
                
                if page < max_pages:
                    time.sleep(delay)
                    
            except KeyboardInterrupt:
                print("Scraping interrupted by user")
                break
            except Exception as e:
                print(f"Error scraping page {page}: {e}")
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
                        type_name = self.get_property_type_by_code(int(prop_id.strip()))
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
            filename = f"yad2_listings_{timestamp}.json"
        
        data = {
            'search_summary': self.get_search_summary(),
            'scrape_time': datetime.now().isoformat(),
            'total_listings': len(self.listings),
            'listings': [listing.to_dict() for listing in self.listings]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(self.listings)} listings to {filename}")
        return filename
    
    @classmethod
    def from_url(cls, url, **kwargs):
        """Create scraper from existing Yad2 URL."""
        params_dict = URLUtils.extract_url_parameters(url)
        return cls(search_params=params_dict, **kwargs)