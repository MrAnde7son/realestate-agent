variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Region for regional resources"
  type        = string
  default     = "me-west1"
}

variable "domain" {
  description = "Root domain for public endpoints"
  type        = string
}

variable "ui_cname_target" {
  description = "Vercel-provided CNAME target for the UI"
  type        = string
}

variable "api_image" {
  description = "Container image for the Django API service"
  type        = string
}

variable "worker_image" {
  description = "Container image for the Celery worker service"
  type        = string
}

variable "api_env_vars" {
  description = "Environment variables to inject into the API service"
  type        = map(string)
  default     = {}
}

variable "worker_env_vars" {
  description = "Environment variables to inject into the worker service"
  type        = map(string)
  default     = {}
}

variable "subnet_cidr" {
  description = "CIDR range for the regional subnet"
  type        = string
  default     = "10.10.10.0/24"
}

variable "db_name" {
  description = "Primary PostgreSQL database name"
  type        = string
  default     = "nadlaner"
}

variable "db_user" {
  description = "Primary PostgreSQL user"
  type        = string
  default     = "nadlaner"
}

variable "db_password" {
  description = "Password for the PostgreSQL user"
  type        = string
  sensitive   = true
}

variable "db_host" {
  description = "PostgreSQL host address. Use '127.0.0.1' for Cloud Run with Cloud SQL Proxy, or the private IP (e.g., '10.204.0.2') for direct connections"
  type        = string
  default     = "127.0.0.1"
}

variable "allowed_office_cidrs" {
  description = "CIDR ranges allowed through Cloud Armor"
  type        = list(string)
  default     = []
}

variable "labels" {
  description = "Common labels applied to managed resources"
  type        = map(string)
  default     = {}
}

variable "redis_tier" {
  description = "Memorystore tier"
  type        = string
  default     = "STANDARD_HA"
}

variable "redis_size_gb" {
  description = "Memorystore capacity in GB"
  type        = number
  default     = 1
}

variable "enable_cloud_scheduler" {
  description = "Enable Cloud Scheduler for periodic tasks (alternative to Celery Beat)"
  type        = bool
  default     = false
}
