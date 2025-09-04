import json
from datetime import timedelta

import pytest
from django.test import RequestFactory
from django.utils import timezone
from django.contrib.auth import get_user_model

from core import views
from core.models import Asset
from core.tasks import cleanup_demo_data


@pytest.mark.django_db
def test_demo_start_creates_demo_user_and_assets():
    factory = RequestFactory()
    request = factory.post("/api/demo/start/")
    response = views.demo_start(request)
    assert response.status_code == 200
    data = response.data
    assert "access_token" in data
    User = get_user_model()
    user = User.objects.get(is_demo=True)
    assets = Asset.objects.filter(is_demo=True)
    assert assets.count() >= 2
    cities = {a.city for a in assets}
    assert len(cities) >= 2
    assert user.email.endswith("@demo.local")


@pytest.mark.django_db
def test_cleanup_demo_data_removes_old_entries():
    User = get_user_model()
    user = User.objects.create_user(
        username="old_demo",
        email="old@demo.local",
        password="x",
        is_demo=True,
    )
    asset = Asset.objects.create(scope_type="address", city="A", is_demo=True, status="ready")
    old = timezone.now() - timedelta(days=2)
    User.objects.filter(id=user.id).update(created_at=old)
    Asset.objects.filter(id=asset.id).update(created_at=old)

    cleanup_demo_data()

    assert User.objects.filter(id=user.id).count() == 0
    assert Asset.objects.filter(id=asset.id).count() == 0
