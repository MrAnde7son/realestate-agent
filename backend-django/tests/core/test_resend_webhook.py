"""Tests for notification webhook handling."""
from __future__ import annotations

import hmac
import json
from hashlib import sha256

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
def test_resend_webhook_updates_user(client, monkeypatch):
    user = get_user_model().objects.create_user(email="user@example.com", username="user", password="pw")
    assert user.notify_email is True

    secret = "topsecret"
    monkeypatch.setenv("RESEND_WEBHOOK_SECRET", secret)

    payload = {
        "type": "bounce",
        "data": {"email": "user@example.com"},
    }
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, sha256).hexdigest()

    response = client.post(
        reverse("resend_webhook"),
        data=body,
        content_type="application/json",
        HTTP_X_RESEND_SIGNATURE=f"v1={signature}",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.notify_email is False
    assert response.json()["processed"] == 1


@pytest.mark.django_db
def test_resend_webhook_rejects_bad_signature(client, monkeypatch):
    monkeypatch.setenv("RESEND_WEBHOOK_SECRET", "secret")

    payload = {"type": "delivery", "data": {"email": "noreply@example.com"}}
    body = json.dumps(payload).encode("utf-8")

    response = client.post(
        reverse("resend_webhook"),
        data=body,
        content_type="application/json",
        HTTP_X_RESEND_SIGNATURE="v1=invalid",
    )

    assert response.status_code == 401
