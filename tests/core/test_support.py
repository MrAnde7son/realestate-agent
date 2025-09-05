import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from core.models import SupportTicket, ConsultationRequest


@pytest.mark.django_db
def test_support_contact():
    User = get_user_model()
    user = User.objects.create_user(username="u1", email="u1@example.com", password="pass")
    token = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    resp = client.post("/api/support/contact", {"subject": "s", "message": "m"}, format="json")
    assert resp.status_code == 201
    assert SupportTicket.objects.filter(user=user, kind="contact").exists()


@pytest.mark.django_db
def test_support_bug_with_file(tmp_path):
    User = get_user_model()
    user = User.objects.create_user(username="u2", email="u2@example.com", password="pass")
    token = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    uploaded = SimpleUploadedFile("bug.txt", b"bug", content_type="text/plain")
    resp = client.post(
        "/api/support/bug",
        {"message": "bug", "attachment": uploaded},
        format="multipart",
    )
    assert resp.status_code == 201
    ticket = SupportTicket.objects.get(id=resp.json()["id"])
    assert ticket.attachment.name.endswith(".txt")


@pytest.mark.django_db
def test_support_consultation():
    User = get_user_model()
    user = User.objects.create_user(username="u3", email="u3@example.com", password="pass")
    token = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    payload = {
        "full_name": "A",
        "email": "a@example.com",
        "phone": "123",
        "preferred_time": "now",
        "channel": "phone",
        "topic": "t",
    }
    resp = client.post("/api/support/consultation", payload, format="json")
    assert resp.status_code == 201
    assert ConsultationRequest.objects.filter(user=user, email="a@example.com").exists()
