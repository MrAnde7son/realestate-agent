
import os
import json
import logging
from typing import Dict, Any, List
from celery import shared_task
from django.utils import timezone
from .models import Alert
import requests

log = logging.getLogger(__name__)

# --- Stub data source (replace with your Yad2 puller) ---
def pull_new_listings() -> List[Dict[str, Any]]:
    """Return newly pulled listings since last run.
    Replace this with your Yad2 ingestion output (e.g., rows inserted in the last N minutes).
    Minimal fields expected by the matcher are included below.
    """
    # Demo listings (simulate two new items)
    return [
        {
            'id': 'demo-1',
            'address': 'הגולן 3',
            'city': 'תל אביב-יפו',
            'rooms': 4,
            'price': 7900000,
            'confidence': 76,
            'riskFlags': [],
            'remaining_rights': 22,
            'link': 'https://example.com/listings/demo-1'
        },
        {
            'id': 'demo-2',
            'address': 'הרב לוי 12',
            'city': 'בת-ים',
            'rooms': 3,
            'price': 2350000,
            'confidence': 62,
            'riskFlags': ['רעש'],
            'remaining_rights': 0,
            'link': 'https://example.com/listings/demo-2'
        }
    ]

def matches(criteria: Dict[str, Any], listing: Dict[str, Any]) -> bool:
    c = criteria or {}
    # city
    if c.get('city') and listing.get('city') != c['city']:
        return False
    # price cap
    if c.get('max_price') is not None and listing.get('price') is not None:
        if listing['price'] > float(c['max_price']):
            return False
    # beds range
    beds = c.get('beds') or {}
    if beds.get('min') is not None and listing.get('rooms') is not None:
        if listing['rooms'] < int(beds['min']):
            return False
    if beds.get('max') is not None and listing.get('rooms') is not None:
        if listing['rooms'] > int(beds['max']):
            return False
    # model confidence
    if c.get('confidence_min') is not None and listing.get('confidence') is not None:
        if listing['confidence'] < float(c['confidence_min']):
            return False
    # risk flags
    risk = c.get('risk')
    if risk == 'none' and listing.get('riskFlags'):
        return False
    # remaining rights
    if c.get('remaining_rights_min') is not None:
        if (listing.get('remaining_rights') or 0) < float(c['remaining_rights_min']):
            return False
    return True

def notify_email(subject: str, body: str, to_email: str) -> None:
    api_key = os.environ.get('SENDGRID_API_KEY')
    email_from = os.environ.get('EMAIL_FROM', 'noreply@example.com')
    if not (api_key and to_email):
        log.info("[EMAIL MOCK] %s -> %s\n%s", subject, to_email or '(unset)', body)
        return
    # SendGrid minimal REST call
    try:
        resp = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'personalizations': [{'to': [{'email': to_email}]}],
                'from': {'email': email_from},
                'subject': subject,
                'content': [{'type': 'text/plain', 'value': body}]
            },
            timeout=10
        )
        if resp.status_code >= 300:
            log.error('SendGrid failed: %s %s', resp.status_code, resp.text)
    except Exception as e:
        log.exception('SendGrid error: %s', e)

def notify_whatsapp(body: str, to_number: str) -> None:
    sid = os.environ.get('TWILIO_ACCOUNT_SID')
    token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_num = os.environ.get('TWILIO_WHATSAPP_FROM')  # e.g., 'whatsapp:+14155238886'
    if not (sid and token and from_num and to_number):
        log.info("[WHATSAPP MOCK] -> %s\n%s", to_number or '(unset)', body)
        return
    url = f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json'
    data = {
        'To': f'whatsapp:{to_number}' if not to_number.startswith('whatsapp:') else to_number,
        'From': from_num,
        'Body': body
    }
    try:
        resp = requests.post(url, data=data, auth=(sid, token), timeout=10)
        if resp.status_code >= 300:
            log.error('Twilio failed: %s %s', resp.status_code, resp.text)
    except Exception as e:
        log.exception('Twilio error: %s', e)

def notify(alert: Alert, listing: Dict[str, Any]) -> None:
    subject = f"התראה: פריט חדש תואם — {listing.get('address')}"
    body = (        f"נמצא נכס תואם חוק '{alert.id}'.\n"
        f"כתובת: {listing.get('address')} ({listing.get('city')})\n"
        f"חדרים: {listing.get('rooms')}\n"
        f"מחיר: {listing.get('price')}\n"
        f"Confidence: {listing.get('confidence')}\n"
        f"זכויות נותרות: {listing.get('remaining_rights')}\n"
        f"קישור: {listing.get('link')}\n"
    )
    channels = alert.notify or []
    default_email = os.environ.get('ALERT_DEFAULT_EMAIL')
    default_wa = os.environ.get('ALERT_DEFAULT_WHATSAPP_TO')
    if 'email' in channels:
        notify_email(subject, body, default_email)
    if 'whatsapp' in channels:
        notify_whatsapp(body, default_wa or '')

@shared_task(name='core.tasks.evaluate_alerts')
def evaluate_alerts():
    """Periodic task: check new listings against active alerts and notify."""
    alerts = Alert.objects.filter(active=True).order_by('-id')
    if not alerts.exists():
        log.info('No active alerts; skipping evaluation.')
        return {'processed': 0, 'matches': 0}
    listings = pull_new_listings()
    processed = 0
    matched = 0
    for listing in listings:
        for alert in alerts:
            if matches(alert.criteria, listing):
                matched += 1
                notify(alert, listing)
        processed += 1
    log.info('evaluate_alerts: processed=%s matches=%s', processed, matched)
    return {'processed': processed, 'matches': matched}
