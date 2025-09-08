import json

from core import views
from core.models import Asset
from django.test import RequestFactory
import pytest


class DummyTask:
    def __init__(self):
        self.calls = []
        self.job_id = "job-123"

    def delay(self, asset_id, max_pages=1):
        self.calls.append((asset_id, max_pages))
        return type("AsyncResult", (), {"id": self.job_id})()


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
    # For DRF Response, access data directly instead of parsing content
    data = response.data
    assert data["job_id"] == dummy.job_id


@pytest.mark.django_db
def test_assets_delete_removes_asset():
    factory = RequestFactory()
    asset = Asset.objects.create(scope_type="address", city="City")
    request = factory.delete(
        "/api/assets/", data=json.dumps({"assetId": asset.id}), content_type="application/json"
    )

    response = views.assets(request)

    assert response.status_code == 200
    with pytest.raises(Asset.DoesNotExist):
        Asset.objects.get(id=asset.id)
