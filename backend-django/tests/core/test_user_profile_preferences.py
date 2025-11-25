import uuid

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
def test_update_profile_persists_preferences():
    User = get_user_model()
    uid = uuid.uuid4().hex
    user = User.objects.create_user(
        username=f"tester_{uid}", email=f"{uid}@example.com", password="pass123"
    )

    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "preference_city": "תל אביב",
        "preference_streets": "רוטשילד, דיזינגוף",
        "preference_asset_type": "דירה",
        "preference_area_min": 70,
        "preference_area_max": 120,
        "preference_floor": "3-5",
        "preference_notes": "קרוב לפארק",
    }

    resp = client.put("/api/auth/update-profile", payload, format="json")
    assert resp.status_code == 200

    user.refresh_from_db()
    assert user.preference_city == payload["preference_city"]
    assert user.preference_streets == payload["preference_streets"]
    assert user.preference_asset_type == payload["preference_asset_type"]
    assert user.preference_area_min == payload["preference_area_min"]
    assert user.preference_area_max == payload["preference_area_max"]
    assert user.preference_floor == payload["preference_floor"]
    assert user.preference_notes == payload["preference_notes"]

    data = resp.json()["user"]
    for key, value in payload.items():
        assert data[key] == value


@pytest.mark.django_db
def test_update_profile_validates_area_range():
    User = get_user_model()
    uid = uuid.uuid4().hex
    user = User.objects.create_user(
        username=f"tester_{uid}", email=f"{uid}@example.com", password="pass123"
    )

    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    payload = {
        "preference_area_min": 150,
        "preference_area_max": 100,
    }

    resp = client.put("/api/auth/update-profile", payload, format="json")
    assert resp.status_code == 400

    user.refresh_from_db()
    assert user.preference_area_min is None
    assert user.preference_area_max is None
