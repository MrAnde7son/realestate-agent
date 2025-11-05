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
