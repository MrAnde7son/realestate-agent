# -*- coding: utf-8 -*-
import json
from typing import Dict
from unittest import mock

import requests

from govmap.api_client import GovMapClient, GovMapError, itm_to_wgs84, wgs84_to_itm


def _make_response(status: int = 200, json_payload: Dict = None, text: str = "", headers: Dict = None):
    r = requests.Response()
    r.status_code = status
    r._content = text.encode("utf-8")
    r.headers.update(headers or {})
    if json_payload is not None:
        r._content = json.dumps(json_payload).encode("utf-8")
        r.headers["Content-Type"] = "application/json"
    return r


def test_autocomplete_success():
    """Test successful autocomplete request"""
    client = GovMapClient()
    payload = {
        "res": {
            "NEIGHBORHOOD": [{"Key": "test_key", "Value": "Test Neighborhood"}],
            "STREET": [{"Key": "street_key", "Value": "Test Street"}]
        }
    }

    def fake_get(url, params=None, headers=None, timeout=30, verify=False):
        assert "AutoComplete" in url
        assert params["query"] == "test query"
        return _make_response(json_payload=payload)

    with mock.patch.object(client.http, 'get', side_effect=fake_get):
        result = client.autocomplete("test query")
        assert result == payload


def test_autocomplete_error():
    """Test autocomplete with HTTP error"""
    client = GovMapClient()

    def fake_get(url, params=None, headers=None, timeout=30, verify=False):
        return _make_response(status=500, text="Server Error")

    with mock.patch.object(client.http, 'get', side_effect=fake_get):
        try:
            client.autocomplete("test query")
            assert False, "Expected GovMapError"
        except GovMapError as e:
            assert "HTTP 500" in str(e)


def test_wms_getfeatureinfo_success():
    """Test successful WMS GetFeatureInfo request"""
    client = GovMapClient()
    payload = {
        "features": [
            {
                "properties": {
                    "parcel_id": "12345",
                    "area": 500.0
                }
            }
        ]
    }

    def fake_get(url, params=None, headers=None, timeout=30):
        assert "wms" in url.lower()
        assert params["service"] == "WMS"
        assert params["request"] == "GetFeatureInfo"
        return _make_response(json_payload=payload)

    with mock.patch.object(client.http, 'get', side_effect=fake_get):
        result = client.wms_getfeatureinfo(layer="test_layer", x=100.0, y=200.0)
        assert len(result) == 1
        assert result[0].layer == "test_layer"
        assert result[0].attributes["parcel_id"] == "12345"


def test_wms_getfeatureinfo_error():
    """Test WMS GetFeatureInfo with HTTP error"""
    client = GovMapClient()

    def fake_get(url, params=None, headers=None, timeout=30):
        return _make_response(status=404, text="Not Found")

    with mock.patch.object(client.http, 'get', side_effect=fake_get):
        try:
            client.wms_getfeatureinfo(layer="test_layer", x=100.0, y=200.0)
            assert False, "Expected GovMapError"
        except GovMapError as e:
            assert "HTTP 404" in str(e)


def test_wfs_get_features_success():
    """Test successful WFS GetFeature request"""
    client = GovMapClient()
    payload = {
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "parcel_id": "12345",
                    "area": 500.0
                }
            }
        ]
    }

    def fake_get(url, params=None, headers=None, timeout=30):
        assert "ows" in url.lower()
        assert params["service"] == "WFS"
        assert params["request"] == "GetFeature"
        return _make_response(json_payload=payload)

    with mock.patch.object(client.http, 'get', side_effect=fake_get):
        result = client.wfs_get_features(layer="test_layer")
        assert result == payload


def test_wfs_get_features_with_cql_filter():
    """Test WFS GetFeature with CQL filter"""
    client = GovMapClient()
    payload = {"features": []}

    def fake_get(url, params=None, headers=None, timeout=30):
        assert params["CQL_FILTER"] == "INTERSECTS(the_geom,POINT(100 200))"
        return _make_response(json_payload=payload)

    with mock.patch.object(client.http, 'get', side_effect=fake_get):
        result = client.wfs_get_features(layer="test_layer", cql_filter="INTERSECTS(the_geom,POINT(100 200))")
        assert result == payload


def test_wfs_get_features_error():
    """Test WFS GetFeature with HTTP error"""
    client = GovMapClient()

    def fake_get(url, params=None, headers=None, timeout=30):
        return _make_response(status=400, text="Bad Request")

    with mock.patch.object(client.http, 'get', side_effect=fake_get):
        try:
            client.wfs_get_features(layer="test_layer")
            assert False, "Expected GovMapError"
        except GovMapError as e:
            assert "HTTP 400" in str(e)


def test_get_parcel_at_point_wfs_success():
    """Test get_parcel_at_point using WFS (successful)"""
    client = GovMapClient()
    payload = {
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "parcel_id": "12345",
                    "area": 500.0
                }
            }
        ]
    }

    def fake_get(url, params=None, headers=None, timeout=30):
        if "ows" in url.lower():
            return _make_response(json_payload=payload)
        raise AssertionError(f"Unexpected URL: {url}")

    with mock.patch.object(client.http, 'get', side_effect=fake_get):
        result = client.get_parcel_at_point(100.0, 200.0)
        assert result is not None
        assert result["type"] == "Feature"
        assert result["properties"]["parcel_id"] == "12345"


def test_get_parcel_at_point_wfs_fallback_wms():
    """Test get_parcel_at_point with WFS failure, WMS fallback"""
    client = GovMapClient()
    wms_payload = {
        "features": [
            {
                "properties": {
                    "parcel_id": "12345",
                    "area": 500.0
                }
            }
        ]
    }

    def fake_get(url, params=None, headers=None, timeout=30):
        if "ows" in url.lower():
            return _make_response(status=500, text="WFS Error")
        elif "wms" in url.lower():
            return _make_response(json_payload=wms_payload)
        raise AssertionError(f"Unexpected URL: {url}")

    with mock.patch.object(client.http, 'get', side_effect=fake_get):
        result = client.get_parcel_at_point(100.0, 200.0)
        assert result is not None
        assert result["type"] == "Feature"
        assert result["properties"]["parcel_id"] == "12345"


def test_get_parcel_at_point_no_results():
    """Test get_parcel_at_point when no parcel is found"""
    client = GovMapClient()

    def fake_get(url, params=None, headers=None, timeout=30):
        if "ows" in url.lower():
            return _make_response(json_payload={"features": []})
        elif "wms" in url.lower():
            return _make_response(json_payload={"features": []})
        raise AssertionError(f"Unexpected URL: {url}")

    with mock.patch.object(client.http, 'get', side_effect=fake_get):
        result = client.get_parcel_at_point(100.0, 200.0)
        assert result is None


def test_coordinate_conversion_itm_to_wgs84():
    """Test coordinate conversion from ITM to WGS84"""
    # Test coordinates in Tel Aviv area
    x_itm, y_itm = 184391.15, 668715.93
    lon, lat = itm_to_wgs84(x_itm, y_itm)
    
    # Should be approximately in Tel Aviv area (adjusted for actual conversion)
    assert 34.8 < lon < 34.9
    assert 32.1 < lat < 32.2
    assert isinstance(lon, float)
    assert isinstance(lat, float)


def test_coordinate_conversion_wgs84_to_itm():
    """Test coordinate conversion from WGS84 to ITM"""
    # Test coordinates in Tel Aviv area
    lon, lat = 34.8329, 32.1113
    x, y = wgs84_to_itm(lon, lat)
    
    # Should be approximately in Tel Aviv area (adjusted for actual conversion)
    assert 180000 < x < 190000
    assert 660000 < y < 670000
    assert isinstance(x, float)
    assert isinstance(y, float)


def test_coordinate_conversion_roundtrip():
    """Test coordinate conversion roundtrip (ITM -> WGS84 -> ITM)"""
    x_original, y_original = 184391.15, 668715.93
    lon, lat = itm_to_wgs84(x_original, y_original)
    x_back, y_back = wgs84_to_itm(lon, lat)
    
    # Should be very close to original values (within 1 meter)
    assert abs(x_back - x_original) < 1.0
    assert abs(y_back - y_original) < 1.0


def test_client_initialization():
    """Test client initialization with custom parameters"""
    client = GovMapClient(
        wms_url="https://custom-wms.com",
        wfs_url="https://custom-wfs.com",
        autocomplete_url="https://custom-autocomplete.com",
        timeout=60
    )
    
    assert client.wms_url == "https://custom-wms.com"
    assert client.wfs_url == "https://custom-wfs.com"
    assert client.autocomplete_url == "https://custom-autocomplete.com"
    assert client.timeout == 60


def test_client_headers():
    """Test that client sets appropriate headers"""
    client = GovMapClient()
    
    expected_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }
    
    for key, value in expected_headers.items():
        assert client.http.headers[key] == value
