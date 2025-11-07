"""Tests for managing LLM-related user settings."""

import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
def test_user_can_store_llm_keys_via_settings_api():
    """Users can persist LLM API keys and see indicator flags."""
    User = get_user_model()
    uid = uuid.uuid4().hex
    user = User.objects.create_user(
        username=f"tester_{uid}",
        email=f"{uid}@example.com",
        password="pass123",
    )

    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    payload = {
        "openai_api_key": "sk-openai-1234567890",
        "gemini_api_key": "gm-gemini-1234567890",
        "groq_api_key": "gr-groq-1234567890",
        "llm_provider_preference": "openai",
    }
    response = client.put("/api/settings", payload, format="json")
    assert response.status_code == 200

    user.refresh_from_db()
    assert user.openai_api_key == "sk-openai-1234567890"
    assert user.gemini_api_key == "gm-gemini-1234567890"
    assert user.groq_api_key == "gr-groq-1234567890"
    assert user.llm_provider_preference == "openai"

    response = client.get("/api/settings")
    data = response.json()
    assert data["has_openai_key"] is True
    assert data["has_gemini_key"] is True
    assert data["has_groq_key"] is True
    assert data["llm_provider_preference"] == "openai"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload",
    [
        {"openai_api_key": "short"},
        {"gemini_api_key": "tiny"},
        {"groq_api_key": "small"},
    ],
)
def test_invalid_llm_keys_rejected(payload):
    """LLM keys must meet minimum length requirements."""
    User = get_user_model()
    uid = uuid.uuid4().hex
    user = User.objects.create_user(
        username=f"tester_{uid}",
        email=f"{uid}@example.com",
        password="pass123",
    )

    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    response = client.put("/api/settings", payload, format="json")
    assert response.status_code == 400
    assert "Invalid" in response.json()["error"]
