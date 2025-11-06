# -*- coding: utf-8 -*-
"""
Madlan Response Parser

Parses Madlan API responses and converts them to RealEstateListing objects.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from yad2.core.models import RealEstateListing

logger = logging.getLogger(__name__)


def parse_listing_response(response: Dict[str, Any]) -> List[RealEstateListing]:
    """
    Parse a Madlan searchPoiV2 response and convert to RealEstateListing objects.

    Args:
        response: The full API response dictionary containing searchPoiV2

    Returns:
        List of RealEstateListing objects
    """
    if not isinstance(response, dict):
        logger.warning(f"Invalid response type: {type(response)}")
        return []

    search_result = response.get("searchPoiV2", {})
    poi_list = search_result.get("poi", [])

    if not isinstance(poi_list, list):
        logger.warning(f"Invalid poi list type: {type(poi_list)}")
        return []

    listings = []
    for poi_item in poi_list:
        try:
            listing = parse_poi_to_listing(poi_item)
            if listing:
                listings.append(listing)
        except Exception as e:
            logger.error(f"Failed to parse POI item: {e}")
            continue

    return listings


def parse_poi_to_listing(poi_item: Dict[str, Any]) -> Optional[RealEstateListing]:
    """
    Parse a single POI item from Madlan API response to RealEstateListing.

    Args:
        poi_item: A POI item from the searchPoiV2 response (contains 'poi' key)

    Returns:
        RealEstateListing object or None if parsing fails
    """
    if not isinstance(poi_item, dict):
        return None

    # Extract the actual POI data
    poi = poi_item.get("poi", poi_item)

    if not isinstance(poi, dict):
        return None

    try:
        listing = RealEstateListing()
        listing.listing_id = poi.get("id")
        listing.meta["source"] = "madlan"
        listing.meta["madlan_raw"] = poi

        # Extract address details
        address_details = poi.get("addressDetails", {})
        address = poi.get("address")
        if not address and address_details:
            # Build address from addressDetails
            parts = []
            street_name = address_details.get("streetName")
            street_number = address_details.get("streetNumber")
            if street_name:
                if street_number:
                    parts.append(f"{street_name} {street_number}")
                else:
                    parts.append(street_name)
            city = address_details.get("city")
            if city:
                parts.append(city)
            address = ", ".join(parts)

        listing.address = address

        # Store address details in meta
        if address_details:
            listing.meta["address_details"] = {
                "docId": address_details.get("docId"),
                "city": address_details.get("city"),
                "streetName": address_details.get("streetName"),
                "streetNumber": address_details.get("streetNumber"),
                "neighbourhood": address_details.get("neighbourhood"),
                "neighbourhoodDocId": address_details.get("neighbourhoodDocId"),
                "cityDocId": address_details.get("cityDocId"),
                "district": address_details.get("district"),
            }

        # Extract coordinates
        location_point = poi.get("locationPoint", {})
        if location_point:
            lat = location_point.get("lat")
            lng = location_point.get("lng")
            if lat is not None and lng is not None:
                listing.coordinates = {"lat": lat, "lng": lng}

        # Extract basic property details based on POI type
        poi_type = poi.get("type", "").lower()

        if poi_type == "bulletin":
            _parse_bulletin(poi, listing)
        elif poi_type == "project":
            _parse_project(poi, listing)
        elif poi_type == "commercialbulletin":
            _parse_commercial_bulletin(poi, listing)
        else:
            # Generic parsing for unknown types
            _parse_generic(poi, listing)

        # Extract listing type from dealType
        deal_type = poi.get("dealType", "")
        if deal_type == "unitBuy":
            listing.listing_type = "buy"
        elif deal_type == "unitRent":
            listing.listing_type = "rent"
        else:
            listing.listing_type = deal_type or "buy"

        # Extract date posted
        last_updated = poi.get("lastUpdated")
        if last_updated:
            listing.date_posted = last_updated
            # Try to parse the date string
            try:
                # Parse format like "Wed Oct 22 07:09:30 GMT 2025"
                if isinstance(last_updated, str):
                    listing.date_posted = last_updated
            except Exception:
                pass

        first_time_seen = poi.get("firstTimeSeen")
        if first_time_seen and not listing.date_posted:
            listing.date_posted = first_time_seen

        # Extract URL
        url = poi.get("url")
        if url:
            if not url.startswith("http"):
                url = f"https://www.madlan.co.il{url}"
            listing.url = url

        # Extract images
        images = poi.get("images", [])
        if isinstance(images, list):
            image_urls = []
            for img in images:
                if isinstance(img, dict):
                    image_url = img.get("imageUrl") or img.get("path")
                    if image_url:
                        if not image_url.startswith("http"):
                            image_url = f"https://www.madlan.co.il{image_url}"
                        image_urls.append(image_url)
                elif isinstance(img, str):
                    if not img.startswith("http"):
                        img = f"https://www.madlan.co.il{img}"
                    image_urls.append(img)
            listing.images = image_urls

        # Extract virtual tours
        virtual_tours = poi.get("virtualTours")
        if virtual_tours:
            listing.meta["virtual_tours"] = virtual_tours

        # Extract contact information
        poc = poi.get("poc", {})
        if poc and poc.get("type") == "agent":
            contact_info = {
                "type": "agent",
                "officeId": poc.get("officeId"),
            }
            office_contact = poc.get("officeContact", {})
            if office_contact:
                image_url = office_contact.get("imageUrl")
                if image_url:
                    if not image_url.startswith("http"):
                        image_url = f"https://www.madlan.co.il{image_url}"
                    contact_info["imageUrl"] = image_url

            exclusivity = poc.get("exclusivity", {})
            if exclusivity:
                contact_info["exclusive"] = exclusivity.get("exclusive")

            listing.contact_info = contact_info

        # Extract tags and insights
        tags = poi.get("tags", {})
        if tags:
            listing.meta["tags"] = tags

        insights = poi.get("insights", {})
        if insights:
            listing.meta["insights"] = insights

        # Extract events history
        events_history = poi.get("eventsHistory", [])
        if events_history:
            listing.meta["events_history"] = events_history

        # Extract status
        status = poi.get("status", {})
        if status:
            listing.meta["status"] = status
            listing.meta["promoted"] = status.get("promoted", False)

        return listing

    except Exception as e:
        logger.error(f"Error parsing POI to listing: {e}")
        return None


def _parse_bulletin(poi: Dict[str, Any], listing: RealEstateListing) -> None:
    """Parse a Bulletin type POI."""
    listing.price = poi.get("price")
    listing.rooms = poi.get("beds")  # Madlan uses "beds" for rooms
    listing.floor = poi.get("floor")
    listing.size = poi.get("area")  # Madlan uses "area" for size

    # Store additional fields in meta
    listing.meta["baths"] = poi.get("baths")
    listing.meta["buildingYear"] = poi.get("buildingYear")
    listing.meta["generalCondition"] = poi.get("generalCondition")
    listing.meta["buildingClass"] = poi.get("buildingClass")
    listing.meta["rentalBrokerFee"] = poi.get("rentalBrokerFee")
    listing.meta["matchScore"] = poi.get("matchScore")

    # Extract investors data
    investors_data = poi.get("investorsData", {})
    if investors_data:
        listing.meta["investorsData"] = investors_data

    # Extract commute/walk times
    listing.meta["commuteTime"] = poi.get("commuteTime")
    listing.meta["dogsParkWalkTime"] = poi.get("dogsParkWalkTime")
    listing.meta["parkWalkTime"] = poi.get("parkWalkTime")

    promoted_until = poi.get("promotedUntil")
    if promoted_until:
        listing.meta["promotedUntil"] = promoted_until

    # Create title from address and rooms
    if listing.address and listing.rooms:
        listing.title = f"{listing.rooms} חדרים, {listing.address}"
    elif listing.address:
        listing.title = listing.address


def _parse_project(poi: Dict[str, Any], listing: RealEstateListing) -> None:
    """Parse a Project type POI."""
    project_name = poi.get("projectName")
    listing.title = project_name or listing.address

    # Extract apartment type info (can be a list or dict)
    apartment_type = poi.get("apartmentType", {})
    if apartment_type:
        if isinstance(apartment_type, list) and len(apartment_type) > 0:
            # Use the first apartment type if it's a list
            apartment_type = apartment_type[0]
        
        if isinstance(apartment_type, dict):
            listing.rooms = apartment_type.get("beds")
            listing.size = apartment_type.get("size")
            listing.price = apartment_type.get("price")
            listing.meta["apartmentSpecification"] = apartment_type.get("apartmentSpecification")
            listing.meta["apartmentType"] = apartment_type.get("type")
        
        # Store full apartment type data
        listing.meta["apartmentTypes"] = poi.get("apartmentType")

    # Extract price and beds ranges
    beds_range = poi.get("bedsRange", {})
    if beds_range:
        listing.meta["bedsRange"] = beds_range

    price_range = poi.get("priceRange", {})
    if price_range:
        listing.meta["priceRange"] = price_range
        if not listing.price and price_range.get("min"):
            listing.price = price_range.get("min")

    # Store project-specific fields
    listing.meta["projectName"] = project_name
    listing.meta["projectLogo"] = poi.get("projectLogo")
    listing.meta["dealType"] = poi.get("dealType")
    listing.meta["isCommercial"] = poi.get("isCommercial", False)
    listing.meta["isFundedByBankHapoalim"] = poi.get("isFundedByBankHapoalim", False)
    listing.meta["buildingStage"] = poi.get("buildingStage")
    listing.meta["phoneNumber"] = poi.get("phoneNumber")

    # Extract block details
    block_details = poi.get("blockDetails", {})
    if block_details:
        listing.meta["blockDetails"] = block_details

    # Extract developers
    developers = poi.get("developers", [])
    if developers:
        listing.meta["developers"] = developers

    # Extract discount/promo info
    discount = poi.get("discount", {})
    if discount:
        listing.meta["discount"] = discount

    promo_info = poi.get("promoInfo", {})
    if promo_info:
        listing.meta["promoInfo"] = promo_info

    # Extract project messages
    project_messages = poi.get("projectMessages", {})
    if project_messages:
        listing.description = project_messages.get("listingDescription")
        listing.meta["projectMessages"] = project_messages

    # Extract preview image
    preview_image = poi.get("previewImage", {})
    if preview_image:
        preview_path = preview_image.get("path")
        if preview_path:
            if not preview_path.startswith("http"):
                preview_path = f"https://www.madlan.co.il{preview_path}"
            if not listing.images:
                listing.images = []
            listing.images.insert(0, preview_path)


def _parse_commercial_bulletin(poi: Dict[str, Any], listing: RealEstateListing) -> None:
    """Parse a CommercialBulletin type POI."""
    listing.price = poi.get("price")
    listing.rooms = poi.get("rooms")
    listing.size = poi.get("area")
    listing.floor = poi.get("floor")

    # Store additional commercial fields
    listing.meta["commercial"] = True
    listing.meta["buildingYear"] = poi.get("buildingYear")
    listing.meta["generalCondition"] = poi.get("generalCondition")
    listing.meta["buildingClass"] = poi.get("buildingClass")
    listing.meta["monthlyTaxes"] = poi.get("monthlyTaxes")
    listing.meta["ppm"] = poi.get("ppm")  # Price per square meter
    listing.meta["rentalBrokerFee"] = poi.get("rentalBrokerFee")
    listing.meta["qualityClass"] = poi.get("qualityClass")
    listing.meta["qualityBin"] = poi.get("qualityBin")
    listing.meta["buildingType"] = poi.get("buildingType")
    listing.meta["availabilityType"] = poi.get("availabilityType")
    listing.meta["availableDate"] = poi.get("availableDate")
    listing.meta["balconyArea"] = poi.get("balconyArea")
    listing.meta["floors"] = poi.get("floors")
    listing.meta["numberOfEmployees"] = poi.get("numberOfEmployees")
    listing.meta["leaseTerm"] = poi.get("leaseTerm")
    listing.meta["leaseType"] = poi.get("leaseType")
    listing.meta["feeType"] = poi.get("feeType")
    listing.meta["furnitureDetails"] = poi.get("furnitureDetails")
    listing.meta["matchScore"] = poi.get("matchScore")
    listing.meta["newListing"] = poi.get("newListing", False)
    listing.meta["originalId"] = poi.get("originalId")
    listing.meta["source"] = poi.get("source")

    # Extract amenities
    amenities = poi.get("amenities", {})
    if amenities:
        listing.meta["amenities"] = amenities
        listing.features = amenities

    # Create title
    if listing.address and listing.size:
        listing.title = f"{listing.size} מ\"ר, {listing.address}"
    elif listing.address:
        listing.title = listing.address


def _parse_generic(poi: Dict[str, Any], listing: RealEstateListing) -> None:
    """Generic parsing for unknown POI types."""
    listing.price = poi.get("price")
    listing.rooms = poi.get("beds") or poi.get("rooms")
    listing.size = poi.get("area") or poi.get("size")
    listing.floor = poi.get("floor")
    listing.address = poi.get("address") or listing.address

    # Create basic title
    if listing.address:
        listing.title = listing.address
    elif poi.get("id"):
        listing.title = f"Listing {poi.get('id')}"

