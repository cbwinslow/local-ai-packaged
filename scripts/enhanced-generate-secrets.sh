#!/bin/bash

# =============================================================================
# Enhanced Secrets Generation Script for Local AI Package
# =============================================================================
# This script generates all necessary secrets and API keys for the system
# Includes cloud integration setup for Cloudflare, Oracle OCI, and Azure
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}  Local AI Package - Enhanced Secrets & Environment Generator${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo

# Check if .env already exists
if [ -f .env ]; then
    echo -e "${YELLOW}Warning: .env file already exists!${NC}"
    read -p "Do you want to backup the existing .env file? (y/n): " backup_choice
    if [ "$backup_choice" = "y" ] || [ "$backup_choice" = "Y" ]; then
        backup_file=".env.backup.$(date +%Y%m%d_%H%M%S)"
        cp .env "$backup_file"
        echo -e "${GREEN}✅ Backup created: $backup_file${NC}"
    fi
    
    read -p "Do you want to overwrite the existing .env file? (y/n): " overwrite_choice
    if [ "$overwrite_choice" != "y" ] && [ "$overwrite_choice" != "Y" ]; then
        echo -e "${RED}❌ Script aborted by user${NC}"
        exit 1
    fi
fi

echo -e "${YELLOW}Generating secure secrets and environment variables...${NC}"

# =============================================================================
# CORE SECURITY SECRETS
# =============================================================================
echo -e "${BLUE}📝 Generating core security secrets...${NC}"

# Generate strong passwords and keys
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
JWT_SECRET=$(openssl rand -hex 64)
ANON_KEY=$(openssl rand -hex 32)
SERVICE_ROLE_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
NEXTAUTH_SECRET=$(openssl rand -hex 32)
SECRET_KEY_BASE=$(openssl rand -hex 64)
VAULT_ENC_KEY=$(openssl rand -hex 32)

# N8N specific secrets
N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
N8N_USER_MANAGEMENT_JWT_SECRET=$(openssl rand -hex 32)

# Database passwords
CLICKHOUSE_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
MINIO_ROOT_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
NEO4J_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
FALKORDB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Application passwords
FLOWISE_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-12)
DASHBOARD_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-12)
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-12)

# Langfuse specific
LANGFUSE_SALT=$(openssl rand -hex 16)

# RabbitMQ credentials
RABBITMQ_USER=$(openssl rand -hex 8)
RABBITMQ_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Graylog credentials
GRAYLOG_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
GRAYLOG_PASSWORD_SECRET=$(openssl rand -hex 32)

# Compute Graylog SHA256
GRAYLOG_ROOT_PASSWORD_SHA2="sha256:$(echo -n "$GRAYLOG_PASSWORD" | sha256sum | cut -d' ' -f1)"

# Write to .env
cat > .env << EOF
# =============================================================================
# Local AI Package - Complete Environment Configuration
# =============================================================================
# Generated on: $(date)
# This file contains all environment variables for the Local AI Package
# =============================================================================

# =============================================================================
# CORE APPLICATION SETTINGS
# =============================================================================
NODE_ENV=development
ENVIRONMENT=private
DOCKER_PROJECT_NAME=localai

# =============================================================================
# CORE SECURITY SECRETS (Generated)
# =============================================================================
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
JWT_SECRET=${JWT_SECRET}
ANON_KEY=${ANON_KEY}
SERVICE_ROLE_KEY=${SERVICE_ROLE_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
SECRET_KEY_BASE=${SECRET_KEY_BASE}
VAULT_ENC_KEY=${VAULT_ENC_KEY}

# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=${DASHBOARD_PASSWORD}
POOLER_TENANT_ID=1000
POSTGRES_HOST=db
POSTGRES_DB=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
SITE_URL=http://localhost:3000
POOLER_PROXY_PORT_TRANSACTION=6543
POOLER_DEFAULT_POOL_SIZE=20
POOLER_MAX_CLIENT_CONN=100
POOLER_DB_POOL_SIZE=5

# =============================================================================
# DATABASE SERVICES
# =============================================================================
POSTGRES_VERSION=16-alpine
CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD}
CLICKHOUSE_USER=clickhouse
CLICKHOUSE_MIGRATION_URL=clickhouse://clickhouse:9000
CLICKHOUSE_URL=http://clickhouse:8123
CLICKHOUSE_CLUSTER_ENABLED=false

# Neo4j Configuration
NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
NEO4J_PASSWORD=${NEO4J_PASSWORD}
NEO4J_HOSTNAME=localhost

# FalkorDB Configuration
FALKORDB_PASSWORD=${FALKORDB_PASSWORD}

# Redis/Valkey Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_AUTH=LOCALONLYREDIS
REDIS_TLS_ENABLED=false

# =============================================================================
# AI SERVICES CONFIGURATION
# =============================================================================
# N8N Workflow Automation
N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
N8N_USER_MANAGEMENT_JWT_SECRET=${N8N_USER_MANAGEMENT_JWT_SECRET}
N8N_HOSTNAME=localhost

# Flowise
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=${FLOWISE_PASSWORD}
FLOWISE_HOSTNAME=localhost

# OpenWebUI
WEBUI_HOSTNAME=localhost

# Langfuse (LLM Observability)
LANGFUSE_HOSTNAME=localhost
LANGFUSE_SALT=${LANGFUSE_SALT}
TELEMETRY_ENABLED=false
LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES=true

# =============================================================================
# STORAGE SERVICES
# =============================================================================
# MinIO (S3-Compatible Storage)
MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}

# Langfuse S3 Configuration
LANGFUSE_S3_EVENT_UPLOAD_BUCKET=langfuse
LANGFUSE_S3_EVENT_UPLOAD_REGION=auto
LANGFUSE_S3_EVENT_UPLOAD_ACCESS_KEY_ID=minio
LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT=http://minio:9000
LANGFUSE_S3_EVENT_UPLOAD_FORCE_PATH_STYLE=true
LANGFUSE_S3_EVENT_UPLOAD_PREFIX=events/

LANGFUSE_S3_MEDIA_UPLOAD_BUCKET=langfuse
LANGFUSE_S3_MEDIA_UPLOAD_REGION=auto
LANGFUSE_S3_MEDIA_UPLOAD_ACCESS_KEY_ID=minio
LANGFUSE_S3_MEDIA_UPLOAD_ENDPOINT=http://localhost:9090
LANGFUSE_S3_MEDIA_UPLOAD_FORCE_PATH_STYLE=true
LANGFUSE_S3_MEDIA_UPLOAD_PREFIX=media/

LANGFUSE_S3_BATCH_EXPORT_ENABLED=false
LANGFUSE_S3_BATCH_EXPORT_BUCKET=langfuse
LANGFUSE_S3_BATCH_EXPORT_PREFIX=exports/
LANGFUSE_S3_BATCH_EXPORT_REGION=auto
LANGFUSE_S3_BATCH_EXPORT_ENDPOINT=http://minio:9000
LANGFUSE_S3_BATCH_EXPORT_EXTERNAL_ENDPOINT=http://localhost:9090
LANGFUSE_S3_BATCH_EXPORT_ACCESS_KEY_ID=minio
LANGFUSE_S3_BATCH_EXPORT_FORCE_PATH_STYLE=true

# =============================================================================
# SEARCH & DISCOVERY
# =============================================================================
SEARXNG_HOSTNAME=localhost
SEARXNG_SECRET_KEY=$(openssl rand -hex 16)
SEARXNG_UWSGI_WORKERS=4
SEARXNG_UWSGI_THREADS=4

# Qdrant Vector Database
QDRANT_URL=http://qdrant:6333
# Generate Qdrant API Key
QDRANT_API_KEY=$(openssl rand -hex 16)

# =============================================================================
# FRONTEND APPLICATIONS
# =============================================================================
FRONTEND_HOSTNAME=localhost
FRONTEND_TITLE=Local AI Package
FRONTEND_DESCRIPTION=Self-hosted AI Development Environment
AGENTIC_HOSTNAME=localhost
SUPABASE_HOSTNAME=localhost

# =============================================================================
# MONITORING & OBSERVABILITY
# =============================================================================
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
PROMETHEUS_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-12)

# =============================================================================
# CLOUD INTEGRATION CREDENTIALS
# =============================================================================
# Cloudflare (Free Tier)
CLOUDFLARE_API_TOKEN=${CLOUDFLARE_API_TOKEN}
CLOUDFLARE_ZONE_ID=${CLOUDFLARE_ZONE_ID}
CLOUDFLARE_ACCOUNT_ID=${CLOUDFLARE_ACCOUNT_ID}

# Oracle Cloud Infrastructure (Always Free Tier)
OCI_TENANCY_ID=${OCI_TENANCY_ID}
OCI_USER_ID=${OCI_USER_ID}
OCI_FINGERPRINT=${OCI_FINGERPRINT}
OCI_REGION=${OCI_REGION}

# Azure (Free Tier)
AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
AZURE_TENANT_ID=${AZURE_TENANT_ID}
AZURE_SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID}

# =============================================================================
# EXTERNAL API KEYS (Add your own)
# =============================================================================
# AI/ML Services
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GROQ_API_KEY=your-groq-api-key

# Government Data APIs
CONGRESS_GOV_API_KEY=your-congress-gov-api-key
FEDERAL_REGISTER_API_KEY=your-federal-register-api-key
FEC_API_KEY=your-fec-api-key

# Development Tools
GITHUB_TOKEN=your-github-token
STACKHAWK_API_KEY=your-stackhawk-api-key

# =============================================================================
# FEATURE FLAGS
# =============================================================================
ENABLE_EXPERIMENTAL_FEATURES=true
ENABLE_ANALYTICS=false
ENABLE_TELEMETRY=false
DEBUG_MODE=false

# =============================================================================
# BACKUP & RECOVERY
# =============================================================================
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
BACKUP_LOCATION=/backups

# =============================================================================
# PERFORMANCE TUNING
# =============================================================================
MAX_CONCURRENT_INGESTIONS=5
DATABASE_POOL_SIZE=20
VECTOR_DB_BATCH_SIZE=100
API_RATE_LIMIT_PER_MINUTE=1000
EOF

echo -e "${GREEN}✅ .env file created successfully${NC}"

# =============================================================================
# CREATE DIRECTORY STRUCTURE
# =============================================================================
echo -e "${BLUE}📁 Creating directory structure...${NC}"

# Ensure all volume directories exist
mkdir -p volumes/{postgres/data,qdrant/data,langfuse/{postgres,clickhouse/{data,logs},minio},ollama,flowise,open-webui,n8n,valkey,agentic}
mkdir -p volumes/{mcp/{congress/{data,logs},federal/data,fec/data,neo4j-memory/data,postgres/data,vectorize/data,embeddings/cache,azure/{data,config},cloudflare/data,oci/{data,config},pluggedin/data,github/data,stackhawk/data,logs/data},neo4j/{data,logs,import,plugins,conf},memgraph/{data,logs,etc},falkordb/data}
mkdir -p supabase/volumes/{db/{data,init-scripts},storage,functions,api}
mkdir -p backups/{daily,weekly,monthly}
mkdir -p logs/{application,system,error}

# Set proper permissions
chmod 755 volumes
chmod -R 755 volumes/*/
chmod -R 755 supabase/volumes/
chmod -R 755 backups/
chmod -R 755 logs/

echo -e "${GREEN}✅ Directory structure created${NC}"

# =============================================================================
# CLOUD SETUP INSTRUCTIONS
# =============================================================================
if [ "$cloud_setup" = "y" ] || [ "$cloud_setup" = "Y" ]; then
    echo
    echo -e "${BLUE}☁️  Cloud Setup Instructions${NC}"
    echo -e "${YELLOW}=============================================================================${NC}"
    echo
    echo -e "${YELLOW}CLOUDFLARE SETUP:${NC}"
    echo "1. Visit https://dash.cloudflare.com"
    echo "2. Go to 'My Profile' → 'API Tokens'"
    echo "3. Create token with Zone:Read, Zone:Edit permissions"
    echo "4. Update CLOUDFLARE_API_TOKEN in .env file"
    echo
    echo -e "${YELLOW}ORACLE OCI SETUP:${NC}"
    echo "1. Visit https://cloud.oracle.com"
    echo "2. Create Always Free account"
    echo "3. Generate API key pair in Identity → Users → API Keys"
    echo "4. Update OCI_* variables in .env file"
    echo
    echo -e "${YELLOW}AZURE SETUP:${NC}"
    echo "1. Visit https://portal.azure.com"
    echo "2. Create a service principal: az ad sp create-for-rbac"
    echo "3. Update AZURE_* variables in .env file"
    echo
fi

# =============================================================================
# FINAL INSTRUCTIONS
# =============================================================================
echo
echo -e "${GREEN}=============================================================================${NC}"
echo -e "${GREEN}  ✅ Environment Setup Complete!${NC}"
echo -e "${GREEN}=============================================================================${NC}"
echo
echo -e "${YELLOW}NEXT STEPS:${NC}"
echo "1. Update API keys in .env file for external services"
echo "2. Run: docker compose up -d"
echo "3. Visit http://localhost:8000 for Supabase Dashboard"
echo "4. Visit http://localhost:3000 for the main application"
echo
echo -e "${YELLOW}IMPORTANT SECURITY NOTES:${NC}"
echo "• Never commit .env file to version control"
echo "• Store production secrets in a proper secret management system"
echo "• Regularly rotate passwords and API keys"
echo "• Use strong, unique passwords for production deployments"
echo
echo -e "${YELLOW}BACKUP INFORMATION:${NC}"
echo "• All data is stored in ./volumes/ directory"
echo "• Backup this directory regularly for data persistence"
echo "• Consider cloud backup solutions for production use"
echo
echo -e "${BLUE}Generated credentials:${NC}"
echo "• Supabase Dashboard: admin / ${DASHBOARD_PASSWORD}"
echo "• Flowise: admin / ${FLOWISE_PASSWORD}"
echo "• Grafana: admin / ${GRAFANA_ADMIN_PASSWORD}"
echo "• Neo4j: neo4j / ${NEO4J_PASSWORD}"
echo
echo -e "${GREEN}Setup complete! Happy building! 🚀${NC}"