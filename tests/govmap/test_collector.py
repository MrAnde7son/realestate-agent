# -*- coding: utf-8 -*-
from unittest import mock

from orchestration.collectors.govmap_collector import GovMapCollector
from govmap.api_client import GovMapClient


def test_collector_initialization():
    """Test collector initialization with default client"""
    collector = GovMapCollector()
    assert isinstance(collector.client, GovMapClient)


def test_collector_initialization_custom_client():
    """Test collector initialization with custom client"""
    custom_client = GovMapClient()
    collector = GovMapCollector(client=custom_client)
    assert collector.client is custom_client


def test_collect_success():
    """Test successful data collection with address"""
    collector = GovMapCollector()
    
    # Mock API responses
    autocomplete_result = {
        "results": [{
            "shape": "POINT(100.0 200.0)",
            "value": "Test Address"
        }]
    }
    parcel_data = {"parcel_id": "12345", "area": 500.0}
    
    def mock_autocomplete(address):
        return autocomplete_result
    
    def mock_get_parcel_data(x, y):
        assert x == 100.0
        assert y == 200.0
        return parcel_data
    
    locate_result = {"data": [{"Values": ["111", "222"]}]}
    with mock.patch.object(collector.client, 'autocomplete', side_effect=mock_autocomplete), \
         mock.patch.object(collector.client, 'get_parcel_data', side_effect=mock_get_parcel_data), \
         mock.patch.object(collector.client, 'search_and_locate_address', return_value=locate_result):

        result = collector.collect(address="Test Address")

        assert result["address"] == "Test Address"
        assert result["x"] == 100.0
        assert result["y"] == 200.0
        assert "api_data" in result
        assert result["api_data"]["parcel"] == parcel_data
        assert result["api_data"]["search_and_locate"] == locate_result
        assert result["block"] == 111
        assert result["parcel"] == 222


def test_collect_with_api_failures():
    """Test collection when API calls fail"""
    collector = GovMapCollector()
    
    # Mock autocomplete to return coordinates
    autocomplete_result = {
        "results": [{
            "shape": "POINT(100.0 200.0)",
            "value": "Test Address"
        }]
    }
    
    def mock_autocomplete(address):
        return autocomplete_result
    
    def mock_get_parcel_data(x, y):
        raise Exception("API Error")
    
    locate_result = {"data": [{"Values": ["111", "222"]}]}

    with mock.patch.object(collector.client, 'autocomplete', side_effect=mock_autocomplete), \
         mock.patch.object(collector.client, 'get_parcel_data', side_effect=mock_get_parcel_data), \
         mock.patch.object(collector.client, 'search_and_locate_address', return_value=locate_result):

        result = collector.collect(address="Test Address")

        assert result["address"] == "Test Address"
        assert result["x"] == 100.0
        assert result["y"] == 200.0
        assert "api_data" in result
        # Parcel data should not be in the result due to API failure
        assert "parcel" not in result["api_data"]
        assert result["block"] == 111
        assert result["parcel"] == 222


def test_validate_parameters_valid():
    """Test parameter validation with valid parameters"""
    collector = GovMapCollector()
    assert collector.validate_parameters(address="Test Address") is True


def test_validate_parameters_invalid():
    """Test parameter validation with invalid parameters"""
    collector = GovMapCollector()
    assert collector.validate_parameters(address="") is False
    assert collector.validate_parameters(address=None) is False
    assert collector.validate_parameters() is False  # Missing address
