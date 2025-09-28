"""Yad2 data collector implementation."""

from typing import Dict, List, Optional

from yad2.scrapers.yad2_scraper import RealEstateListing, Yad2Scraper

from .base_collector import BaseCollector


class Yad2Collector(BaseCollector):
    """Wrapper around :class:`Yad2Scraper` implementing a simple interface."""

    def __init__(self, client: Optional[Yad2Scraper] = None) -> None:
        self.client = client or Yad2Scraper()

    @staticmethod
    def _extract_first_value(entry: Dict, keys: List[str]) -> Optional[str]:
        """Return the first matching non-empty value for the provided keys."""

        if not entry:
            return None

        for key in keys:
            value = entry.get(key) if isinstance(entry, dict) else None
            if value not in (None, "", []):
                return value
        return None

    @staticmethod
    def _coerce_numeric(value: Optional[str]) -> Optional[int]:
        """Convert string/integer identifiers to integers when possible."""

        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            digits = value.strip()
            if digits.isdigit():
                return int(digits)
        return None

    @classmethod
    def _prepare_location_parameters(cls, location: Dict) -> Dict[str, object]:
        """Translate autocomplete response into search parameters."""

        if not location:
            return {}

        params: Dict[str, object] = {}

        cities = location.get("cities") or []
        areas = location.get("areas") or []
        top_areas = location.get("top_areas") or []
        hoods = location.get("hoods") or []
        streets = location.get("streets") or []

        selected_city = cities[0] if cities else {}

        city_id = cls._coerce_numeric(
            cls._extract_first_value(selected_city, ["cityId", "id", "value"])
        )
        if city_id is not None:
            params["city"] = city_id

        top_area_id = cls._coerce_numeric(
            cls._extract_first_value(
                selected_city, ["topAreaId", "topArea", "regionId"]
            )
        )
        if top_area_id is None and top_areas:
            top_area_id = cls._coerce_numeric(
                cls._extract_first_value(top_areas[0], ["topAreaId", "id", "value", "code"])
            )
        if top_area_id is not None:
            params["topArea"] = top_area_id

        area_id = cls._coerce_numeric(
            cls._extract_first_value(selected_city, ["areaId", "area", "regionId"])
        )
        if area_id is None and areas:
            area_id = cls._coerce_numeric(
                cls._extract_first_value(areas[0], ["areaId", "id", "value"])
            )
        if area_id is not None:
            params["area"] = area_id

        if hoods:
            hood_entry = None
            if city_id is not None:
                for hood in hoods:
                    hood_city_id = cls._coerce_numeric(
                        cls._extract_first_value(hood, ["cityId", "cityID", "city"])
                    )
                    if hood_city_id is not None and hood_city_id == city_id:
                        hood_entry = hood
                        break
            hood_entry = hood_entry or hoods[0]
            hood_id = cls._coerce_numeric(
                cls._extract_first_value(
                    hood_entry, ["hoodId", "id", "value", "neighborhoodId"]
                )
            )
            if hood_id is not None:
                params["neighborhood"] = hood_id

        if streets:
            street_entry = None
            if city_id is not None:
                for street in streets:
                    street_city_id = cls._coerce_numeric(
                        cls._extract_first_value(street, ["cityId", "cityID", "city"])
                    )
                    if street_city_id is not None and street_city_id == city_id:
                        street_entry = street
                        break
            street_entry = street_entry or streets[0]

            street_id = cls._extract_first_value(
                street_entry, ["streetId", "id", "value"]
            )
            if street_id:
                params["street"] = str(street_id)
            else:
                street_name = cls._extract_first_value(
                    street_entry, ["name", "streetName", "text", "title"]
                )
                if street_name:
                    params["street"] = street_name

        return params

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
                search_params = self._prepare_location_parameters(location)
                if search_params:
                    self.client.set_search_parameters(**search_params)
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
