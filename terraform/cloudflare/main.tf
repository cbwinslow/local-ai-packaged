# =============================================================================
# Terraform Configuration for Local AI Package on Cloudflare
# =============================================================================
# This configuration deploys the Local AI Package infrastructure to Cloudflare
# including DNS, Workers, Pages, R2 storage, and D1 database
# =============================================================================

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }
}

# =============================================================================
# Variables
# =============================================================================

variable "cloudflare_api_token" {
  description = "Cloudflare API token with zone and account permissions"
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the deployment"
  type        = string
  default     = "opendiscourse.net"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "enable_analytics" {
  description = "Enable Cloudflare Web Analytics"
  type        = bool
  default     = true
}

variable "enable_bot_protection" {
  description = "Enable bot protection"
  type        = bool
  default     = true
}

# =============================================================================
# Provider Configuration
# =============================================================================

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# =============================================================================
# Data Sources
# =============================================================================

data "cloudflare_zone" "domain" {
  name = var.domain_name
}

# =============================================================================
# DNS Records
# =============================================================================

# Root domain
resource "cloudflare_record" "root" {
  zone_id = data.cloudflare_zone.domain.id
  name    = "@"
  value   = "192.0.2.1" # Placeholder IP - update with actual server IP
  type    = "A"
  ttl     = 300
  proxied = true

  tags = [
    "terraform",
    "local-ai-package",
    var.environment
  ]
}

# Service subdomains
locals {
  services = {
    "n8n"        = "N8N Workflow Automation"
    "webui"      = "Open WebUI Chat Interface"
    "flowise"    = "Flowise AI Agent Builder"
    "supabase"   = "Supabase Database & Auth"
    "langfuse"   = "Langfuse LLM Observability"
    "ollama"     = "Ollama LLM API"
    "searxng"    = "SearXNG Search Engine"
    "neo4j"      = "Neo4j Knowledge Graph"
    "agentic"    = "Agentic Knowledge RAG"
    "traefik"    = "Traefik Load Balancer"
    "grafana"    = "Grafana Monitoring"
    "prometheus" = "Prometheus Metrics"
  }
}

resource "cloudflare_record" "services" {
  for_each = local.services

  zone_id = data.cloudflare_zone.domain.id
  name    = each.key
  value   = "192.0.2.1" # Placeholder IP - update with actual server IP
  type    = "A"
  ttl     = 300
  proxied = true

  tags = [
    "terraform",
    "local-ai-package",
    var.environment,
    "service-${each.key}"
  ]

  comment = each.value
}

# =============================================================================
# R2 Storage for File Uploads
# =============================================================================

resource "cloudflare_r2_bucket" "ai_storage" {
  account_id = var.cloudflare_account_id
  name       = "local-ai-${var.environment}-storage"
  location   = "ENAM" # Eastern North America
}

resource "cloudflare_r2_bucket" "model_cache" {
  account_id = var.cloudflare_account_id
  name       = "local-ai-${var.environment}-models"
  location   = "ENAM"
}

resource "cloudflare_r2_bucket" "backup" {
  account_id = var.cloudflare_account_id
  name       = "local-ai-${var.environment}-backup"
  location   = "ENAM"
}

# =============================================================================
# D1 Database for Configuration
# =============================================================================

resource "cloudflare_d1_database" "config_db" {
  account_id = var.cloudflare_account_id
  name       = "local-ai-${var.environment}-config"
}

# =============================================================================
# Random Secrets
# =============================================================================

resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "random_password" "api_key" {
  length  = 32
  special = false
}

# =============================================================================
# Outputs
# =============================================================================

output "zone_id" {
  description = "Cloudflare Zone ID"
  value       = data.cloudflare_zone.domain.id
}

output "domain" {
  description = "Primary domain"
  value       = var.domain_name
}

output "services" {
  description = "Service endpoints"
  value = {
    for service, description in local.services :
    service => "https://${service}.${var.domain_name}"
  }
}

output "r2_buckets" {
  description = "R2 bucket names"
  value = {
    storage = cloudflare_r2_bucket.ai_storage.name
    models  = cloudflare_r2_bucket.model_cache.name
    backup  = cloudflare_r2_bucket.backup.name
  }
}

output "d1_database" {
  description = "D1 database info"
  value = {
    name = cloudflare_d1_database.config_db.name
    id   = cloudflare_d1_database.config_db.id
  }
}