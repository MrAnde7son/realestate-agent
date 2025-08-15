"""Tests for the RamiClient class."""

import json
import requests

from rami.rami_client import RamiClient


def _make_response(payload: dict) -> requests.Response:
    r = requests.Response()
    r.status_code = 200
    r._content = json.dumps(payload).encode("utf-8")
    return r


def test_fetch_plans_paginates(monkeypatch):
    """RamiClient.fetch_plans should follow pagination until all results are fetched."""
    pages = [
        {"data": [{"id": 1}, {"id": 2}], "total": 4},
        {"data": [{"id": 3}, {"id": 4}], "total": 4},
    ]

    def fake_post(url, json=None, headers=None, cookies=None, timeout=None):  # noqa: D401
        return _make_response(pages.pop(0))

    client = RamiClient(page_size=2, delay=0)
    monkeypatch.setattr(client.session, "post", fake_post)
    df = client.fetch_plans({"foo": "bar"})
    assert list(df["id"]) == [1, 2, 3, 4]
