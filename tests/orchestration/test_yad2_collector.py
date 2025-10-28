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
    mock_client.fetch_location_autocomplete.return_value = location_payload
    mock_client.fetch_listings.return_value = []
    mock_client.scrape_all_pages.return_value = ["listing"]
    mock_client.fetch_latest_deals.return_value = []

    collector = Yad2Collector(client=mock_client)
    location = LocationQuery(street="הברזל", house_number=32, city="תל אביב")
    result = collector.collect(location)

    assert result == ["listing"]
    mock_client.set_search_parameters.assert_called_once_with(
        city=5000, topArea=2, area=1, neighborhood=203, street="123"
    )
    mock_client.scrape_all_pages.assert_called_once_with(delay=0)
