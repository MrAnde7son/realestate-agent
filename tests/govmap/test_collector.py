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


def test_autocomplete():
    """Test autocomplete method"""
    collector = GovMapCollector()
    
    expected_result = {
        "results": [{"id": "test", "originalText": "test query"}],
        "resultsCount": 1,
        "aggregations": []
    }
    
    with mock.patch.object(collector.client, 'autocomplete', return_value=expected_result):
        result = collector.autocomplete("test query")
        assert result == expected_result


def test_collect_success():
    """Test successful data collection with new API"""
    collector = GovMapCollector()
    
    # Mock API responses
    parcel_data = {"parcel_id": "12345", "area": 500.0}
    layers_catalog = {"layers": ["layer1", "layer2"]}
    search_types = {"types": ["address", "parcel"]}
    base_layers = {"baseLayers": ["satellite", "street"]}
    
    def mock_get_parcel_data(x, y):
        assert x == 100.0
        assert y == 200.0
        return parcel_data
    
    def mock_get_layers_catalog():
        return layers_catalog
    
    def mock_get_search_types():
        return search_types
    
    def mock_get_base_layers():
        return base_layers
    
    with mock.patch.object(collector.client, 'get_parcel_data', side_effect=mock_get_parcel_data), \
         mock.patch.object(collector.client, 'get_layers_catalog', side_effect=mock_get_layers_catalog), \
         mock.patch.object(collector.client, 'get_search_types', side_effect=mock_get_search_types), \
         mock.patch.object(collector.client, 'get_base_layers', side_effect=mock_get_base_layers):
        
        result = collector.collect(x=100.0, y=200.0)
        
        assert result["x"] == 100.0
        assert result["y"] == 200.0
        assert "api_data" in result
        assert result["api_data"]["parcel"] == parcel_data
        assert result["api_data"]["layers_catalog"] == layers_catalog
        assert result["api_data"]["search_types"] == search_types
        assert result["api_data"]["base_layers"] == base_layers


def test_collect_with_api_failures():
    """Test collection when some API calls fail"""
    collector = GovMapCollector()
    
    parcel_data = {"parcel_id": "12345"}
    
    def mock_get_parcel_data(x, y):
        return parcel_data
    
    def mock_get_layers_catalog():
        raise Exception("API Error")
    
    def mock_get_search_types():
        return {"types": ["address"]}
    
    def mock_get_base_layers():
        raise Exception("API Error")
    
    with mock.patch.object(collector.client, 'get_parcel_data', side_effect=mock_get_parcel_data), \
         mock.patch.object(collector.client, 'get_layers_catalog', side_effect=mock_get_layers_catalog), \
         mock.patch.object(collector.client, 'get_search_types', side_effect=mock_get_search_types), \
         mock.patch.object(collector.client, 'get_base_layers', side_effect=mock_get_base_layers):
        
        result = collector.collect(x=100.0, y=200.0)
        
        assert result["x"] == 100.0
        assert result["y"] == 200.0
        assert "api_data" in result
        assert result["api_data"]["parcel"] == parcel_data
        assert result["api_data"]["search_types"] == {"types": ["address"]}
        # Failed APIs should not be in the result
        assert "layers_catalog" not in result["api_data"]
        assert "base_layers" not in result["api_data"]


def test_validate_parameters_valid():
    """Test parameter validation with valid parameters"""
    collector = GovMapCollector()
    assert collector.validate_parameters(x=100.0, y=200.0) is True


def test_validate_parameters_invalid():
    """Test parameter validation with invalid parameters"""
    collector = GovMapCollector()
    assert collector.validate_parameters(x="invalid", y=200.0) is False
    assert collector.validate_parameters(x=100.0, y="invalid") is False
    assert collector.validate_parameters(x=100.0) is False  # Missing y
    assert collector.validate_parameters(y=200.0) is False  # Missing x
