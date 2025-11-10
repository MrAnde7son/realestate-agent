#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 Scraper Package

A comprehensive, flexible real estate scraper for Yad2.co.il with MCP server integration.
"""

# CLI interface
from .cli import InteractiveCLI

# Core functionality
from .core import (
    RealEstateListing,
    URLUtils,
    Yad2ParameterReference,
    Yad2SearchParameters,
)

# Scrapers
from .scrapers import Yad2Scraper

# API Client
from .api_client import Yad2APIClient, ListingType

__version__ = "1.0.0"
__author__ = "Yad2 Scraper Team"
__email__ = "support@yad2scraper.com"

__all__ = [
    # Core
    "Yad2SearchParameters",
    "Yad2ParameterReference", 
    "RealEstateListing",
    "URLUtils",
    # Scrapers
    "Yad2Scraper",
    # API Client
    "Yad2APIClient",
    "ListingType",
    # CLI
    "InteractiveCLI",
    # Smart Search (new)
    "Yad2SearchHelper",
    "search_houses_in_neighborhood",
    "search_apartments_in_city", 
    "search_property_by_type_and_location",
    # Configuration (new)
    "get_property_type_code",
    "get_city_code",
    "get_neighborhood_code",
    "get_search_preset",
    "validate_search_params",
] 