#!/bin/bash
set -euo pipefail

# Script to fix Secret Manager permissions for Cloud Build GitHub connections
# This removes conditional permissions and adds unconditional ones

PROJECT_ID="${PROJECT_ID:-nadlaner-production}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID environment variable is required"
    echo "Usage: PROJECT_ID=your-project-id ./scripts/fix-secret-manager-permissions.sh"
    exit 1
fi

echo "=========================================="
echo "Fixing Secret Manager Permissions"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo ""

# Get project number for service account
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
CLOUD_BUILD_SERVICE_AGENT="service-${PROJECT_NUMBER}@gcp-sa-cloudbuild.iam.gserviceaccount.com"

echo "Cloud Build Service Account: $CLOUD_BUILD_SA"
echo "Cloud Build Service Agent: $CLOUD_BUILD_SERVICE_AGENT"
echo ""

# Add unconditional Secret Manager Admin role
echo "Adding unconditional Secret Manager Admin role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/secretmanager.admin" \
    --condition=None \
    --quiet || echo "  ⚠ May already exist (this is OK)"

# Add unconditional Secret Manager Secret Accessor role
echo "Adding unconditional Secret Manager Secret Accessor role..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None \
    --quiet || echo "  ⚠ May already exist (this is OK)"

# Also grant to Cloud Build Service Agent
echo "Adding Secret Manager Admin to Cloud Build Service Agent..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SERVICE_AGENT}" \
    --role="roles/secretmanager.admin" \
    --condition=None \
    --quiet || echo "  ⚠ May already exist (this is OK)"

echo ""
echo "Checking for broken secrets from failed connection attempts..."
echo ""

# List secrets that might be from failed GitHub connection attempts
BROKEN_SECRETS=$(gcloud secrets list --project="$PROJECT_ID" --filter="name~github.*oauth" --format="value(name)" 2>/dev/null || echo "")

if [ -n "$BROKEN_SECRETS" ]; then
    echo "Found potentially broken secrets:"
    echo "$BROKEN_SECRETS"
    echo ""
    echo "⚠️  You may need to delete these secrets manually if they're causing issues:"
    echo ""
    for SECRET in $BROKEN_SECRETS; do
        echo "  gcloud secrets delete $SECRET --project=$PROJECT_ID"
    done
    echo ""
    echo "Or delete them via Console:"
    echo "https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
    echo ""
else
    echo "No broken secrets found."
    echo ""
fi

echo "=========================================="
echo "Permissions updated!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Wait 30-60 seconds for permissions to propagate"
echo "2. Try connecting GitHub again in the GCP Console"
echo "3. If you still get errors, check for and delete any broken secrets"
echo ""
echo "Note: If there are conditional permissions causing issues,"
echo "you may need to remove them manually in the GCP Console:"
echo "https://console.cloud.google.com/iam-admin/iam?project=$PROJECT_ID"
echo ""
echo "Look for bindings with condition 'cloudbuild-connection-setup' and"
echo "remove them if they're causing conflicts."
echo ""

