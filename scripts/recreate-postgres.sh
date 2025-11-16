#!/bin/bash
# Script to delete and recreate the Cloud SQL PostgreSQL instance
# WARNING: This will delete all data in the database!

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}⚠️  WARNING: This script will DELETE the PostgreSQL instance and all its data!${NC}"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Check for authentication
echo -e "${YELLOW}Checking Google Cloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ No active Google Cloud authentication found.${NC}"
    echo -e "${YELLOW}Please authenticate first:${NC}"
    echo "  gcloud auth login"
    echo "  gcloud auth application-default login"
    exit 1
fi

# Get the project ID and region from Terraform
cd infra/gcp

# Check if terraform is initialized
if [ ! -d ".terraform" ]; then
    echo -e "${YELLOW}Initializing Terraform...${NC}"
    terraform init
fi

echo -e "${YELLOW}Step 1: Disabling deletion protection...${NC}"
# Temporarily set deletion_protection to false
sed -i.bak 's/deletion_protection = true/deletion_protection = false/' main.tf

echo -e "${YELLOW}Step 2: Applying Terraform to disable deletion protection...${NC}"
terraform apply -target=google_sql_database_instance.postgres -auto-approve

echo -e "${YELLOW}Step 3: Destroying the PostgreSQL instance and related resources...${NC}"
echo -e "${BLUE}Using gcloud to delete the instance directly (avoids Terraform dependency issues)...${NC}"

# Get project ID - try multiple sources
PROJECT_ID=""

# First, try gcloud config (most reliable)
PROJECT_ID=$(gcloud config get-value project 2>/dev/null | tr -d '\n' | xargs)

# If empty, try Terraform variables file
if [ -z "$PROJECT_ID" ] && [ -f terraform.tfvars ]; then
    PROJECT_ID=$(grep -E '^\s*project_id\s*=' terraform.tfvars | sed 's/.*=\s*"\([^"]*\)".*/\1/' | head -1 | tr -d '[:space:]')
fi

# If still empty, use known default
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "" ]; then
    PROJECT_ID="nadlaner-production"
    echo -e "${YELLOW}Using default project ID: ${PROJECT_ID}${NC}"
    echo -e "${BLUE}To use a different project, run: gcloud config set project YOUR_PROJECT_ID${NC}"
fi

echo -e "${BLUE}Using project: ${PROJECT_ID}${NC}"
INSTANCE_NAME="nadlaner-postgres"

# Check if instance exists
if ! gcloud sql instances describe ${INSTANCE_NAME} --project=${PROJECT_ID} &>/dev/null; then
    echo -e "${YELLOW}Instance ${INSTANCE_NAME} not found. It may have already been deleted.${NC}"
    echo -e "${YELLOW}Removing from Terraform state and proceeding to recreation...${NC}"
    terraform state rm google_sql_database.app 2>/dev/null || true
    terraform state rm google_sql_user.app 2>/dev/null || true
    terraform state rm google_sql_database_instance.postgres 2>/dev/null || true
else
    # Delete database and user first using gcloud (they'll be auto-deleted with instance, but let's be explicit)
    echo -e "${YELLOW}Deleting database and user...${NC}"
    gcloud sql databases delete nadlaner --instance=${INSTANCE_NAME} --project=${PROJECT_ID} --quiet 2>/dev/null || true
    gcloud sql users delete nadlaner --instance=${INSTANCE_NAME} --project=${PROJECT_ID} --quiet 2>/dev/null || true

    # Delete the instance using gcloud (this is safer than Terraform destroy which tries to resolve dependencies)
    echo -e "${YELLOW}Deleting PostgreSQL instance (this may take a few minutes)...${NC}"
    gcloud sql instances delete ${INSTANCE_NAME} --project=${PROJECT_ID} --quiet

    echo -e "${GREEN}✓ Instance deleted${NC}"

    # Remove from Terraform state since we deleted it manually
    echo -e "${YELLOW}Removing deleted resources from Terraform state...${NC}"
    terraform state rm google_sql_database.app 2>/dev/null || true
    terraform state rm google_sql_user.app 2>/dev/null || true
    terraform state rm google_sql_database_instance.postgres 2>/dev/null || true
fi

echo -e "${YELLOW}Step 4: Re-enabling deletion protection...${NC}"
# Restore deletion_protection to true
sed -i.bak 's/deletion_protection = false/deletion_protection = true/' main.tf
rm -f main.tf.bak

echo -e "${YELLOW}Step 5: Recreating the PostgreSQL instance...${NC}"
terraform apply -auto-approve

echo -e "${GREEN}✅ PostgreSQL instance has been recreated successfully!${NC}"
echo -e "${YELLOW}Note: You may need to run database migrations to set up your schema.${NC}"

