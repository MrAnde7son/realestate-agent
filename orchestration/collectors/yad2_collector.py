"""Yad2 data collector implementation."""

from typing import List, Optional

from yad2.scrapers.yad2_scraper import RealEstateListing, Yad2Scraper

from .base_collector import BaseCollector


class Yad2Collector(BaseCollector):
    """Wrapper around :class:`Yad2Scraper` implementing a simple interface."""

    def __init__(self, client: Optional[Yad2Scraper] = None) -> None:
        self.client = client or Yad2Scraper()

    def collect(self, address: str, max_pages: int = 1) -> List[RealEstateListing]:
        """Collect Yad2 listings for a given address.

        This method implements the base collect interface and provides
        backward compatibility with the existing ``fetch_listings`` helper
        which is now considered internal.
        """
        return self._fetch_listings(address, max_pages)

    def _fetch_listings(self, address: str, max_pages: int) -> List[RealEstateListing]:
        """Fetch Yad2 listings for a given address."""
        try:
            location = self.client.fetch_location_autocomplete(address)
            if location:
                city = location.get("cities") or []
                streets = location.get("streets") or []
                if city:
                    self.client.set_search_parameters(city=city[0].get("id"))
                if streets:
                    self.client.set_search_parameters(street=streets[0].get("id"))
            return self.client.scrape_all_pages(max_pages=max_pages, delay=0)
        except Exception as e:
            # Handle captcha or other blocking issues gracefully
            print(f"Yad2 scraping failed (likely captcha protection): {e}")
            # Return empty list instead of failing
            return []

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for Yad2 collection."""
        required_params = ['address']
        return all(param in kwargs for param in required_params)
