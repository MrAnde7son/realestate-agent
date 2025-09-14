import json
from typing import Dict
from unittest import mock

import requests

from gis.gis_client import TelAvivGS


def _make_response(status: int = 200, json_payload: Dict = None, text: str = "", headers: Dict = None):
    r = requests.Response()
    r.status_code = status
    r._content = text.encode("utf-8")
    r.headers.update(headers or {})
    if json_payload is not None:
        r._content = json.dumps(json_payload).encode("utf-8")
        r.headers["Content-Type"] = "application/json"
    return r


def test_privilege_page(tmp_path):
    gs = TelAvivGS()
    x, y = 184320.94, 668548.65
    blocks_payload = {"features": [{"attributes": {"ms_gush": "6638"}}]}
    parcels_payload = {"features": [{"attributes": {"ms_chelka": "572"}}]}
    privilege_content = b"%PDF-1.4\n%Test PDF content"

    def fake_get(url, params=None, headers=None, timeout=30, allow_redirects=True):
        if "MapServer/525/query" in url:
            return _make_response(json_payload=blocks_payload)
        if "MapServer/524/query" in url:
            return _make_response(json_payload=parcels_payload)
        if "medamukdam/fr_asp/fr_meda_main.asp?block=6638&parcel=572" in url:
            r = requests.Response()
            r.status_code = 200
            r._content = privilege_content
            r.headers["Content-Type"] = "application/pdf"
            return r
        raise AssertionError(f"Unexpected URL: {url}")

    save_dir = tmp_path / "privilege_pages"
    with mock.patch("requests.get", side_effect=fake_get):
        blocks = gs.get_blocks(x, y)
        parcels = gs.get_parcels(x, y)
        result = gs.get_building_privilege_page(x, y, save_dir=str(save_dir))

    assert len(blocks) == 1 and blocks[0]["ms_gush"] == "6638"
    assert len(parcels) == 1 and parcels[0]["ms_chelka"] == "572"
    assert result is not None
    assert result["block"] == "6638"
    assert result["parcel"] == "572"
    assert result["content_type"] == "pdf"
    assert (save_dir / "privilege_block_6638_parcel_572.pdf").exists()


def test_block_parcel_extraction():
    gs = TelAvivGS()
    x, y = 184320.94, 668548.65
    blocks_payload = {"features": [{"attributes": {"ms_gush": "6638"}}]}
    parcels_payload = {"features": [{"attributes": {"ms_chelka": "572"}}]}

    def fake_get(url, params=None, headers=None, timeout=30, allow_redirects=True):
        if "MapServer/525/query" in url:
            return _make_response(json_payload=blocks_payload)
        if "MapServer/524/query" in url:
            return _make_response(json_payload=parcels_payload)
        raise AssertionError(f"Unexpected URL: {url}")

    with mock.patch("requests.get", side_effect=fake_get):
        result = gs.get_block_parcel_info(x, y)

    assert result["success"] is True
    assert result["block"] == "6638"
    assert result["parcel"] == "572"
