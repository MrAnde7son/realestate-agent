# GCP Authentication Setup for Terraform

This guide covers how to authenticate Terraform with Google Cloud Platform.

## Option 1: Application Default Credentials (Recommended for Development)

This is the easiest method for local development. It uses your personal Google Cloud credentials.

### Step 1: Install Google Cloud SDK

If you haven't already:

```bash
# macOS
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

### Step 2: Authenticate with Your Google Account

```bash
# Login with your Google account
gcloud auth login

# Set your project
gcloud config set project nadlaner-production

# Enable Application Default Credentials
gcloud auth application-default login
```

This creates credentials at `~/.config/gcloud/application_default_credentials.json` that Terraform will automatically use.

### Step 3: Verify Authentication

```bash
# Test that you're authenticated
gcloud auth list

# Test that you can access the project
gcloud projects describe my-project-1506156422083
```

### Step 4: Initialize Terraform

```bash
cd infra/gcp
terraform init
```

Terraform will automatically use your Application Default Credentials.

---

## Option 2: Service Account (Recommended for Production/CI/CD)

This is more secure and suitable for production environments and CI/CD pipelines.

### Step 1: Create a Service Account

```bash
# Create the service account
gcloud iam service-accounts create terraform-admin \
  --display-name="Terraform Admin" \
  --project=my-project-1506156422083
```

### Step 2: Grant Required Permissions

The service account needs these roles to manage all resources:

```bash
PROJECT_ID="nadlaner-production"
SERVICE_ACCOUNT="terraform-admin@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant roles needed for Terraform
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/owner"

# Or for more granular permissions (recommended), grant these specific roles:
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/compute.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/sql.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/redis.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/dns.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudscheduler.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/iam.serviceAccountAdmin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/serviceusage.serviceUsageAdmin"
```

### Step 3: Create and Download Service Account Key

```bash
# Create a key file
gcloud iam service-accounts keys create ~/terraform-key.json \
  --iam-account=terraform-admin@my-project-1506156422083.iam.gserviceaccount.com
```

### Step 4: Set Environment Variable

```bash
# Set the credentials file path
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/terraform-key.json"

# Or add to your shell profile (~/.zshrc, ~/.bashrc, etc.)
echo 'export GOOGLE_APPLICATION_CREDENTIALS="$HOME/terraform-key.json"' >> ~/.zshrc
source ~/.zshrc
```

### Step 5: Verify Service Account Access

```bash
# Test authentication
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
gcloud projects describe my-project-1506156422083
```

### Step 6: Initialize Terraform

```bash
cd infra/gcp
terraform init
```

---

## Option 3: Explicit Provider Configuration (Alternative)

You can also specify credentials directly in the Terraform provider configuration.

### Update `versions.tf`

```hcl
provider "google" {
  project = var.project_id
  region  = var.region
  # Optionally specify credentials file
  # credentials = file("~/terraform-key.json")
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  # credentials = file("~/terraform-key.json")
}
```

**Note:** This is less secure than using environment variables, as credentials may end up in state files.

---

## Security Best Practices

### For Local Development
✅ Use Application Default Credentials (`gcloud auth application-default login`)
✅ Never commit credentials to version control
✅ Use `terraform.tfvars` (already in `.gitignore`)

### For CI/CD
✅ Use Service Account with minimal required permissions
✅ Store service account key in CI/CD secret manager (GitHub Secrets, GitLab CI Variables, etc.)
✅ Set `GOOGLE_APPLICATION_CREDENTIALS` as an environment variable in CI/CD
✅ Use Workload Identity Federation (recommended for GCP-native CI/CD)

### For Production
✅ Use separate service accounts per environment
✅ Grant least-privilege permissions
✅ Rotate service account keys regularly
✅ Use Workload Identity for Kubernetes/Cloud Run

---

## Troubleshooting

### Error: "Could not load default credentials"

**Solution:**
```bash
# Re-authenticate
gcloud auth application-default login
```

### Error: "Permission denied" or "Insufficient permissions"

**Solution:**
1. Check your current user/account:
   ```bash
   gcloud auth list
   ```

2. Verify project access:
   ```bash
   gcloud projects describe my-project-1506156422083
   ```

3. If using service account, ensure all required roles are granted (see Step 2 above)

### Error: "Project not found" or "Project does not exist"

**Solution:**
1. Verify the project ID is correct:
   ```bash
   gcloud projects list
   ```

2. Ensure billing is enabled:
   ```bash
   gcloud billing projects describe my-project-1506156422083
   ```

3. If project doesn't exist, create it:
   ```bash
   gcloud projects create my-project-1506156422083 --name="Nadlaner Production"
   ```

### Error: "gcloud.config.virtualenv.create" - Python path not found

This error occurs when gcloud can't find the Python interpreter at the expected path, often with Python 3.13 on macOS. The issue is that Python 3.13's `libexec/bin` directory doesn't have a `python3` symlink (only `python`), but gcloud expects `python3` to exist.

**Solution:**

**Option 1: Create the missing symlink (Recommended for Python 3.13)**

```bash
# Create the python3 symlink in libexec/bin
ln -s ../../Frameworks/Python.framework/Versions/3.13/bin/python3.13 /opt/homebrew/opt/python@3.13/libexec/bin/python3

# Verify it works
/opt/homebrew/opt/python@3.13/libexec/bin/python3 --version

# Reinstall gcloud
brew uninstall --cask google-cloud-sdk 2>/dev/null || brew uninstall --cask gcloud-cli 2>/dev/null
brew install --cask gcloud-cli
```

**Option 2: Use Python 3.11 (which already has the symlink)**

```bash
# Python 3.11 already has python3 in libexec/bin, so just reinstall gcloud
brew uninstall --cask google-cloud-sdk 2>/dev/null || brew uninstall --cask gcloud-cli 2>/dev/null
brew install --cask gcloud-cli
```

**Option 3: Set CLOUDSDK_PYTHON environment variable**

If the above doesn't work, you can also set the environment variable:

```bash
# For zsh (default on macOS)
echo 'export CLOUDSDK_PYTHON=/opt/homebrew/opt/python@3.13/bin/python3' >> ~/.zshrc
source ~/.zshrc

# For bash
echo 'export CLOUDSDK_PYTHON=/opt/homebrew/opt/python@3.13/bin/python3' >> ~/.bash_profile
source ~/.bash_profile
```

**Verify the installation:**

```bash
gcloud --version
```

### Error: "gcloud: line 182: /opt/homebrew/opt/python@3.11/bin/python3: No such file or directory"

This error occurs when you have an old gcloud installation in `/usr/local/bin/gcloud` that conflicts with the new Homebrew installation.

**Solution:**

1. Remove the old gcloud symlinks:
   ```bash
   rm /usr/local/bin/gcloud /usr/local/bin/gsutil /usr/local/bin/bq \
      /usr/local/bin/docker-credential-gcloud /usr/local/bin/git-credential-gcloud.sh
   ```

2. Verify the correct gcloud is being used:
   ```bash
   which gcloud  # Should show /opt/homebrew/bin/gcloud
   gcloud --version
   ```

3. If `/opt/homebrew/bin` is not in your PATH, add it:
   ```bash
   # For zsh (default on macOS)
   echo 'export PATH=/opt/homebrew/bin:$PATH' >> ~/.zshrc
   source ~/.zshrc
   
   # For bash
   echo 'export PATH=/opt/homebrew/bin:$PATH' >> ~/.bash_profile
   source ~/.bash_profile
   ```

---

## Quick Setup Commands (Development)

For a quick local development setup:

```bash
# 1. Install gcloud (if not installed)
brew install google-cloud-sdk

# 2. Authenticate
gcloud auth login
gcloud config set project my-project-1506156422083
gcloud auth application-default login

# 3. Verify
gcloud projects describe my-project-1506156422083

# 4. Initialize Terraform
cd infra/gcp
terraform init

# 5. Plan (dry run)
terraform plan -var-file=terraform.tfvars
```

---

## Next Steps

After setting up authentication:

1. ✅ Verify authentication works
2. ✅ Run `terraform init`
3. ✅ Run `terraform plan` to see what will be created
4. ✅ Review the plan carefully
5. ✅ Run `terraform apply` to create resources

For more details, see [GCP_MIGRATION_CHECKLIST.md](./GCP_MIGRATION_CHECKLIST.md).

