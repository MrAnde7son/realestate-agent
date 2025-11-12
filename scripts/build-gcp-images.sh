#!/bin/bash
set -euo pipefail

# Build script for GCP Cloud Run images
# Ensures the build context is the repository root

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

# Default values
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-me-west1}"
REPO_NAME="${REPO_NAME:-realestate-agent}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID environment variable is required"
    echo "Usage: PROJECT_ID=your-project-id ./scripts/build-gcp-images.sh"
    exit 1
fi

ARTIFACT_REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

echo "Building images for project: $PROJECT_ID"
echo "Artifact Registry: $ARTIFACT_REGISTRY"
echo "Build context: $REPO_ROOT"
echo ""

# Build API image
echo "Building Django API image..."
docker build \
    -t "${ARTIFACT_REGISTRY}/api:${IMAGE_TAG}" \
    -f backend-django/Dockerfile \
    .  # <-- Repository root as build context

# Build Worker image
echo "Building Celery Worker image..."
docker build \
    -t "${ARTIFACT_REGISTRY}/worker:${IMAGE_TAG}" \
    -f orchestration/Dockerfile.celery \
    .  # <-- Repository root as build context

echo ""
echo "Images built successfully!"
echo ""
echo "To push images to Artifact Registry:"
echo "  docker push ${ARTIFACT_REGISTRY}/api:${IMAGE_TAG}"
echo "  docker push ${ARTIFACT_REGISTRY}/worker:${IMAGE_TAG}"
echo ""
echo "Or use Cloud Build:"
echo "  gcloud builds submit --config=cloudbuild.yaml"

