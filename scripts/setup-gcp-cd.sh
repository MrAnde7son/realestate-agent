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

# Grant Cloud Run Invoker role (needed when deploying with --allow-unauthenticated)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/run.invoker" \
    --condition=None \
    --quiet || echo "  ✓ Cloud Run Invoker (may already be granted)"

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

# Grant Secret Manager Admin role (required for GitHub OAuth token storage in second-gen)
echo "Granting Secret Manager Admin role (required for GitHub connections)..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/secretmanager.admin" \
    --condition=None \
    --quiet || echo "  ✓ Secret Manager Admin (may already be granted)"

# Grant Secret Manager Secret Accessor role
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None \
    --quiet || echo "  ✓ Secret Manager Secret Accessor (may already be granted)"

echo ""
echo "Checking GitHub repository connection..."

# Check if any GitHub connections exist
CONNECTED_REPOS=$(gcloud builds triggers list --project="$PROJECT_ID" --format="value(github.owner)" 2>/dev/null | sort -u || echo "")

if [ -z "$CONNECTED_REPOS" ]; then
    echo ""
    echo "⚠️  WARNING: GitHub repository not connected to Cloud Build yet!"
    echo ""
    echo "You must connect your GitHub repository through the GCP Console first."
    echo "The CLI cannot create triggers for unconnected repositories."
    echo ""
    echo "Please follow these steps:"
    echo ""
    echo "STEP 0: Grant Secret Manager Permissions (REQUIRED FIRST!)"
    echo "⚠️  If you're getting OAuth callback errors, run these commands first:"
    echo ""
    echo "   PROJECT_ID=$PROJECT_ID"
    echo "   PROJECT_NUMBER=\$(gcloud projects describe \$PROJECT_ID --format=\"value(projectNumber)\")"
    echo "   CLOUD_BUILD_SA=\"\${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com\""
    echo ""
    echo "   gcloud projects add-iam-policy-binding \$PROJECT_ID \\"
    echo "     --member=\"serviceAccount:\${CLOUD_BUILD_SA}\" \\"
    echo "     --role=\"roles/secretmanager.admin\""
    echo ""
    echo "   gcloud projects add-iam-policy-binding \$PROJECT_ID \\"
    echo "     --member=\"serviceAccount:\${CLOUD_BUILD_SA}\" \\"
    echo "     --role=\"roles/secretmanager.secretAccessor\""
    echo ""
    echo "STEP 1: Create Host Connection (Second-Gen)"
    echo "1. Go to Cloud Build Repositories:"
    echo "   https://console.cloud.google.com/cloud-build/repositories?project=$PROJECT_ID"
    echo ""
    echo "2. Click 'Connect Repository'"
    echo "3. Select 'GitHub (Cloud Build GitHub App)' - This is second-gen (recommended)"
    echo "   ⚠️  Do NOT select 'GitHub (first generation)' - that's the legacy option"
    echo ""
    echo "4. Configure Host Connection:"
    echo "   - Region: Select 'me-west1 (Tel Aviv)'"
    echo "   - Name: Keep 'github.com' (for regular GitHub, not Enterprise)"
    echo "   - Click 'Connect'"
    echo "   - You'll be redirected to GitHub to authorize"
    echo "   - Authorize the Cloud Build GitHub App"
    echo "   - Select repositories to grant access (or select all)"
    echo "   - Complete the authorization"
    echo ""
    echo "STEP 2: Connect Your Repository"
    echo "5. After host connection is created, you'll see your repositories listed"
    echo "6. Find '$REPO_NAME' and click 'Connect'"
    echo ""
    echo "STEP 3: Create Trigger"
    echo "7. After connecting the repository, run this script again to create the trigger."
    echo "   Or create the trigger manually in Cloud Build Triggers page."
    echo ""
    echo "Alternatively, you can create the trigger manually in the Console:"
    echo "   - Event: Push to a branch"
    echo "   - Branch: ^main$"
    echo "   - Configuration file: cloudbuild.yaml"
    echo "   - Substitution variables:"
    echo "     _REGION = $REGION"
    echo "     _REPO_NAME = realestate-agent"
    echo "     _API_SERVICE_NAME = nadlaner-api"
    echo "     _WORKER_SERVICE_NAME = nadlaner-worker"
    echo ""
    exit 1
fi

echo "✓ GitHub connection found"
echo ""
echo "Creating Cloud Build trigger..."

# Check if trigger already exists
if gcloud builds triggers list --project="$PROJECT_ID" --filter="name:$TRIGGER_NAME" --format="value(name)" 2>/dev/null | grep -q "$TRIGGER_NAME"; then
    echo "Trigger '$TRIGGER_NAME' already exists. Updating..."
    if gcloud builds triggers update github \
        --name="$TRIGGER_NAME" \
        --repo-name="$REPO_NAME" \
        --repo-owner="$REPO_OWNER" \
        --branch-pattern="^${BRANCH}$" \
        --build-config="cloudbuild.yaml" \
        --region="$REGION" \
        --substitutions="_REGION=$REGION,_REPO_NAME=realestate-agent,_API_SERVICE_NAME=nadlaner-api,_WORKER_SERVICE_NAME=nadlaner-worker" \
        --project="$PROJECT_ID" 2>&1; then
        echo "✓ Trigger updated"
    else
        echo "⚠️  Failed to update trigger. You may need to update it manually in the Console."
        exit 1
    fi
else
    echo "Creating new trigger..."
    if gcloud builds triggers create github \
        --name="$TRIGGER_NAME" \
        --repo-name="$REPO_NAME" \
        --repo-owner="$REPO_OWNER" \
        --branch-pattern="^${BRANCH}$" \
        --build-config="cloudbuild.yaml" \
        --region="$REGION" \
        --substitutions="_REGION=$REGION,_REPO_NAME=realestate-agent,_API_SERVICE_NAME=nadlaner-api,_WORKER_SERVICE_NAME=nadlaner-worker" \
        --project="$PROJECT_ID" 2>&1; then
        echo "✓ Trigger created successfully"
    else
        echo ""
        echo "⚠️  Failed to create trigger via CLI."
        echo ""
        echo "This might happen if:"
        echo "  - The repository connection was just created (wait a few seconds and try again)"
        echo "  - The repository name or owner doesn't match the connected repository"
        echo ""
        echo "Please create the trigger manually in the Console:"
        echo "  https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
        echo ""
        echo "Or verify the repository connection and try again."
        exit 1
    fi
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



