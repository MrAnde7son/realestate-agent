import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_admin_can_access_analytics(django_user_model):
    admin = django_user_model.objects.create_user(
        username="adm",
        email="adm@example.com",
        password="pw",
        role="admin",
    )
    client = APIClient()
    client.force_authenticate(admin)
    r = client.get("/api/analytics/timeseries")
    assert r.status_code == 200


@pytest.mark.django_db
def test_private_cannot_access_analytics(django_user_model):
    user = django_user_model.objects.create_user(
        username="mem",
        email="mem@example.com",
        password="pw",
        role="private",
    )
    client = APIClient()
    client.force_authenticate(user)
    r = client.get("/api/analytics/timeseries")
    assert r.status_code in (401, 403)
