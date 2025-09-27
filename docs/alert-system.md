# Alert System Documentation

## Overview

The real estate agent includes a comprehensive alert system that can send notifications via email and WhatsApp when properties matching user criteria are found. The system supports both immediate and daily digest notifications.

## Features

- **Multi-channel notifications**: Email and WhatsApp support
- **Flexible criteria**: Users can set complex search criteria for alerts
- **Multiple trigger types**: Price drops, new listings, market trends, etc.
- **Immediate and digest modes**: Get alerts instantly or in daily summaries
- **Fallback support**: Sandbox mode and console fallback for development
- **Error handling**: Graceful error handling with logging

## Configuration

### Environment Variables

#### Email Configuration (Resend)

```env
RESEND_API_KEY=your_resend_api_key
RESEND_FROM="RealEstate Agent <no-reply@yourcompany.com>"
RESEND_REPLY_TO=support@yourcompany.com
RESEND_SANDBOX=true
EMAIL_FALLBACK_TO_CONSOLE=true
RESEND_WEBHOOK_SECRET=your_resend_webhook_secret
```

#### WhatsApp Configuration

```env
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

#### Test Configuration (Optional)

```env
ALERT_DEFAULT_EMAIL=test@yourcompany.com
ALERT_DEFAULT_WHATSAPP_TO=+972501234567
```

### Service Setup

#### Resend Setup
1. Create an account at [Resend](https://resend.com)
2. Verify your sending domain and from address
3. Generate an API key and set `RESEND_API_KEY`
4. Configure the webhook endpoint to `https://your-domain/webhooks/resend`
5. (Optional) Enable sandbox mode in development with `RESEND_SANDBOX=true`

#### Twilio Setup (WhatsApp)
1. Create a free account at [Twilio](https://twilio.com)
2. Get your Account SID and Auth Token
3. Set up WhatsApp sandbox or production number
4. Set the environment variables

SMTP configuration is no longer required. When `EMAIL_FALLBACK_TO_CONSOLE` is
set to `true` and no API key is configured, outbound messages are printed to
the console for safe local testing.

## Usage

### Creating Alert Rules

Users can create alert rules through the API or admin interface:

```python
# Example alert rule
{
    "scope": "global",
    "trigger_type": "NEW_LISTING",
    "params": {
        "city": "5000",  # Tel Aviv
        "rooms": "4",
        "maxPrice": 3000000
    },
    "channels": ["email", "whatsapp"],
    "frequency": "immediate",
    "active": True
}
```

### Testing Alerts

#### Using Django Management Command
```bash
cd backend-django
python manage.py test_alerts
```

#### Using Test Script
```bash
python test_alerts.py
```

#### Testing Specific Channels
```bash
# Test with specific email
python manage.py test_alerts --email test@example.com

# Test with specific phone
python manage.py test_alerts --phone +972501234567

# Test with specific user
python manage.py test_alerts --user-id 1
```

### API Endpoints

#### Create Alert Rule
```http
POST /api/alerts/
Content-Type: application/json

{
    "scope": "global",
    "trigger_type": "NEW_LISTING",
    "params": {
        "city": "5000",
        "rooms": "4",
        "maxPrice": 3000000
    },
    "channels": ["email", "whatsapp"],
    "frequency": "immediate"
}
```

#### Test Alert
```http
POST /api/alert-test/
```

#### List Alert Rules
```http
GET /api/alerts/
```

## Architecture

### Components

1. **Alert Classes** (`orchestration/alerts.py`)
   - `EmailAlert`: Handles email notifications
   - `WhatsAppAlert`: Handles WhatsApp notifications
   - `Notifier`: Manages multiple alert channels

2. **Database Models** (`backend-django/core/models.py`)
   - `AlertRule`: User-defined alert criteria
   - `AlertEvent`: Individual alert occurrences
   - `Snapshot`: Asset data snapshots for comparison

3. **Background Tasks** (`backend-django/core/tasks.py`)
   - `evaluate_alerts_for_asset`: Evaluates alerts for specific assets
   - `alerts_daily_digest`: Sends daily digest emails

4. **Data Pipeline** (`orchestration/data_pipeline.py`)
   - Integrates alert evaluation into data collection
   - Triggers immediate notifications

### Message Format

#### Email Messages
```html
<p>🏠 נכס חדש נמצא!</p>
<p>📍 דירה 4 חדרים בתל אביב</p>
<p>💰 מחיר: 2,500,000 ₪</p>
<p>🔗 קישור: https://example.com/listing/123</p>
<p>נדלנר - מערכת התראות נדלן</p>
```

#### WhatsApp Messages
```
🏠 נכס חדש נמצא!

📍 דירה 4 חדרים בתל אביב
💰 מחיר: 2,500,000 ₪
🔗 קישור: https://example.com/listing/123

נדלנר - מערכת התראות נדלן
```

## Troubleshooting

### Common Issues

1. **Alerts not sending**
   - Check environment variables are set correctly
   - Verify API keys are valid
   - Check logs for error messages

2. **Email not working**
   - Verify Resend API key and webhook secret
   - Check email address format
   - Ensure sender email is verified in Resend

3. **WhatsApp not working**
   - Verify Twilio credentials
   - Check phone number format (include country code)
   - Ensure WhatsApp number is verified with Twilio

4. **User not receiving alerts**
   - Check user has `notify_email` or `notify_whatsapp` enabled
   - Verify user has valid email/phone
   - Check alert rule is active

### Debugging

Enable debug logging:
```python
import logging
logging.getLogger('orchestration.alerts').setLevel(logging.DEBUG)
```

Check alert events in database:
```python
from core.models import AlertEvent
events = AlertEvent.objects.filter(delivered_at__isnull=True)
```

## Monitoring

### Metrics to Track

- Alert delivery success rate
- Alert delivery latency
- Failed alert reasons
- User engagement with alerts

### Logs

Alert system logs are available in:
- Django logs: `backend-django/logs/`
- Celery logs: Check Celery worker output
- Application logs: Standard Django logging

## Security Considerations

1. **API Keys**: Store securely, never commit to version control
2. **Rate Limiting**: Implement rate limiting for alert endpoints
3. **User Privacy**: Only send alerts to verified user contacts
4. **Content Filtering**: Sanitize alert content to prevent injection

## Future Enhancements

- SMS notifications
- Push notifications
- Slack/Teams integration
- Advanced filtering options
- Alert templates customization
- A/B testing for alert content
