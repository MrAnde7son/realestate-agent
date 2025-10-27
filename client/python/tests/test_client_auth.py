from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from realestate_api.client import RealEstateAPIClient


class DummyResponse:
    def __init__(self, status_code=200, data=None, text=""):
        self.status_code = status_code
        self._data = data or {}
        self.text = text or ""
        self.ok = status_code < 400

    def json(self):
        return self._data


@pytest.fixture
def client():
    return RealEstateAPIClient(base_url="http://api")


def test_login_sets_authorization_header(monkeypatch, client):
    captured = {}

    def fake_request(method, url, **kwargs):  # noqa: ANN001
        captured["method"] = method
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        return DummyResponse(data={"access_token": "new-token", "refresh_token": "other"})

    monkeypatch.setattr(client.session, "request", fake_request)

    result = client.login("user@example.com", "secret")

    assert result["access_token"] == "new-token"
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/auth/login")
    assert captured["json"] == {"email": "user@example.com", "password": "secret"}
    assert client.session.headers["Authorization"] == "Bearer new-token"


def test_refresh_token_uses_correct_payload(monkeypatch, client):
    captured = {}

    def fake_request(method, url, **kwargs):  # noqa: ANN001
        captured["json"] = kwargs.get("json")
        return DummyResponse(data={"access_token": "updated", "refresh_token": "refreshed"})

    monkeypatch.setattr(client.session, "request", fake_request)

    response = client.refresh_token("refresh-value")

    assert captured["json"] == {"refresh_token": "refresh-value"}
    assert response["access_token"] == "updated"
    assert client.session.headers["Authorization"] == "Bearer updated"
