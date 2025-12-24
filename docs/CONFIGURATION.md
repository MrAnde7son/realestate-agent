# Configuration Guide

This document explains all configuration files in the realestate-agent project and how to use them.

## Table of Contents

- [Pytest Configuration](#pytest-configuration)
- [Environment Variables](#environment-variables)
- [Docker Configuration](#docker-configuration)
- [Django Settings](#django-settings)
- [Deployment Configuration](#deployment-configuration)

---

## Pytest Configuration

The project uses pytest for testing with configuration split across multiple files for different environments.

### Configuration Files

#### `pyproject.toml` (Primary Configuration)
**Location:** Project root  
**Purpose:** Main pytest configuration (modern Python standard)  
**Contains:**
- Django settings
- Test discovery paths
- All test markers
- Default pytest options
- Warning filters

**Usage:** Automatically used by pytest (default):
```bash
pytest tests/
```

**Note:** This is the single source of truth for pytest configuration. All settings are centralized here.

### Test Markers

The project uses pytest markers to categorize tests:

| Marker | Description | Usage |
|--------|-------------|-------|
| `django` | Django-specific tests | `pytest -m django` |
| `slow` | Slow-running tests | `pytest -m slow` |
| `integration` | Integration tests | `pytest -m integration` |
| `asyncio` | Async tests | `pytest -m asyncio` |
| `mavat` | Mavat collector tests | `pytest -m mavat` |
| `yad2` | Yad2 scraper tests | `pytest -m yad2` |
| `nadlan` | Nadlan scraper tests | `pytest -m nadlan` |
| `decisive` | Decisive appraisal tests | `pytest -m decisive` |
| `gis` | GIS client tests | `pytest -m gis` |
| `rami` | RAMI client tests | `pytest -m rami` |
| `govmap` | GovMap client tests | `pytest -m govmap` |
| `external_service` | Tests requiring external APIs | `pytest -m external_service` |

### Running Tests

The project provides a convenient script for running tests with different strategies:

```bash
# Unit tests only (fast, no external dependencies)
./scripts/run-tests.sh unit

# Integration tests
./scripts/run-tests.sh integration

# CI-optimized tests (skips slow/external_service, maxfail=5)
./scripts/run-tests.sh ci

# All tests
./scripts/run-tests.sh all

# Module-specific tests
./scripts/run-tests.sh mavat
./scripts/run-tests.sh yad2
./scripts/run-tests.sh nadlan
```

**Note:** The CI strategy uses command-line options directly (no separate config file needed):
```bash
pytest tests/ -v --tb=short --strict-markers -m "not slow and not external_service" --maxfail=5
```

---

## Environment Variables

### Development Environment

**File:** `env.development`  
**Purpose:** Template for local development  
**Usage:** Copied to `backend-django/.env` by `dev_start.sh`

**Key Variables:**
- `DJANGO_SETTINGS_MODULE=broker_backend.settings`
- `DATABASE_URL` (SQLite for development)
- `SECRET_KEY` (development key)
- `DEBUG=True`

### Docker Environment

**File:** `env.docker`  
**Purpose:** Docker Compose environment variables  
**Usage:** Used by `docker-compose.yml`

### Production Environment

**File:** `env.example`  
**Purpose:** Template showing required production variables  
**Usage:** Reference for production deployment

**Key Variables:**
- `DATABASE_URL` (PostgreSQL connection string)
- `SECRET_KEY` (production secret key)
- `DEBUG=False`
- `ALLOWED_HOSTS` (comma-separated host list)
- `RESEND_API_KEY` (for email notifications)
- `TWILIO_ACCOUNT_SID` (for WhatsApp notifications)

---

## Docker Configuration

### `docker-compose.yml`
**Purpose:** Local development with Docker Compose  
**Services:**
- Django API backend
- Celery worker
- Redis (for Celery broker)
- PostgreSQL (optional, can use SQLite)

**Usage:**
```bash
docker-compose up -d
```

### `Dockerfile` (Root)
**Purpose:** General Docker configuration  
**Usage:** Base configuration for various services

### `backend-django/Dockerfile`
**Purpose:** Django API service container  
**Usage:** Production deployment to Cloud Run

### `orchestration/Dockerfile.celery`
**Purpose:** Celery worker container  
**Usage:** Production deployment to Cloud Run

---

## Django Settings

### `backend-django/broker_backend/settings.py`
**Purpose:** Main Django configuration  
**Key Settings:**
- Database configuration
- Installed apps
- Middleware
- Authentication
- Celery configuration
- Email backend (Resend)
- WhatsApp integration (Twilio)

**Environment-Specific:**
- Development: Uses SQLite, debug enabled
- Production: Uses PostgreSQL, debug disabled, Cloud SQL connection

---

## Deployment Configuration

### `cloudbuild.yaml`
**Purpose:** Google Cloud Build configuration  
**Usage:** CI/CD pipeline for building and deploying to GCP

**Steps:**
1. Build API Docker image
2. Build Celery worker Docker image
3. Push images to Artifact Registry
4. Deploy API to Cloud Run
5. Deploy Worker to Cloud Run

**Substitution Variables:**
- `_REGION`: GCP region (default: `me-west1`)
- `_REPO_NAME`: Artifact Registry repository name
- `_API_SERVICE_NAME`: Cloud Run service name for API
- `_WORKER_SERVICE_NAME`: Cloud Run service name for worker

### `render.yaml`
**Purpose:** Render.com deployment configuration  
**Usage:** Alternative deployment platform

### `infra/gcp/`
**Purpose:** Terraform infrastructure as code  
**Usage:** GCP resource provisioning

---

## Configuration File Priority

Pytest uses the following priority:

1. **Command-line options** (highest priority)
   ```bash
   pytest -v -m "not slow" tests/
   ```

2. **pyproject.toml** (default, automatically used)
   ```bash
   pytest tests/  # Uses pyproject.toml automatically
   ```

**Note:** The project uses `pyproject.toml` as the single source of truth. CI-specific options are passed via command-line arguments in `scripts/run-tests.sh`.

---

## Best Practices

### For Local Development
1. Use `pyproject.toml` as the primary config (automatic)
2. Use `./scripts/run-tests.sh unit` for fast feedback
3. Use `./scripts/run-tests.sh all` before committing

### For CI/CD
1. Use `./scripts/run-tests.sh ci` which passes CI-specific options via command-line
2. Options include: `-m "not slow and not external_service" --maxfail=5`
3. Focuses on `tests/` directory (not `backend-django/tests`)

### For Production
1. Use environment variables from `env.example` as reference
2. Never commit `.env` files with secrets
3. Use secret management (GCP Secret Manager, etc.)

---

## Troubleshooting

### Tests Not Running
- Check `DJANGO_SETTINGS_MODULE` is set correctly
- Verify `pythonpath` includes project root
- Ensure test files match `python_files` pattern

### Import Errors
- Verify `pythonpath` in `pyproject.toml` includes all necessary directories
- Check that `tests/utils/test_utils.py` is imported for path setup
- Ensure virtual environment is activated

### CI Tests Failing
- Check if tests are marked with `@pytest.mark.slow` or `@pytest.mark.external_service`
- Verify CI script is using correct options: `./scripts/run-tests.sh ci`
- Review `--maxfail` setting (may stop after 5 failures)

---

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) - Development setup
- [INFRASTRUCTURE.md](INFRASTRUCTURE.md) - Infrastructure details
- [WORKFLOWS.md](WORKFLOWS.md) - Operational workflows

---

**Last Updated:** 2025-01-XX  
**Maintained by:** Development Team

