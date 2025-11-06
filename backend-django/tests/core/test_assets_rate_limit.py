import json

from django.test import RequestFactory

from core import views
from core.models import Asset
from django.core.cache import cache


class DummyTask:
    def delay(self, asset_id):
        pass


def make_request(factory):
    payload = {
        "scope": {"type": "address", "city": "City"},
        "city": "City",
        "street": "Main",
        "number": 5,
    }
    return factory.post(
        "/api/assets", data=json.dumps(payload), content_type="application/json"
    )


def test_assets_post_rate_limited(monkeypatch):
    factory = RequestFactory()
    cache.clear()
    views._assets_rate_limit.clear()

    monkeypatch.setattr(views, "run_data_pipeline", DummyTask())

    # Mock find_existing_asset to return None (no existing asset found)
    from core.services import asset_deduplication
    monkeypatch.setattr(asset_deduplication, "find_existing_asset", lambda *args, **kwargs: None)

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
