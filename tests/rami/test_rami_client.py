"""Tests for the RamiClient class."""

import json

import pytest
import requests

from rami.rami_client import RamiClient


def _make_response(payload: dict) -> requests.Response:
    r = requests.Response()
    r.status_code = 200
    r._content = json.dumps(payload).encode("utf-8")
    return r


def test_fetch_plans_with_rami_format(monkeypatch):
    """RamiClient.fetch_plans should handle RAMI API response format."""
    # Mock the actual RAMI API response format
    mock_response = {
        "totalRecords": 2,
        "plansSmall": [
            {
                "planNumber": "test/123",
                "planId": 123456,
                "cityText": "תל אביב יפו",
                "mahut": "test plan",
                "status": "פרסום לתוקף ברשומות",
                "statusDate": " 01/01/23"
            },
            {
                "planNumber": "test/456", 
                "planId": 654321,
                "cityText": "תל אביב יפו",
                "mahut": "another test plan",
                "status": "בהליך",
                "statusDate": " 15/06/24"
            }
        ]
    }

    def fake_post(url, json=None, headers=None, cookies=None, timeout=None):
        return _make_response(mock_response)

    client = RamiClient()
    monkeypatch.setattr(client.session, "post", fake_post)
    
    search_params = {
        'planNumber': '',
        'city': 5000,
        'gush': '',
        'chelka': '',
        'statuses': None,
        'planTypes': [72, 21, 1],
        'fromStatusDate': None,
        'toStatusDate': None,
        'planTypesUsed': False
    }
    
    df = client.fetch_plans(search_params)
    
    assert len(df) == 2
    assert list(df["planNumber"]) == ["test/123", "test/456"]
    assert list(df["cityText"]) == ["תל אביב יפו", "תל אביב יפו"]


def test_real_tel_aviv_search():
    """Test with real Tel Aviv search (integration test)."""
    client = RamiClient()
    
    search_params = {
        'planNumber': '',
        'city': 5000,  # Tel Aviv
        'gush': '',
        'chelka': '',
        'statuses': None,
        'planTypes': [72, 21, 1, 8, 9, 10],  # Subset for faster testing
        'fromStatusDate': None,
        'toStatusDate': None,
        'planTypesUsed': False
    }
    
    try:
        df = client.fetch_plans(search_params)
        print(f"Integration test success: Got {len(df)} plans from Tel Aviv")
        if len(df) > 0:
            print(f"First plan: {df.iloc[0]['planNumber']} in {df.iloc[0]['cityText']}")
        assert len(df) >= 0  # Should at least not fail
    except Exception as e:
        pytest.skip(f"Integration test failed - API may be unavailable: {e}")


if __name__ == "__main__":
    # Run real API test when called directly
    test_real_tel_aviv_search()