import json

from yad2.core import Yad2SearchParameters
from yad2.api_client import Yad2APIClient
from yad2.scrapers import Yad2Scraper


def test_build_search_url_and_from_url():
    params = Yad2SearchParameters(maxPrice=1000000, city=5000)
    scraper = Yad2Scraper(params)
    url = scraper.build_search_url(page=2)
    assert "maxPrice=1000000" in url
    assert "city=5000" in url
    assert "page=2" in url

    cloned = Yad2Scraper.from_url(url)
    original = {k: str(v) for k, v in scraper.search_params.get_active_parameters().items()}
    assert cloned.search_params.get_active_parameters() == original



def test_fetch_listings_converts_markers(monkeypatch):
    payload = {
        "data": {
        "markers": [
            {
                "address": {
                    "city": {"text": "תל אביב יפו"},
                    "neighborhood": {"text": "רמת החייל"},
                    "street": {"text": "ליפא קרפל"},
                    "house": {"number": 15, "floor": 0},
                    "coords": {"lon": 34.832671, "lat": 32.111408},
                },
                "subcategoryId": 1,
                "categoryId": 2,
                "adType": "private",
                "price": 8_500_000,
                "token": "j1l4opy9",
                "orderId": 56008383,
                "additionalDetails": {
                    "property": {"text": "דו משפחתי"},
                    "roomsCount": 3.5,
                    "squareMeter": 336,
                },
                "metaData": {
                    "coverImage": "https://example.com/cover.jpg",
                    "images": [
                        "https://example.com/cover.jpg",
                        "https://example.com/extra.jpg",
                    ],
                    "squareMeterBuild": 120,
                },
                "tags": [{"name": "חניה"}],
            }
        ],
        "yad1Markers": [],
        }
    }

    class DummyResponse:
        status_code = 200

        def __init__(self, payload_data):
            self._payload = payload_data

        @property
        def text(self):
            return json.dumps(self._payload)

        def json(self):
            return self._payload

    scraper = Yad2APIClient(Yad2SearchParameters(city=5000, neighborhood=203))
    # fetch_listings calls the API 3 times (sale, rent, commercial) when listing_type is ALL
    # So we need to return the same response for all 3 calls
    def mock_get(url, params, timeout):
        return DummyResponse(payload)
    
    monkeypatch.setattr(scraper.session, "get", mock_get)

    listings = scraper.fetch_listings()
    assert len(listings) == 3
    listing_types = {entry.listing_type for entry in listings}
    assert listing_types == {"sale", "rent", "commercial"}
    listing = listings[0]

    assert listing.price == 8_500_000
    assert listing.listing_id == "56008383"
    assert listing.coordinates == (34.832671, 32.111408)
    assert listing.property_type == "דו משפחתי"
    assert listing.total_size == 336
    assert listing.size == 120
    assert listing.images == [
        "https://example.com/cover.jpg",
        "https://example.com/extra.jpg",
    ]
    assert listing.meta["marker_type"] == "yad2"
