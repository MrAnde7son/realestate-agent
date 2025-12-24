"""Yad2 data collector implementation."""

import logging

from typing import List, Optional

from yad2.api_client import Yad2APIClient, RealEstateListing
from orchestration.location import LocationQuery, ensure_location_query

from orchestration.collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class Yad2Collector(BaseCollector):
    """Wrapper around :class:`Yad2Scraper` implementing a simple interface."""

    def __init__(self, client: Optional[Yad2APIClient] = None) -> None:
        self.client = client or Yad2APIClient()

    def collect(
        self, location: Optional[LocationQuery] = None, **kwargs
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
                self.client.set_search_parameters(search_params)

            map_listings = self.client.fetch_listings(pull_contacts=True)
            if map_listings:
                listings.extend(map_listings)

            if len(listings) > 0:
                # Safely extract neighborhood and city from meta
                neighborhood = listings[0].meta.get("neighborhood", "")
                city = listings[0].meta.get("city", "")

                # Only fetch latest deals if we have location information
                if neighborhood or city:
                    location_query = f"{neighborhood} {city}".strip()
                    if location_query:
                        search_params = self.client.fetch_location_autocomplete(
                            location_query
                        )
                        if search_params:
                            self.client.set_search_parameters(search_params)
                    latest_deals = self.client.fetch_latest_deals()
                    listings.extend(latest_deals)

        except Exception as e:
            logger.error(f"Yad2 collector failed: {e}")

        return listings

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for Yad2 collection."""
        location = kwargs.get("location")
        return isinstance(location, LocationQuery) and not location.is_empty()


if __name__ == "__main__":
    collector = Yad2Collector()
    listings = collector.collect(
        location=LocationQuery(city="תל אביב יפו", street="רוזוב", house_number=14)
    )
    print(listings)
