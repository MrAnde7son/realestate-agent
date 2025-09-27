"""Tests for the custom Resend email backend."""
from __future__ import annotations

import importlib
import logging
from typing import Dict

import pytest
from celery.exceptions import Retry
from django.core.mail import EmailMultiAlternatives

from core.tasks import send_notification_email


@pytest.fixture
def reload_backend(monkeypatch, settings):
    """Reload the backend after mutating environment variables."""

    settings.EMAIL_BACKEND = "core.email_backends.resend_backend.ResendEmailBackend"

    def _reload(*, api_key: str | None = "test_api_key", **env: str) -> object:
        if api_key is None:
            monkeypatch.delenv("RESEND_API_KEY", raising=False)
        else:
            monkeypatch.setenv("RESEND_API_KEY", api_key)

        monkeypatch.setenv("RESEND_FROM", env.pop("RESEND_FROM", "no-reply@example.com"))
        for key, value in env.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, value)

        import core.email_backends.resend_backend as backend

        return importlib.reload(backend)

    return _reload


def _mock_response(payload: Dict[str, str]):
    class Response:
        ok = True
        status_code = 200
        text = ""

        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

    return Response(payload)


@pytest.mark.django_db
def test_send_html_and_text(monkeypatch, reload_backend):
    """HTML alternatives are delivered successfully via the REST client."""

    backend = reload_backend()
    backend.resend = None

    def fake_post(*args, **kwargs):
        return _mock_response({"id": "email_123"})

    monkeypatch.setattr(backend.requests, "post", fake_post)

    message = EmailMultiAlternatives("Subject", "Plain body", to=["user@example.com"])
    message.attach_alternative("<strong>Hi</strong>", "text/html")
    sent = message.send()
    assert sent == 1


@pytest.mark.django_db
def test_attachments_trim_when_over_limit(monkeypatch, reload_backend):
    """Attachments over the configured limit are dropped with a warning."""

    monkeypatch.setenv("RESEND_ATTACHMENT_LIMIT_BYTES", "5")
    backend = reload_backend()
    backend.resend = None

    captured = {}

    def fake_post(*args, **kwargs):
        captured.update(kwargs)
        return _mock_response({"id": "email_456"})

    monkeypatch.setattr(backend.requests, "post", fake_post)

    message = EmailMultiAlternatives("Subject", "Plain body", to=["user@example.com"])
    message.attach("a.txt", b"0123456789", "text/plain")
    sent = message.send()

    assert sent == 1
    payload_str = captured.get("data", "{}")
    assert "attachments" not in payload_str


@pytest.mark.django_db
def test_sandbox_blocks_external_recipients(monkeypatch, reload_backend, caplog):
    """Sandbox mode prevents sending to non-whitelisted addresses."""

    backend = reload_backend(RESEND_SANDBOX="true")
    backend.resend = None

    caplog.set_level(logging.INFO)

    message = EmailMultiAlternatives("Subject", "Plain body", to=["user@outside.com"])
    sent = message.send()
    assert sent == 0
    assert any("RESEND_SANDBOX" in record.message for record in caplog.records)


def test_send_notification_email_retries(monkeypatch):
    """The Celery task retries when delivery raises an exception."""

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("core.tasks.send_email", boom)

    with pytest.raises(Retry):
        send_notification_email.apply(args=("Hi", ["test@example.com"]), throw=True)


@pytest.mark.django_db
def test_sdk_delivery_success(monkeypatch, reload_backend):
    """When the Resend SDK is available, it is used for delivery."""

    backend = reload_backend()

    class StubResend:
        payload: Dict[str, object] | None = None

        class Emails:
            @staticmethod
            def send(payload):
                StubResend.payload = payload
                return {"id": "email_789"}

    backend.resend = StubResend

    message = EmailMultiAlternatives("Subject", "Plain body", to=["user@example.com"])
    sent = message.send()

    assert sent == 1
    assert StubResend.payload["to"] == ["user@example.com"]


@pytest.mark.django_db
def test_console_fallback_without_api_key(monkeypatch, reload_backend, caplog):
    """Emails are logged to the console when no API key is configured."""

    backend = reload_backend(api_key=None, EMAIL_FALLBACK_TO_CONSOLE="true")
    backend.resend = None

    caplog.set_level(logging.INFO)

    message = EmailMultiAlternatives("Subject", "Plain body", to=["user@example.com"])
    sent = message.send()

    assert sent == 1
    assert "[EMAIL:CONSOLE]" in caplog.text
