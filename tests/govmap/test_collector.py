# -*- coding: utf-8 -*-
from unittest import mock

from orchestration.collectors.govmap_collector import GovMapCollector
from govmap.api_client import GovMapClient, WMSFeatureInfo


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
    """Test successful data collection"""
    collector = GovMapCollector()
    
    # Mock parcel data
    parcel_data = {
        "type": "Feature",
        "properties": {
            "parcel_id": "12345",
            "area": 500.0
        }
    }
    
    # Mock nearby layer data
    nearby_data = [
        WMSFeatureInfo(layer="test_layer", attributes={"feature_id": "1", "value": "test"})
    ]
    
    def mock_get_parcel_at_point(x, y, layer=None, geom_fields=None):
        assert x == 100.0
        assert y == 200.0
        assert layer == "opendata:PARCEL_ALL"
        return parcel_data
    
    def mock_wms_getfeatureinfo(layer, x, y, buffer_m=None):
        assert x == 100.0
        assert y == 200.0
        assert buffer_m == 150
        return nearby_data
    
    with mock.patch.object(collector.client, 'get_parcel_at_point', side_effect=mock_get_parcel_at_point), \
         mock.patch.object(collector.client, 'wms_getfeatureinfo', side_effect=mock_wms_getfeatureinfo):
        
        result = collector.collect(x=100.0, y=200.0, extra_layers=["test_layer"])
        
        assert result["x"] == 100.0
        assert result["y"] == 200.0
        assert result["parcel"] == parcel_data
        assert "test_layer" in result["nearby"]
        assert len(result["nearby"]["test_layer"]) == 1
        assert result["nearby"]["test_layer"][0]["feature_id"] == "1"


def test_collect_no_extra_layers():
    """Test collection without extra layers"""
    collector = GovMapCollector()
    
    parcel_data = {
        "type": "Feature",
        "properties": {"parcel_id": "12345"}
    }
    
    def mock_get_parcel_at_point(x, y, layer=None, geom_fields=None):
        return parcel_data
    
    with mock.patch.object(collector.client, 'get_parcel_at_point', side_effect=mock_get_parcel_at_point):
        result = collector.collect(x=100.0, y=200.0)
        
        assert result["x"] == 100.0
        assert result["y"] == 200.0
        assert result["parcel"] == parcel_data
        assert result["nearby"] == {}


def test_collect_no_parcel_found():
    """Test collection when no parcel is found"""
    collector = GovMapCollector()
    
    def mock_get_parcel_at_point(x, y, layer=None, geom_fields=None):
        return None
    
    with mock.patch.object(collector.client, 'get_parcel_at_point', side_effect=mock_get_parcel_at_point):
        result = collector.collect(x=100.0, y=200.0)
        
        assert result["x"] == 100.0
        assert result["y"] == 200.0
        assert result["parcel"] is None
        assert result["nearby"] == {}


def test_collect_custom_parameters():
    """Test collection with custom parameters"""
    collector = GovMapCollector()
    
    parcel_data = {"type": "Feature", "properties": {"parcel_id": "12345"}}
    nearby_data = [WMSFeatureInfo(layer="custom_layer", attributes={"id": "1"})]
    
    def mock_get_parcel_at_point(x, y, layer=None, geom_fields=None):
        assert layer == "custom:parcels"
        return parcel_data
    
    def mock_wms_getfeatureinfo(layer, x, y, buffer_m=None):
        assert layer == "custom_layer"
        assert buffer_m == 200
        return nearby_data
    
    with mock.patch.object(collector.client, 'get_parcel_at_point', side_effect=mock_get_parcel_at_point), \
         mock.patch.object(collector.client, 'wms_getfeatureinfo', side_effect=mock_wms_getfeatureinfo):
        
        result = collector.collect(
            x=100.0, 
            y=200.0, 
            parcel_layer="custom:parcels",
            extra_layers=["custom_layer"],
            buffer_m=200
        )
        
        assert result["parcel"] == parcel_data
        assert "custom_layer" in result["nearby"]


def test_validate_parameters_valid():
    """Test parameter validation with valid parameters"""
    collector = GovMapCollector()
    
    assert collector.validate_parameters(x=100.0, y=200.0) is True
    assert collector.validate_parameters(x=100, y=200) is True


def test_validate_parameters_invalid():
    """Test parameter validation with invalid parameters"""
    collector = GovMapCollector()
    
    assert collector.validate_parameters(x="invalid", y=200.0) is False
    assert collector.validate_parameters(x=100.0, y="invalid") is False
    assert collector.validate_parameters(x=100.0) is False  # missing y
    assert collector.validate_parameters(y=200.0) is False  # missing x
    assert collector.validate_parameters() is False  # missing both


def test_collect_multiple_nearby_layers():
    """Test collection with multiple nearby layers"""
    collector = GovMapCollector()
    
    parcel_data = {"type": "Feature", "properties": {"parcel_id": "12345"}}
    
    def mock_get_parcel_at_point(x, y, layer=None, geom_fields=None):
        return parcel_data
    
    def mock_wms_getfeatureinfo(layer, x, y, buffer_m=None):
        if layer == "layer1":
            return [WMSFeatureInfo(layer="layer1", attributes={"id": "1"})]
        elif layer == "layer2":
            return [WMSFeatureInfo(layer="layer2", attributes={"id": "2"})]
        return []
    
    with mock.patch.object(collector.client, 'get_parcel_at_point', side_effect=mock_get_parcel_at_point), \
         mock.patch.object(collector.client, 'wms_getfeatureinfo', side_effect=mock_wms_getfeatureinfo):
        
        result = collector.collect(
            x=100.0, 
            y=200.0, 
            extra_layers=["layer1", "layer2"]
        )
        
        assert "layer1" in result["nearby"]
        assert "layer2" in result["nearby"]
        assert len(result["nearby"]["layer1"]) == 1
        assert len(result["nearby"]["layer2"]) == 1
        assert result["nearby"]["layer1"][0]["id"] == "1"
        assert result["nearby"]["layer2"][0]["id"] == "2"
