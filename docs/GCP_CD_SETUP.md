# GCP Continuous Deployment Setup

This guide explains how to set up automatic deployment from GitHub to GCP Cloud Run.

## Overview

When you push code to GitHub, Cloud Build will:
1. Build Docker images from your code
2. Push images to Artifact Registry
3. Deploy new revisions to Cloud Run services

## Prerequisites

- GCP project with billing enabled
- Cloud Build API enabled
- Artifact Registry repository created
- Cloud Run services created (via Terraform)
- GitHub repository access

## Step 1: Connect GitHub Repository to Cloud Build

### Option A: Using GCP Console (Recommended)

1. **Go to Cloud Build Triggers**
   - Navigate to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
   - Select your GCP project

2. **Create a New Trigger**
   - Click "Create Trigger"
   - Name: `deploy-backend` (or your preferred name)

3. **Connect Repository**
   - Source: GitHub (Cloud Build GitHub App)
   - Click "Connect Repository"
   - Authenticate with GitHub
   - Select your repository: `realestate-agent`
   - Click "Connect"

4. **Configure Trigger**
   - **Event**: Push to a branch
   - **Branch**: `^main$` (or your main branch name)
   - **Configuration**: Cloud Build configuration file
   - **Location**: Repository
   - **Cloud Build configuration file**: `cloudbuild.yaml`

5. **Set Substitution Variables**
   Click "Show included and ignored files" → "Substitution variables" and add:
   ```
   _REGION = me-west1
   _REPO_NAME = realestate-agent
   _API_SERVICE_NAME = nadlaner-api
   _WORKER_SERVICE_NAME = nadlaner-worker
   ```

6. **Service Account Permissions**
   - The default Cloud Build service account needs these roles:
     - `Cloud Run Admin` (to deploy services)
     - `Cloud Run Invoker` (needed when using `--allow-unauthenticated` so IAM policy binding succeeds)
     - `Service Account User` (to use Cloud Run service accounts)
     - `Artifact Registry Writer` (to push images)

   Grant permissions:
   ```bash
   PROJECT_ID=your-project-id
   PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
   CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
   
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:${CLOUD_BUILD_SA}" \
     --role="roles/run.admin"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:${CLOUD_BUILD_SA}" \
     --role="roles/run.invoker"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:${CLOUD_BUILD_SA}" \
     --role="roles/iam.serviceAccountUser"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:${CLOUD_BUILD_SA}" \
     --role="roles/artifactregistry.writer"
   ```

   If Cloud Build still fails to mark the service public because it cannot set the IAM policy, run:

   ```bash
   gcloud run services add-iam-policy-binding nadlaner-api \
     --region=me-west1 \
     --member=allUsers \
     --role=roles/run.invoker
   ```

### Option B: Using gcloud CLI

```bash
# Set variables
PROJECT_ID=your-project-id
REPO_NAME=realestate-agent
BRANCH=main
REGION=me-west1

# Create the trigger
gcloud builds triggers create github \
  --name="deploy-backend" \
  --repo-name="$REPO_NAME" \
  --repo-owner="YOUR_GITHUB_USERNAME" \
  --branch-pattern="^${BRANCH}$" \
  --build-config="cloudbuild.yaml" \
  --region="$REGION" \
  --substitutions="_REGION=$REGION,_REPO_NAME=realestate-agent,_API_SERVICE_NAME=nadlaner-api,_WORKER_SERVICE_NAME=nadlaner-worker"
```

## Step 2: Verify Cloud Build Service Account Permissions

Ensure the Cloud Build service account has the necessary permissions:

```bash
PROJECT_ID=your-project-id
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Check current permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:${CLOUD_BUILD_SA}" \
  --format="table(bindings.role)"
```

If permissions are missing, grant them (see Step 1, Option A).

## Step 3: Test the Deployment

1. **Make a small change** to your code (e.g., add a comment)
2. **Commit and push** to your main branch:
   ```bash
   git add .
   git commit -m "Test CD pipeline"
   git push origin main
   ```

3. **Monitor the build**:
   - Go to [Cloud Build History](https://console.cloud.google.com/cloud-build/builds)
   - You should see a new build triggered automatically
   - Click on it to see the build logs

4. **Verify deployment**:
   - Go to [Cloud Run Services](https://console.cloud.google.com/run)
   - Check that your services have new revisions
   - The new revision should be serving 100% of traffic

## Step 4: Configure Branch Protection (Optional but Recommended)

For production, consider:
- Requiring pull request reviews before merging
- Running tests before deployment
- Using separate triggers for different branches (e.g., `staging`, `production`)

## Troubleshooting

### Build fails with "permission denied"
- Check Cloud Build service account permissions (Step 2)
- Ensure Artifact Registry repository exists and is accessible

### Images not found during deployment
- Verify images were pushed successfully in build logs
- Check Artifact Registry repository name matches `_REPO_NAME`

### Cloud Run deployment fails
- Ensure Cloud Run services exist (created via Terraform)
- Check service account permissions
- Verify region matches `_REGION` substitution variable

### GitHub connection issues
- Re-authenticate GitHub connection in Cloud Build settings
- Check repository visibility (private repos need proper access)

## Advanced: Conditional Deployments

To deploy only when specific files change, add a filter to your trigger:

```bash
gcloud builds triggers create github \
  --name="deploy-backend" \
  --repo-name="$REPO_NAME" \
  --repo-owner="YOUR_GITHUB_USERNAME" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml" \
  --included-files="backend-django/**,orchestration/**,cloudbuild.yaml" \
  --substitutions="_REGION=$REGION,_REPO_NAME=realestate-agent
```

This will only trigger builds when files in `backend-django/`, `orchestration/`, or `cloudbuild.yaml` change.

## Manual Deployment

If you need to deploy manually without pushing to GitHub:

```bash
gcloud builds submit --config=cloudbuild.yaml
```

Or use the build script:

```bash
PROJECT_ID=your-project-id ./scripts/build-gcp-images.sh
```



