#!/bin/bash
# Test script for enhanced Bitwarden population - simulates the process without actual Bitwarden access
# This allows us to test the secret generation and validation logic

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[TEST INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[TEST SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[TEST WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[TEST ERROR]${NC} $1"
}

log_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Test secret generation functions
test_secret_generation() {
    log_header "TESTING SECRET GENERATION"
    
    # Test hex generation
    local hex_secret=$(openssl rand -hex 32)
    if [[ ${#hex_secret} -eq 64 ]] && [[ "$hex_secret" =~ ^[0-9a-fA-F]+$ ]]; then
        log_success "Hex secret generation works: ${#hex_secret} chars"
    else
        log_error "Hex secret generation failed"
        return 1
    fi
    
    # Test base64 generation
    local base64_secret=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    if [[ ${#base64_secret} -eq 32 ]]; then
        log_success "Base64 secret generation works: ${#base64_secret} chars"
    else
        log_error "Base64 secret generation failed"
        return 1
    fi
    
    # Test password generation
    local password=$(openssl rand -base64 32 | tr -d "=+/1Il0Oo" | cut -c1-24)
    if [[ ${#password} -eq 24 ]]; then
        log_success "Password generation works: ${#password} chars"
    else
        log_error "Password generation failed"
        return 1
    fi
    
    log_success "All secret generation tests passed"
}

# Create a test .env file with generated secrets
create_test_env() {
    log_header "CREATING TEST .env FILE"
    
    # Backup existing .env if it exists
    if [ -f .env ]; then
        cp .env .env.backup.test.$(date +%Y%m%d_%H%M%S)
        log_info "Backed up existing .env file"
    fi
    
    # Create test .env with generated secrets
    cat > .env << EOF
# Test .env file with generated secrets
# Generated on $(date)

# Supabase Core Secrets
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/1Il0Oo" | cut -c1-32)
JWT_SECRET=$(openssl rand -hex 64)
ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJhbm9uIiwKICAgICJpc3MiOiAic3VwYWJhc2UtZGVtbyIsCiAgICAiaWF0IjogMTY0MTc2OTIwMCwKICAgICJleHAiOiAxNzk5NTM1NjAwCn0.dc_X5iR_VP_qT0zsiyj_I_OZ2T9FtRU2BBNWN8Bu4GE
SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJzZXJ2aWNlX3JvbGUiLAogICAgImlzcyI6ICJzdXBhYmFzZS1kZW1vIiwKICAgICJpYXQiOiAxNjQxNzY5MjAwLAogICAgImV4cCI6IDE3OTk1MzU2MDAKfQ.DaYlNEoUrrEn2Ig7tqibS-PHK5vgusbcbo7X36XVt4Q
DASHBOARD_USERNAME=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
DASHBOARD_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/1Il0Oo" | cut -c1-24)
POOLER_TENANT_ID=$(openssl rand -hex 8)

# n8n Workflow Automation
N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
N8N_USER_MANAGEMENT_JWT_SECRET=$(openssl rand -hex 32)

# Database and Infrastructure  
NEO4J_AUTH=neo4j/$(openssl rand -base64 32 | tr -d "=+/1Il0Oo" | cut -c1-24)
CLICKHOUSE_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/1Il0Oo" | cut -c1-24)
MINIO_ROOT_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
GRAYLOG_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/1Il0Oo" | cut -c1-24)
RABBITMQ_USER=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
RABBITMQ_PASS=$(openssl rand -base64 32 | tr -d "=+/1Il0Oo" | cut -c1-24)
QDRANT_API_KEY=$(openssl rand -hex 32)

# Authentication and Security
LANGFUSE_SALT=$(openssl rand -hex 32)
NEXTAUTH_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
SECRET_KEY_BASE=$(openssl rand -hex 64)
VAULT_ENC_KEY=$(openssl rand -hex 32)
SEARXNG_SECRET_KEY=$(openssl rand -hex 32)
LOCALAI_API_KEY=$(openssl rand -hex 32)
GRAYLOG_PASSWORD_SECRET=$(openssl rand -hex 32)

# AI Services (using placeholder values for testing)
OPENAI_API_KEY=sk-test$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-45)
SERPAPI_API_KEY=test_$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-60)
GRAPHRAG_API_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
CRAWL4AI_API_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

# Monitoring and Logging
LOGFLARE_PUBLIC_ACCESS_TOKEN=$(openssl rand -hex 32)
LOGFLARE_PRIVATE_ACCESS_TOKEN=$(openssl rand -hex 32)

# Optional Services
FLOWISE_USERNAME=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
FLOWISE_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/1Il0Oo" | cut -c1-24)

# Standard Configuration
POSTGRES_HOST=db
POSTGRES_DB=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POOLER_PROXY_PORT_TRANSACTION=6543
POOLER_DEFAULT_POOL_SIZE=20
POOLER_MAX_CLIENT_CONN=100
POOLER_DB_POOL_SIZE=5
FRONTEND_TITLE=Local AI Package
FRONTEND_DESCRIPTION=Self-hosted AI Development Environment
SITE_URL=http://localhost:3000
ADDITIONAL_REDIRECT_URLS=
JWT_EXPIRY=3600
DISABLE_SIGNUP=false
API_EXTERNAL_URL=http://localhost:8000
MAILER_URLPATHS_CONFIRMATION="/auth/v1/verify"
MAILER_URLPATHS_INVITE="/auth/v1/verify"
MAILER_URLPATHS_RECOVERY="/auth/v1/verify"
MAILER_URLPATHS_EMAIL_CHANGE="/auth/v1/verify"
ENABLE_EMAIL_SIGNUP=true
ENABLE_EMAIL_AUTOCONFIRM=true
SMTP_ADMIN_EMAIL=admin@example.com
SMTP_HOST=supabase-mail
SMTP_PORT=2500
SMTP_USER=fake_mail_user
SMTP_PASS=fake_mail_password
SMTP_SENDER_NAME=fake_sender
ENABLE_ANONYMOUS_USERS=false
ENABLE_PHONE_SIGNUP=true
ENABLE_PHONE_AUTOCONFIRM=true
STUDIO_DEFAULT_ORGANIZATION=Default Organization
STUDIO_DEFAULT_PROJECT=Default Project
STUDIO_PORT=3000
SUPABASE_PUBLIC_URL=http://localhost:8000
IMGPROXY_ENABLE_WEBP_DETECTION=true
FUNCTIONS_VERIFY_JWT=false
DOCKER_SOCKET_LOCATION=/var/run/docker.sock
GOOGLE_PROJECT_ID=GOOGLE_PROJECT_ID
GOOGLE_PROJECT_NUMBER=GOOGLE_PROJECT_NUMBER
PGRST_DB_SCHEMAS=public,storage,graphql_public
KONG_HTTP_PORT=8000
KONG_HTTPS_PORT=8443
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
LIBSQL_URL=http://libsql:8080
CREWAI_MODEL=gpt-4
CREWAI_TEMPERATURE=0.7
CREWAI_MAX_TOKENS=4000
LETTA_STORAGE_PATH=/data
LETTA_MAX_MEMORY_ITEMS=10000
GRAPHRAG_STORAGE_PATH=/data
GRAPHRAG_EMBEDDING_MODEL=text-embedding-ada-002
FALKOR_URL=redis://falkor:6379
FALKOR_MAX_CONNECTIONS=100
CRAWL4AI_STORAGE_PATH=/data
CRAWL4AI_MAX_DEPTH=3
CRAWL4AI_MAX_PAGES=100
GRAPHITE_PORT=8080
LIBSQL_PORT=8081
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
CREWAI_PORT=8000
LETTA_PORT=8001
FALKOR_PORT=6379
GRAPHRAG_PORT=8002
LLAMA_PORT=8003
CRAWL4AI_PORT=8004
EOF

    # Set proper permissions
    chmod 600 .env
    log_success "Test .env file created with proper permissions (600)"
    
    # Count variables
    local total_vars=$(grep -c "^[A-Z_]*=" .env)
    log_info "Created $total_vars environment variables"
}

# Test validation
test_validation() {
    log_header "TESTING .env VALIDATION"
    
    if [ -f "scripts/enhanced-validate-env.sh" ]; then
        log_info "Running enhanced validation script..."
        ./scripts/enhanced-validate-env.sh
    else
        log_warning "Enhanced validation script not found, using original..."
        if [ -f "scripts/validate-env.sh" ]; then
            ./scripts/validate-env.sh
        else
            log_error "No validation script found"
            return 1
        fi
    fi
    
    log_success "Validation test completed"
}

# Test Docker Compose syntax
test_docker_compose() {
    log_header "TESTING DOCKER COMPOSE SYNTAX"
    
    log_info "Testing docker-compose.yml syntax..."
    if docker compose config &>/dev/null; then
        log_success "docker-compose.yml syntax is valid"
    else
        log_error "docker-compose.yml has syntax errors"
        return 1
    fi
    
    log_info "Testing docker-compose.traefik.yml syntax..."
    if docker compose -f docker-compose.traefik.yml config &>/dev/null; then
        log_success "docker-compose.traefik.yml syntax is valid"
    else
        log_error "docker-compose.traefik.yml has syntax errors"
        return 1
    fi
    
    log_success "All Docker Compose files have valid syntax"
}

# Main test execution
main() {
    log_header "BITWARDEN INTEGRATION TEST SUITE"
    
    # Change to project root
    cd "$(dirname "$0")/.."
    log_info "Working directory: $(pwd)"
    
    # Run tests
    test_secret_generation
    create_test_env  
    test_validation
    test_docker_compose
    
    log_header "TEST SUMMARY"
    log_success "✅ All tests completed successfully!"
    log_info "Test .env file created and validated"
    log_info "Ready for deployment testing"
    
    log_warning "Note: This was a simulation - actual Bitwarden integration requires:"
    log_info "  1. Bitwarden account and CLI authentication"
    log_info "  2. Secrets stored in Bitwarden vault"
    log_info "  3. Run: ./scripts/enhanced-populate-env-from-bitwarden.sh"
}

# Execute tests
main "$@"