#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 Utilities

Shared utility functions for URL handling, data processing, and common operations.
"""

import re
try:
    from urllib.parse import urlparse, parse_qs, unquote
except ImportError:
    from urlparse import urlparse, parse_qs
    from urllib import unquote


class URLUtils:
    """Utilities for URL handling and parameter extraction."""
    
    @staticmethod
    def extract_url_parameters(url):
        """
        Extract parameters from a Yad2 URL.
        
        Args:
            url (str): The URL to parse
            
        Returns:
            dict: Dictionary of parameters
        """
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        extracted_params = {}
        for key, values in query_params.items():
            if values:
                extracted_params[key] = unquote(values[0])
        
        return extracted_params
    
    @staticmethod
    def clean_price(price_text):
        """Clean and normalize price text."""
        if not price_text:
            return None
        
        # Remove common Hebrew/English price indicators
        price_text = price_text.replace('₪', '').replace('NIS', '').replace('שח', '')
        price_text = price_text.replace(',', '').replace(' ', '')
        
        # Extract numeric value
        numbers = re.findall(r'\d+', price_text)
        if numbers:
            return int(numbers[0])
        return price_text.strip()
    
    @staticmethod
    def extract_number(text):
        """Extract the first number from text."""
        if not text:
            return None
        numbers = re.findall(r'\d+', text)
        return float(numbers[0]) if numbers else None
    
    @staticmethod
    def extract_listing_id(url):
        """Extract listing ID from URL."""
        if not url:
            return None
        match = re.search(r'/(\d+)/?$', url)
        return match.group(1) if match else None


class DataUtils:
    """Utilities for data processing and analysis."""
    
    @staticmethod
    def calculate_price_stats(listings):
        """Calculate price statistics from listings."""
        prices = [l.price for l in listings if l.price and isinstance(l.price, (int, float))]
        
        if not prices:
            return None
        
        return {
            'count': len(prices),
            'average': sum(prices) / len(prices),
            'median': sorted(prices)[len(prices) // 2],
            'min': min(prices),
            'max': max(prices)
        }
    
    @staticmethod
    def group_by_location(listings):
        """Group listings by location."""
        location_groups = {}
        
        for listing in listings:
            if listing.address:
                # Extract city (simple heuristic - last part after comma)
                parts = listing.address.split(',')
                location = parts[-1].strip() if parts else 'Unknown'
                
                if location not in location_groups:
                    location_groups[location] = []
                location_groups[location].append(listing)
        
        return location_groups
    
    @staticmethod
    def filter_by_criteria(listings, min_price=None, max_price=None, min_rooms=None, max_rooms=None):
        """Filter listings by criteria."""
        filtered = []
        
        for listing in listings:
            # Price filter
            if min_price and listing.price and listing.price < min_price:
                continue
            if max_price and listing.price and listing.price > max_price:
                continue
            
            # Rooms filter
            if min_rooms and listing.rooms and listing.rooms < min_rooms:
                continue
            if max_rooms and listing.rooms and listing.rooms > max_rooms:
                continue
            
            filtered.append(listing)
        
        return filtered


class ValidationUtils:
    """Utilities for data validation."""
    
    @staticmethod
    def validate_city_id(city_id):
        """Validate city ID."""
        valid_cities = {5000, 6200, 6300, 6100, 8600, 7400}  # Common cities
        return city_id in valid_cities
    
    @staticmethod
    def validate_property_type(property_type):
        """Validate property type ID."""
        valid_types = {1, 2, 5, 6, 15, 31, 32, 33, 34, 35, 36, 37, 39}
        return property_type in valid_types
    
    @staticmethod
    def validate_price_range(min_price, max_price):
        """Validate price range."""
        if min_price and max_price:
            return min_price < max_price
        return True 