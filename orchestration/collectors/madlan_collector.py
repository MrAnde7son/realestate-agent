"""Madlan data collector implementation."""
import logging

from typing import List, Optional

from madlan.api_client import MadlanAPIClient, DealType
from yad2.core.models import RealEstateListing

from orchestration.location import LocationQuery, ensure_location_query

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class MadlanCollector(BaseCollector):
    """Wrapper around :class:`MadlanAPIClient` implementing a simple interface."""

    def __init__(self, client: Optional[MadlanAPIClient] = None) -> None:
        self.client = client or MadlanAPIClient()

    def collect(
        self,
        location: Optional[LocationQuery] = None,
        **kwargs
    ) -> List[RealEstateListing]:
        """Collect Madlan listings for a given location.

        Parameters
        ----------
        location: Optional[LocationQuery]
            Structured location information. When ``None`` an empty query is
            assumed.
        **kwargs
            Additional parameters:
            - deal_type: "unitBuy", "unitRent", or "both" (default: "both" to fetch both types)
            - price_range: [min, max] price range
            - rooms_range: [min, max] number of rooms range
            - limit: Maximum number of results per deal type (default: 50)
        """
        query = ensure_location_query(location)
        
        # Build address string from location query
        address_parts = []
        if query.street:
            address_parts.append(query.street)
        if query.house_number:
            address_parts.append(str(query.house_number))
        if query.city:
            address_parts.append(query.city)
        
        address = " ".join(address_parts)
        
        if not address:
            return []

        listings = []
        try:
            # Get deal_type from kwargs - default to "both" to fetch both types
            deal_type_str = kwargs.get("deal_type", "both")
            
            # Determine which deal types to fetch
            if deal_type_str == "both":
                deal_types = [DealType.UNIT_BUY, DealType.UNIT_RENT]
            elif deal_type_str == "unitRent":
                deal_types = [DealType.UNIT_RENT]
            else:  # default to unitBuy
                deal_types = [DealType.UNIT_BUY]
            
            # Search for addresses matching the location
            addresses = self.client.get_addresses(address)
            
            if not addresses:
                logger.warning(f"No addresses found for: {address}")
                return []
            
            # Use the first matching address's docId
            first_address = addresses[0]
            location_doc_id = first_address.get("docId")
            
            if not location_doc_id:
                logger.warning(f"No docId found for address: {address}")
                return []
            
            # Extract search parameters from kwargs
            price_range = kwargs.get("price_range")
            rooms_range = kwargs.get("rooms_range")
            area_range = kwargs.get("area_range")
            floor_range = kwargs.get("floor_range")
            limit = kwargs.get("limit", 50)
            
            # Fetch all listings for each deal type with pagination
            for deal_type in deal_types:
                try:
                    all_fetched_listings = []
                    offset = 0
                    page = 0
                    
                    # Paginate through all results
                    while True:
                        page += 1
                        page_listings = self.client.fetch_listings(
                            location_doc_id=location_doc_id,
                            deal_type=deal_type,
                            price_range=price_range,
                            rooms_range=rooms_range,
                            area_range=area_range,
                            floor_range=floor_range,
                            limit=limit,
                            offset=offset,
                        )
                        
                        if not page_listings:
                            # No more results
                            break
                        
                        all_fetched_listings.extend(page_listings)
                        logger.info(f"Fetched page {page} for {deal_type.value}: {len(page_listings)} listings (total so far: {len(all_fetched_listings)})")
                        
                        # If we got fewer results than the limit, we've reached the end
                        if len(page_listings) < limit:
                            break
                        
                        # Update offset for next page
                        offset += limit
                    
                    listings.extend(all_fetched_listings)
                    logger.info(f"Fetched {len(all_fetched_listings)} total {deal_type.value} listings across {page} page(s)")
                except Exception as e:
                    logger.error(f"Failed to fetch {deal_type.value} listings: {e}")
                    # Continue with other deal types even if one fails
            
        except Exception as e:
            logger.error(f"Madlan collection failed: {e}")

        return listings

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for Madlan collection."""
        location = kwargs.get("location")
        return isinstance(location, LocationQuery) and not location.is_empty()

