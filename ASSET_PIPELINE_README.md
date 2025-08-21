# 🏗️ Asset Enrichment Pipeline

A production-ready pipeline for enriching real estate assets with data from multiple sources including Yad2, Nadlan, GIS, and RAMI.

## 🎯 Overview

The Asset Enrichment Pipeline allows users to create assets with different scope types (address, neighborhood, street, city, parcel) and automatically enriches them with comprehensive data from multiple sources through a Celery-based background processing system.

## 🏗️ Architecture

### Data Layer
- **SQLAlchemy Models**: `Asset`, `SourceRecord`, `RealEstateTransaction`
- **PostgreSQL Database**: Shared between Django and SQLAlchemy
- **Indexed Fields**: Optimized for performance on common queries

### Backend (Django + Celery)
- **Asset API**: Create and retrieve assets
- **Enrichment Pipeline**: Geocoding → Parallel Data Collection → Finalization
- **Celery Tasks**: Asynchronous processing with Redis broker
- **Error Handling**: Graceful fallbacks and status tracking

### Frontend (Next.js)
- **Dynamic Forms**: Scope-based form fields
- **Real-time Status**: Polling for asset enrichment progress
- **Responsive UI**: Modern interface with Hebrew support

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone the repository
git clone <your-repo>
cd realestate-agent

# Set environment variables
cp env.example .env
# Edit .env with your Google OAuth credentials
```

### 2. Database Setup
```bash
# Run the setup script
python setup_assets.py

# Or manually:
cd backend-django
python manage.py makemigrations
python manage.py migrate
```

### 3. Start Services
```bash
# Start all services
docker-compose up

# Or start individual services:
docker-compose up postgres redis
docker-compose up backend celery-worker celery-beat
docker-compose up ui
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 📊 Asset Scope Types

### 1. Address (`address`)
- **Required**: `address`, `city`
- **Optional**: `radius`
- **Use Case**: Specific property location

### 2. Neighborhood (`neighborhood`)
- **Required**: `neighborhood`, `city`
- **Optional**: `radius`
- **Use Case**: Area analysis and market research

### 3. Street (`street`)
- **Required**: `street`, `city`
- **Optional**: `number`, `radius`
- **Use Case**: Street-level analysis

### 4. City (`city`)
- **Required**: `city`
- **Optional**: `radius`
- **Use Case**: City-wide market overview

### 5. Parcel (`parcel`)
- **Required**: `gush`, `helka`, `city`
- **Optional**: `radius`
- **Use Case**: Land parcel analysis

## 🔄 Enrichment Pipeline

### Phase 1: Geocoding & IDs
```python
geocode_and_ids(asset_id)
├── Extract coordinates (lat/lon)
├── Get gush/helka (if available)
├── Identify neighborhood_id
└── Update asset status to 'enriching'
```

### Phase 2: Parallel Data Collection
```python
parallel_tasks(context)
├── pull_yad2(context)      # Yad2 listings
├── pull_nadlan(context)    # Transaction history
├── pull_gis(context)       # Permits & rights
└── pull_rami(context)      # Plans & documents
```

### Phase 3: Finalization
```python
finalize(context)
├── Update asset status to 'ready'
├── Store enrichment metadata
└── Log completion
```

## 🗄️ Database Schema

### Asset Table
```sql
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    scope_type VARCHAR(50) NOT NULL,
    city VARCHAR(100),
    neighborhood VARCHAR(100),
    street VARCHAR(200),
    number INTEGER,
    gush VARCHAR(20),
    helka VARCHAR(20),
    lat FLOAT,
    lon FLOAT,
    normalized_address VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending',
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### SourceRecord Table
```sql
CREATE TABLE source_records (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id),
    source VARCHAR(50) NOT NULL,
    external_id VARCHAR(100),
    title VARCHAR(500),
    url VARCHAR(500),
    file_path VARCHAR(500),
    raw JSONB,
    fetched_at TIMESTAMP DEFAULT NOW()
);
```

### RealEstateTransaction Table
```sql
CREATE TABLE real_estate_transactions (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id),
    deal_id VARCHAR(100),
    date TIMESTAMP,
    price INTEGER,
    rooms INTEGER,
    area FLOAT,
    floor INTEGER,
    address VARCHAR(200),
    raw JSONB,
    fetched_at TIMESTAMP DEFAULT NOW()
);
```

## 🔌 API Endpoints

### Create Asset
```http
POST /api/assets/
Content-Type: application/json

{
  "scope": {
    "type": "neighborhood",
    "value": "רמת החייל",
    "city": "תל אביב"
  },
  "city": "תל אביב",
  "radius": 250
}
```

### Get Asset Details
```http
GET /api/assets/{id}/
```

**Response**:
```json
{
  "id": 1,
  "scope_type": "neighborhood",
  "city": "תל אביב",
  "neighborhood": "רמת החייל",
  "status": "ready",
  "records": {
    "yad2": [...],
    "gis_permit": [...],
    "gis_rights": [...],
    "rami_plan": [...]
  },
  "transactions": [...]
}
```

## 🎨 Frontend Features

### Dynamic Form Fields
- **Scope-based validation**: Only required fields shown
- **Real-time updates**: Form adapts to scope type selection
- **Hebrew support**: Full RTL and Hebrew text support

### Asset Status Tracking
- **Real-time polling**: 3-second intervals during enrichment
- **Status indicators**: pending → enriching → ready/error
- **Progress feedback**: User sees enrichment progress

### Responsive Design
- **Mobile-first**: Optimized for all screen sizes
- **Accessibility**: Screen reader support and keyboard navigation
- **Modern UI**: Shadcn/ui components with Tailwind CSS

## 🧪 Testing

### Backend Tests
```bash
cd backend-django
python manage.py test

# Run specific tests
python manage.py test core.tests.test_asset_views
```

### Frontend Tests
```bash
cd realestate-broker-ui
npm test

# Run specific tests
npm test -- app/listings/page.test.tsx
```

### Integration Tests
```bash
# Test the complete pipeline
python -m pytest tests/test_integration.py -v
```

## 🚨 Error Handling

### Graceful Degradation
- **Missing Dependencies**: Fallback to mock data
- **External API Failures**: Continue with available data
- **Database Issues**: Return appropriate error codes

### Status Tracking
- **Asset States**: `pending` → `enriching` → `ready`/`error`
- **Error Details**: Stored in `asset.meta.error`
- **Retry Logic**: Failed tasks can be retried

### Logging
- **Structured Logging**: JSON format with context
- **Error Context**: Asset ID, task type, failure reason
- **Performance Metrics**: Task duration and success rates

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db
POSTGRES_DB=realestate
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Backend URLs
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

### Celery Configuration
```python
# backend-django/broker_backend/settings.py
CELERY_TIMEZONE = TIME_ZONE
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
```

## 📈 Performance

### Database Optimization
- **Indexes**: On frequently queried fields
- **Connection Pooling**: SQLAlchemy with PostgreSQL
- **Query Optimization**: Efficient joins and filters

### Celery Optimization
- **Task Batching**: Parallel execution where possible
- **Resource Limits**: Prevent memory leaks
- **Monitoring**: Task success rates and timing

### Frontend Optimization
- **Polling Intervals**: Configurable status updates
- **Lazy Loading**: Load data only when needed
- **Caching**: Browser-level caching for static assets

## 🔒 Security

### Authentication
- **JWT Tokens**: Secure API access
- **Google OAuth**: Social login integration
- **Route Protection**: Middleware-based access control

### Data Validation
- **Input Sanitization**: Prevent injection attacks
- **Schema Validation**: Zod-based frontend validation
- **Database Constraints**: SQL-level data integrity

### API Security
- **CORS Configuration**: Controlled cross-origin access
- **Rate Limiting**: Prevent abuse
- **Error Handling**: No sensitive data in error messages

## 🚀 Deployment

### Production Considerations
- **Environment Variables**: Secure credential management
- **Database Backups**: Regular PostgreSQL backups
- **Monitoring**: Health checks and alerting
- **Scaling**: Horizontal scaling for Celery workers

### Docker Deployment
```bash
# Production build
docker-compose -f docker-compose.prod.yml up -d

# Health checks
docker-compose ps
docker-compose logs -f backend
```

### Environment-Specific Configs
- **Development**: Local PostgreSQL, debug mode
- **Staging**: Staging database, production-like settings
- **Production**: Production database, optimized settings

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch
3. **Implement** your changes
4. **Test** thoroughly
5. **Submit** a pull request

### Code Standards
- **Python**: PEP 8, type hints, docstrings
- **JavaScript/TypeScript**: ESLint, Prettier
- **Tests**: Minimum 80% coverage
- **Documentation**: Update README for new features

## 📚 Additional Resources

### Documentation
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/14/orm/)
- [Next.js App Router](https://nextjs.org/docs/app)

### Related Projects
- [Yad2 Scraper](../yad2/)
- [GIS Client](../gis/)
- [RAMI Client](../rami/)
- [Government Data](../gov/)

## 🆘 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
python -c "from db.database import SQLAlchemyDatabase; db = SQLAlchemyDatabase(); print(db.init_db())"
```

#### Celery Worker Issues
```bash
# Check Redis status
docker-compose ps redis

# Restart workers
docker-compose restart celery-worker celery-beat

# Check task queue
docker-compose exec redis redis-cli LLEN celery
```

#### Frontend Build Issues
```bash
# Clear Next.js cache
cd realestate-broker-ui
rm -rf .next
npm run build

# Check for dependency conflicts
npm ls
```

### Getting Help
- **Issues**: Create GitHub issues with detailed error logs
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check this README and inline code comments

---

**🎉 Congratulations!** You now have a production-ready asset enrichment pipeline that can process real estate data from multiple sources automatically. The system is designed to be scalable, maintainable, and user-friendly.
