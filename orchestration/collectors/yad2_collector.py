"""Yad2 data collector implementation."""
import logging

from typing import Dict, List, Optional

from yad2.scrapers.yad2_scraper import RealEstateListing, Yad2Scraper

from orchestration.location import LocationQuery, ensure_location_query

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class Yad2Collector(BaseCollector):
    """Wrapper around :class:`Yad2Scraper` implementing a simple interface."""

    def __init__(self, client: Optional[Yad2Scraper] = None) -> None:
        self.client = client or Yad2Scraper()


    def collect(
            self,
            location: Optional[LocationQuery] = None,
            **kwargs
    ) -> List[RealEstateListing]:
        """Collect Yad2 listings for a given location.

        Parameters
        ----------
        location: Optional[LocationQuery]
            Structured location information. When ``None`` an empty query is
            assumed.
        """

        query = ensure_location_query(location)
        address = f"{query.street} {query.city.replace('-', ' ')}"
        if not address:
            return []

        listings = []
        try:
            search_params = self.client.fetch_location_autocomplete(address)
            if search_params:
                self.client.set_search_parameters(**search_params)

            map_listings = self.client.fetch_listings(pull_contacts=True)
            if map_listings:
                listings.extend(map_listings)
            else:
                listings.extend(self.client.scrape_all_pages(delay=0))

            listings.extend(self.client.fetch_latest_deals())

        except Exception as e:
            logger.error(f"Yad2 scraping failed: {e}")

        return listings

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for Yad2 collection."""
        location = kwargs.get("location")
        return isinstance(location, LocationQuery) and not location.is_empty()
