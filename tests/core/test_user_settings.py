"""Tests for the user settings API."""


import uuid
import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from core.constants import DEFAULT_REPORT_SECTIONS


@pytest.mark.django_db
def test_user_settings_get_and_update():
    User = get_user_model()
    uid = uuid.uuid4().hex
    user = User.objects.create_user(
        username=f"tester_{uid}", email=f"{uid}@example.com", password="pass123"
    )

    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    # Check default settings
    resp = client.get("/api/settings/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["timezone"] == "UTC"
    assert data["language"] == "en"
    assert data["report_sections"] == DEFAULT_REPORT_SECTIONS

    # Update some settings
    payload = {
        "timezone": "Asia/Jerusalem",
        "language": "he",
        "notify_email": False,
        "report_sections": ["summary", "plans"],
    }
    resp = client.put("/api/settings/", payload, format="json")
    assert resp.status_code == 200

    user.refresh_from_db()
    assert user.timezone == "Asia/Jerusalem"
    assert user.language == "he"
    assert user.notify_email is False
    assert user.report_sections == ["summary", "plans"]

