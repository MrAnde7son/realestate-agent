"""Utilities for scraping permits from the Tel Aviv Handasa portal."""

from .scraper import HandasaScraper, HandasaScraperError

__all__ = [
    "HandasaScraper",
    "HandasaScraperError",
]
