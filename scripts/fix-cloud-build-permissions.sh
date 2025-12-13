#!/bin/bash
set -euo pipefail

# Script to fix Cloud Build IAM permissions for GCP deployment
# This script grants all necessary permissions to the Cloud Build service account

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-europe-west1}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID environment variable is required"
    echo "Usage: PROJECT_ID=your-project-id [REGION=europe-west1] ./scripts/fix-cloud-build-permissions.sh"
    exit 1
fi

echo "=========================================="
echo "Fixing Cloud Build IAM Permissions"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Get project number for service account
echo "Getting project number..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

echo "Cloud Build Service Account: $CLOUD_BUILD_SA"
echo ""

# Check current permissions
echo "Checking current permissions..."
echo "----------------------------------------"
gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --filter="bindings.members:${CLOUD_BUILD_SA}" \
    --format="table(bindings.role)" || echo "No permissions found or error checking permissions"
echo ""

# Grant required permissions
echo "Granting required permissions..."
echo "----------------------------------------"

# Cloud Run Admin - Required to deploy Cloud Run services
echo "Granting Cloud Run Admin role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/run.admin" \
    --condition=None \
    --quiet && echo "  ✓ Cloud Run Admin granted" || echo "  ⚠ Cloud Run Admin (may already be granted or error occurred)"

# Cloud Run Invoker - Required when deploying with --allow-unauthenticated
echo "Granting Cloud Run Invoker role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/run.invoker" \
    --condition=None \
    --quiet && echo "  ✓ Cloud Run Invoker granted" || echo "  ⚠ Cloud Run Invoker (may already be granted or error occurred)"

# Service Account User - Required to use Cloud Run service accounts
echo "Granting Service Account User role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None \
    --quiet && echo "  ✓ Service Account User granted" || echo "  ⚠ Service Account User (may already be granted or error occurred)"

# Artifact Registry Writer - Required to push Docker images
echo "Granting Artifact Registry Writer role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/artifactregistry.writer" \
    --condition=None \
    --quiet && echo "  ✓ Artifact Registry Writer granted" || echo "  ⚠ Artifact Registry Writer (may already be granted or error occurred)"

# Storage Admin - Required to pull base images from GCR/AR and access build artifacts
echo "Granting Storage Admin role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/storage.admin" \
    --condition=None \
    --quiet && echo "  ✓ Storage Admin granted" || echo "  ⚠ Storage Admin (may already be granted or error occurred)"

# Cloud Build Service Account - Required for Cloud Build to operate
echo "Granting Cloud Build Service Account role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/cloudbuild.builds.builder" \
    --condition=None \
    --quiet && echo "  ✓ Cloud Build Service Account role granted" || echo "  ⚠ Cloud Build Service Account role (may already be granted or error occurred)"

# Logging Writer - Required for build logs
echo "Granting Logging Writer role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/logging.logWriter" \
    --condition=None \
    --quiet && echo "  ✓ Logging Writer granted" || echo "  ⚠ Logging Writer (may already be granted or error occurred)"

# Source Repository Reader - If using source repos
echo "Granting Source Repository Reader role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/source.reader" \
    --condition=None \
    --quiet && echo "  ✓ Source Repository Reader granted" || echo "  ⚠ Source Repository Reader (may already be granted or error occurred)"

echo ""
echo "=========================================="
echo "Verifying permissions..."
echo "=========================================="
gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --filter="bindings.members:${CLOUD_BUILD_SA}" \
    --format="table(bindings.role)"

echo ""
echo "=========================================="
echo "Permission fix complete!"
echo "=========================================="
echo ""
echo "If you're still experiencing permission errors:"
echo "1. Wait a few minutes for IAM changes to propagate"
echo "2. Check the specific error message in Cloud Build logs"
echo "3. Verify the Artifact Registry repository exists:"
echo "   gcloud artifacts repositories list --location=$REGION --project=$PROJECT_ID"
echo "4. Verify Cloud Run services exist:"
echo "   gcloud run services list --region=$REGION --project=$PROJECT_ID"
echo ""
echo "To check build logs:"
echo "   gcloud builds list --project=$PROJECT_ID --limit=5"
echo ""

