# -*- coding: utf-8 -*-
from unittest import mock

import requests

from govmap.scraper import GovMapAutocomplete


def _make_response(status: int = 200, json_payload: dict = None, text: str = ""):
    r = requests.Response()
    r.status_code = status
    r._content = text.encode("utf-8")
    if json_payload is not None:
        import json
        r._content = json.dumps(json_payload).encode("utf-8")
        r.headers["Content-Type"] = "application/json"
    return r


def test_search_success():
    """Test successful search request"""
    scraper = GovMapAutocomplete()
    payload = {
        "res": {
            "NEIGHBORHOOD": [{"Key": "test_key", "Value": "Test Neighborhood"}],
            "STREET": [{"Key": "street_key", "Value": "Test Street"}]
        }
    }

    def fake_get(url, params=None, headers=None, timeout=30, verify=False):
        assert "AutoComplete" in url
        assert params["query"] == "test query"
        assert params["ids"] == "276267023"
        assert params["gid"] == "govmap"
        return _make_response(json_payload=payload)

    with mock.patch.object(scraper.sess, 'get', side_effect=fake_get):
        result = scraper.search("test query")
        assert result == payload


def test_search_custom_params():
    """Test search with custom parameters"""
    scraper = GovMapAutocomplete()
    payload = {"res": {}}

    def fake_get(url, params=None, headers=None, timeout=30, verify=False):
        assert params["ids"] == "custom_ids"
        assert params["gid"] == "custom_gid"
        return _make_response(json_payload=payload)

    with mock.patch.object(scraper.sess, 'get', side_effect=fake_get):
        result = scraper.search("test query", ids="custom_ids", gid="custom_gid")
        assert result == payload


def test_search_error():
    """Test search with HTTP error"""
    scraper = GovMapAutocomplete()

    def fake_get(url, params=None, headers=None, timeout=30, verify=False):
        return _make_response(status=500, text="Server Error")

    with mock.patch.object(scraper.sess, 'get', side_effect=fake_get):
        try:
            scraper.search("test query")
            assert False, "Expected requests.HTTPError"
        except requests.HTTPError:
            pass


def test_top_neighborhood_id_found():
    """Test top_neighborhood_id when neighborhood is found"""
    scraper = GovMapAutocomplete()
    payload = {
        "res": {
            "NEIGHBORHOOD": [
                {"Key": "https://example.com?id=12345", "Value": "Test Neighborhood"}
            ],
            "STREET": [
                {"Key": "https://example.com?id=67890", "Value": "Test Street"}
            ]
        }
    }

    def fake_get(url, params=None, headers=None, timeout=30, verify=False):
        return _make_response(json_payload=payload)

    with mock.patch.object(scraper.sess, 'get', side_effect=fake_get):
        result = scraper.top_neighborhood_id("test query")
        assert result == "12345"


def test_top_neighborhood_id_poi_fallback():
    """Test top_neighborhood_id with POI fallback when no neighborhood"""
    scraper = GovMapAutocomplete()
    payload = {
        "res": {
            "POI_MID_POINT": [
                {"Key": "https://example.com?id=54321", "Value": "Test POI"}
            ],
            "STREET": [
                {"Key": "https://example.com?id=67890", "Value": "Test Street"}
            ]
        }
    }

    def fake_get(url, params=None, headers=None, timeout=30, verify=False):
        return _make_response(json_payload=payload)

    with mock.patch.object(scraper.sess, 'get', side_effect=fake_get):
        result = scraper.top_neighborhood_id("test query")
        assert result == "54321"


def test_top_neighborhood_id_no_id_in_key():
    """Test top_neighborhood_id when key doesn't contain id parameter"""
    scraper = GovMapAutocomplete()
    payload = {
        "res": {
            "NEIGHBORHOOD": [
                {"Key": "https://example.com/other", "Value": "Test Neighborhood"}
            ]
        }
    }

    def fake_get(url, params=None, headers=None, timeout=30, verify=False):
        return _make_response(json_payload=payload)

    with mock.patch.object(scraper.sess, 'get', side_effect=fake_get):
        result = scraper.top_neighborhood_id("test query")
        assert result is None


def test_top_neighborhood_id_no_results():
    """Test top_neighborhood_id when no results are found"""
    scraper = GovMapAutocomplete()
    payload = {"res": {}}

    def fake_get(url, params=None, headers=None, timeout=30, verify=False):
        return _make_response(json_payload=payload)

    with mock.patch.object(scraper.sess, 'get', side_effect=fake_get):
        result = scraper.top_neighborhood_id("test query")
        assert result is None


def test_top_neighborhood_id_malformed_url():
    """Test top_neighborhood_id with malformed URL in key"""
    scraper = GovMapAutocomplete()
    payload = {
        "res": {
            "NEIGHBORHOOD": [
                {"Key": "not-a-url", "Value": "Test Neighborhood"}
            ]
        }
    }

    def fake_get(url, params=None, headers=None, timeout=30, verify=False):
        return _make_response(json_payload=payload)

    with mock.patch.object(scraper.sess, 'get', side_effect=fake_get):
        result = scraper.top_neighborhood_id("test query")
        assert result is None


def test_scraper_initialization():
    """Test scraper initialization with custom parameters"""
    scraper = GovMapAutocomplete(
        base_url="https://custom-autocomplete.com",
        timeout=60
    )
    
    assert scraper.base_url == "https://custom-autocomplete.com"
    assert scraper.timeout == 60


def test_scraper_headers():
    """Test that scraper sets appropriate headers"""
    scraper = GovMapAutocomplete()
    
    expected_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }
    
    for key, value in expected_headers.items():
        assert scraper.sess.headers[key] == value
