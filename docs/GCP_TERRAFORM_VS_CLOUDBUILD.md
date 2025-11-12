# Terraform vs Cloud Build: Understanding the Difference

## Overview

**Terraform** and **Cloud Build** serve different but complementary purposes in your GCP deployment:

| Aspect | Terraform (`infra/gcp/main.tf`) | Cloud Build (`cloudbuild.yaml`) |
|--------|--------------------------------|--------------------------------|
| **Purpose** | Infrastructure as Code (IaC) | Continuous Integration/Deployment (CI/CD) |
| **What it manages** | GCP resources (services, databases, networking) | Application builds and deployments |
| **When it runs** | Manually or via CI/CD (infrastructure changes) | Automatically on every code push |
| **What it creates** | Cloud Run services, Cloud SQL, Redis, VPC, etc. | Docker images and deploys them |
| **Frequency** | Infrequent (when infrastructure changes) | Frequent (every code change) |

## Terraform: Infrastructure Provisioning

**File**: `infra/gcp/main.tf`

**What it does:**
- Creates and manages GCP infrastructure resources
- Provisions Cloud Run services (but doesn't deploy code to them)
- Sets up Cloud SQL PostgreSQL database
- Creates Memorystore Redis instance
- Configures VPC networking and serverless connectors
- Sets up Cloud Storage buckets
- Creates Artifact Registry repository
- Configures HTTPS Load Balancer and Cloud Armor
- Sets up Cloud DNS records
- Manages IAM roles and service accounts

**Key point**: Terraform creates the **empty** Cloud Run services. It doesn't build or deploy your application code.

**Example**: When you run `terraform apply`, it creates:
```hcl
resource "google_cloud_run_service" "api" {
  name     = "nadlaner-api"
  # ... configuration ...
  containers {
    image = var.api_image  # ← This is just a placeholder/reference
  }
}
```

The `var.api_image` is just a reference to where the image **should be**. Terraform doesn't build it.

## Cloud Build: Application Deployment

**File**: `cloudbuild.yaml`

**What it does:**
- Builds Docker images from your source code
- Pushes images to Artifact Registry
- Deploys new revisions to existing Cloud Run services
- Runs automatically when you push to GitHub

**Key point**: Cloud Build assumes the infrastructure already exists (created by Terraform) and focuses on building and deploying your application.

**Example**: When you push code, Cloud Build:
1. Builds: `docker build -f backend-django/Dockerfile .`
2. Pushes: `docker push me-west1-docker.pkg.dev/.../api:latest`
3. Deploys: `gcloud run deploy nadlaner-api --image=...`

## How They Work Together

```
┌─────────────────────────────────────────────────────────────┐
│                    Initial Setup (Once)                      │
│                                                               │
│  1. Run Terraform                                             │
│     → Creates Cloud Run services (empty)                     │
│     → Creates Cloud SQL, Redis, VPC, etc.                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Continuous Deployment (Every Push)              │
│                                                               │
│  2. Push code to GitHub                                      │
│     → Triggers Cloud Build                                   │
│     → Builds Docker images                                   │
│     → Pushes to Artifact Registry                            │
│     → Deploys to existing Cloud Run services                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Typical Workflow

### First Time Setup

1. **Provision Infrastructure** (Terraform):
   ```bash
   cd infra/gcp
   terraform init
   terraform apply
   ```
   This creates all GCP resources but services are empty (no code deployed yet).

2. **Build and Deploy Initial Version** (Cloud Build):
   ```bash
   gcloud builds submit --config=cloudbuild.yaml
   ```
   Or push to GitHub to trigger automatic build.

### Ongoing Development

**Every code change:**
- Push to GitHub → Cloud Build automatically builds and deploys
- No Terraform changes needed unless infrastructure changes

**Infrastructure changes:**
- Update `infra/gcp/main.tf`
- Run `terraform apply`
- Cloud Build continues to work normally

## Key Differences Summary

### Terraform
- ✅ Creates infrastructure (services, databases, networking)
- ✅ Manages infrastructure state
- ✅ Idempotent (can run multiple times safely)
- ❌ Doesn't build application code
- ❌ Doesn't deploy application code

### Cloud Build
- ✅ Builds Docker images from source code
- ✅ Pushes images to Artifact Registry
- ✅ Deploys code to existing Cloud Run services
- ✅ Runs automatically on code changes
- ❌ Doesn't create infrastructure
- ❌ Assumes infrastructure already exists

## When to Use Each

### Use Terraform when:
- Setting up infrastructure for the first time
- Adding new GCP resources (databases, buckets, etc.)
- Changing infrastructure configuration
- Managing infrastructure state

### Use Cloud Build when:
- Deploying application code changes
- Building Docker images
- Automating deployments from GitHub
- Running CI/CD pipelines

## Configuration Files

### Terraform Configuration
- **Main file**: `infra/gcp/main.tf`
- **Variables**: `infra/gcp/variables.tf`
- **Values**: `infra/gcp/terraform.tfvars` (not in git)
- **Example**: `infra/gcp/terraform.tfvars.example`

### Cloud Build Configuration
- **Build config**: `cloudbuild.yaml` (in repo root)
- **Dockerfile**: `backend-django/Dockerfile`
- **Trigger setup**: Via GCP Console or `scripts/setup-gcp-cd.sh`

## Important Notes

1. **Artifact Registry Name**: Both use `realestate-agent` as the repository name
   - Terraform creates it: `resource "google_artifact_registry_repository" "app" { repository_id = "realestate-agent" }`
   - Cloud Build uses it: `_REPO_NAME: 'realestate-agent'`

2. **Image References**: 
   - Terraform expects images to exist (created by Cloud Build)
   - Cloud Build creates the images Terraform references

3. **Service Names**: Both use the same service names:
   - API: `nadlaner-api`
   - Worker: `nadlaner-worker`

4. **Region**: Both use `me-west1` (Tel Aviv region)

## Best Practices

1. **Infrastructure changes**: Always use Terraform, never modify manually in GCP Console
2. **Code deployments**: Let Cloud Build handle it automatically via GitHub triggers
3. **State management**: Keep Terraform state in a remote backend (GCS bucket)
4. **Versioning**: Tag Docker images with commit SHAs for traceability
5. **Separation**: Keep infrastructure code (Terraform) separate from application code

