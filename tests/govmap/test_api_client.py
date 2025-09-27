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
        "results": [
            {
                "id": "test_id",
                "originalText": "test query",
                "score": 100.0,
                "data": {},
                "shape": "POINT(3877998.167083787 3778264.858683848)"
            }
        ],
        "resultsCount": 1,
        "aggregations": []
    }

    def fake_post(url, json=None, headers=None, timeout=30, verify=False):
        assert "autocomplete" in url
        assert json["searchText"] == "test query"
        return _make_response(json_payload=payload)

    with mock.patch('requests.Session.post', side_effect=fake_post):
        result = client.autocomplete("test query")
        assert result == payload


def test_autocomplete_error():
    """Test autocomplete with HTTP error"""
    client = GovMapClient()

    def fake_post(url, json=None, headers=None, timeout=30, verify=False):
        return _make_response(status=500, text="Server Error")

    with mock.patch('requests.Session.post', side_effect=fake_post):
        try:
            client.autocomplete("test query")
            assert False, "Expected GovMapError"
        except GovMapError as e:
            assert "HTTP 500" in str(e)


def test_coordinate_conversion_itm_to_wgs84():
    """Test ITM to WGS84 coordinate conversion"""
    x, y = 184391.15, 668715.93
    lon, lat = itm_to_wgs84(x, y)
    assert isinstance(lon, float)
    assert isinstance(lat, float)
    assert 34.0 < lon < 35.0  # Tel Aviv longitude range
    assert 32.0 < lat < 33.0  # Tel Aviv latitude range


def test_coordinate_conversion_wgs84_to_itm():
    """Test WGS84 to ITM coordinate conversion"""
    lon, lat = 34.7818, 32.0853  # Tel Aviv coordinates
    x, y = wgs84_to_itm(lon, lat)
    assert isinstance(x, float)
    assert isinstance(y, float)
    assert 170000 < x < 200000  # ITM X range for Tel Aviv
    assert 650000 < y < 700000  # ITM Y range for Tel Aviv


def test_coordinate_conversion_roundtrip():
    """Test roundtrip coordinate conversion"""
    x_original, y_original = 184391.15, 668715.93
    lon, lat = itm_to_wgs84(x_original, y_original)
    x_back, y_back = wgs84_to_itm(lon, lat)
    
    # Should be within 1 meter
    assert abs(x_back - x_original) < 1.0
    assert abs(y_back - y_original) < 1.0


def test_client_initialization():
    """Test client initialization with default parameters"""
    client = GovMapClient()
    assert client.autocomplete_url == "https://www.govmap.gov.il/api/search-service/autocomplete"
    assert client.timeout == 30


def test_client_headers():
    """Test client headers are set correctly"""
    client = GovMapClient()
    assert "Accept" in client.http.headers
    assert "User-Agent" in client.http.headers


def test_search_and_locate_success():
    """Test the SearchAndLocate endpoint wrapper"""
    client = GovMapClient()
    payload = {"data": [{"Values": [123, 456]}]}

    def fake_post(url, json=None, headers=None, timeout=30, verify=False):
        assert client.search_and_locate_url in url
        assert json == {"type": 0, "address": "Example"}
        return _make_response(json_payload=payload)

    with mock.patch.object(client.http, "post", side_effect=fake_post):
        result = client.search_and_locate_address("Example")
        assert result == payload


def test_extract_block_parcel():
    """Ensure block/parcel extraction works"""
    response = {"data": [{"Values": ["100", "200", "ignored"]}]}
    assert GovMapClient.extract_block_parcel(response) == (100, 200)


def test_extract_block_parcel_invalid():
    """Gracefully handle malformed responses"""
    assert GovMapClient.extract_block_parcel({}) is None
    assert GovMapClient.extract_block_parcel({"data": []}) is None
    assert GovMapClient.extract_block_parcel({"data": [{"Values": ["abc"]}]}) is None

