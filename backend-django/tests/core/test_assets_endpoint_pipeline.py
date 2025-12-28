import json

from core import views
from core.models import Asset
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
import pytest


class DummyTask:
    def __init__(self):
        self.calls = []
        self.job_id = "job-123"

    def delay(self, asset_id):
        self.calls.append((asset_id))
        return type("AsyncResult", (), {"id": self.job_id})()

    def __call__(self, asset_id):
        """Called when run_data_pipeline is called directly (not as Celery task)"""
        self.calls.append((asset_id))
        return []


def test_assets_post_triggers_pipeline(monkeypatch):
    factory = APIRequestFactory()
    payload = {
        "scope": {"type": "address", "city": "City"},
        "city": "City",
        "street": "Main",
        "number": 5,
    }
    request = factory.post(
        "/api/assets", data=json.dumps(payload), content_type="application/json"
    )

    dummy_asset = type("Asset", (), {"id": 1})()
    monkeypatch.setattr(Asset.objects, "create", lambda **kw: dummy_asset)

    # Mock find_existing_asset to return None (no existing asset found)
    from core.services import asset_deduplication

    monkeypatch.setattr(
        asset_deduplication, "find_existing_asset", lambda *args, **kwargs: None
    )

    # Mock Celery settings to make it appear available
    from django.conf import settings

    monkeypatch.setattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")

    dummy = DummyTask()
    monkeypatch.setattr(views, "run_data_pipeline", dummy)

    response = views.assets(request)

    assert response.status_code == 201
    # Ensure the Celery task was called with the new asset ID
    assert dummy.calls == [(dummy_asset.id)]
    # For DRF Response, access data directly instead of parsing content
    data = response.data
    # Now that Celery is mocked as available, job_id should be returned
    assert data["job_id"] == dummy.job_id


@pytest.mark.django_db
def test_assets_delete_requires_admin_user():
    factory = APIRequestFactory()
    asset = Asset.objects.create(scope_type="address", city="City")
    user = get_user_model().objects.create_user(
        email="user@example.com",
        username="user",
        password="password",
        role="broker",
    )
    request = factory.delete(
        "/api/assets",
        data=json.dumps({"assetId": asset.id}),
        content_type="application/json",
    )
    force_authenticate(request, user=user)

    response = views.assets(request)

    assert response.status_code == 403
    assert Asset.objects.filter(id=asset.id).exists()


@pytest.mark.django_db
def test_assets_delete_removes_asset_for_admin():
    factory = APIRequestFactory()
    asset = Asset.objects.create(scope_type="address", city="City")
    admin_user = get_user_model().objects.create_user(
        email="admin-delete@example.com",
        username="admin-delete",
        password="password",
        role="admin",
        is_superuser=True,
        is_staff=True,
    )
    request = factory.delete(
        "/api/assets",
        data=json.dumps({"assetId": asset.id}),
        content_type="application/json",
    )
    force_authenticate(request, user=admin_user)

    response = views.assets(request)

    assert response.status_code == 200
    with pytest.raises(Asset.DoesNotExist):
        Asset.objects.get(id=asset.id)
