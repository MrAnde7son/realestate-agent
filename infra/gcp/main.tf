resource "google_project_service" "required" {
  for_each = toset([
    "compute.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com",
    "dns.googleapis.com",
    "redis.googleapis.com",
    "cloudbuild.googleapis.com"
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
  service                 = "services.servicenetworking.googleapis.com"
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
      require_ssl     = true
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
  api_env = merge({
    DATABASE_HOST     = google_sql_database_instance.postgres.private_ip_address,
    DATABASE_NAME     = var.db_name,
    DATABASE_USER     = var.db_user,
    DATABASE_PASSWORD = var.db_password,
    DATABASE_PORT     = "5432",
    REDIS_HOST        = google_redis_instance.primary.host,
    REDIS_PORT        = tostring(google_redis_instance.primary.port),
    REDIS_TLS_ENABLED = "false"
  }, var.api_env_vars)

  worker_env = merge({
    DATABASE_HOST     = google_sql_database_instance.postgres.private_ip_address,
    DATABASE_NAME     = var.db_name,
    DATABASE_USER     = var.db_user,
    DATABASE_PASSWORD = var.db_password,
    DATABASE_PORT     = "5432",
    REDIS_HOST        = google_redis_instance.primary.host,
    REDIS_PORT        = tostring(google_redis_instance.primary.port),
    REDIS_TLS_ENABLED = "false"
  }, var.worker_env_vars)
}

resource "google_cloud_run_service" "api" {
  name     = "nadlaner-api"
  location = var.region

  template {
    metadata {
      annotations = {
        "run.googleapis.com/vpc-access-connector"    = google_vpc_access_connector.serverless.id
        "run.googleapis.com/ingress"                 = "internal-and-cloud-load-balancing"
        "run.googleapis.com/cloudsql-instances"      = google_sql_database_instance.postgres.connection_name
        "autoscaling.knative.dev/maxScale"           = "10"
        "autoscaling.knative.dev/minScale"           = "1"
      }
      labels = var.labels
    }

    spec {
      service_account_name = google_service_account.api.email

      containers {
        image = var.api_image

        env = [for key, value in local.api_env : {
          name  = key
          value = value
        }]

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

  depends_on = [google_project_service.required]
}

resource "google_cloud_run_service" "worker" {
  name     = "nadlaner-worker"
  location = var.region

  template {
    metadata {
      annotations = {
        "run.googleapis.com/vpc-access-connector"    = google_vpc_access_connector.serverless.id
        "run.googleapis.com/ingress"                 = "internal"
        "run.googleapis.com/cloudsql-instances"      = google_sql_database_instance.postgres.connection_name
        "autoscaling.knative.dev/maxScale"           = "5"
        "autoscaling.knative.dev/minScale"           = "1"
      }
      labels = var.labels
    }

    spec {
      service_account_name = google_service_account.worker.email
      container_concurrency = 1

      containers {
        image = var.worker_image

        env = [for key, value in local.worker_env : {
          name  = key
          value = value
        }]

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

  depends_on = [google_project_service.required]
}

resource "google_cloud_run_service_iam_member" "api_invoker" {
  location = google_cloud_run_service.api.location
  project  = var.project_id
  service  = google_cloud_run_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

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
  health_checks                   = [google_compute_health_check.http.id]
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
  name         = "${var.domain}."
  managed_zone = google_dns_managed_zone.primary.name
  type         = "CNAME"
  ttl          = 300
  rrdatas      = [var.ui_cname_target]
}
