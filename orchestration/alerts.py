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
        self.from_email = from_email or os.getenv("EMAIL_FROM", self.user)

    def send(self, message: str) -> None:
        if not self.to_email:
            return

        # Try SendGrid first if available
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        if sendgrid_api_key:
            try:
                import sendgrid  # type: ignore
                from sendgrid.helpers.mail import Mail  # type: ignore
                
                sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
                mail = Mail(
                    from_email=os.getenv("EMAIL_FROM", "no-reply@nadlaner.com"),
                    to_emails=self.to_email,
                    subject="נדלנר: התראה חדשה",
                    html_content=f"<p>{message}</p>"
                )
                sg.send(mail)
                return
            except Exception as e:
                print(f"SendGrid failed, falling back to SMTP: {e}")

        # Fallback to SMTP
        if not (
            self.host
            and self.user
            and self.password
            and self.from_email
        ):
            print("Email configuration incomplete, skipping email alert")
            return

        try:
            msg = MIMEText(message, 'html', 'utf-8')
            msg["Subject"] = "נדלנר: התראה חדשה"
            msg["From"] = self.from_email
            msg["To"] = self.to_email

            with smtplib.SMTP(self.host, 587) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_email, [self.to_email], msg.as_string())
        except Exception as e:
            print(f"Failed to send email alert: {e}")


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
            print("WhatsApp configuration incomplete, skipping WhatsApp alert")
            return

        try:
            client = Client(self.account_sid, self.auth_token)
            client.messages.create(
                body=message,
                from_=self.from_number,
                to=f"whatsapp:{self.to_number}",
            )
        except Exception as e:
            print(f"Failed to send WhatsApp alert: {e}")


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

        # Create a more detailed message
        title = getattr(listing, 'title', 'Unknown Property')
        price = getattr(listing, 'price', 'Price not available')
        url = getattr(listing, 'url', '')
        
        message = "🏠 נכס חדש נמצא!\n\n"
        message += f"📍 {title}\n"
        message += f"💰 מחיר: {price}\n"
        if url:
            message += f"🔗 קישור: {url}\n"
        message += "\nנדלנר - מערכת התראות נדלן"
        
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


def create_notifier_for_alert_rule(alert_rule: Any) -> Optional[Notifier]:
    """Create a :class:`Notifier` configured for a specific alert rule.
    
    This function works with the new AlertRule model and creates notifiers
    based on the channels specified in the alert rule.
    
    Parameters
    ----------
    alert_rule:
        An AlertRule instance with channels, user, and other configuration.
        
    Returns
    -------
    Optional[Notifier]
        A configured ``Notifier`` instance or ``None`` if no alert channels
        could be created for the alert rule.
    """
    channels: List[Alert] = []
    user = alert_rule.user
    
    # Check if email is enabled in channels
    if 'email' in alert_rule.channels:
        email = getattr(user, "email", None)
        if email:
            channels.append(EmailAlert(email))
    
    # Check if WhatsApp is enabled in channels
    if 'whatsapp' in alert_rule.channels:
        phone = getattr(user, "phone", None)
        if phone:
            channels.append(WhatsAppAlert(phone))
    
    if not channels:
        return None
    
    # Create criteria from alert rule params
    criteria = alert_rule.params.copy()
    
    return Notifier(criteria, channels)

