# GCP Migration Checklist

## Overview

This document outlines the migration plan for moving all services (except UI) to Google Cloud Platform (GCP). The UI remains on Vercel, while backend services migrate to GCP in the `me-west1` region.

## ✅ Completed Infrastructure

### Core Services
- [x] VPC Network with private IPs
- [x] Cloud SQL PostgreSQL (Regional HA)
- [x] Memorystore Redis
- [x] Cloud Run for Django API
- [x] Cloud Run for Celery Worker
- [x] HTTPS Load Balancer with Cloud Armor
- [x] Cloud DNS
- [x] Service Accounts with proper IAM

### New Additions
- [x] Artifact Registry for container images
- [x] Cloud Storage buckets for static/media files
- [x] Secret Manager IAM permissions
- [x] Cloud Scheduler (optional, for Celery Beat replacement)

## 📋 Pre-Migration Checklist

### 1. GCP Project Setup
- [ ] Create GCP project (or use existing)
- [ ] Enable billing
- [ ] Set up authentication (Service Account or User credentials)
- [ ] Configure `terraform.tfvars` with project details

### 2. Container Images
- [ ] Build and push Django API image to Artifact Registry
- [ ] Build and push Celery Worker image to Artifact Registry
- [ ] Test images locally
- [ ] Set up CI/CD pipeline for automated builds

### 3. Database Migration
- [ ] Export data from current database
- [ ] Create database backup strategy
- [ ] Plan migration window (if needed)
- [ ] Test database connection from Cloud Run

### 4. Secrets Management
- [ ] Create secrets in Secret Manager:
  - `DJANGO_SECRET_KEY`
  - `DATABASE_PASSWORD` (or use Cloud SQL managed password)
  - `REDIS_PASSWORD` (if using auth)
  - API keys (Resend, Twilio, etc.)
  - OAuth credentials
- [ ] Update Terraform to reference secrets
- [ ] Test secret access from Cloud Run

### 5. Static/Media Files Migration
- [ ] Upload existing static files to Cloud Storage
- [ ] Upload existing media files to Cloud Storage
- [ ] Configure Django `STATIC_URL` and `MEDIA_URL` to use GCS
- [ ] Set up signed URLs for media files
- [ ] Configure CORS on buckets if needed

### 6. DNS Configuration
- [ ] Verify domain ownership in GCP
- [ ] Create DNS zone (or use existing)
- [ ] Update nameservers if creating new zone
- [ ] Configure A record for `api.<domain>`
- [ ] Configure CNAME for apex domain (Vercel)

### 7. Network Security
- [ ] Configure Cloud Armor rules (IP allowlists)
- [ ] Set up firewall rules if needed
- [ ] Review VPC connector configuration
- [ ] Test private IP connectivity

## 🚀 Migration Steps

### Phase 1: Infrastructure Provisioning

1. **Initialize Terraform**
   ```bash
   cd infra/gcp
   terraform init
   ```

2. **Review Plan**
   ```bash
   terraform plan -var-file=terraform.tfvars
   ```

3. **Apply Infrastructure**
   ```bash
   terraform apply -var-file=terraform.tfvars
   ```

4. **Verify Resources**
   - Check Cloud SQL instance
   - Check Memorystore Redis
   - Check Cloud Storage buckets
   - Check Artifact Registry repository

### Phase 2: Application Deployment

1. **Build and Push Images**
   ```bash
   # Build API image
   docker build -t gcr.io/PROJECT_ID/nadlaner-api:latest -f backend-django/Dockerfile .
   docker push gcr.io/PROJECT_ID/nadlaner-api:latest
   
   # Build Worker image
   docker build -t gcr.io/PROJECT_ID/nadlaner-worker:latest -f orchestration/Dockerfile.celery .
   docker push gcr.io/PROJECT_ID/nadlaner-worker:latest
   ```

2. **Update Terraform Variables**
   - Set `api_image` and `worker_image` to pushed images
   - Add environment variables for secrets
   - Re-apply Terraform

3. **Deploy Services**
   ```bash
   terraform apply -var-file=terraform.tfvars
   ```

### Phase 3: Data Migration

1. **Database Migration**
   - Export from current database
   - Import to Cloud SQL
   - Run Django migrations
   - Verify data integrity

2. **Static/Media Files**
   - Upload static files to GCS bucket
   - Upload media files to GCS bucket
   - Update Django settings

### Phase 4: DNS & Testing

1. **DNS Cutover**
   - Update DNS records
   - Wait for propagation
   - Test API endpoints

2. **Functional Testing**
   - Test API endpoints
   - Test Celery tasks
   - Test authentication
   - Test file uploads/downloads

### Phase 5: Monitoring & Optimization

1. **Set Up Monitoring**
   - Enable Cloud Monitoring
   - Set up alerts for errors
   - Monitor database performance
   - Monitor Cloud Run metrics

2. **Optimize Costs**
   - Review Cloud Run scaling
   - Optimize database instance size
   - Review storage lifecycle policies

## 🔧 Configuration Changes Required

### Django Settings

Update `backend-django/broker_backend/settings.py`:

```python
# Database - Cloud SQL connection
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': f'/cloudsql/{os.getenv("CLOUD_SQL_CONNECTION_NAME")}',
        'PORT': '',
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Redis - Memorystore
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Static/Media files - Cloud Storage
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
GS_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
```

### Environment Variables

Add to Cloud Run services via Terraform:

```hcl
api_env_vars = {
  CLOUD_SQL_CONNECTION_NAME = google_sql_database_instance.postgres.connection_name
  GCS_BUCKET_NAME          = google_storage_bucket.static.name
  GCS_MEDIA_BUCKET_NAME    = google_storage_bucket.media.name
  GCP_PROJECT_ID           = var.project_id
  # Secrets from Secret Manager
  DJANGO_SECRET_KEY        = "projects/${var.project_id}/secrets/django-secret-key/versions/latest:secret"
}
```

## ⚠️ Important Considerations

### Celery Beat Replacement

The current setup uses Celery Beat for periodic tasks. Options:

1. **Keep Celery Beat** - Run as separate Cloud Run service (recommended)
2. **Use Cloud Scheduler** - Replace with Cloud Scheduler calling API endpoints
3. **Hybrid** - Use Cloud Scheduler for critical tasks, Celery Beat for others

### Cost Optimization

- **Cloud Run**: Pay per request, scale to zero
- **Cloud SQL**: Consider smaller instance for dev/test
- **Memorystore**: Start with 1GB, scale as needed
- **Storage**: Configure lifecycle policies to delete old files

### Security Best Practices

- [ ] Use Secret Manager for all sensitive data
- [ ] Enable Cloud Armor WAF rules
- [ ] Restrict Cloud Run ingress (internal-only where possible)
- [ ] Use private IPs for database/Redis
- [ ] Enable Cloud SQL SSL connections
- [ ] Rotate secrets regularly

### Backup Strategy

- [ ] Enable Cloud SQL automated backups
- [ ] Set up Cloud Storage bucket versioning
- [ ] Configure backup retention policies
- [ ] Test restore procedures

## 📊 Monitoring & Alerts

Recommended Cloud Monitoring alerts:

1. **API Errors**: Error rate > 5%
2. **Database**: CPU > 80% or connection count > 90%
3. **Cloud Run**: Latency p99 > 2s
4. **Memorystore**: Memory usage > 80%
5. **Storage**: Bucket size > 90% quota

## 🔄 Rollback Plan

If issues occur:

1. **DNS Rollback**: Revert DNS records to previous infrastructure
2. **Service Rollback**: Use Cloud Run revision rollback
3. **Database Rollback**: Restore from Cloud SQL backup
4. **Terraform Rollback**: Use `terraform destroy` (carefully!)

## 📝 Terraform Variables Example

```hcl
# terraform.tfvars
project_id        = "nadlaner-prod"
domain            = "nadlaner.com"
ui_cname_target   = "cname.vercel-dns.com."
api_image         = "me-west1-docker.pkg.dev/nadlaner-prod/nadlaner-app/api:latest"
worker_image      = "me-west1-docker.pkg.dev/nadlaner-prod/nadlaner-app/worker:latest"
db_password       = "change-me-in-production"
allowed_office_cidrs = ["203.0.113.0/24"]
enable_cloud_scheduler = false
labels = {
  environment = "production"
  owner        = "nadlaner-platform"
}
```

## ✅ Post-Migration Tasks

- [ ] Update CI/CD pipelines
- [ ] Update documentation
- [ ] Train team on GCP services
- [ ] Set up cost alerts
- [ ] Review and optimize resource sizes
- [ ] Set up disaster recovery procedures

