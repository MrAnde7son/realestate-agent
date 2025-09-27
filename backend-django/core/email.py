"""Utilities for composing emails that are delivered via Resend."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from django.core.mail import EmailMultiAlternatives

HeadersType = Optional[Dict[str, Any]]
AttachmentsType = Optional[Iterable[tuple]]


def _normalize_header_dict(raw: HeadersType) -> Dict[str, Any]:
    """Extract tags/metadata/custom headers from a user supplied dict."""
    if not raw:
        return {}
    data = dict(raw)
    custom_headers: Dict[str, Any] = {}

    nested_header_keys = ("headers", "extra_headers", "custom_headers")
    for key in nested_header_keys:
        nested = data.pop(key, None)
        if isinstance(nested, dict):
            custom_headers.update(nested)

    # Remaining values are interpreted as plain headers unless reserved below
    tags = data.pop("tags", data.pop("resend_tags", None))
    metadata = data.pop("metadata", data.pop("resend_metadata", None))

    # Stash the reserved values on the dict so send_email can retrieve them
    if tags is not None:
        custom_headers.setdefault("X-Resend-Tags", tags)
    if metadata is not None:
        custom_headers.setdefault("X-Resend-Metadata", metadata)

    for key, value in data.items():
        custom_headers[key] = value

    return custom_headers


def send_email(
    subject: str,
    to: List[str],
    text: str = "",
    html: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    reply_to: Optional[List[str]] = None,
    attachments: AttachmentsType = None,
    headers: HeadersType = None,
) -> int:
    """Send an email using the configured Django backend.

    The helper constructs a :class:`~django.core.mail.EmailMultiAlternatives`
    instance with both text and HTML bodies, optional attachments and
    metadata. Tags and metadata intended for Resend can be supplied via the
    ``headers`` parameter::

        send_email(
            "Subject",
            ["user@example.com"],
            text="Plain", html="<b>Plain</b>",
            headers={"tags": {"campaign": "welcome"}, "metadata": {"user_id": 42}},
        )
    """

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text or "",
        to=to,
        cc=cc or None,
        bcc=bcc or None,
        reply_to=reply_to or None,
    )

    if html:
        msg.attach_alternative(html, "text/html")

    if attachments:
        for attachment in attachments:
            if isinstance(attachment, tuple) and len(attachment) >= 2:
                filename = attachment[0]
                content = attachment[1]
                mimetype = attachment[2] if len(attachment) >= 3 else None
                msg.attach(filename, content, mimetype)

    header_values = _normalize_header_dict(headers)
    tags = header_values.pop("X-Resend-Tags", None)
    metadata = header_values.pop("X-Resend-Metadata", None)

    if tags is not None:
        setattr(msg, "resend_tags", tags)
    if metadata is not None:
        setattr(msg, "resend_metadata", metadata)

    if header_values:
        msg.extra_headers.update({str(k): str(v) for k, v in header_values.items()})

    return msg.send()
