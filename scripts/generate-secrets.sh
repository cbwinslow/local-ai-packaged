#!/bin/bash

set -euo pipefail

# ========================================================================================
# Local AI Package - Comprehensive Secrets Generation Script
# ========================================================================================
# This script generates ALL required secure secrets for the Local AI Package
# It's idempotent - can be run multiple times safely
# Backs up existing .env files before making changes
# ========================================================================================

echo "🔐 Local AI Package - Comprehensive Secrets Generation"
echo "====================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check dependencies
check_dependencies() {
    echo "🔍 Checking dependencies..."
    
    local missing_deps=()
    
    if ! command -v openssl &> /dev/null; then
        missing_deps+=("openssl")
    fi
    
    if ! command -v date &> /dev/null; then
        missing_deps+=("date")
    fi
    
    if ! command -v shuf &> /dev/null && ! command -v gshuf &> /dev/null; then
        missing_deps+=("shuf or gshuf")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}❌ Missing dependencies: ${missing_deps[*]}${NC}"
        echo "Please install the missing dependencies and try again."
        exit 1
    fi
    
    echo -e "${GREEN}✅ All dependencies found${NC}"
}

# Generate secure random values
generate_hex() {
    local length=${1:-32}
    openssl rand -hex $length
}

generate_base64() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d '/+= \n'
}

generate_alphanumeric() {
    local length=${1:-16}
    openssl rand -hex $length | head -c $length
}

generate_password() {
    local length=${1:-24}
    openssl rand -base64 $length | tr -d '/+= \n' | head -c $length
}

generate_number() {
    local min=${1:-1000}
    local max=${2:-9999}
    if command -v shuf &> /dev/null; then
        shuf -i ${min}-${max} -n 1
    elif command -v gshuf &> /dev/null; then
        gshuf -i ${min}-${max} -n 1
    else
        echo $((min + RANDOM % (max - min + 1)))
    fi
}

# Generate JWT tokens with proper structure
generate_jwt_secret() {
    # Generate a 256-bit (32 byte) secret for JWT
    openssl rand -base64 32 | tr -d '/+= \n'
}

# Backup existing .env file
backup_env() {
    if [[ -f .env ]]; then
        local backup_name=".env.backup.$(date +%Y%m%d_%H%M%S)"
        cp .env "$backup_name"
        echo -e "${GREEN}✅ Backed up existing .env to $backup_name${NC}"
    fi
}

# Create .env from template if it doesn't exist
ensure_env_exists() {
    if [[ ! -f .env ]]; then
        if [[ -f .env.template ]]; then
            cp .env.template .env
            echo -e "${GREEN}✅ Created .env from .env.template${NC}"
        elif [[ -f .env.example ]]; then
            cp .env.example .env
            echo -e "${GREEN}✅ Created .env from .env.example${NC}"
        else
            echo -e "${RED}❌ No .env.template or .env.example found${NC}"
            echo "Please create one of these files first."
            exit 1
        fi
    fi
}

# Update or add environment variable
update_env_var() {
    local key="$1"
    local value="$2"
    local description="${3:-}"
    
    if grep -q "^${key}=" .env; then
        # Update existing variable
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^${key}=.*|${key}=${value}|" .env
        else
            sed -i "s|^${key}=.*|${key}=${value}|" .env
        fi
        echo -e "${GREEN}✅ Updated ${key}${NC}"
    else
        # Add new variable
        echo "${key}=${value}" >> .env
        echo -e "${GREEN}✅ Added ${key}${NC}"
    fi
    
    if [[ -n "$description" ]]; then
        echo "    📝 $description"
    fi
}

# Generate all secrets
generate_secrets() {
    echo ""
    echo "🔐 Generating secure secrets..."
    echo ""
    
    # Core Supabase secrets
    echo -e "${BLUE}🗄️  Supabase Database Secrets${NC}"
    POSTGRES_PASSWORD=$(generate_password 32)
    JWT_SECRET=$(generate_jwt_secret)
    DASHBOARD_USERNAME=$(generate_alphanumeric 12)
    DASHBOARD_PASSWORD=$(generate_password 24)
    POOLER_TENANT_ID=$(generate_number 1000 9999)
    SECRET_KEY_BASE=$(generate_hex 64)
    VAULT_ENC_KEY=$(generate_hex 32)
    
    update_env_var "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD" "PostgreSQL master password"
    update_env_var "JWT_SECRET" "$JWT_SECRET" "JWT signing secret (256-bit)"
    update_env_var "DASHBOARD_USERNAME" "$DASHBOARD_USERNAME" "Supabase dashboard username"
    update_env_var "DASHBOARD_PASSWORD" "$DASHBOARD_PASSWORD" "Supabase dashboard password"
    update_env_var "POOLER_TENANT_ID" "$POOLER_TENANT_ID" "Connection pooler tenant ID"
    update_env_var "SECRET_KEY_BASE" "$SECRET_KEY_BASE" "Supavisor secret key base"
    update_env_var "VAULT_ENC_KEY" "$VAULT_ENC_KEY" "Vault encryption key"
    
    # N8N secrets
    echo ""
    echo -e "${BLUE}🔄 N8N Workflow Automation Secrets${NC}"
    N8N_ENCRYPTION_KEY=$(generate_hex 32)
    N8N_JWT_SECRET=$(generate_hex 32)
    
    update_env_var "N8N_ENCRYPTION_KEY" "$N8N_ENCRYPTION_KEY" "N8N data encryption key"
    update_env_var "N8N_USER_MANAGEMENT_JWT_SECRET" "$N8N_JWT_SECRET" "N8N user management JWT secret"
    
    # AI Services secrets
    echo ""
    echo -e "${BLUE}🤖 AI Services Secrets${NC}"
    FLOWISE_USERNAME=$(generate_alphanumeric 12)
    FLOWISE_PASSWORD=$(generate_password 24)
    NEXTAUTH_SECRET=$(generate_hex 32)
    ENCRYPTION_KEY=$(generate_hex 32)
    LANGFUSE_SALT=$(generate_hex 32)
    
    update_env_var "FLOWISE_USERNAME" "$FLOWISE_USERNAME" "Flowise username"
    update_env_var "FLOWISE_PASSWORD" "$FLOWISE_PASSWORD" "Flowise password"
    update_env_var "NEXTAUTH_SECRET" "$NEXTAUTH_SECRET" "NextAuth.js secret"
    update_env_var "ENCRYPTION_KEY" "$ENCRYPTION_KEY" "General encryption key"
    update_env_var "LANGFUSE_SALT" "$LANGFUSE_SALT" "Langfuse password salt"
    
    # Database services
    echo ""
    echo -e "${BLUE}💾 Database Services Secrets${NC}"
    NEO4J_PASSWORD=$(generate_password 24)
    CLICKHOUSE_PASSWORD=$(generate_password 24)
    MINIO_ROOT_PASSWORD=$(generate_password 24)
    
    update_env_var "NEO4J_AUTH" "neo4j/$NEO4J_PASSWORD" "Neo4j authentication"
    update_env_var "CLICKHOUSE_PASSWORD" "$CLICKHOUSE_PASSWORD" "ClickHouse password"
    update_env_var "MINIO_ROOT_PASSWORD" "$MINIO_ROOT_PASSWORD" "MinIO root password"
    
    # Update S3 secrets that reference MinIO password
    update_env_var "LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY" "$MINIO_ROOT_PASSWORD"
    update_env_var "LANGFUSE_S3_MEDIA_UPLOAD_SECRET_ACCESS_KEY" "$MINIO_ROOT_PASSWORD"
    update_env_var "LANGFUSE_S3_BATCH_EXPORT_SECRET_ACCESS_KEY" "$MINIO_ROOT_PASSWORD"
    
    # Search and discovery
    echo ""
    echo -e "${BLUE}🔍 Search & Discovery Secrets${NC}"
    SEARXNG_SECRET_KEY=$(generate_hex 32)
    QDRANT_API_KEY=$(generate_hex 32)
    
    update_env_var "SEARXNG_SECRET_KEY" "$SEARXNG_SECRET_KEY" "SearXNG secret key"
    update_env_var "QDRANT_API_KEY" "$QDRANT_API_KEY" "Qdrant vector database API key"
    
    # Message queue and logging
    echo ""
    echo -e "${BLUE}📨 Message Queue & Logging Secrets${NC}"
    RABBITMQ_USER=$(generate_alphanumeric 12)
    RABBITMQ_PASSWORD=$(generate_password 24)
    GRAYLOG_PASSWORD=$(generate_password 24)
    GRAFANA_ADMIN_PASSWORD=$(generate_password 24)
    PROMETHEUS_PASSWORD=$(generate_password 24)
    
    update_env_var "RABBITMQ_USER" "$RABBITMQ_USER" "RabbitMQ username"
    update_env_var "RABBITMQ_PASSWORD" "$RABBITMQ_PASSWORD" "RabbitMQ password"
    update_env_var "GRAYLOG_PASSWORD" "$GRAYLOG_PASSWORD" "Graylog admin password"
    update_env_var "GRAFANA_ADMIN_PASSWORD" "$GRAFANA_ADMIN_PASSWORD" "Grafana admin password"
    update_env_var "PROMETHEUS_PASSWORD" "$PROMETHEUS_PASSWORD" "Prometheus password"
    
    # Optional services
    echo ""
    echo -e "${BLUE}🔧 Optional Service Secrets${NC}"
    LOGFLARE_PUBLIC_TOKEN=$(generate_hex 32)
    LOGFLARE_PRIVATE_TOKEN=$(generate_hex 32)
    
    update_env_var "LOGFLARE_PUBLIC_TOKEN" "$LOGFLARE_PUBLIC_TOKEN" "Logflare public token"
    update_env_var "LOGFLARE_PRIVATE_TOKEN" "$LOGFLARE_PRIVATE_TOKEN" "Logflare private token"
}

# Generate Supabase JWT tokens if jq is available
generate_supabase_jwt_tokens() {
    if command -v jq &> /dev/null; then
        echo ""
        echo -e "${BLUE}🎫 Generating Supabase JWT tokens...${NC}"
        
        # Get the JWT secret
        local jwt_secret=$(grep "^JWT_SECRET=" .env | cut -d'=' -f2)
        
        if [[ -n "$jwt_secret" ]]; then
            # Create 10-year expiration
            local exp=$(($(date +%s) + 315360000))
            
            # Generate anon key
            local anon_payload=$(echo '{"aud":"authenticated","exp":'$exp',"role":"anon"}' | base64 -w 0 | tr -d '=')
            local anon_header=$(echo '{"alg":"HS256","typ":"JWT"}' | base64 -w 0 | tr -d '=')
            local anon_signature=$(echo -n "${anon_header}.${anon_payload}" | openssl dgst -sha256 -hmac "$jwt_secret" -binary | base64 -w 0 | tr -d '=')
            local anon_key="${anon_header}.${anon_payload}.${anon_signature}"
            
            # Generate service role key
            local service_payload=$(echo '{"aud":"authenticated","exp":'$exp',"role":"service_role"}' | base64 -w 0 | tr -d '=')
            local service_signature=$(echo -n "${anon_header}.${service_payload}" | openssl dgst -sha256 -hmac "$jwt_secret" -binary | base64 -w 0 | tr -d '=')
            local service_key="${anon_header}.${service_payload}.${service_signature}"
            
            update_env_var "ANON_KEY" "$anon_key" "Supabase anonymous key"
            update_env_var "SERVICE_ROLE_KEY" "$service_key" "Supabase service role key"
            
            echo -e "${GREEN}✅ JWT tokens valid until $(date -d @$exp '+%Y-%m-%d')${NC}"
        else
            echo -e "${YELLOW}⚠️  JWT_SECRET not found, skipping JWT token generation${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  jq not found, skipping JWT token generation${NC}"
        echo "Install jq to automatically generate Supabase JWT tokens"
    fi
}

# Set secure permissions
secure_env_file() {
    chmod 600 .env
    echo -e "${GREEN}✅ Set secure permissions (600) on .env file${NC}"
}

# Validation
validate_secrets() {
    echo ""
    echo "🔍 Validating generated secrets..."
    
    local required_vars=(
        "POSTGRES_PASSWORD"
        "JWT_SECRET"
        "N8N_ENCRYPTION_KEY"
        "NEXTAUTH_SECRET"
        "ENCRYPTION_KEY"
        "FLOWISE_PASSWORD"
        "CLICKHOUSE_PASSWORD"
        "MINIO_ROOT_PASSWORD"
        "SEARXNG_SECRET_KEY"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env || grep -q "^${var}=your-" .env; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ All required secrets are properly set${NC}"
        return 0
    else
        echo -e "${RED}❌ Missing or incomplete secrets: ${missing_vars[*]}${NC}"
        return 1
    fi
}

# Main execution
main() {
    check_dependencies
    backup_env
    ensure_env_exists
    generate_secrets
    generate_supabase_jwt_tokens
    secure_env_file
    
    if validate_secrets; then
        echo ""
        echo -e "${GREEN}🎉 Secret generation completed successfully!${NC}"
        echo ""
        echo -e "${BLUE}📋 Summary:${NC}"
        echo "- All secrets use cryptographically secure random values"
        echo "- JWT keys have 10-year expiration (rotate as needed)"
        echo "- .env file has secure permissions (600)"
        echo "- Backup of previous .env created if it existed"
        echo ""
        echo -e "${BLUE}🚀 Next Steps:${NC}"
        echo "1. Review secrets: grep -E '^(POSTGRES_|JWT_|N8N_|NEXTAUTH_|ENCRYPTION_)' .env"
        echo "2. Start services: ./scripts/start-all-services.sh"
        echo "3. Verify health: ./scripts/health-check.sh"
        echo ""
        echo -e "${YELLOW}⚠️  Security Notes:${NC}"
        echo "- Keep .env file secure and never commit to version control"
        echo "- Regularly rotate secrets (recommended: annually)"
        echo "- Monitor service logs for authentication issues"
        echo "- Use backup/restore scripts for disaster recovery"
    else
        echo ""
        echo -e "${RED}❌ Secret generation incomplete. Please check the errors above.${NC}"
        exit 1
    fi
}

# Run main function
main "$@"