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
            - deal_type: "unitBuy" or "unitRent" (default: "unitBuy")
            - price_range: [min, max] price range
            - rooms_range: [min, max] number of rooms range
            - limit: Maximum number of results (default: 50)
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
            # Get deal_type from kwargs or default to unitBuy
            deal_type_str = kwargs.get("deal_type", "unitBuy")
            deal_type = DealType.UNIT_BUY if deal_type_str == "unitBuy" else DealType.UNIT_RENT
            
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
            
            # Fetch listings
            fetched_listings = self.client.fetch_listings(
                location_doc_id=location_doc_id,
                deal_type=deal_type,
                price_range=price_range,
                rooms_range=rooms_range,
                area_range=area_range,
                floor_range=floor_range,
                limit=limit,
            )
            
            listings.extend(fetched_listings)
            
        except Exception as e:
            logger.error(f"Madlan collection failed: {e}")

        return listings

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for Madlan collection."""
        location = kwargs.get("location")
        return isinstance(location, LocationQuery) and not location.is_empty()

