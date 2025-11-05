output "load_balancer_ip" {
  description = "Global static IP used by the HTTPS load balancer"
  value       = google_compute_global_address.lb_ip.address
}

output "api_url" {
  description = "External URL for the Django API"
  value       = "https://${google_compute_global_address.lb_ip.address}"
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL connection string for private access"
  value       = google_sql_database_instance.postgres.connection_name
  sensitive   = true
}

output "redis_host" {
  description = "Memorystore private host"
  value       = google_redis_instance.primary.host
}

output "redis_port" {
  description = "Memorystore port"
  value       = google_redis_instance.primary.port
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = google_artifact_registry_repository.app.name
}

output "static_bucket_name" {
  description = "Cloud Storage bucket name for static files"
  value       = google_storage_bucket.static.name
}

output "media_bucket_name" {
  description = "Cloud Storage bucket name for media files"
  value       = google_storage_bucket.media.name
}
