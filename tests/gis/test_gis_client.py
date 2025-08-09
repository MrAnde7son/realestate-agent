# -*- coding: utf-8 -*-
import os
import io
import json
import shutil
from unittest import mock
from typing import Dict

import requests
from gis.gis_client import TelAvivGS, ArcGISError


def _make_response(status: int = 200, json_payload: Dict = None, text: str = "", headers: Dict = None):
    r = requests.Response()
    r.status_code = status
    r._content = text.encode("utf-8")
    r.headers.update(headers or {})
    if json_payload is not None:
        r._content = json.dumps(json_payload).encode("utf-8")
        r.headers["Content-Type"] = "application/json"
    return r


def test_geocode_address_success(monkeypatch):
    gs = TelAvivGS()
    payload = {"features": [{"attributes": {"x": 178000.5, "y": 665000.25}}]}

    def fake_get(url, params=None, headers=None, timeout=30):
        assert "IView2RekaHeb/MapServer/0/query" in url
        return _make_response(json_payload=payload)

    with mock.patch("requests.get", side_effect=fake_get):
        x, y = gs.get_address_coordinates("הגולן", 1)
        assert isinstance(x, float) and isinstance(y, float)
        assert x == 178000.5 and y == 665000.25


def test_geocode_address_not_found(monkeypatch):
    gs = TelAvivGS()
    payload = {"features": []}

    def fake_get(url, params=None, headers=None, timeout=30):
        return _make_response(json_payload=payload)

    with mock.patch("requests.get", side_effect=fake_get):
        try:
            gs.get_address_coordinates("missing", 999)
            assert False, "Expected ArcGISError"
        except ArcGISError:
            pass


def test_get_building_permits_no_download(monkeypatch, tmp_path):
    gs = TelAvivGS()
    permit_payload = {
        "features": [
            {"attributes": {"permission_num": "123", "request_num": None, "url_hadmaya": "/docs/123.pdf"}}
        ]
    }

    def fake_get(url, params=None, headers=None, timeout=30):
        if "MapServer/772/query" in url:
            return _make_response(json_payload=permit_payload)
        raise AssertionError("Unexpected URL: " + url)

    with mock.patch("requests.get", side_effect=fake_get):
        results = gs.get_building_permits(178000, 665000, radius=30, download_pdfs=False)
        assert len(results) == 1
        assert results[0]["permission_num"] == "123"


def test_get_building_permits_with_download(monkeypatch, tmp_path):
    gs = TelAvivGS()
    save_dir = tmp_path / "permits"
    permit_payload = {
        "features": [
            {"attributes": {"permission_num": "123", "request_num": None, "url_hadmaya": "/docs/123.pdf"}}
        ]
    }

    def fake_get(url, params=None, headers=None, timeout=30, allow_redirects=True):
        if "MapServer/772/query" in url:
            return _make_response(json_payload=permit_payload)
        if url.endswith("/docs/123.pdf"):
            r = requests.Response()
            r.status_code = 200
            r._content = b"%PDF-1.4\n..."
            r.headers["Content-Type"] = "application/pdf"
            return r
        raise AssertionError("Unexpected URL: " + url)

    with mock.patch("requests.get", side_effect=fake_get):
        results = gs.get_building_permits(178000, 665000, radius=30, download_pdfs=True, save_dir=str(save_dir))
        assert len(results) == 1
        pdf_path = save_dir / "123.pdf"
        assert pdf_path.exists()
        assert pdf_path.read_bytes().startswith(b"%PDF") 