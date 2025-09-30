"""Custom Django email backend powered by Resend."""
from __future__ import annotations

"""Django email backend that delivers mail via Resend."""

import base64
import json
import logging
import os
from typing import Any, Dict, Iterable, List, Optional

try:  # pragma: no cover - import guard for optional SDK
    import resend  # type: ignore
except Exception:  # pragma: no cover - SDK may be unavailable
    resend = None  # type: ignore

import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage, EmailMultiAlternatives

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM = os.getenv("RESEND_FROM", "")
RESEND_REPLY_TO = os.getenv("RESEND_REPLY_TO", "")
RESEND_SANDBOX = os.getenv("RESEND_SANDBOX", "false").lower() == "true"
EMAIL_FALLBACK_TO_CONSOLE = os.getenv("EMAIL_FALLBACK_TO_CONSOLE", "false").lower() == "true"
RESEND_ENDPOINT = "https://api.resend.com/emails"
ATTACHMENT_LIMIT_BYTES = int(os.getenv("RESEND_ATTACHMENT_LIMIT_BYTES", str(20 * 1024 * 1024)))


def _to_str_list(values: Optional[Iterable[str]]) -> List[str]:
    return [str(v) for v in values or [] if v]


def _clean_tags(raw: Any) -> Optional[List[Dict[str, str]]]:
    if not raw:
        return None
    tags: List[Dict[str, str]] = []
    if isinstance(raw, dict):
        for name, value in raw.items():
            tags.append({"name": str(name), "value": str(value)})
    elif isinstance(raw, (list, tuple)):
        for entry in raw:
            if isinstance(entry, dict) and "name" in entry and "value" in entry:
                tags.append({"name": str(entry["name"]), "value": str(entry["value"])})
            else:
                tags.append({"name": str(entry), "value": "true"})
    else:
        tags.append({"name": str(raw), "value": "true"})
    return tags


def _attachments(dj_email: EmailMessage) -> List[Dict[str, Any]]:
    attachments: List[Dict[str, Any]] = []
    total_size = 0
    for attachment in dj_email.attachments:
        if isinstance(attachment, tuple) and len(attachment) >= 2:
            filename = attachment[0]
            content = attachment[1]
            mimetype = attachment[2] if len(attachment) >= 3 else "application/octet-stream"
            if isinstance(content, str):
                content_bytes = content.encode("utf-8")
            else:
                content_bytes = content
        else:
            payload = attachment.get_payload(decode=True)
            content_bytes = payload or b""
            filename = getattr(attachment, "get_filename", lambda: "attachment")() or "attachment"
            mimetype = (
                attachment.get_content_type() if hasattr(attachment, "get_content_type") else "application/octet-stream"
            )
        total_size += len(content_bytes)
        attachments.append({
            "filename": filename,
            "content": content_bytes,
            "content_type": mimetype or "application/octet-stream",
        })
    if total_size > ATTACHMENT_LIMIT_BYTES:
        logger.warning(
            "Attachment payload (%s bytes) exceeds limit (%s). Sending without attachments.",
            total_size,
            ATTACHMENT_LIMIT_BYTES,
        )
        return []
    return attachments


def _deliver_via_rest(payload: Dict[str, Any]) -> bool:
    headers = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}
    prepared = dict(payload)
    if prepared.get("attachments"):
        converted: List[Dict[str, str]] = []
        for att in prepared["attachments"]:
            converted.append({
                "filename": att["filename"],
                "content": base64.b64encode(att["content"]).decode("ascii"),
                "content_type": att.get("content_type") or "application/octet-stream",
            })
        prepared["attachments"] = converted
    response = requests.post(RESEND_ENDPOINT, headers=headers, data=json.dumps(prepared), timeout=20)
    if response.ok:
        body = response.json()
        if body.get("id"):
            return True
    logger.error("Resend REST delivery failed: %s %s", response.status_code, response.text)
    return False


class ResendEmailBackend(BaseEmailBackend):
    """Django Email Backend for Resend with console fallback."""

    def send_messages(self, email_messages: List[EmailMessage]) -> int:
        if not email_messages:
            return 0

        if not RESEND_FROM:
            logger.warning("RESEND_FROM is not configured. Messages may be rejected.")

        use_sdk = resend is not None and bool(RESEND_API_KEY)
        if use_sdk:
            resend.api_key = RESEND_API_KEY

        sent_count = 0
        for message in email_messages:
            if RESEND_SANDBOX:
                allowed_fragments = {"@example.", "@test.", "@localhost", "@local", "@nadlaner.local"}
                recipients = _to_str_list(message.to)
                if not any(any(fragment in recipient for fragment in allowed_fragments) for recipient in recipients):
                    logger.info("RESEND_SANDBOX active - blocking send to %s", recipients)
                    continue

            payload = self._build_payload(message)

            if not RESEND_API_KEY:
                if EMAIL_FALLBACK_TO_CONSOLE:
                    self._log_to_console(message)
                    sent_count += 1
                else:
                    logger.error("RESEND_API_KEY missing and EMAIL_FALLBACK_TO_CONSOLE disabled. Email dropped.")
                continue

            try:
                if use_sdk:
                    result = resend.Emails.send(payload)  # type: ignore[attr-defined]
                    if isinstance(result, dict) and result.get("id"):
                        sent_count += 1
                    else:
                        logger.error("Resend SDK returned error: %s", result)
                else:
                    if _deliver_via_rest(payload):
                        sent_count += 1
            except Exception as exc:  # pragma: no cover - network exceptions
                logger.exception("Resend delivery failed: %s", exc)
        return sent_count

    @staticmethod
    def _log_to_console(message: EmailMessage) -> None:
        logger.info(
            "[EMAIL:CONSOLE]\nSubject: %s\nTo: %s\nCC: %s\nBCC: %s\nBody: %s",
            message.subject,
            message.to,
            message.cc,
            message.bcc,
            message.body,
        )

    def _build_payload(self, message: EmailMessage) -> Dict[str, Any]:
        html_body: Optional[str] = None
        text_body: str = message.body or ""
        if isinstance(message, EmailMultiAlternatives) and message.alternatives:
            for alternative, mimetype in message.alternatives:
                if mimetype == "text/html":
                    html_body = alternative
                elif mimetype == "text/plain" and not text_body:
                    text_body = alternative

        reply_to = _to_str_list(message.reply_to) or _to_str_list([RESEND_REPLY_TO])
        payload: Dict[str, Any] = {
            "from": RESEND_FROM or message.from_email,
            "to": _to_str_list(message.to),
            "cc": _to_str_list(message.cc) or None,
            "bcc": _to_str_list(message.bcc) or None,
            "reply_to": reply_to or None,
            "subject": message.subject or "",
            "html": html_body,
            "text": text_body if not html_body else text_body,
        }

        attachments = _attachments(message)
        if attachments:
            payload["attachments"] = attachments

        tags = _clean_tags(getattr(message, "resend_tags", None))
        if tags:
            payload["tags"] = tags

        metadata = getattr(message, "resend_metadata", None)
        if metadata:
            payload["metadata"] = metadata

        headers = getattr(message, "extra_headers", None)
        if headers:
            payload["headers"] = headers

        return payload
