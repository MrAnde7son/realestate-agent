#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 Scraper Core Module

Core functionality for Yad2 real estate scraping with dynamic parameters.
"""

from .parameters import Yad2SearchParameters, Yad2ParameterReference
from .models import RealEstateListing
from .utils import URLUtils

__version__ = "1.0.0"
__all__ = [
    "Yad2SearchParameters",
    "Yad2ParameterReference", 
    "RealEstateListing",
    "URLUtils"
] 