resource "google_project_service" "required" {
  for_each = toset([
    "compute.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com",
    "dns.googleapis.com",
    "redis.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudscheduler.googleapis.com",
    "cloudtasks.googleapis.com"
  ])

  project = var.project_id
  service = each.key
}

resource "google_compute_network" "main" {
  name                    = "nadlaner-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
}

resource "google_compute_subnetwork" "regional" {
  name          = "nadlaner-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.main.id
  stack_type    = "IPV4_ONLY"
  private_ip_google_access = true
}

resource "google_compute_global_address" "private_service_connect" {
  name          = "nadlaner-psc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_connect.name]
  depends_on = [
    google_project_service.required
  ]
}

resource "google_vpc_access_connector" "serverless" {
  name          = "nadlaner-serverless"
  region        = var.region
  network       = google_compute_network.main.name
  ip_cidr_range = "10.8.0.0/28"
  min_instances = 2
  max_instances = 4
  # OR Option B (throughput-based, comment out instances if you use this)
  # min_throughput = 300   # Mbps
  # max_throughput = 600

  lifecycle {
    ignore_changes = [min_instances, max_instances]
  }
}

resource "google_service_account" "api" {
  account_id   = "nadlaner-api"
  display_name = "Nadlaner Django API"
}

resource "google_service_account" "worker" {
  account_id   = "nadlaner-worker"
  display_name = "Nadlaner Celery Worker"
}

resource "google_project_iam_member" "api_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "worker_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "api_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "worker_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_sql_database_instance" "postgres" {
  name             = "nadlaner-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = "db-custom-2-7680"
    availability_type = "REGIONAL"

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.main.id
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }
  }

  deletion_protection = true

  depends_on = [
    google_service_networking_connection.private_vpc_connection
  ]
}

resource "google_sql_database" "app" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

resource "google_redis_instance" "primary" {
  name           = "nadlaner-redis"
  tier           = var.redis_tier
  memory_size_gb = var.redis_size_gb
  region         = var.region
  location_id    = "${var.region}-a"
  authorized_network = google_compute_network.main.id

  depends_on = [
    google_service_networking_connection.private_vpc_connection
  ]
}

locals {
  redis_url = "redis://${google_redis_instance.primary.host}:${google_redis_instance.primary.port}/0"
  
  # Use Unix socket for Cloud SQL when db_host is set to use Cloud SQL Proxy
  # Format: /cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
  postgres_host = var.db_host == "127.0.0.1" ? "/cloudsql/${google_sql_database_instance.postgres.connection_name}" : var.db_host
  postgres_port = var.db_host == "127.0.0.1" ? "" : "5432"
  
  # Base API environment variables
  api_env_base = {
    # Enable PostgreSQL (required for Django to use PostgreSQL instead of SQLite)
    USE_POSTGRES      = "true",
    # PostgreSQL connection settings (Django expects POSTGRES_* variables)
    # For Cloud Run: use Unix socket path /cloudsql/PROJECT:REGION:INSTANCE
    # For direct connections: use the private IP (e.g., 10.204.0.2)
    # The annotation "run.googleapis.com/cloudsql-instances" sets up the proxy
    POSTGRES_HOST     = local.postgres_host,
    POSTGRES_DB       = var.db_name,
    POSTGRES_USER     = var.db_user,
    POSTGRES_PASSWORD = var.db_password,
    # Redis connection settings
    REDIS_HOST        = google_redis_instance.primary.host,
    REDIS_PORT        = tostring(google_redis_instance.primary.port),
    REDIS_TLS_ENABLED = "false",
    # Celery configuration
    CELERY_BROKER_URL = local.redis_url,
    CELERY_RESULT_BACKEND = local.redis_url,
    USE_CELERY        = "true"
  }
  
  # Add POSTGRES_PORT only when not using Unix socket (not empty)
  api_env = merge(
    local.api_env_base,
    local.postgres_port != "" ? { POSTGRES_PORT = local.postgres_port } : {},
    var.api_env_vars
  )

  # Base worker environment variables
  worker_env_base = {
    # Enable PostgreSQL (required for Django to use PostgreSQL instead of SQLite)
    USE_POSTGRES      = "true",
    # PostgreSQL connection settings (Django expects POSTGRES_* variables)
    # For Cloud Run: use Unix socket path /cloudsql/PROJECT:REGION:INSTANCE
    # For direct connections: use the private IP (e.g., 10.204.0.2)
    # The annotation "run.googleapis.com/cloudsql-instances" sets up the proxy
    POSTGRES_HOST     = local.postgres_host,
    POSTGRES_DB       = var.db_name,
    POSTGRES_USER     = var.db_user,
    POSTGRES_PASSWORD = var.db_password,
    # Redis connection settings
    REDIS_HOST        = google_redis_instance.primary.host,
    REDIS_PORT        = tostring(google_redis_instance.primary.port),
    REDIS_TLS_ENABLED = "false",
    # Celery configuration
    CELERY_BROKER_URL = local.redis_url,
    CELERY_RESULT_BACKEND = local.redis_url,
    USE_CELERY        = "true"
  }
  
  # Add POSTGRES_PORT only when not using Unix socket (not empty)
  worker_env = merge(
    local.worker_env_base,
    local.postgres_port != "" ? { POSTGRES_PORT = local.postgres_port } : {},
    var.worker_env_vars
  )
}

resource "google_cloud_run_service" "api" {
  name     = "nadlaner-api"
  location = var.region

  metadata {
    annotations = {
      "run.googleapis.com/ingress" = "internal-and-cloud-load-balancing"
    }
    labels = var.labels
  }

  template {
    metadata {
      annotations = {
        # Enable VPC connector to allow direct connection to private IP
        # This is needed for both Cloud SQL Proxy and direct private IP connections
        "run.googleapis.com/vpc-access-connector"    = google_vpc_access_connector.serverless.id
        # Allow egress to private IP ranges (required for Redis and Cloud SQL)
        "run.googleapis.com/vpc-access-egress"      = "private-ranges-only"
        "run.googleapis.com/cloudsql-instances"      = google_sql_database_instance.postgres.connection_name
        "autoscaling.knative.dev/maxScale"           = "10"
        "autoscaling.knative.dev/minScale"           = "1"
        # Increase startup timeout for database connection
        "run.googleapis.com/startup-cpu-boost"      = "true"
      }
      labels = var.labels
    }

    spec {
      service_account_name = google_service_account.api.email
      timeout_seconds      = 300  # 5 minutes for request timeout
      
      containers {
        image = var.api_image

        dynamic "env" {
          for_each = local.api_env
          content {
            name  = env.key
            value = env.value
          }
        }

        ports {
          name           = "http1"
          container_port = 8000
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  lifecycle {
    # Ignore entire template - deployments are managed by direct repo connection
    # The repository connection manages the template (containers, annotations, etc.)
    ignore_changes = [
      template
    ]
  }

  depends_on = [google_project_service.required]
}

resource "google_cloud_run_service" "worker" {
  name     = "nadlaner-worker"
  location = var.region

  metadata {
    annotations = {
      "run.googleapis.com/ingress" = "internal"
    }
    labels = var.labels
  }

  template {
    metadata {
      annotations = {
        # Enable VPC connector to allow direct connection to private IP
        "run.googleapis.com/vpc-access-connector"    = google_vpc_access_connector.serverless.id
        # Allow egress to private IP ranges (required for Redis and Cloud SQL)
        "run.googleapis.com/vpc-access-egress"      = "private-ranges-only"
        "run.googleapis.com/cloudsql-instances"      = google_sql_database_instance.postgres.connection_name
        "autoscaling.knative.dev/maxScale"           = "5"
        "autoscaling.knative.dev/minScale"           = "1"
        # Increase startup timeout for database connection
        "run.googleapis.com/startup-cpu-boost"      = "true"
      }
      labels = var.labels
    }

    spec {
      service_account_name = google_service_account.worker.email
      container_concurrency = 1

      containers {
        image = var.worker_image

        dynamic "env" {
          for_each = local.worker_env
          content {
            name  = env.key
            value = env.value
          }
        }

        ports {
          name           = "http1"
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  lifecycle {
    # Ignore entire template - deployments are managed by direct repo connection
    # The repository connection manages the template (containers, annotations, etc.)
    ignore_changes = [
      template
    ]
  }

  depends_on = [google_project_service.required]
}

# Cloud Load Balancing automatically has permission to invoke Cloud Run services
# via serverless NEGs, so no explicit IAM binding is needed.
# If direct public access to the Cloud Run URL is needed, uncomment and adjust:
# resource "google_cloud_run_service_iam_member" "api_invoker" {
#   location = google_cloud_run_service.api.location
#   project  = var.project_id
#   service  = google_cloud_run_service.api.name
#   role     = "roles/run.invoker"
#   member   = "allUsers"  # Note: May be blocked by organization policy
# }

resource "google_compute_region_network_endpoint_group" "api_neg" {
  name                  = "nadlaner-api-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_service.api.name
  }
}

resource "google_compute_health_check" "http" {
  name = "nadlaner-http-health"

  http_health_check {
    port_specification = "USE_SERVING_PORT"
    request_path       = "/health/"
  }
}

resource "google_compute_backend_service" "run_backend" {
  name                            = "nadlaner-run-backend"
  load_balancing_scheme           = "EXTERNAL_MANAGED"
  protocol                        = "HTTP"
  security_policy                 = google_compute_security_policy.waf.id
  # Note: Serverless NEG backends (Cloud Run) cannot have health checks
  # Cloud Run manages its own health checks automatically
  enable_cdn                      = false
  connection_draining_timeout_sec = 10

  backend {
    group = google_compute_region_network_endpoint_group.api_neg.id
  }
}

resource "google_compute_security_policy" "waf" {
  name = "nadlaner-armor"

  rule {
    action   = "allow"
    priority = 1000

    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = length(var.allowed_office_cidrs) > 0 ? var.allowed_office_cidrs : ["0.0.0.0/0"]
      }
    }
  }

  rule {
    action   = "deny(403)"
    priority = 2147483647

    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }
}

resource "google_compute_url_map" "https" {
  name            = "nadlaner-url-map"
  default_service = google_compute_backend_service.run_backend.id
}

resource "google_compute_managed_ssl_certificate" "primary" {
  name = "nadlaner-ssl"

  managed {
    domains = ["api.${var.domain}"]
  }
}

resource "google_compute_target_https_proxy" "https" {
  name             = "nadlaner-https-proxy"
  url_map          = google_compute_url_map.https.id
  ssl_certificates = [google_compute_managed_ssl_certificate.primary.id]
}

resource "google_compute_global_address" "lb_ip" {
  name = "nadlaner-lb-ip"
}

resource "google_compute_global_forwarding_rule" "https" {
  name                  = "nadlaner-https-forwarding"
  target                = google_compute_target_https_proxy.https.id
  load_balancing_scheme = "EXTERNAL"
  port_range            = "443"
  ip_protocol           = "TCP"
  ip_address            = google_compute_global_address.lb_ip.address
}

resource "google_dns_managed_zone" "primary" {
  name     = "nadlaner-zone"
  dns_name = "${var.domain}."
}

resource "google_dns_record_set" "api" {
  name         = "api.${var.domain}."
  managed_zone = google_dns_managed_zone.primary.name
  type         = "A"
  ttl          = 300
  rrdatas      = [google_compute_global_address.lb_ip.address]
}

resource "google_dns_record_set" "ui" {
  name         = "app.${var.domain}."
  managed_zone = google_dns_managed_zone.primary.name
  type         = "CNAME"
  ttl          = 300
  rrdatas      = [var.ui_cname_target]
}

# Artifact Registry for container images
resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = "realestate-agent"
  description   = "Container images for Nadlaner services"
  format        = "DOCKER"
}

# Cloud Storage for static/media files
resource "google_storage_bucket" "static" {
  name          = "${var.project_id}-static"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  labels = var.labels
}

resource "google_storage_bucket" "media" {
  name          = "${var.project_id}-media"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = var.labels
}

# Service account for Cloud Storage access
resource "google_service_account" "storage" {
  account_id   = "nadlaner-storage"
  display_name = "Nadlaner Cloud Storage Access"
}

resource "google_project_iam_member" "storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.storage.email}"
}

resource "google_project_iam_member" "api_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "worker_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

# Secret Manager access
resource "google_project_iam_member" "api_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "worker_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

# Artifact Registry access for pulling container images
resource "google_project_iam_member" "api_artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "worker_artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

# Cloud Scheduler for periodic tasks (alternative to Celery Beat)
resource "google_cloud_scheduler_job" "celery_beat_tasks" {
  count = var.enable_cloud_scheduler ? 1 : 0

  name             = "nadlaner-celery-beat"
  region           = var.region
  schedule         = "*/5 * * * *"  # Every 5 minutes
  time_zone        = "Asia/Jerusalem"
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.api.status[0].url}/api/internal/trigger-celery-beat/"
    oidc_token {
      service_account_email = google_service_account.api.email
    }
  }
}
