#!/bin/bash
set -euo pipefail

# Script to set up Cloud Build trigger for continuous deployment from GitHub

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default values
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-me-west1}"
REPO_NAME="${REPO_NAME:-realestate-agent}"
REPO_OWNER="${REPO_OWNER:-}"
BRANCH="${BRANCH:-main}"
TRIGGER_NAME="${TRIGGER_NAME:-deploy-backend}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID environment variable is required"
    echo "Usage: PROJECT_ID=your-project-id REPO_OWNER=your-github-username ./scripts/setup-gcp-cd.sh"
    exit 1
fi

if [ -z "$REPO_OWNER" ]; then
    echo "Error: REPO_OWNER environment variable is required (your GitHub username or organization)"
    echo "Usage: PROJECT_ID=your-project-id REPO_OWNER=your-github-username ./scripts/setup-gcp-cd.sh"
    exit 1
fi

echo "Setting up Cloud Build trigger for continuous deployment"
echo "Project: $PROJECT_ID"
echo "Repository: $REPO_OWNER/$REPO_NAME"
echo "Branch: $BRANCH"
echo ""

# Check if Cloud Build API is enabled
echo "Checking Cloud Build API..."
if ! gcloud services list --enabled --project="$PROJECT_ID" | grep -q "cloudbuild.googleapis.com"; then
    echo "Enabling Cloud Build API..."
    gcloud services enable cloudbuild.googleapis.com --project="$PROJECT_ID"
fi

# Get project number for service account
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

echo ""
echo "Granting permissions to Cloud Build service account..."
echo "Service Account: $CLOUD_BUILD_SA"

# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/run.admin" \
    --condition=None \
    --quiet || echo "  ✓ Cloud Run Admin (may already be granted)"

# Grant Service Account User role
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None \
    --quiet || echo "  ✓ Service Account User (may already be granted)"

# Grant Artifact Registry Writer role
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/artifactregistry.writer" \
    --condition=None \
    --quiet || echo "  ✓ Artifact Registry Writer (may already be granted)"

echo ""
echo "Creating Cloud Build trigger..."

# Check if trigger already exists
if gcloud builds triggers list --project="$PROJECT_ID" --filter="name:$TRIGGER_NAME" --format="value(name)" | grep -q "$TRIGGER_NAME"; then
    echo "Trigger '$TRIGGER_NAME' already exists. Updating..."
    gcloud builds triggers update github \
        --name="$TRIGGER_NAME" \
        --repo-name="$REPO_NAME" \
        --repo-owner="$REPO_OWNER" \
        --branch-pattern="^${BRANCH}$" \
        --build-config="cloudbuild.yaml" \
        --region="$REGION" \
        --substitutions="_REGION=$REGION,_REPO_NAME=realestate-agent,_API_SERVICE_NAME=nadlaner-api,_WORKER_SERVICE_NAME=nadlaner-worker" \
        --project="$PROJECT_ID"
    echo "✓ Trigger updated"
else
    echo "Creating new trigger..."
    gcloud builds triggers create github \
        --name="$TRIGGER_NAME" \
        --repo-name="$REPO_NAME" \
        --repo-owner="$REPO_OWNER" \
        --branch-pattern="^${BRANCH}$" \
        --build-config="cloudbuild.yaml" \
        --region="$REGION" \
        --substitutions="_REGION=$REGION,_REPO_NAME=realestate-agent,_API_SERVICE_NAME=nadlaner-api,_WORKER_SERVICE_NAME=nadlaner-worker" \
        --project="$PROJECT_ID"
    echo "✓ Trigger created"
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Connect your GitHub repository in the GCP Console:"
echo "   https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
echo ""
echo "2. If this is the first time, you'll need to:"
echo "   - Click 'Connect Repository'"
echo "   - Authenticate with GitHub"
echo "   - Select your repository"
echo ""
echo "3. Test the trigger by pushing to the $BRANCH branch:"
echo "   git push origin $BRANCH"
echo ""
echo "4. Monitor builds at:"
echo "   https://console.cloud.google.com/cloud-build/builds?project=$PROJECT_ID"
echo ""



