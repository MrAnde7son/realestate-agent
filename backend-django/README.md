
# Django Backend (alerts + mortgage analyzer + Celery)

## Quick start (dev)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## Celery worker & beat (scheduler)
Requires Redis (default: `redis://localhost:6379/0`). You can change via env vars.

```bash
# Terminal 1 – Redis
redis-server

# Terminal 2 – Celery worker
CELERY_BROKER_URL=redis://localhost:6379/0 celery -A broker_backend worker -l info

# Terminal 3 – Celery beat (scheduler)
CELERY_BROKER_URL=redis://localhost:6379/0 celery -A broker_backend beat -l info
```

A periodic task `core.tasks.evaluate_alerts` runs every **5 minutes** and:
- pulls new listings (stub: `pull_new_listings()` — replace with your Yad2 ingestion)
- matches them against active alerts
- notifies via Email and/or WhatsApp

### Env (optional, for real notifications)
```
SENDGRID_API_KEY=...
EMAIL_FROM=alerts@example.com
ALERT_DEFAULT_EMAIL=broker@example.com

TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
ALERT_DEFAULT_WHATSAPP_TO=+9725XXXXXXXX
```

If these aren’t set, notifications are **logged** (mock mode).

### API endpoints
- `POST /api/alerts/` — create alert rule (`GET` lists rules)
- `POST /api/mortgage/analyze/` — affordability from transactions + savings
