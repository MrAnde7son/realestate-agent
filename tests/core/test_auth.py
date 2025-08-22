import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_alerts_requires_login(api_client):
    response = api_client.post("/api/alerts/", {"criteria": {}}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_create_asset_requires_login(api_client):
    payload = {"scope": {"type": "city", "value": "Tel Aviv"}, "city": "Tel Aviv"}
    response = api_client.post("/api/assets/", payload, format="json")
    assert response.status_code == 401
