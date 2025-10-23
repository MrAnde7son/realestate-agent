import json

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from core import views
from core.models import Asset


class DummyTask:
    def __init__(self):
        self.calls = []
        self.job_id = "bulk-job"

    def delay(self, asset_id, max_pages=1):
        self.calls.append((asset_id, max_pages))
        return type("AsyncResult", (), {"id": self.job_id})()


@pytest.mark.django_db
def test_bulk_action_requires_authentication():
    factory = APIRequestFactory()
    asset = Asset.objects.create(scope_type="address", city="City", street="Main", number=1)

    request = factory.post(
        "/api/assets/bulk-action",
        data=json.dumps({"action": "sync", "assetIds": [asset.id]}),
        content_type="application/json",
    )

    response = views.assets_bulk_action(request)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_bulk_delete_requires_admin():
    factory = APIRequestFactory()
    asset = Asset.objects.create(scope_type="address", city="City", street="Main", number=2)

    user = get_user_model().objects.create_user(
        email="user@example.com",
        username="user",
        password="password",
        role="broker",
    )

    request = factory.post(
        "/api/assets/bulk-action",
        data=json.dumps({"action": "delete", "assetIds": [asset.id]}),
        content_type="application/json",
    )
    force_authenticate(request, user=user)

    response = views.assets_bulk_action(request)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Asset.objects.filter(id=asset.id).exists()


@pytest.mark.django_db
def test_bulk_delete_removes_assets_for_admin():
    factory = APIRequestFactory()
    assets = [
        Asset.objects.create(scope_type="address", city="City", street="Main", number=idx)
        for idx in (10, 11)
    ]

    admin_user = get_user_model().objects.create_user(
        email="bulk-admin@example.com",
        username="bulk-admin",
        password="password",
        role="admin",
        is_superuser=True,
        is_staff=True,
    )

    request = factory.post(
        "/api/assets/bulk-action",
        data=json.dumps({
            "action": "delete",
            "assetIds": [asset.id for asset in assets],
        }),
        content_type="application/json",
    )
    force_authenticate(request, user=admin_user)

    response = views.assets_bulk_action(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["success"] == 2
    assert Asset.objects.filter(id__in=[asset.id for asset in assets]).count() == 0


@pytest.mark.django_db
def test_bulk_sync_triggers_pipeline(monkeypatch, settings):
    factory = APIRequestFactory()
    assets = [
        Asset.objects.create(
            scope_type="address",
            city="City",
            street="Sync",
            number=idx,
            normalized_address=f"Sync {idx}",
        )
        for idx in (20, 21)
    ]

    user = get_user_model().objects.create_user(
        email="sync@example.com",
        username="sync-user",
        password="password",
        role="broker",
    )

    settings.CELERY_BROKER_URL = "redis://localhost:6379/0"
    dummy = DummyTask()
    monkeypatch.setattr("core.tasks.run_data_pipeline", dummy)

    request = factory.post(
        "/api/assets/bulk-action",
        data=json.dumps({
            "action": "sync",
            "assetIds": [asset.id for asset in assets],
        }),
        content_type="application/json",
    )
    force_authenticate(request, user=user)

    response = views.assets_bulk_action(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["success"] == 2
    assert dummy.calls == [(assets[0].id, 1), (assets[1].id, 1)]
    for asset in Asset.objects.filter(id__in=[asset.id for asset in assets]):
        asset.refresh_from_db()
        assert asset.status == "syncing"


@pytest.mark.django_db
def test_bulk_report_generation(monkeypatch):
    factory = APIRequestFactory()
    assets = [
        Asset.objects.create(scope_type="address", city="City", street="Report", number=idx)
        for idx in (30, 31)
    ]

    user = get_user_model().objects.create_user(
        email="bulk-report@example.com",
        username="bulk-report-user",
        password="password",
        role="broker",
    )

    class DummyReport:
        def __init__(self, asset_id):
            self.id = asset_id + 1000
            self.filename = f"r{asset_id}.pdf"

    created_reports = []

    def fake_create(asset_id, sections):
        report = DummyReport(asset_id)
        created_reports.append((asset_id, tuple(sections)))
        return report

    def fake_generate(report):
        return True

    monkeypatch.setattr(views.report_service, "create_report", fake_create)
    monkeypatch.setattr(views.report_service, "generate_pdf", fake_generate)

    request = factory.post(
        "/api/assets/bulk-action",
        data=json.dumps({
            "action": "create_report",
            "assetIds": [asset.id for asset in assets],
        }),
        content_type="application/json",
    )
    force_authenticate(request, user=user)

    response = views.assets_bulk_action(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["success"] == 2
    assert len(created_reports) == 2

