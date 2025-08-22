import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture(autouse=True)
def _setup_db():
    call_command("migrate", run_syncdb=True, verbosity=0)
    call_command("flush", verbosity=0, interactive=False)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(
        username="tester", email="tester@example.com", password="pass1234"
    )


def test_assets_requires_authentication(api_client):
    payload = {
        "scope": {"type": "address", "city": "תל אביב"},
        "city": "תל אביב",
        "street": "הרצל",
        "number": 1,
    }
    response = api_client.post("/api/assets/", payload, format="json")
    assert response.status_code == 401


def test_assets_allows_authenticated_post(api_client, user):
    token = RefreshToken.for_user(user).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    payload = {
        "scope": {"type": "address", "city": "תל אביב"},
        "city": "תל אביב",
        "street": "הרצל",
        "number": 1,
    }
    response = api_client.post("/api/assets/", payload, format="json")
    assert response.status_code == 201
    assert "id" in response.json()
