import json

from core import views
from core.models import Asset
from django.test import RequestFactory


class DummyTask:
    def __init__(self):
        self.calls = []

    def delay(self, asset_id, max_pages=1):
        self.calls.append((asset_id, max_pages))


def test_assets_post_triggers_pipeline(monkeypatch):
    factory = RequestFactory()
    payload = {
        "scope": {"type": "address", "city": "City"},
        "city": "City",
        "street": "Main",
        "number": 5,
    }
    request = factory.post(
        "/api/assets/", data=json.dumps(payload), content_type="application/json"
    )

    dummy_asset = type("Asset", (), {"id": 1})()
    monkeypatch.setattr(Asset.objects, "create", lambda **kw: dummy_asset)

    dummy = DummyTask()
    monkeypatch.setattr(views, "run_data_pipeline", dummy)

    response = views.assets(request)

    assert response.status_code == 201
    # Ensure the Celery task was called with the new asset ID
    assert dummy.calls == [(dummy_asset.id, 1)]
