import pytest
from unittest.mock import Mock

from orchestration.collectors.yad2_collector import Yad2Collector
from orchestration.location import LocationQuery


@pytest.fixture
def location_payload():
    return {
        "top_areas": [{"topAreaId": "2", "name": "מרכז"}],
        "areas": [{"areaId": "1", "name": "תל אביב"}],
        "cities": [
            {
                "cityId": "5000",
                "name": "תל אביב-יפו",
                "topAreaId": "2",
                "areaId": "1",
            }
        ],
        "hoods": [
            {
                "hoodId": "203",
                "cityId": "5000",
                "name": "רמת החייל",
            }
        ],
        "streets": [
            {
                "streetId": "123",
                "cityId": "5000",
                "name": "הברזל",
            }
        ],
    }


def test_collect_applies_location_parameters(location_payload):
    mock_client = Mock()
    # The collector calls fetch_location_autocomplete with address string
    # It then extracts search params from the returned payload
    # The payload should return a dict with search parameters
    mock_client.fetch_location_autocomplete.return_value = {
        "city": 5000, "topArea": 2, "area": 1, "neighborhood": 203, "street": "123"
    }
    mock_client.set_search_parameters = Mock()
    mock_client.fetch_listings.return_value = []
    mock_client.scrape_all_pages.return_value = ["listing"]
    mock_client.fetch_latest_deals.return_value = []

    collector = Yad2Collector(client=mock_client)
    location = LocationQuery(street="הברזל", house_number=32, city="תל אביב")
    result = collector.collect(location)

    assert result == ["listing"]
    # Verify that set_search_parameters was called with the expected parameters
    mock_client.set_search_parameters.assert_called_once()
