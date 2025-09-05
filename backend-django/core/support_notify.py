import requests
from django.conf import settings
from django.core.mail import send_mail


def notify_ticket(t):
    body = (
        f"[{t.kind.upper()}] #{t.id}\n"
        f"User: {getattr(t.user, 'email', 'anonymous')}\n"
        f"Subject: {t.subject}\nSeverity: {t.severity}\n"
        f"URL: {t.url}\nUA: {t.user_agent}\nVersion: {t.app_version}\n\n{t.message}"
    )
    send_mail(
        subject=f"Nadlaner Support: {t.kind} #{t.id}",
        message=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@nadlaner.com"),
        recipient_list=["support@nadlaner.com"],
        fail_silently=True,
    )
    hook = getattr(settings, "SUPPORT_SLACK_WEBHOOK", "")
    if hook:
        try:
            requests.post(hook, json={"text": body}, timeout=5)
        except Exception:
            pass


def notify_consultation(c):
    body = (
        f"[CONSULT] #{c.id}\n"
        f"Name: {c.full_name}\nEmail: {c.email}\nPhone: {c.phone}\n"
        f"Preferred: {c.preferred_time}\nChannel: {c.channel}\nTopic: {c.topic}"
    )
    send_mail(
        subject=f"Nadlaner Consultation #{c.id}",
        message=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@nadlaner.com"),
        recipient_list=["support@nadlaner.com"],
        fail_silently=True,
    )
    hook = getattr(settings, "SUPPORT_SLACK_WEBHOOK", "")
    if hook:
        try:
            requests.post(hook, json={"text": body}, timeout=5)
        except Exception:
            pass
