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
from .scraper import NadlanDealsScraper

__all__ = [
    "Deal",
    "NadlanAPIError", 
    "NadlanError",
    "NadlanConfigError",
    "NadlanDecodeError",
    "NadlanDealsScraper"
]
