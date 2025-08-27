# -*- coding: utf-8 -*-
"""Nadlan (nadlan.gov.il) deals client.

High-level API:
    from gov.nadlan import NadlanDealsScraper

    # Browser-based scraper (recommended - no tokens needed)
    scraper = NadlanDealsScraper()
    deals = scraper.get_deals_by_neighborhood_id("65210036")
"""
