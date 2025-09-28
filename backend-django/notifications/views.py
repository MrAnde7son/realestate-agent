"""Views handling notification webhooks and delivery updates."""
from __future__ import annotations

import hmac
import json
import logging
import os
from hashlib import sha256
from typing import Any, Dict, Iterable

from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


def _verify_signature(request: HttpRequest) -> bool:
    secret = os.getenv("RESEND_WEBHOOK_SECRET", "")
    if not secret:
        return True

    header = request.headers.get("X-Resend-Signature")
    if not header:
        logger.warning("Missing X-Resend-Signature header on webhook request")
        return False

    parts: Dict[str, str] = {}
    for item in header.split(","):
        if "=" in item:
            key, value = item.split("=", 1)
            parts[key.strip()] = value.strip()
    signature = parts.get("v1", header.strip())

    expected = hmac.new(secret.encode("utf-8"), msg=request.body, digestmod=sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        logger.warning("Invalid Resend webhook signature")
        return False
    return True


def _normalize_events(payload: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "events" in payload:
        events = payload.get("events")
        if isinstance(events, list):
            return events
    return [payload]


@csrf_exempt
@require_POST
def resend_webhook(request: HttpRequest) -> HttpResponse:
    """Process webhook events from Resend.

    The handler records bounce/complaint events and disables ``notify_email``
    on matching users to avoid repeated delivery failures. Other events are
    logged for observability.
    """

    if not _verify_signature(request):
        return HttpResponse(status=401)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        logger.exception("Invalid JSON payload from Resend")
        return JsonResponse({"error": "invalid payload"}, status=400)

    processed = 0
    User = get_user_model()

    for event in _normalize_events(payload):
        event_type = (event.get("type") or event.get("event") or "").lower()
        data = event.get("data") or {}
        email = (
            data.get("email")
            or data.get("to")
            or data.get("recipient")
            or event.get("to")
        )

        logger.info("Resend webhook received", extra={"event": event_type, "email": email})

        if event_type in {"bounce", "complaint", "delivery.attempt_failed", "hard_bounce"} and email:
            updated = User.objects.filter(email__iexact=email).update(notify_email=False)
            if updated:
                logger.info("Disabled email notifications for %s due to %s", email, event_type)
        processed += 1

    return JsonResponse({"status": "ok", "processed": processed})
