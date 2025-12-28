# -*- coding: utf-8 -*-
"""
Madlan API Client - GraphQL API client for madlan.co.il

This client provides methods to interact with the Madlan GraphQL API,
including address autocomplete and property listing retrieval.
"""

from enum import Enum
import logging
import re
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from madlan.parser import parse_poi_to_listing
from yad2.core.models import RealEstateListing

logger = logging.getLogger(__name__)

# Default API endpoint
DEFAULT_API_URL = "https://www.madlan.co.il/api2"


class DealType(Enum):
    UNIT_BUY = "unitBuy"
    UNIT_RENT = "unitRent"


# Default completion types for address autocomplete
DEFAULT_COMPLETION_TYPES = [
    "neighbourhood",
    "street",
    "address",
    "city",
    "project",
    "commercialProject",
    "schoolDoc",
    "developer",
    "agent",
    "office",
    "customZone",
    "country",
]

# GraphQL query for getAddresses
GET_ADDRESSES_QUERY = """
query getAddresses($text: String!, $completionTypes: [String]) {
  addresses(text: $text, completionTypes: $completionTypes) {
    id
    docId
    identityDocId
    name
    type
    location
    reference
    hierarchyLevel {
      docId
      __typename
    }
    ... on address {
      unitsTotal
      constructionYear
      floorCount
      street
      houseNumber
      city
      relevantDocIds {
        docId
        type
        text
        __typename
      }
      __typename
    }
    ... on neighbourhood {
      neighbourhood
      __typename
    }
    ... on borough {
      borough
      __typename
    }
    ... on street {
      street
      __typename
    }
    ... on office {
      url
      __typename
    }
    ... on agent {
      url
      __typename
    }
    ... on developer {
      url
      __typename
    }
    ... on schoolDoc {
      url
      schoolName
      __typename
    }
    ... on county {
      county
      __typename
    }
    ... on city {
      city
      __typename
    }
    __typename
  }
}
"""

# GraphQL query for searchPoi (listings search)
SEARCH_POI_QUERY = """
query searchPoi($dealType: String, $userContext: JSONObject, $abtests: JSONObject, $noFee: Boolean, $adPlacement: AdPlacement, $priceRange: [Int], $ppmRange: [Int], $monthlyTaxRange: [Int], $roomsRange: [Float], $bathsRange: [Float], $buildingClass: [String], $amenities: inputAmenitiesFilter, $generalCondition: [GeneralCondition], $sellerType: [SellerType], $floorRange: [Int], $areaRange: [Int], $tileRanges: [TileRange], $tileRangesExcl: [TileRange], $sort: [SortField], $limit: Int, $offset: Int, $cursor: inputCursor, $poiTypes: [PoiType], $locationDocId: String, $searchContext: SearchContext, $underPriceEstimation: Boolean, $discountedProjects: Boolean, $priceDrop: Boolean, $isCommercialRealEstate: Boolean, $commercialAmenities: inputCommercialAmenitiesFilter, $qualityClass: [String], $numberOfEmployeesRange: [Float], $creationDaysRange: Int, $onlyImmediate: Boolean) {
  searchPoiV2(noFee: $noFee, adPlacement: $adPlacement, dealType: $dealType, userContext: $userContext, abtests: $abtests, priceRange: $priceRange, ppmRange: $ppmRange, monthlyTaxRange: $monthlyTaxRange, roomsRange: $roomsRange, bathsRange: $bathsRange, buildingClass: $buildingClass, sellerType: $sellerType, floorRange: $floorRange, areaRange: $areaRange, generalCondition: $generalCondition, amenities: $amenities, tileRanges: $tileRanges, tileRangesExcl: $tileRangesExcl, sort: $sort, limit: $limit, offset: $offset, cursor: $cursor, poiTypes: $poiTypes, locationDocId: $locationDocId, discountedProjects: $discountedProjects, searchContext: $searchContext, underPriceEstimation: $underPriceEstimation, priceDrop: $priceDrop, isCommercialRealEstate: $isCommercialRealEstate, commercialAmenities: $commercialAmenities, qualityClass: $qualityClass, numberOfEmployeesRange: $numberOfEmployeesRange, creationDaysRange: $creationDaysRange, onlyImmediate: $onlyImmediate) {
    total
    cursor {
      bulletinsOffset
      projectsOffset
      seenProjects
      __typename
    }
    totalNearby
    lastInGeometryId
    cursor {
      bulletinsOffset
      projectsOffset
      __typename
    }
    ...PoiFragment
    __typename
  }
}

fragment PoiFragment on PoiSearchResult {
  poi {
    ...PoiInner
    ... on Bulletin {
      rentalBrokerFee
      investorsData {
        yield
        approximateRent
        updatedAt
        __typename
      }
      eventsHistory {
        eventType
        price
        date
        __typename
      }
      insights {
        insights {
          category
          tradeoff {
            insightPlace
            value
            tagLine
            impactful
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment PoiInner on Poi {
  id
  locationPoint {
    lat
    lng
    __typename
  }
  type
  firstTimeSeen
  addressDetails {
    docId
    city
    borough
    zipcode
    streetName
    neighbourhood
    neighbourhoodDocId
    cityDocId
    resolutionPreferences
    streetNumber
    unitNumber
    district
    __typename
  }
  ... on Project {
    discount {
      showDiscount
      description
      bannerUrl
      __typename
    }
    promoInfo {
      isVisible
      description
      bannerUrl
      __typename
    }
    isFundedByBankHapoalim
    dealType
    phoneNumber
    apartmentType {
      size
      beds
      apartmentSpecification
      type
      price
      __typename
    }
    bedsRange {
      min
      max
      __typename
    }
    priceRange {
      min
      max
      __typename
    }
    images {
      path
      __typename
    }
    promotionStatus {
      status
      __typename
    }
    projectName
    projectLogo
    isCommercial
    projectMessages {
      listingDescription
      __typename
    }
    previewImage {
      path
      __typename
    }
    developers {
      id
      logoPath
      __typename
    }
    tags {
      bestSchool
      bestSecular
      bestReligious
      safety
      parkAccess
      quietStreet
      dogPark
      familyFriendly
      lightRail
      commute
      __typename
    }
    buildingStage
    blockDetails {
      buildingsNum
      floorRange {
        min
        max
        __typename
      }
      units
      mishtakenPrice
      urbanRenewal
      __typename
    }
    __typename
  }
  ... on CommercialBulletin {
    address
    agentId
    qualityClass
    amenities {
      accessible
      airConditioner
      alarm
      conferenceRoom
      doorman
      elevator
      fullTimeAccess
      kitchenette
      outerSpace
      parkingBikes
      parkingEmployee
      parkingVisitors
      reception
      secureRoom
      storage
      subDivisible
      __typename
    }
    area
    availabilityType
    availableDate
    balconyArea
    buildingClass
    buildingType
    buildingYear
    currency
    dealType
    description
    estimatedPrice
    lastUpdated
    eventsHistory {
      eventType
      price
      date
      __typename
    }
    feeType
    floor
    floors
    fromDateTime
    furnitureDetails
    generalCondition
    images {
      ...ImageItem
      __typename
    }
    lastActiveMarkDate
    leaseTerm
    leaseType
    matchScore
    monthlyTaxes
    newListing
    numberOfEmployees
    originalId
    poc {
      type
      ... on BulletinAgent {
        madadSearchResult
        officeId
        officeContact {
          imageUrl
          __typename
        }
        exclusivity {
          exclusive
          __typename
        }
        __typename
      }
      __typename
    }
    ppm
    price
    qualityBin
    rentalBrokerFee
    rooms
    source
    status {
      promoted
      __typename
    }
    url
    virtualTours
    __typename
  }
  ... on Bulletin {
    dealType
    address
    matchScore
    beds
    floor
    baths
    buildingYear
    area
    price
    virtualTours
    rentalBrokerFee
    generalCondition
    lastUpdated
    promotedUntil
    investorsData {
      approximateRent
      updatedAt
      yield
      __typename
    }
    eventsHistory {
      eventType
      price
      date
      __typename
    }
    status {
      promoted
      __typename
    }
    poc {
      type
      ... on BulletinAgent {
        madadSearchResult
        officeId
        officeContact {
          imageUrl
          __typename
        }
        exclusivity {
          exclusive
          __typename
        }
        __typename
      }
      __typename
    }
    tags {
      bestSchool
      bestSecular
      bestReligious
      safety
      parkAccess
      quietStreet
      dogPark
      familyFriendly
      lightRail
      commute
      __typename
    }
    commuteTime
    dogsParkWalkTime
    parkWalkTime
    buildingClass
    images {
      ...ImageItem
      __typename
    }
    __typename
  }
  ... on Ad {
    addressDetails {
      docId
      city
      borough
      zipcode
      streetName
      neighbourhood
      neighbourhoodDocId
      resolutionPreferences
      streetNumber
      unitNumber
      __typename
    }
    city
    district
    firstTimeSeen
    id
    locationPoint {
      lat
      lng
      __typename
    }
    neighbourhood
    type
    __typename
  }
  __typename
}

fragment ImageItem on ImageItem {
  description
  imageUrl
  isFloorplan
  rotation
  __typename
}
"""


class MadlanAPIError(Exception):
    """Base exception for Madlan API errors."""

    pass


class MadlanAPIClient:
    """
    GraphQL API client for madlan.co.il.

    This client provides methods to interact with the Madlan GraphQL API
    for address autocomplete and property data retrieval.
    """

    def __init__(
        self,
        api_url: str = DEFAULT_API_URL,
        session: Optional[requests.Session] = None,
        timeout: int = 30,
        user_token: Optional[str] = None,
        auto_fetch_token: bool = True,
    ):
        """
        Initialize the Madlan API client.

        Args:
            api_url: Base URL for the Madlan GraphQL API
            session: Optional requests session for maintaining cookies and state
            timeout: Request timeout in seconds
            user_token: Optional user token (JWT). If not provided and auto_fetch_token is True,
                       will attempt to fetch from the homepage
            auto_fetch_token: If True, automatically fetch token from homepage if not provided
        """
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.session = session or self._create_session()
        self.user_token: Optional[str] = user_token
        self._token_fetched = False

        if auto_fetch_token and not self.user_token:
            try:
                self.user_token = self._fetch_user_token()
            except Exception as e:
                logger.warning(f"Failed to fetch user token automatically: {e}")

    def _create_session(self) -> requests.Session:
        """Create a configured requests session with retry strategy."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update(
            {
                "Accept": "application/json",
                "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            }
        )

        return session

    def _fetch_user_token(self) -> Optional[str]:
        """
        Fetch user token from Madlan by visiting the homepage.

        The token is stored in cookies as USER_TOKEN_V2. This method visits
        the homepage with browser-like cookies and headers to trigger token
        generation, similar to how a browser would receive the token.

        Returns:
            User token (JWT) or None if not found

        Raises:
            MadlanAPIError: If fetching fails
        """
        # Desktop user-agent matching the request
        desktop_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"

        # Headers matching the browser request
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": desktop_user_agent,
            "Sec-Ch-Ua": '"Chromium";v="141", "Not?A_Brand";v="8"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Upgrade-Insecure-Requests": "1",
            "Priority": "u=0, i",
            "Connection": "keep-alive",
        }

        # First, check if token already exists in session cookies
        if hasattr(self.session, "cookies") and self.session.cookies.get(
            "USER_TOKEN_V2"
        ):
            token = self.session.cookies.get("USER_TOKEN_V2").value
            if token and len(token) > 50 and token.count(".") == 2:
                logger.info("User token already exists in session cookies")
                return token

        # Set initial cookies that help trigger token generation
        # These cookies help establish a session similar to a browser
        initial_cookies = {
            "_gcl_au": "1.1.1199690251.1762098874",
            "_hjSessionUser_1261107": "eyJpZCI6ImI2MjIzMGJkLWE1ODctNWMxMy05MzQyLWZlNDZmNDY3MDBjOSIsImNyZWF0ZWQiOjE3NjIwOTg4NzQzMjQsImV4aXN0aW5nIjpmYWxzZX0=",
            "_tt_enable_cookie": "1",
            "_ttp": "01K92ME544MMQHAG747T4X2BHX_.tt.2",
        }

        # Set cookies in session (don't overwrite existing cookies)
        for cookie_name, cookie_value in initial_cookies.items():
            if not self.session.cookies.get(cookie_name):
                self.session.cookies.set(
                    cookie_name, cookie_value, domain=".madlan.co.il"
                )

        try:
            response = self.session.get(
                "https://www.madlan.co.il/",
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch homepage for token: {e}")
            raise MadlanAPIError(f"Failed to fetch user token: {e}")

        # Check session cookies after request (server may have set it)
        if hasattr(self.session, "cookies") and self.session.cookies.get(
            "USER_TOKEN_V2"
        ):
            token = self.session.cookies.get("USER_TOKEN_V2").value
            if token and len(token) > 50 and token.count(".") == 2:
                logger.info("Successfully extracted user token from session cookies")
                return token

        # Check response cookies
        cookies = response.cookies
        if cookies.get("USER_TOKEN_V2"):
            token = (
                cookies.get("USER_TOKEN_V2").value
                if hasattr(cookies.get("USER_TOKEN_V2"), "value")
                else str(cookies.get("USER_TOKEN_V2"))
            )
            if token and len(token) > 50 and token.count(".") == 2:
                logger.info("Successfully extracted user token from response cookies")
                # Store in session for future requests
                self.session.cookies.set("USER_TOKEN_V2", token, domain=".madlan.co.il")
                return token

        # Check Set-Cookie headers
        set_cookie_headers = response.headers.get("Set-Cookie", "")
        if isinstance(set_cookie_headers, list):
            set_cookie_headers = "; ".join(set_cookie_headers)

        if "USER_TOKEN_V2=" in set_cookie_headers:
            # Extract token from Set-Cookie header
            match = re.search(r"USER_TOKEN_V2=([^;]+)", set_cookie_headers)
            if match:
                token = match.group(1)
                if token and len(token) > 50 and token.count(".") == 2:
                    logger.info(
                        "Successfully extracted user token from Set-Cookie header"
                    )
                    # Store in session for future requests
                    self.session.cookies.set(
                        "USER_TOKEN_V2", token, domain=".madlan.co.il"
                    )
                    return token

        # Fallback: Check HTML content for userToken
        html_content = response.text

        # Try multiple patterns for finding the token in HTML
        patterns = [
            r'"userToken"\s*:\s*"([^"]+)"',  # "userToken": "..."
            r'userToken["\']?\s*[:=]\s*["\']([^"\']+)',  # userToken: "..." or userToken="..."
            r'USER_TOKEN_V2["\']?\s*[:=]\s*["\']([^"\']+)',  # USER_TOKEN_V2: "..." or USER_TOKEN_V2="..."
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for token in matches:
                if (
                    len(token) > 50
                    and token.count(".") == 2
                    and token.startswith("eyJ")
                ):
                    logger.info("Successfully extracted user token from HTML content")
                    # Store in session for future requests
                    self.session.cookies.set(
                        "USER_TOKEN_V2", token, domain=".madlan.co.il"
                    )
                    return token

        logger.warning(
            "Could not find userToken in cookies or HTML. "
            "The token is typically set by JavaScript after page load. "
            "You may need to extract it manually from your browser's cookies "
            "(USER_TOKEN_V2) or use a headless browser."
        )
        return None

    def set_user_token(self, token: str) -> None:
        """
        Set the user token manually.

        Args:
            token: User token (JWT) to use for authentication
        """
        self.user_token = token
        self._token_fetched = True

    def _make_graphql_request(
        self,
        operation_name: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a GraphQL request to the Madlan API.

        Args:
            operation_name: Name of the GraphQL operation
            query: GraphQL query string
            variables: Variables for the GraphQL query

        Returns:
            Response JSON data

        Raises:
            MadlanAPIError: If the request fails
        """
        # Ensure we have a token
        if not self.user_token and not self._token_fetched:
            try:
                self.user_token = self._fetch_user_token()
            except Exception as e:
                logger.warning(f"Could not fetch token before request: {e}")

        payload = {
            "operationName": operation_name,
            "query": query,
        }

        if variables:
            payload["variables"] = variables

        # Prepare headers with token if available
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-Source": "web",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
            "Referer": "https://www.madlan.co.il/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/json",
            "Origin": "https://www.madlan.co.il",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        if self.user_token:
            headers["Authorization"] = f"Bearer {self.user_token}"

        try:
            response = self.session.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                raise MadlanAPIError(
                    f"Madlan API request failed with status {response.status_code}: {response.text}"
                )

            data = response.json()

            # Check for GraphQL errors
            if "errors" in data:
                error_messages = [
                    err.get("message", "Unknown error") for err in data["errors"]
                ]
                raise MadlanAPIError(f"GraphQL errors: {'; '.join(error_messages)}")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Madlan API request failed: {e}")
            raise MadlanAPIError(f"Request failed: {e}")

    def get_addresses(
        self,
        text: str,
        completion_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Autocomplete addresses and get address details.

        This method searches for addresses matching the provided text and returns
        detailed address information including location, hierarchy, and relevant
        document IDs.

        Args:
            text: Search text for address autocomplete (e.g., "רוזוב 14 תל")
            completion_types: Optional list of completion types to search.
                             Defaults to all available types if not provided.

        Returns:
            List of address dictionaries, each containing:
            - id: Address identifier
            - docId: Document ID
            - identityDocId: Identity document ID
            - name: Display name
            - type: Address type (address, street, city, etc.)
            - location: [longitude, latitude] coordinates
            - reference: Reference information
            - hierarchyLevel: List of hierarchy levels
            - Additional fields depend on the address type

        Raises:
            MadlanAPIError: If the request fails

        Example:
            >>> client = MadlanAPIClient()
            >>> addresses = client.get_addresses("רוזוב 14 תל")
            >>> for addr in addresses:
            ...     print(f"{addr['name']} at {addr['location']}")
        """
        if completion_types is None:
            completion_types = DEFAULT_COMPLETION_TYPES

        variables = {
            "text": text,
            "completionTypes": completion_types,
        }

        try:
            response = self._make_graphql_request(
                operation_name="getAddresses",
                query=GET_ADDRESSES_QUERY,
                variables=variables,
            )

            # Extract addresses from response
            data = response.get("data", {})
            addresses = data.get("addresses", [])

            logger.info(f"Found {len(addresses)} addresses for query: {text}")
            return addresses

        except MadlanAPIError:
            raise
        except Exception as e:
            logger.error(f"Failed to get addresses for '{text}': {e}")
            raise MadlanAPIError(f"Failed to get addresses: {e}")

    def fetch_listings(
        self,
        location_doc_id: Optional[str] = None,
        deal_type: DealType = DealType.UNIT_BUY,
        tile_ranges: Optional[List[Dict[str, int]]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        price_range: Optional[List[Optional[int]]] = None,
        rooms_range: Optional[List[Optional[float]]] = None,
        area_range: Optional[List[Optional[int]]] = None,
        floor_range: Optional[List[Optional[int]]] = None,
        baths_range: Optional[List[Optional[float]]] = None,
        building_class: Optional[List[str]] = None,
        general_condition: Optional[List[str]] = None,
        seller_type: Optional[List[str]] = None,
        amenities: Optional[Dict[str, Any]] = None,
        commercial_amenities: Optional[Dict[str, Any]] = None,
        quality_class: Optional[List[str]] = None,
        ppm_range: Optional[List[Optional[int]]] = None,
        monthly_tax_range: Optional[List[Optional[int]]] = None,
        number_of_employees_range: Optional[List[Optional[float]]] = None,
        poi_types: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
        cursor: Optional[Dict[str, Any]] = None,
        no_fee: bool = False,
        price_drop: bool = False,
        under_price_estimation: bool = False,
        discounted_projects: bool = False,
        only_immediate: bool = False,
        is_commercial_real_estate: bool = False,
        search_context: str = "marketplace",
        abtests: Optional[Dict[str, str]] = None,
    ) -> List[RealEstateListing]:
        """
        Fetch real estate listings (POIs - Points of Interest) from Madlan.

        This method searches for property listings based on various filters including
        location, price, rooms, area, and other property characteristics.

        Args:
            location_doc_id: Document ID for location (e.g., "רוזוב-14-תל-אביב-יפו-ישראל")
            deal_type: Type of deal - "unitBuy" (for sale) or "unitRent" (for rent)
            tile_ranges: List of tile ranges to search, each with x1, y1, x2, y2
            sort: List of sort fields, each with field, order, reference, docIds
            price_range: [min, max] price range (None means no limit)
            rooms_range: [min, max] number of rooms range
            area_range: [min, max] area in square meters range
            floor_range: [min, max] floor number range
            baths_range: [min, max] number of bathrooms range
            building_class: List of building class filters
            general_condition: List of general condition filters
            seller_type: List of seller type filters
            amenities: Dictionary of amenity filters
            commercial_amenities: Dictionary of commercial amenity filters
            quality_class: List of quality class filters
            ppm_range: [min, max] price per square meter range
            monthly_tax_range: [min, max] monthly tax range
            number_of_employees_range: [min, max] number of employees range (commercial)
            poi_types: List of POI types to search - ["bulletin", "project"]
            limit: Maximum number of results to return (default: 50)
            offset: Offset for pagination (default: 0)
            cursor: Cursor for pagination with bulletinsOffset, projectsOffset, seenProjects
            no_fee: Filter for no fee listings
            price_drop: Filter for listings with price drops
            under_price_estimation: Filter for listings under price estimation
            discounted_projects: Filter for discounted projects
            only_immediate: Filter for immediate availability only
            is_commercial_real_estate: Filter for commercial real estate
            search_context: Search context (default: "marketplace")
            abtests: A/B test configuration dictionary

        Returns:
            Dictionary containing:
            - total: Total number of results
            - totalNearby: Total number of nearby results
            - lastInGeometryId: Last geometry ID
            - cursor: Cursor for pagination
            - poi: List of POI (Point of Interest) objects with listing details

        Raises:
            MadlanAPIError: If the request fails

        Example:
            >>> client = MadlanAPIClient()
            >>> # Search for listings at a specific address
            >>> listings = client.fetch_listings(
            ...     location_doc_id="רוזוב-14-תל-אביב-יפו-ישראל",
            ...     deal_type="unitBuy",
            ...     price_range=[1000000, 5000000],
            ...     rooms_range=[3, 5],
            ...     limit=20
            ... )
            >>> print(f"Found {listings['total']} listings")
            >>> for poi in listings['poi']:
            ...     print(f"{poi['poi'].get('address')} - {poi['poi'].get('price')}")
        """
        # Build variables dictionary
        variables: Dict[str, Any] = {
            "dealType": deal_type.value,
            "noFee": no_fee,
            "priceDrop": price_drop,
            "underPriceEstimation": under_price_estimation,
            "discountedProjects": discounted_projects,
            "onlyImmediate": only_immediate,
            "isCommercialRealEstate": is_commercial_real_estate,
            "searchContext": search_context,
            "limit": limit,
            "offset": offset,
        }

        # Add optional filters
        if location_doc_id:
            variables["locationDocId"] = location_doc_id

        if tile_ranges:
            variables["tileRanges"] = tile_ranges

        if sort:
            variables["sort"] = sort

        # Add range filters (using None for null values)
        if price_range is not None:
            variables["priceRange"] = price_range
        else:
            variables["priceRange"] = [None, None]

        if rooms_range is not None:
            variables["roomsRange"] = rooms_range
        else:
            variables["roomsRange"] = [None, None]

        if area_range is not None:
            variables["areaRange"] = area_range
        else:
            variables["areaRange"] = [None, None]

        if floor_range is not None:
            variables["floorRange"] = floor_range
        else:
            variables["floorRange"] = [None, None]

        if baths_range is not None:
            variables["bathsRange"] = baths_range
        else:
            variables["bathsRange"] = [None, None]

        if ppm_range is not None:
            variables["ppmRange"] = ppm_range
        else:
            variables["ppmRange"] = [None, None]

        if monthly_tax_range is not None:
            variables["monthlyTaxRange"] = monthly_tax_range
        else:
            variables["monthlyTaxRange"] = [None, None]

        if number_of_employees_range is not None:
            variables["numberOfEmployeesRange"] = number_of_employees_range
        else:
            variables["numberOfEmployeesRange"] = [None, None]

        # Add list filters
        if building_class:
            variables["buildingClass"] = building_class
        else:
            variables["buildingClass"] = []

        if general_condition:
            variables["generalCondition"] = general_condition
        else:
            variables["generalCondition"] = []

        if seller_type:
            variables["sellerType"] = seller_type
        else:
            variables["sellerType"] = []

        if quality_class:
            variables["qualityClass"] = quality_class
        else:
            variables["qualityClass"] = []

        # Add dictionary filters
        if amenities:
            variables["amenities"] = amenities
        else:
            variables["amenities"] = {}

        if commercial_amenities:
            variables["commercialAmenities"] = commercial_amenities
        else:
            variables["commercialAmenities"] = {}

        # Add POI types
        if poi_types:
            variables["poiTypes"] = poi_types
        else:
            variables["poiTypes"] = ["bulletin", "project"]

        # Add cursor
        if cursor:
            variables["cursor"] = cursor
        else:
            variables["cursor"] = {
                "seenProjects": None,
                "bulletinsOffset": 0,
            }

        # Add A/B tests
        if abtests:
            variables["abtests"] = abtests
        else:
            variables["abtests"] = {
                "_be_sortMarketplaceByDate": "modeA",
                "_be_sortMarketplaceAgeWeight": "modeA",
                "_be_sortMarketplaceByHasAtLeastOneImage": "modeA",
            }

        # Add userContext (can be None)
        variables["userContext"] = None

        try:
            response = self._make_graphql_request(
                operation_name="searchPoi",
                query=SEARCH_POI_QUERY,
                variables=variables,
            )

            # Extract search results from response
            data = response.get("data", {})
            search_result = data.get("searchPoiV2", {})

            logger.info(
                f"Found {search_result.get('total', 0)} listings "
                f"(totalNearby: {search_result.get('totalNearby', 0)})"
            )

            listings = []
            for poi_item in search_result.get("poi", []):
                listing = parse_poi_to_listing(poi_item)
                if listing:
                    listings.append(listing)
            return listings

        except MadlanAPIError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch listings: {e}")
            raise MadlanAPIError(f"Failed to fetch listings: {e}")


if __name__ == "__main__":
    client = MadlanAPIClient()
    addresses = client.get_addresses("רמת החייל")
    if addresses:
        first_address = addresses[0]
        doc_id = first_address.get("docId")
        if doc_id:
            try:
                listings = client.fetch_listings(
                    location_doc_id=doc_id,
                    limit=10,
                    price_range=[5000000, 10000000],
                )
                print(listings)
            except MadlanAPIError as e:
                pass
