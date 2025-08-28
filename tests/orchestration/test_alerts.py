from tests import test_utils  # noqa: F401

from orchestration.alerts import (
    EmailAlert,
    WhatsAppAlert,
    create_notifier_for_user,
)


class DummyUser:
    def __init__(
        self,
        *,
        email: str | None = "user@example.com",
        phone: str | None = "+15551234567",
        notify_email: bool = True,
        notify_whatsapp: bool = True,
    ) -> None:
        self.email = email
        self.phone = phone
        self.notify_email = notify_email
        self.notify_whatsapp = notify_whatsapp


def test_create_notifier_for_user_adds_channels():
    user = DummyUser()
    notifier = create_notifier_for_user(user, {"city": "tel aviv"})
    assert notifier is not None
    channel_types = {type(ch) for ch in notifier.alerts}
    assert EmailAlert in channel_types
    assert WhatsAppAlert in channel_types


def test_create_notifier_for_user_returns_none_without_channels():
    user = DummyUser(email=None, phone=None, notify_email=False, notify_whatsapp=False)
    notifier = create_notifier_for_user(user, {"city": "tel aviv"})
    assert notifier is None
