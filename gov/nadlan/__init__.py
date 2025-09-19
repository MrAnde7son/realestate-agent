# -*- coding: utf-8 -*-
"""Nadlan (nadlan.gov.il) deals client.

High-level API:
    from gov.nadlan import NadlanDealsScraper

    # Browser-based scraper (recommended - no tokens needed)
    scraper = NadlanDealsScraper()
    deals = scraper.get_deals_by_neighborhood_id("65210036")
"""

from .models import Deal
from .exceptions import NadlanAPIError, NadlanError, NadlanConfigError, NadlanDecodeError

# Import scraper only if selenium is available
try:
    from .scraper import NadlanDealsScraper
except ImportError:
    # Selenium not available, define a placeholder
    class NadlanDealsScraper:
        def __init__(self, *args, **kwargs):
            raise ImportError("NadlanDealsScraper requires selenium. Install with: pip install selenium webdriver-manager")

__all__ = [
    "Deal",
    "NadlanAPIError", 
    "NadlanError",
    "NadlanConfigError",
    "NadlanDecodeError",
    "NadlanDealsScraper"
]
