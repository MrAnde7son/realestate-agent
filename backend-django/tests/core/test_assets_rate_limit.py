import json

import pytest
from django.test import RequestFactory

from core import views
from core.models import Asset
from django.core.cache import cache


class DummyTask:
    def delay(self, asset_id, max_pages=1):
        pass


def make_request(factory):
    payload = {
        "scope": {"type": "address", "city": "City"},
        "city": "City",
        "street": "Main",
        "number": 5,
    }
    return factory.post(
        "/api/assets/", data=json.dumps(payload), content_type="application/json"
    )


def test_assets_post_rate_limited(monkeypatch):
    factory = RequestFactory()
    cache.clear()
    views._assets_rate_limit.clear()

    monkeypatch.setattr(views, "run_data_pipeline", DummyTask())

    counter = {"value": 0}

    def create_asset(**kwargs):
        counter["value"] += 1
        return type("Asset", (), {"id": counter["value"]})()

    monkeypatch.setattr(Asset.objects, "create", create_asset)

    for _ in range(views.ASSETS_POST_LIMIT):
        response = views.assets(make_request(factory))
        assert response.status_code == 201

    response = views.assets(make_request(factory))
    assert response.status_code == 429
