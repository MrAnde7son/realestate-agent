
# Django Backend API

Professional backend service for the Real Estate Broker platform, providing alerts, mortgage analysis, and integration with the Next.js frontend.

## 🚀 Features

### 🚨 Alert System
- **Real-time Monitoring**: Automated property monitoring with Celery background tasks
- **Multi-channel Notifications**: Email (SendGrid) and WhatsApp (Twilio) alerts
- **Flexible Criteria**: Custom alert rules with complex filtering
- **Scheduled Processing**: Every 5-minute evaluation cycle

### 💰 Mortgage Analysis
- **Affordability Calculator**: Advanced mortgage calculations
- **Bank of Israel Integration**: Real-time interest rate data
- **Transaction Analysis**: Historical data and market comparables
- **Savings Assessment**: Down payment and monthly payment calculations

### 🔧 API Integration
- **RESTful API**: Clean, documented endpoints for frontend integration
- **Django REST Framework**: Robust API with serialization and validation
- **CORS Support**: Configured for Next.js frontend communication

## 📋 Prerequisites

- **Python 3.10+**
- **Redis** (for Celery task queue)
- **PostgreSQL** (recommended) or SQLite (development)

## 🚀 Quick Start

### 1️⃣ Basic Setup

```bash
# Navigate to backend directory
cd backend-django

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver 0.0.0.0:8000
```

### 2️⃣ Celery Setup (Real-time Alerts)

**Terminal 1: Redis Server**
```bash
redis-server
```

**Terminal 2: Celery Worker**
```bash
cd backend-django
source .venv/bin/activate
CELERY_BROKER_URL=redis://localhost:6379/0 celery -A broker_backend worker -l info
```

**Terminal 3: Celery Beat Scheduler**
```bash
cd backend-django
source .venv/bin/activate
CELERY_BROKER_URL=redis://localhost:6379/0 celery -A broker_backend beat -l info
```

### 3️⃣ Environment Configuration

Create `.env` file in `backend-django/` directory:

```env
# Database (optional - uses SQLite by default)
DATABASE_URL=postgresql://user:password@localhost:5432/realestate_db

# Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Notifications (SendGrid)
SENDGRID_API_KEY=your_sendgrid_api_key
EMAIL_FROM=alerts@yourcompany.com
ALERT_DEFAULT_EMAIL=broker@yourcompany.com

# WhatsApp Notifications (Twilio)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
ALERT_DEFAULT_WHATSAPP_TO=+972XXXXXXXXX

# Security
SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# CORS (for Next.js frontend)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 📚 API Endpoints

### 🚨 Alerts API

#### `GET /api/alerts/`
List all alert rules for the user.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Tel Aviv 4-room apartments",
    "criteria": {
      "city": 5000,
      "rooms": "4",
      "maxPrice": 8000000
    },
    "email_enabled": true,
    "whatsapp_enabled": false,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### `POST /api/alerts/`
Create a new alert rule.

**Request:**
```json
{
  "name": "Jerusalem Penthouses",
  "criteria": {
    "city": 6200,
    "property": "33",
    "minPrice": 5000000,
    "maxPrice": 15000000
  },
  "email_enabled": true,
  "whatsapp_enabled": true,
  "email_address": "buyer@example.com",
  "whatsapp_number": "+972501234567"
}
```

#### `PUT /api/alerts/{id}/`
Update an existing alert rule.

#### `DELETE /api/alerts/{id}/`
Delete an alert rule.

### 💰 Mortgage API

#### `POST /api/mortgage/analyze/`
Calculate mortgage affordability and payment scenarios.

**Request:**
```json
{
  "property_price": 4500000,
  "down_payment": 900000,
  "monthly_income": 25000,
  "monthly_expenses": 8000,
  "loan_term_years": 25,
  "interest_rate": null
}
```

**Response:**
```json
{
  "affordability": {
    "can_afford": true,
    "max_affordable_price": 5200000,
    "recommended_price": 4800000
  },
  "loan_details": {
    "loan_amount": 3600000,
    "monthly_payment": 18234,
    "total_interest": 1870200,
    "interest_rate": 4.25
  },
  "boi_data": {
    "current_rate": 4.25,
    "last_updated": "2024-01-15",
    "trend": "stable"
  },
  "scenarios": [
    {
      "down_payment_percent": 15,
      "monthly_payment": 19456
    },
    {
      "down_payment_percent": 25,
      "monthly_payment": 16789
    }
  ]
}
```

#### `GET /api/boi-rate/`
Get current Bank of Israel interest rate.

**Response:**
```json
{
  "rate": 4.25,
  "last_updated": "2024-01-15",
  "trend": "stable"
}
```

### 🏠 Listings API

#### `GET /api/listings/`
List property listings with filtering and pagination.

**Parameters:**
- `city` - City code (e.g., 5000 for Tel Aviv)
- `max_price` - Maximum price filter
- `min_price` - Minimum price filter
- `rooms` - Number of rooms
- `page` - Page number for pagination

#### `GET /api/listings/{id}/`
Get detailed information for a specific listing.

#### `GET /api/listings/{id}/appraisal/`
Get appraisal analysis for a property (comparable transactions, market analysis).

#### `GET /api/listings/{id}/rights/`
Get building rights information for a property.

### 🔄 Sync API

#### `POST /api/sync/`
Trigger manual synchronization of property data.

## 🔧 Development

### 🧪 Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### 🔍 Database Management

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell
```

### 📊 Monitoring Celery Tasks

```bash
# Monitor task queue
celery -A broker_backend inspect active

# Purge failed tasks
celery -A broker_backend purge

# Celery flower (web monitoring)
pip install flower
celery -A broker_backend flower
# Visit http://localhost:5555
```

## 🚨 Alert System Details

### Task Schedule
The alert evaluation task (`core.tasks.evaluate_alerts`) runs every **5 minutes** via Celery Beat.

### Alert Processing Flow
1. **Fetch New Listings**: Query latest properties from Yad2 integration
2. **Match Criteria**: Compare new listings against active alert rules
3. **Send Notifications**: Dispatch email/WhatsApp messages for matches
4. **Log Activity**: Track notification history and delivery status

### Notification Channels

#### Email (SendGrid)
- Template-based HTML emails
- Unsubscribe link management
- Delivery tracking and bounce handling

#### WhatsApp (Twilio)
- Rich media support (property images)
- Formatted property details
- Delivery status callbacks

### Mock Mode
If notification credentials aren't configured, the system operates in **mock mode**:
- Notifications are logged instead of sent
- Full alert processing continues
- Useful for development and testing

## 🛠️ Configuration

### Django Settings
Key configuration in `broker_backend/settings.py`:

- **Database**: PostgreSQL recommended for production
- **Celery**: Redis broker configuration
- **CORS**: Configured for Next.js frontend
- **Static Files**: Configured for production deployment
- **Security**: CSRF, CORS, and authentication settings

### Celery Configuration
Defined in `broker_backend/celery.py`:

- **Task routing** for different queue priorities
- **Retry policies** for failed notifications
- **Rate limiting** for external API calls
- **Result backend** for task monitoring

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure proper `SECRET_KEY`
- [ ] Set up PostgreSQL database
- [ ] Configure Redis for production
- [ ] Set up proper logging
- [ ] Configure static file serving
- [ ] Set up monitoring (Sentry, DataDog, etc.)

### Docker Support
```bash
# Build and run with Docker Compose
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

## 📝 API Documentation

Visit `/api/docs/` when the server is running for interactive API documentation (Swagger/OpenAPI).
