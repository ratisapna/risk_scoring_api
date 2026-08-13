variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "risk_scoring_db"
  sensitive   = true
}

variable "db_username" {
  description = "Master username for PostgreSQL"
  type        = string
  default     = "risk_admin"
  sensitive   = true
}

variable "db_password" {
  description = "Master password for PostgreSQL (change this!)"
  type        = string
  sensitive   = true
  # Use: TF_VAR_db_password or terraform.tfvars
}

variable "ssh_public_key" {
  description = "Public SSH key for EC2 access"
  type        = string
  sensitive   = true
  # Use: TF_VAR_ssh_public_key or terraform.tfvars
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed for SSH (e.g., your IP/32)"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Change to your IP for security!
}

variable "github_repo" {
  description = "GitHub repository URL for app deployment"
  type        = string
  default     = "https://github.com/ratisapna/risk_scoring_api.git"
}
