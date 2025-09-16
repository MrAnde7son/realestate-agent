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
        result = scraper.search("test query")
        assert result == payload


def test_search_custom_params():
    """Test search with custom parameters"""
    scraper = GovMapAutocomplete()
    payload = {
        "results": [],
        "resultsCount": 0,
        "aggregations": []
    }

    def fake_post(url, json=None, headers=None, timeout=30, verify=False):
        assert json["searchText"] == "test query"
        assert json["language"] == "he"
        assert json["maxResults"] == 10
        return _make_response(json_payload=payload)

    with mock.patch('requests.Session.post', side_effect=fake_post):
        result = scraper.search("test query", language="he", max_results=10)
        assert result == payload


def test_search_error():
    """Test search with HTTP error"""
    scraper = GovMapAutocomplete()

    def fake_post(url, json=None, headers=None, timeout=30, verify=False):
        return _make_response(status=500, text="Server Error")

    with mock.patch('requests.Session.post', side_effect=fake_post):
        try:
            scraper.search("test query")
            assert False, "Expected requests.HTTPError"
        except requests.HTTPError:
            pass


def test_top_neighborhood_id_found():
    """Test top_neighborhood_id when neighborhood is found"""
    scraper = GovMapAutocomplete()
    payload = {
        "results": [
            {
                "id": "neighborhood_12345",
                "originalText": "test query",
                "score": 100.0,
                "data": {"type": "NEIGHBORHOOD"},
                "shape": "POINT(3877998.167083787 3778264.858683848)"
            }
        ],
        "resultsCount": 1,
        "aggregations": []
    }

    def fake_post(url, json=None, headers=None, timeout=30, verify=False):
        return _make_response(json_payload=payload)

    with mock.patch('requests.Session.post', side_effect=fake_post):
        result = scraper.top_neighborhood_id("test query")
        assert result == "neighborhood_12345"


def test_top_neighborhood_id_poi_fallback():
    """Test top_neighborhood_id with POI fallback when no neighborhood"""
    scraper = GovMapAutocomplete()
    payload = {
        "results": [
            {
                "id": "poi_54321",
                "originalText": "test query",
                "score": 100.0,
                "data": {"type": "POI_MID_POINT"},
                "shape": "POINT(3877998.167083787 3778264.858683848)"
            }
        ],
        "resultsCount": 1,
        "aggregations": []
    }

    def fake_post(url, json=None, headers=None, timeout=30, verify=False):
        return _make_response(json_payload=payload)

    with mock.patch('requests.Session.post', side_effect=fake_post):
        result = scraper.top_neighborhood_id("test query")
        assert result == "poi_54321"


def test_top_neighborhood_id_no_id_in_key():
    """Test top_neighborhood_id when no valid results found"""
    scraper = GovMapAutocomplete()
    payload = {
        "results": [],
        "resultsCount": 0,
        "aggregations": []
    }

    def fake_post(url, json=None, headers=None, timeout=30, verify=False):
        return _make_response(json_payload=payload)

    with mock.patch('requests.Session.post', side_effect=fake_post):
        result = scraper.top_neighborhood_id("test query")
        assert result is None


def test_top_neighborhood_id_no_results():
    """Test top_neighborhood_id when no results are found"""
    scraper = GovMapAutocomplete()
    payload = {
        "results": [],
        "resultsCount": 0,
        "aggregations": []
    }

    def fake_post(url, json=None, headers=None, timeout=30, verify=False):
        return _make_response(json_payload=payload)

    with mock.patch('requests.Session.post', side_effect=fake_post):
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
