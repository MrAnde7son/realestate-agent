"""Alert utilities using pluggable strategies."""

from __future__ import annotations

import os
import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

try:  # optional dependency for WhatsApp via Twilio
    from twilio.rest import Client  # type: ignore
except ImportError:  # pragma: no cover - twilio may not be installed at runtime
    Client = None  # type: ignore


class Alert(ABC):
    """Abstract alert channel."""

    @abstractmethod
    def send(self, message: str) -> None:
        """Send the provided message."""


class EmailAlert(Alert):
    """Email alert implementation with configurable SMTP settings."""

    def __init__(
        self,
        to_email: str,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> None:
        self.to_email = to_email
        self.host = host or os.getenv("SMTP_HOST")
        self.user = user or os.getenv("SMTP_USER")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("SMTP_FROM", self.user)

    def send(self, message: str) -> None:
        if not (
            self.host
            and self.user
            and self.password
            and self.from_email
            and self.to_email
        ):
            return

        msg = MIMEText(message)
        msg["Subject"] = "New listing found"
        msg["From"] = self.from_email
        msg["To"] = self.to_email

        with smtplib.SMTP(self.host) as server:
            server.login(self.user, self.password)
            server.sendmail(self.from_email, [self.to_email], msg.as_string())


class WhatsAppAlert(Alert):
    """WhatsApp alert implementation using Twilio."""

    def __init__(
        self,
        to_number: str,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
    ) -> None:
        self.to_number = to_number
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.getenv("TWILIO_WHATSAPP_FROM")

    def send(self, message: str) -> None:
        if not (
            Client
            and self.account_sid
            and self.auth_token
            and self.from_number
            and self.to_number
        ):
            return

        client = Client(self.account_sid, self.auth_token)
        client.messages.create(
            body=message,
            from_=f"whatsapp:{self.from_number}",
            to=f"whatsapp:{self.to_number}",
        )


class Notifier:
    """Notify about assets using a set of alert channels."""

    def __init__(self, criteria: Dict[str, Any], alerts: List[Alert]) -> None:
        self.criteria = criteria
        self.alerts = alerts

    def notify(self, listing: Any) -> None:
        """Send notifications if the listing matches all criteria."""
        for key, value in self.criteria.items():
            if getattr(listing, key, None) != value:
                return

        message = f"New listing found: {listing.title} for {listing.price} - {listing.url}"
        for alert in self.alerts:
            alert.send(message)


def create_notifier_for_user(user: Any, criteria: Dict[str, Any]) -> Optional[Notifier]:
    """Create a :class:`Notifier` configured for a specific user.

    The function inspects the given ``user`` object for contact details and
    notification preferences. If the user has enabled email or WhatsApp
    alerts (via ``notify_email`` / ``notify_whatsapp``) and provided the
    corresponding contact information, the appropriate alert channels are
    instantiated. When at least one channel is available, a ``Notifier`` is
    returned; otherwise ``None`` is returned.

    Parameters
    ----------
    user:
        An object representing the user. It should expose ``email``,
        ``phone``, ``notify_email`` and ``notify_whatsapp`` attributes.
    criteria:
        Dictionary of attribute/value pairs that a listing must match in
        order to trigger the notification.

    Returns
    -------
    Optional[Notifier]
        A configured ``Notifier`` instance or ``None`` if no alert channels
        could be created for the user.
    """

    channels: List[Alert] = []

    if getattr(user, "notify_email", False):
        email = getattr(user, "email", None)
        if email:
            channels.append(EmailAlert(email))

    if getattr(user, "notify_whatsapp", False):
        phone = getattr(user, "phone", None)
        if phone:
            channels.append(WhatsAppAlert(phone))

    if not channels:
        return None

    return Notifier(criteria, channels)

