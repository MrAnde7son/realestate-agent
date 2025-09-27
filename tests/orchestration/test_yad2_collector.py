import pytest
from unittest.mock import Mock

from orchestration.collectors.yad2_collector import Yad2Collector


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


def test_prepare_location_parameters(location_payload):
    params = Yad2Collector._prepare_location_parameters(location_payload)

    assert params["city"] == 5000
    assert params["topArea"] == 2
    assert params["area"] == 1
    assert params["neighborhood"] == 203
    assert params["street"] == "123"


def test_collect_applies_location_parameters(location_payload):
    mock_client = Mock()
    mock_client.fetch_location_autocomplete.return_value = location_payload
    mock_client.scrape_all_pages.return_value = ["listing"]

    collector = Yad2Collector(client=mock_client)
    result = collector.collect(address="הברזל 32 תל אביב", max_pages=2)

    assert result == ["listing"]
    mock_client.set_search_parameters.assert_called_once_with(
        city=5000, topArea=2, area=1, neighborhood=203, street="123"
    )
    mock_client.scrape_all_pages.assert_called_once_with(max_pages=2, delay=0)
