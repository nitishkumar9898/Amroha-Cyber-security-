variable "aws_region" {
  description = "AWS region (ap-south-1 for India)"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "postgres_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT signing secret"
  type        = string
  sensitive   = true
}

variable "encryption_key" {
  description = "AES-256 encryption key (64 hex chars)"
  type        = string
  sensitive   = true
}
