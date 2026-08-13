output "rds_endpoint" {
  description = "RDS Postgres endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = false
}

output "rds_address" {
  description = "RDS Postgres address (host only)"
  value       = aws_db_instance.postgres.address
  sensitive   = false
}

output "ec2_public_ip" {
  description = "Public IP of EC2 instance"
  value       = aws_eip.app.public_ip
  sensitive   = false
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
  sensitive   = false
}

output "database_url" {
  description = "PostgreSQL connection string (keep secret!)"
  value       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/${var.db_name}"
  sensitive   = true
}

output "app_url" {
  description = "URL to access the deployed app"
  value       = "http://${aws_eip.app.public_ip}:8000"
  sensitive   = false
}

output "health_check_url" {
  description = "Health check endpoint"
  value       = "http://${aws_eip.app.public_ip}:8000/health"
  sensitive   = false
}
