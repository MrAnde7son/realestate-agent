#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 Scraper - Core Functionality

Essential Yad2 scraper with clean, focused implementation.
"""

import json
import logging
import time
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from utils.retry import request_with_retry

from ..core import (
    RealEstateListing,
    URLUtils,
    Yad2ParameterReference,
    Yad2SearchParameters,
)

# Set up logger
logger = logging.getLogger(__name__)


class Yad2Scraper:
    """Focused Yad2 scraper with essential functionality."""
    
    def __init__(self, search_params=None, headers=None):
        """Initialize the scraper."""
        self.base_url = "https://www.yad2.co.il"
        self.search_endpoint = "/realestate/forsale"
        self.api_base_url = "https://gw.yad2.co.il"
        
        # Mobile headers to avoid CAPTCHA
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "he-IL,he;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Initialize search parameters
        if isinstance(search_params, dict):
            self.search_params = Yad2SearchParameters(**search_params)
        elif isinstance(search_params, Yad2SearchParameters):
            self.search_params = search_params
        else:
            self.search_params = Yad2SearchParameters()
        
        self.assets = []
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
                logger.warning(f"Warning: {e}")
    
    def build_search_url(self, page=1):
        """Build the search URL with current parameters."""
        self.search_params.set_parameter('page', page)
        base_url = self.base_url + self.search_endpoint
        return self.search_params.build_url(base_url)
    
    def fetch_page(self, url):
        """Fetch a page with retry logic."""
        try:
            response = request_with_retry(self.session.get, url, timeout=30)
            
            # Check for various captcha indicators
            response_text = response.text.lower()
            captcha_indicators = [
                "shieldsquare captcha",
                "captcha",
                "cloudflare",
                "access denied",
                "blocked",
                "robot",
                "bot detection"
            ]
            
            for indicator in captcha_indicators:
                if indicator in response_text:
                    raise RuntimeError(f"Captcha/Blocking detected: {indicator}")
            
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Failed to fetch page: {e}")
            return None
    
    def extract_listing_info(self, listing_element):
        """Extract information from a listing element."""
        try:
            listing = RealEstateListing()
            meta_time = datetime.utcnow().isoformat()

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

            if listing.url:
                listing.meta['price'] = {
                    'value': listing.price,
                    'source': 'yad2',
                    'fetched_at': meta_time,
                    'url': listing.url,
                }
                if listing.size:
                    listing.meta['size'] = {
                        'value': listing.size,
                        'source': 'yad2',
                        'fetched_at': meta_time,
                        'url': listing.url,
                    }
            
            return listing
            
        except Exception as e:
            logger.error(f"Error extracting listing info: {e}")
            return None
    
    def scrape_page(self, page=1):
        """Scrape a single page of assets."""
        url = self.build_search_url(page)
        logger.info(f"Scraping page {page} from: {url}")
        
        try:
            soup = self.fetch_page(url)
            if not soup:
                logger.warning(f"Failed to fetch page {page}")
                return []
        except RuntimeError as e:
            if "captcha" in str(e).lower() or "blocking" in str(e).lower():
                logger.warning(f"Captcha/Blocking detected on page {page}: {e}")
                raise e  # Re-raise captcha errors
            else:
                logger.error(f"Error fetching page {page}: {e}")
                return []
        
        # Try multiple selectors for different page layouts
        items = soup.select("a.item-layout_itemLink__CZZ7w")
        if not items:
            # Try mobile selectors
            items = soup.select("div[data-testid='feeditem']")
        if not items:
            # Try generic listing selectors
            items = soup.select("div.feeditem")
        if not items:
            # Try any div with listing-like content
            items = soup.find_all('div', class_=lambda x: x and ('item' in x.lower() or 'listing' in x.lower()))
        
        if not items:
            logger.info(f"No assets found on page {page}")
            return []
        
        logger.info(f"Found {len(items)} assets")
        
        assets = []
        for item in items:
            card = item.find_parent("div", class_="card_cardBox__KLi9I")
            if card:
                listing = self.extract_listing_info(card)
                if listing and listing.title:
                    assets.append(listing)
        
        return assets
    
    def scrape_all_pages(self, max_pages=10, delay=2):
        """Scrape multiple pages of assets."""
        all_assets = []
        
        for page in range(1, max_pages + 1):
            try:
                assets = self.scrape_page(page)
                
                if not assets:
                    logger.info(f"No more assets found on page {page}")
                    break
                
                all_assets.extend(assets)
                logger.info(f"Page {page}: Found {len(assets)} assets (Total: {len(all_assets)})")
                
                if page < max_pages:
                    time.sleep(delay)
                    
            except KeyboardInterrupt:
                logger.info("Scraping interrupted by user")
                break
            except RuntimeError as e:
                if "captcha" in str(e).lower() or "blocking" in str(e).lower():
                    logger.warning(f"Captcha/Blocking detected on page {page}: {e}")
                    raise e  # Re-raise captcha errors so test can catch them
                else:
                    logger.error(f"Runtime error on page {page}: {e}")
                    continue
            except Exception as e:
                logger.error(f"Error scraping page {page}: {e}")
                continue
        
        self.assets = all_assets
        return all_assets
    
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
        """Save assets to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"yad2_assets_{timestamp}.json"
        
        data = {
            'search_summary': self.get_search_summary(),
            'scrape_time': datetime.now().isoformat(),
            'total_assets': len(self.assets),
            'assets': [listing.to_dict() for listing in self.assets]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(self.assets)} assets to {filename}")
        return filename
    
    @classmethod
    def from_url(cls, url, **kwargs):
        """Create scraper from existing Yad2 URL."""
        params_dict = URLUtils.extract_url_parameters(url)
        return cls(search_params=params_dict, **kwargs)