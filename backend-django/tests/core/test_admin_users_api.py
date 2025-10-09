import pytest
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_admin_can_list_users_with_filters(django_user_model):
    admin = django_user_model.objects.create_user(
        username="list-admin",
        email="list-admin@example.com",
        password="pw",
        role="admin",
    )
    active_user = django_user_model.objects.create_user(
        username="filters-broker",
        email="filters-broker@example.com",
        password="pw",
        role="broker",
        first_name="Bella",
        last_name="Broker",
        is_active=True,
    )
    inactive_user = django_user_model.objects.create_user(
        username="filters-investor",
        email="filters-investor@example.com",
        password="pw",
        role="investor",
        first_name="Ian",
        last_name="Investor",
        is_active=False,
    )
    old_user = django_user_model.objects.create_user(
        username="filters-viewer",
        email="filters-viewer@example.com",
        password="pw",
        role="viewer",
    )
    old_user.created_at = timezone.now() - timezone.timedelta(days=10)
    old_user.save(update_fields=["created_at"])

    client = APIClient()
    client.force_authenticate(admin)

    response = client.get(
        "/api/admin/users/",
        {
            "search": "bell",
            "role": "broker",
            "status": "active",
            "ordering": "name",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "data" in payload and "pagination" in payload
    assert len(payload["data"]) == 1
    assert payload["data"][0]["email"] == "filters-broker@example.com"

    registration_date = timezone.now().date().isoformat()
    response = client.get(
        "/api/admin/users/",
        {
            "registration_date": registration_date,
            "status": "inactive",
        },
    )
    assert response.status_code == 200
    result = response.json()
    emails = [user["email"] for user in result["data"]]
    assert "filters-investor@example.com" in emails
    assert "filters-viewer@example.com" not in emails


@pytest.mark.django_db
def test_admin_create_update_and_delete_user(django_user_model):
    admin = django_user_model.objects.create_user(
        username="manage-admin",
        email="manage-admin@example.com",
        password="pw",
        role="admin",
    )

    client = APIClient()
    client.force_authenticate(admin)

    create_response = client.post(
        "/api/admin/users/",
        {
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "role": "broker",
            "organization_name": "Nadlaner",
        },
        format="json",
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["email"] == "new@example.com"
    assert created["organization_name"] == "Nadlaner"
    assert "temporary_password" in created

    user_id = created["id"]
    patch_response = client.patch(
        f"/api/admin/users/{user_id}/",
        {"role": "appraiser", "phone_number": "+97250000000"},
        format="json",
    )
    assert patch_response.status_code == 200
    patched = patch_response.json()["data"]
    assert patched["role"] == "appraiser"
    assert patched["phone_number"] == "+97250000000"

    deactivate = client.post(f"/api/admin/users/{user_id}/deactivate/")
    assert deactivate.status_code == 200
    assert deactivate.json()["data"]["is_active"] is False

    activate = client.post(f"/api/admin/users/{user_id}/activate/")
    assert activate.status_code == 200
    assert activate.json()["data"]["is_active"] is True

    reset = client.post(f"/api/admin/users/{user_id}/reset-password/")
    assert reset.status_code == 200
    assert "temporary_password" in reset.json()["data"]

    delete_response = client.delete(f"/api/admin/users/{user_id}/")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "User deleted"


@pytest.mark.django_db
def test_non_admin_cannot_access_admin_users(django_user_model):
    user = django_user_model.objects.create_user(
        username="guard-viewer",
        email="guard-viewer@example.com",
        password="pw",
        role="viewer",
    )
    client = APIClient()
    client.force_authenticate(user)

    response = client.get("/api/admin/users/")
    assert response.status_code in {401, 403}
