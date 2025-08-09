#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 Scraper Package

A comprehensive, flexible real estate scraper for Yad2.co.il with MCP server integration.
"""

# Core functionality
from .core import (
    Yad2SearchParameters,
    Yad2ParameterReference,
    RealEstateListing,
    URLUtils
)

# Scrapers
from .scrapers import Yad2Scraper

# CLI interface
from .cli import InteractiveCLI

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
    # CLI
    "InteractiveCLI",
] 