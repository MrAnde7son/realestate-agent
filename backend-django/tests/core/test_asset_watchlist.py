import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Asset, AssetWatchlistEntry


@pytest.mark.django_db
def test_watch_endpoint_adds_and_removes_asset():
    user = get_user_model().objects.create_user(
        email="singlewatch@example.com",
        username="singlewatch",
        password="password",
    )
    asset = Asset.objects.create(scope_type="address", city="City", number=1)

    client = APIClient()
    client.force_authenticate(user=user)

    add_response = client.post(f"/api/assets/{asset.id}/watch")
    assert add_response.status_code == status.HTTP_201_CREATED
    assert AssetWatchlistEntry.objects.filter(user=user, asset=asset).exists()
    assert add_response.json()["watched"] is True

    repeat_response = client.post(f"/api/assets/{asset.id}/watch")
    assert repeat_response.status_code == status.HTTP_200_OK
    assert AssetWatchlistEntry.objects.filter(user=user, asset=asset).count() == 1

    remove_response = client.delete(f"/api/assets/{asset.id}/watch")
    assert remove_response.status_code == status.HTTP_200_OK
    assert not AssetWatchlistEntry.objects.filter(user=user, asset=asset).exists()
    assert remove_response.json()["watched"] is False


@pytest.mark.django_db
def test_watch_endpoint_requires_authentication():
    asset = Asset.objects.create(scope_type="address", city="City", number=42)
    client = APIClient()

    response = client.post(f"/api/assets/{asset.id}/watch")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
