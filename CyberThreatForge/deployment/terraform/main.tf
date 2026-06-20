terraform {
  required_version = ">= 1.8"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
  }
  backend "s3" {
    bucket         = "ctf-terraform-state"
    key            = "infra/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "ctf-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

# --- VPC for isolated deployment ---
resource "aws_vpc" "ctf_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "cyberthreatforge-vpc" }
}

# --- EKS Cluster ---
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "cyberthreatforge"
  cluster_version = "1.30"

  vpc_id     = aws_vpc.ctf_vpc.id
  subnet_ids = aws_subnet.ctf_private[*].id

  cluster_endpoint_public_access = false
  cluster_endpoint_private_access = true

  enable_cluster_creator_admin_permissions = true

  node_groups = {
    application = {
      desired_size = 3
      min_size     = 2
      max_size     = 6
      instance_types = ["t3.medium", "t3.large"]
      disk_size    = 100
    }
    ai_workers = {
      desired_size = 1
      min_size     = 0
      max_size     = 4
      instance_types = ["g4dn.xlarge"] # GPU for AI inference
      disk_size    = 200
      labels = { workload = "ai" }
    }
  }
}

# --- RDS PostgreSQL with pgvector ---
resource "aws_db_instance" "postgres" {
  identifier        = "ctf-postgres"
  engine            = "postgres"
  engine_version    = "16.3"
  instance_class    = "db.r6g.large"
  allocated_storage = 200
  storage_encrypted = true
  db_name           = "cyberthreatforge"
  username          = "ctf_admin"
  password          = var.postgres_password
  vpc_security_group_ids = [aws_security_group.ctf_db.id]
  db_subnet_group_name   = aws_db_subnet_group.ctf.name
  backup_retention_period = 30
  deletion_protection    = true
  skip_final_snapshot    = false
  enabled_cloudwatch_logs_exports = ["postgresql"]

  parameter_group_name = aws_db_parameter_group.pgvector.name
}

resource "aws_db_parameter_group" "pgvector" {
  family = "postgres16"
  parameter {
    name  = "shared_preload_libraries"
    value = "pgvector"
  }
}

# --- ElastiCache Redis ---
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "ctf-redis"
  engine               = "redis"
  node_type            = "cache.t3.medium"
  num_cache_nodes      = 2
  parameter_group_name = "default.redis7"
  subnet_group_name    = aws_elasticache_subnet_group.ctf.name
  security_group_ids   = [aws_security_group.ctf_cache.id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}

# --- S3 for evidence storage ---
resource "aws_s3_bucket" "evidence" {
  bucket        = "ctf-evidence-${var.environment}"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "evidence" {
  bucket = aws_s3_bucket.evidence.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "evidence" {
  bucket = aws_s3_bucket.evidence.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "evidence" {
  bucket = aws_s3_bucket.evidence.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- WAF ---
resource "aws_wafv2_web_acl" "ctf" {
  name        = "ctf-waf"
  scope       = "REGIONAL"
  default_action { allow {} }

  rule {
    name     = "rate-limit"
    priority = 1
    action   { block {} }
    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit"
      sampled_requests_enabled   = true
    }
  }
}
