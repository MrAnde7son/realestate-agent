#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 API Client

Client for interacting with Yad2's public API endpoints (map feeds, contacts, autocomplete, etc.)
"""
import logging
from enum import Enum

import requests
import json
import time
import os
from typing import Any, Dict, List, Optional

from yad2.core.models import Contact
from yad2.core import Yad2SearchParameters, Yad2ParameterReference, RealEstateListing

logger = logging.getLogger(__name__)


class ListingType(Enum):
    """Listing type constants."""
    SALE = "sale"
    RENT = "rent"
    COMMERCIAL = "commercial"
    ALL = "all"


class Yad2APIClient:
    """Client for Yad2 API endpoints."""
    
    def __init__(self, search_params=None, headers=None):
        """
        Initialize the API client.
        
        Args:
            headers: Custom headers for requests
        """
        self.api_base_url = "https://gw.yad2.co.il"
        
        # Default headers to mimic a real browser
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)... Safari/537.36",
            "Accept": "application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Initialize search parameters
        if isinstance(search_params, dict):
            self.search_params = Yad2SearchParameters(**search_params)
        elif isinstance(search_params, Yad2SearchParameters):
            self.search_params = search_params
        else:
            self.search_params = Yad2SearchParameters()
        
        # Parameter reference for validation
        self.param_reference = Yad2ParameterReference()

        # Contact fetching config (rate limit/backoff)
        self.contacts_per_run_limit = int(os.getenv("YAD2_CONTACTS_PER_RUN_LIMIT", "50"))
        self.contacts_min_interval_s = float(os.getenv("YAD2_CONTACTS_MIN_INTERVAL_S", "0.5"))
        self.contacts_retries = int(os.getenv("YAD2_CONTACTS_RETRIES", "1"))
        
        # Simple in-memory cache for project autocomplete lookups
        self._project_autocomplete_cache: Dict[str, Dict[str, Any]] = {}
        self._project_autocomplete_fetcher = None  # Will be set by scraper if needed

    def _get_active_params(self, search_params: Yad2SearchParameters) -> Dict[str, Any]:
        if self.search_params or search_params:
            return self.search_params and self.search_params.get_active_parameters() or search_params.get_active_parameters()
        return {}

    def set_search_parameters(self, search_params: Yad2SearchParameters):
        """Set or update search parameters."""
        self.search_params = search_params
    

    def fetch_listings(
        self,
        search_params: Optional[Yad2SearchParameters] = None,
        zoom: Optional[int] = None,
        listing_type: str = ListingType.ALL,
        pull_contacts: bool = False,
        project_autocomplete_fetcher=None,
        **overrides
    ) -> List[RealEstateListing]:
        """
        Fetch active listings via Yad2's public map feed API.

        Args:
            search_params: Yad2SearchParameters object with search criteria
            zoom: Optional zoom level (defaults to 15).
            listing_type: Listing type (sale, rent, commercial, all)
            pull_contacts: Whether to pull contact info for the listings
            project_autocomplete_fetcher: Optional function to fetch project autocomplete data
            **overrides: Explicit parameters (city, neighborhood, property, etc.)

        Returns:
            List of :class:`RealEstateListing` instances.
        """
        active = self._get_active_params(search_params)

        params: Dict[str, Any] = active

        zoom_value = overrides.get("zoom")
        if zoom_value is None:
            zoom_value = zoom if zoom is not None else active.get("zoom")
        params["zoom"] = zoom_value if zoom_value is not None else 15

        if listing_type == ListingType.SALE:
            urls = [f"{self.api_base_url}/realestate-feed/forsale/map"]
        elif listing_type == ListingType.RENT:
            urls = [f"{self.api_base_url}/realestate-feed/rent/map"]
        elif listing_type == ListingType.COMMERCIAL:
            urls = [f"{self.api_base_url}/realestate-feed/commercial/map"]
        else:
            urls = [
                f"{self.api_base_url}/realestate-feed/forsale/map",
                f"{self.api_base_url}/realestate-feed/rent/map",
                f"{self.api_base_url}/realestate-feed/commercial/map",
            ]

        listings: List[RealEstateListing] = []
        for url in urls:
            current_listing_type = ListingType(url.split("/")[-2].replace("for", ""))
            try:
                logger.info("Fetching map listings with params: %s", params)
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code != 200:
                    logger.warning("Failed to fetch map listings: %s", response.status_code)
                    continue

                # Check if response is empty before parsing JSON
                if not response.text or not response.text.strip():
                    logger.warning("Empty response from map listings API")
                    continue

                try:
                    payload = response.json()
                except json.JSONDecodeError as e:
                    logger.error("Failed to decode map listings response as JSON: %s. Response: %s", e, response.text[:200])
                    continue

                result = payload.get("data", {})
                for marker in result.get("markers", []):
                    listing = self._convert_map_marker(
                        marker,
                        listing_type=current_listing_type,
                        marker_type="yad2",
                        project_autocomplete_fetcher=project_autocomplete_fetcher
                    )
                    if listing:
                        listings.append(listing)

                for marker in result.get("yad1Markers", []):
                    listing = self._convert_map_marker(
                        marker,
                        listing_type=current_listing_type,
                        marker_type="yad1",
                        project_autocomplete_fetcher=project_autocomplete_fetcher
                    )
                    if listing:
                        listings.append(listing)

                for marker in result.get("agencyPromotions", []):
                    listing = self._convert_map_marker(
                        marker,
                        listing_type=current_listing_type,
                        marker_type="yad2",
                        project_autocomplete_fetcher=project_autocomplete_fetcher
                    )
                    if listing:
                        listings.append(listing)

                logger.info("Fetched %s listings from Yad2 map endpoint", len(listings))

                if pull_contacts:
                    # Build a deduplicated token map to avoid duplicate requests
                    token_to_listings: Dict[str, List[RealEstateListing]] = {}
                    for listing in listings:
                        if not listing.url or listing.contact_info:
                            continue
                        try:
                            token = listing.url.rstrip("/").split("/")[-1]
                        except Exception as e:
                            logger.error("Failed to extract token from listing URL: %s; %s", listing.url, e)
                            continue

                        # seems like integers are irrelevant
                        try:
                            if int(token):
                                continue
                        except (TypeError, ValueError) as parse_error:
                            logger.debug("Token %s is not numeric: %s", token, parse_error)

                        token_to_listings.setdefault(token, []).append(listing)

                    tokens = list(token_to_listings.keys())
                    if not tokens:
                        logger.info("No contact tokens to fetch for this batch")
                    else:
                        limit = self.contacts_per_run_limit
                        tokens_to_fetch = tokens[:limit]
                        if len(tokens) > limit:
                            logger.info("Capping contact fetches at %s of %s tokens", limit, len(tokens))

                        for idx, token in enumerate(tokens_to_fetch, 1):
                            contact_info = self.fetch_contact_info(token)
                            # fetch_contact_info returns None on failure, which is fine

                            for listing_item in token_to_listings.get(token, []):
                                listing_item.contact_info = contact_info

                            # Throttle between requests
                            time.sleep(self.contacts_min_interval_s)
            except Exception as exc:
                logger.error("Error fetching map listings: %s", exc)
                continue

        return listings

    def fetch_contact_info(self, token: str) -> Optional[Contact]:
        """Fetch contact information for a listing token."""
        url = f"{self.api_base_url}/realestate-item/{token}/customer"
        last_exception = None
        for attempt in range(self.contacts_retries):
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    # Check if response is empty before parsing JSON
                    response_text = response.text.strip() if response.text else ""
                    if not response_text:
                        logger.debug("Empty response from contact API for token %s (attempt %d/%d)", 
                                   token, attempt + 1, self.contacts_retries)
                        last_exception = Exception("Empty response from API")
                        continue

                    # Check if response looks like HTML (common error page)
                    if response_text.startswith('<') or response_text.lower().startswith('<!doctype'):
                        logger.debug("Received HTML instead of JSON from contact API for token %s (attempt %d/%d)", 
                                   token, attempt + 1, self.contacts_retries)
                        last_exception = Exception("Received HTML instead of JSON")
                        continue

                    try:
                        payload = response.json()
                    except json.JSONDecodeError as e:
                        logger.debug("Failed to parse JSON from contact API for token %s (attempt %d/%d): %s. Response preview: %s", 
                                   token, attempt + 1, self.contacts_retries, e, response_text[:200])
                        last_exception = e
                        continue

                    result = payload.get("data")
                    if not result:
                        logger.debug("No data field in contact API response for token %s", token)
                        return None
                    return Contact(**result)
                if response.status_code == 429:
                    # Rate limited
                    logger.debug("Rate limited from Yad2 contacts API for token %s (attempt %d/%d)", 
                               token, attempt + 1, self.contacts_retries)
                    continue
                if 500 <= response.status_code < 600:
                    # transient server errors
                    logger.debug("Server error %s from Yad2 contacts API for token %s (attempt %d/%d)", 
                               response.status_code, token, attempt + 1, self.contacts_retries)
                    continue
                # Other status codes considered non-retryable
                logger.debug("Non-retryable status %s from contact API for token %s", response.status_code, token)
                return None
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.debug("Network error fetching contact for token %s (attempt %d/%d): %s", 
                           token, attempt + 1, self.contacts_retries, e)
                continue
            except json.JSONDecodeError as e:
                last_exception = e
                logger.debug("JSON decode error fetching contact for token %s (attempt %d/%d): %s", 
                           token, attempt + 1, self.contacts_retries, e)
                continue
        # Exhausted retries
        if last_exception:
            logger.warning("Contact fetch failed after %d retries for token %s: %s", 
                         self.contacts_retries, token, last_exception)
            return None
        logger.warning("Contact fetch failed after %d retries for token %s: unknown error", 
                     self.contacts_retries, token)
        return None

    def fetch_project_autocomplete(self, phrase: str) -> Optional[Dict[str, Any]]:
        """Fetch project data from Yad1 developers autocomplete API.

        Args:
            phrase: Free-text phrase, e.g. projectName.

        Returns:
            Dict with the best matching project entry or None when not available.
        """
        if not phrase:
            return None

        cached = self._project_autocomplete_cache.get(phrase)
        if cached is not None:
            return cached

        try:
            url = f"{self.api_base_url}/yad1/projects-developers/autocomplete"
            params = {"phrase": phrase}
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.debug("Project autocomplete API returned status %s for phrase '%s'", response.status_code, phrase)
                return None

            # Check if response is empty before parsing JSON
            response_text = response.text.strip() if response.text else ""
            if not response_text:
                logger.debug("Empty response from project autocomplete API for phrase '%s'", phrase)
                return None

            # Check if response looks like HTML (common error page)
            if response_text.startswith('<') or response_text.lower().startswith('<!doctype'):
                logger.debug("Received HTML instead of JSON from project autocomplete API for phrase '%s'", phrase)
                return None

            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.debug("Failed to parse JSON from project autocomplete API for phrase '%s': %s. Response preview: %s", 
                           phrase, e, response_text[:200])
                return None

            entries: List[str, Any] = data.get("data", {}).get('projects', [])

            best: Optional[Dict[str, Any]] = None
            for entry in entries:
                meta = (entry or {}).get("metaData") or {}
                if meta.get("projectName") == phrase:
                    best = entry
                    break

            self._project_autocomplete_cache[phrase] = best
            return best
        except requests.exceptions.RequestException as e:
            logger.debug("Network error fetching project autocomplete for phrase '%s': %s", phrase, e)
            return None
        except json.JSONDecodeError as e:
            logger.debug("JSON decode error fetching project autocomplete for phrase '%s': %s", phrase, e)
            return None
        except Exception as e:
            logger.debug("Unexpected error fetching project autocomplete for phrase '%s': %s", phrase, e)
            return None

    def fetch_location_autocomplete(self, search_text: str) -> Optional[Yad2SearchParameters]:
        """Fetch location data from Yad2 address autocomplete API and return prepared search parameters.
        
        Args:
            search_text: Address text to search for
            
        Returns:
            Dict with prepared search parameters (city, area, neighborhood, street, etc.)
            or None if the request failed
        """
        try:
            url = f"{self.api_base_url}/address-autocomplete/realestate/v2"
            params = {'text': search_text}

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                # Check if response is empty before parsing JSON
                if not response.text or not response.text.strip():
                    logger.warning("Empty response from location autocomplete API")
                    return None

                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse JSON from location autocomplete API: %s. Response: %s", e, response.text[:200])
                    return None

                hoods = data.get("hoods", [])
                cities = data.get("cities", [])
                areas = data.get("areas", [])
                top_areas = data.get("topAreas", [])
                streets = data.get("streets", [])

                # Backfill missing lists from streets
                if streets:
                    # Cities
                    if not cities:
                        city_ids = {s.get("cityId") for s in streets if s.get("cityId")}
                        cities = [{"cityId": cid} for cid in city_ids]

                    # Areas
                    if not areas:
                        area_ids = {s.get("areaId") for s in streets if s.get("areaId")}
                        areas = [{"areaId": aid} for aid in area_ids]

                    # Top areas
                    if not top_areas:
                        top_area_ids = {s.get("topAreaId") for s in streets if s.get("topAreaId")}
                        top_areas = [{"topAreaId": tid} for tid in top_area_ids]

                location_data = {
                    "search_text": search_text,
                    "hoods": hoods,
                    "cities": cities,
                    "areas": areas,
                    "top_areas": top_areas,
                    "streets": streets,
                }

                # Prepare and return search parameters
                return Yad2SearchParameters(**self._prepare_location_parameters(location_data))
            else:
                logger.warning(f"Failed to fetch location data: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching location data: {e}")
            return None

    def fetch_latest_deals(
        self,
        search_params: Optional[Yad2SearchParameters] = None,
        limit: int = 8,
        page: int = 1,
        sort_by: str = "saleDate",
        order: str = "desc",
        city: int = None,
        neighborhood: int = None,
        coords="10.0,10.0",
        max_pages: int = 1
    ):
        """
        Fetch completed deal records from Yad2's latest-deals endpoint.

        Example request (Tel Aviv, Bavli)::

            https://gw.yad2.co.il/latest-deals-completed/?limit=8&page=1&sortBy=distance&order=asc&topArea=2&area=1&city=5000&neighborhood=484&coords=32.082830000000,34.791321000000

        Args:
            search_params: Yad2SearchParameters object with search criteria
            limit: Number of results per page.
            page: Result page to request (starting page when ``max_pages`` > 1).
            sort_by: Sorting field supported by the API (e.g. ``distance``).
            order: Sort order (``asc`` or ``desc``).
            city: Optional city identifier.
            neighborhood: Optional neighborhood identifier.
            coords: Latitude/longitude pair as string ``"lat,long"`` or tuple.
            max_pages: Number of pages to fetch. Set to ``None`` to exhaust all pages.

        Returns:
            List of :class:`RealEstateListing` objects.
        """
        try:
            url = f"{self.api_base_url}/latest-deals-completed/"
            params = {
                "limit": limit,
                "sortBy": sort_by,
                "order": order,
                "coords": coords,
            }

            active = self._get_active_params(search_params)

            def _choose(value, fallback_key):
                return value if value is not None else active.get(fallback_key)

            city_val = _choose(city, "city")
            hood_val = _choose(neighborhood, "neighborhood")

            if city_val is not None:
                params["city"] = city_val
            if hood_val is not None:
                params["neighborhood"] = hood_val

            coords_val = coords if coords is not None else active.get("coords")
            if isinstance(coords_val, (list, tuple)) and len(coords_val) == 2:
                coords_val = "{:.6f},{:.6f}".format(float(coords_val[0]), float(coords_val[1]))
            if coords_val:
                params["coords"] = coords_val

            collected_results = []
            pagination_info = {}
            page_to_fetch = max(page, 1)
            pages_fetched = 0

            while True:
                params["page"] = page_to_fetch
                logger.info(f"Fetching latest deals (page {page_to_fetch}): {params}")
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code != 200:
                    logger.warning("Failed to fetch latest deals (page {}): {}".format(
                        page_to_fetch, response.status_code))
                    break

                # Check if response is empty before parsing JSON
                if not response.text or not response.text.strip():
                    logger.warning("Empty response from latest deals API (page {})".format(page_to_fetch))
                    break

                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse JSON from latest deals API (page {}): {}. Response: {}".format(
                        page_to_fetch, e, response.text[:200]))
                    break

                data = data.get("data", [])
                page_results = data.get("results", [])
                pagination_info = data.get("pagination", {}) or {}

                if not page_results:
                    break

                converted = [self._convert_latest_deal_to_listing(entry) for entry in page_results]
                collected_results.extend(converted)

                pages_fetched += 1

                total_pages = pagination_info.get("totalPages")
                current_page = pagination_info.get("page", page_to_fetch)

                if max_pages is not None and pages_fetched >= max_pages:
                    break
                if total_pages is not None and current_page >= total_pages:
                    break

                page_to_fetch = current_page + 1

            return collected_results
        except Exception as e:
            logger.error("Error fetching latest deals: {}".format(e))
            return []

    @staticmethod
    def _extract_first_value(entry: dict, keys: list[str]) -> Optional[str]:
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

    def _prepare_location_parameters(self, location: Dict[str, Any]) -> Dict[str, object]:
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

        city_id = self._coerce_numeric(
            self._extract_first_value(selected_city, ["cityId", "id", "value"])
        )
        if city_id is not None:
            params["city"] = city_id

        top_area_id = self._coerce_numeric(
            self._extract_first_value(
                selected_city, ["topAreaId", "topArea", "regionId"]
            )
        )
        if top_area_id is None and top_areas:
            top_area_id = self._coerce_numeric(
                self._extract_first_value(top_areas[0], ["topAreaId", "id", "value", "code"])
            )
        if top_area_id is not None:
            params["topArea"] = top_area_id

        area_id = self._coerce_numeric(
            self._extract_first_value(selected_city, ["areaId", "area", "regionId"])
        )
        if area_id is None and areas:
            area_id = self._coerce_numeric(
                self._extract_first_value(areas[0], ["areaId", "id", "value"])
            )
        if area_id is not None:
            params["area"] = area_id

        if hoods:
            hood_entry = None
            if city_id is not None:
                for hood in hoods:
                    hood_city_id = self._coerce_numeric(
                        self._extract_first_value(hood, ["cityId", "cityID", "city"])
                    )
                    if hood_city_id is not None and hood_city_id == city_id:
                        hood_entry = hood
                        break
            hood_entry = hood_entry or hoods[0]
            hood_id = self._coerce_numeric(
                self._extract_first_value(
                    hood_entry, ["hoodId", "id", "value", "neighborhoodId"]
                )
            )
            if hood_id is not None:
                params["neighborhood"] = hood_id

        if streets:
            street_entry = None
            if city_id is not None:
                for street in streets:
                    street_city_id = self._coerce_numeric(
                        self._extract_first_value(street, ["cityId", "cityID", "city"])
                    )
                    if street_city_id is not None and street_city_id == city_id:
                        street_entry = street
                        break
            street_entry = street_entry or streets[0]

            street_id = self._extract_first_value(
                street_entry, ["streetId", "id", "value"]
            )
            if street_id:
                params["street"] = str(street_id)
            else:
                street_name = self._extract_first_value(
                    street_entry, ["name", "streetName", "text", "title"]
                )
                if street_name:
                    params["street"] = street_name

        return params

    def _convert_map_marker(
        self,
        marker: Dict[str, Any],
        listing_type: ListingType = ListingType.RENT,
        marker_type: str = "yad2",
        project_autocomplete_fetcher=None
    ) -> Optional[RealEstateListing]:
        """Convert a map marker response entry into a :class:`RealEstateListing`."""

        if not marker:
            return None

        try:
            listing = RealEstateListing()
            listing.listing_type = listing_type.value

            address = marker.get("address") or {}
            city = self._extract_nested_text(address, "city")
            neighborhood = self._extract_nested_text(address, "neighborhood")
            street = self._extract_nested_text(address, "street")

            house = address.get("house") or {}
            house_number = house.get("number")
            if house_number is not None:
                listing.floor = house.get("floor")
            elif house.get("floor") is not None:
                listing.floor = house.get("floor")

            parts = []
            if street:
                if house_number is not None:
                    parts.append(f"{street} {house_number}")
                else:
                    parts.append(street)
            if city:
                parts.append(city)

            listing.address = ", ".join([part for part in parts if part])
            if neighborhood:
                listing.meta["neighborhood"] = neighborhood
            if city:
                listing.meta["city"] = city
            if street:
                listing.meta["street"] = street

            coords = address.get("coords") or marker.get("coords")
            if isinstance(coords, dict):
                lon = coords.get("lon")
                lat = coords.get("lat")
            elif isinstance(coords, (list, tuple)) and len(coords) >= 2:
                lon, lat = coords[0], coords[1]
            else:
                lon = lat = None
            try:
                if lon is not None and lat is not None:
                    listing.coordinates = (float(lon), float(lat))
            except (TypeError, ValueError):
                listing.coordinates = None

            additional = marker.get("additionalDetails") or {}
            property_details = additional.get("property") or {}
            listing.property_type = property_details.get("text") or property_details.get("name") or marker.get("propertyType")
            listing.rooms = additional.get("roomsCount") or marker.get("rooms")
            listing.total_size = additional.get("squareMeter") or marker.get("size")

            metadata = marker.get("metaData") or {}
            if listing.size is None:
                listing.size = metadata.get("squareMeterBuild")

            cover_image = metadata.get("coverImage")
            if cover_image:
                listing.images.append(cover_image)
            for image in metadata.get("images") or []:
                if image and image not in listing.images:
                    listing.images.append(image)

            video = metadata.get("video")
            if video:
                listing.video = video

            price = marker.get("price")
            if price in (0, "0", 0.0):
                price = None
            listing.price = price

            # Extract previous price from priceBeforeTag if available
            price_before_tag = marker.get("priceBeforeTag")
            if price_before_tag:
                # priceBeforeTag might be a string like "₪2,500,000" or a number
                try:
                    if isinstance(price_before_tag, (int, float)):
                        listing.previous_price = price_before_tag
                    elif isinstance(price_before_tag, str):
                        # Clean the string: remove currency symbols, commas, spaces
                        cleaned = price_before_tag.replace("₪", "").replace(",", "").replace(" ", "").strip()
                        if cleaned:
                            listing.previous_price = int(cleaned)
                except (ValueError, TypeError):
                    # If parsing fails, store in meta for debugging
                    listing.meta["priceBeforeTag"] = price_before_tag

            token = marker.get("token")
            order_id = marker.get("orderId") or marker.get("listingId")
            base_url = "https://www.yad2.co.il"
            if token:
                listing.url = f"{base_url}/item/{token}"
                listing.listing_id = str(order_id or token)
            elif order_id is not None:
                listing.listing_id = str(order_id)
            else:
                listing.listing_id = None

            title_parts = []
            if listing.property_type:
                title_parts.append(listing.property_type)
            if listing.address:
                title_parts.append(listing.address)
            if not title_parts and listing.listing_id:
                title_parts.append(str(listing.listing_id))
            listing.title = " - ".join(title_parts) if title_parts else None

            tags = marker.get("tags") or []
            if tags:
                listing.features["tags"] = [tag.get("name") for tag in tags if tag.get("name")]

            customer = marker.get("customer") or {}
            has_agency = bool(customer.get("agencyName"))
            ad_type_raw = marker.get("adType")
            ad_type = ad_type_raw.lower() if isinstance(ad_type_raw, str) else None

            seller_type: Optional[str] = None
            if has_agency:
                seller_type = "broker"
            elif ad_type in {"private"}:
                seller_type = "private"
            elif ad_type in {"commercial", "agency", "broker"}:
                seller_type = "broker"
            elif ad_type:
                seller_type = ad_type

            if has_agency:
                listing.features["agency"] = {
                    "name": customer.get("agencyName"),
                    "logo": customer.get("agencyLogo"),
                }

            if seller_type:
                listing.features["seller_type"] = seller_type
                listing.meta["seller_type"] = seller_type

            video_url = metadata.get("video")
            if video_url:
                listing.meta["video"] = video_url

            listing.meta.update({
                "source": "yad2_map",
                "marker_type": marker_type,
                "token": token,
                "order_id": order_id,
                "ad_type": marker.get("adType"),
                "category_id": marker.get("categoryId"),
                "subcategory_id": marker.get("subcategoryId"),
                "customer": customer or None,
                "raw": marker,
            })

            if marker_type == "yad1":
                listing.meta["project_id"] = marker.get("projectId")
                project_name = (marker.get("metaData") or {}).get("projectName")
                project_entry = None
                if project_autocomplete_fetcher and project_name:
                    project_entry = project_autocomplete_fetcher(project_name)
                elif project_name:
                    project_entry = self.fetch_project_autocomplete(project_name)

                token = ''
                if isinstance(project_entry, dict):
                    token = project_entry.get("token")
                project_id = marker.get("projectId")
                listing.listing_id = token or project_id
                listing.url = f"{base_url}/yad1/project/{token}"

            return listing
        except Exception as exc:
            logger.debug("Failed to convert map marker: %s", exc)
            return None

    @staticmethod
    def _extract_nested_text(container: Dict[str, Any], key: str) -> Optional[str]:
        """Helper to safely extract nested 'text' values."""
        if not container:
            return None
        value = container.get(key)
        if isinstance(value, dict):
            return value.get("text") or value.get("name")
        if isinstance(value, str):
            return value
        return None

    def _convert_latest_deal_to_listing(self, deal_entry):
        """Convert a latest-deal payload entry into a RealEstateListing."""
        listing = RealEstateListing()
        
        address = deal_entry.get("address") or {}
        street = (address.get("street") or {}).get("text") or (address.get("street") or {}).get("name")
        house_number = address.get("houseNumber")
        neighborhood = (address.get("neighborhood") or {}).get("text")
        city = (address.get("city") or {}).get("text")

        street_line_parts = [part for part in [street, str(house_number) if house_number else None] if part]
        street_line = " ".join(street_line_parts) if street_line_parts else None

        address_parts = [part for part in [street_line, city] if part]
        listing.address = ", ".join(address_parts) if address_parts else None
        if neighborhood:
            listing.meta["neighborhood"] = neighborhood
        if city:
            listing.meta["city"] = city
        if street:
            listing.meta["street"] = street

        listing.property_type = deal_entry.get("propertyType")
        listing.title = listing.property_type or listing.address
        if listing.title and listing.address and listing.title != listing.address:
            listing.title = "{} - {}".format(listing.title, listing.address)
        elif listing.address:
            listing.title = listing.address

        listing.price = deal_entry.get("price")
        listing.rooms = deal_entry.get("rooms")
        listing.floor = deal_entry.get("floor")
        listing.size = deal_entry.get("buildingMR")
        # date_posted is not applicable for completed deals (these are historical sales, not posted listings)
        listing.date_posted = None
        listing.recent_deal = True

        # Preserve supporting data for downstream consumers.
        listing.meta.update({
            "source": "yad2_latest_deals",
            "sale_date": deal_entry.get("saleDate"),
            "number_of_floors": deal_entry.get("numberOfFloors"),
            "build_year": deal_entry.get("buildYear"),
            "address_master_id": address.get("addressMasterId"),
            "raw": deal_entry,
        })

        return listing

if __name__ == "__main__":
    client = Yad2APIClient()
    search_params = client.fetch_location_autocomplete("רמת החייל תל אביב")
    client.set_search_parameters(search_params)
    # listings = client.fetch_listings(search_params)
    # print(listings)
    latest_deals = client.fetch_latest_deals(search_params)
    print(latest_deals)