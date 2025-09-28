#!/bin/bash
# Enhanced .env population from Bitwarden vault
# Supports both stored secrets and generated secrets (using openssl formulas)
# Provides comprehensive validation and error handling

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Check prerequisites
check_prerequisites() {
    log_header "CHECKING PREREQUISITES"
    
    # Check Bitwarden CLI
    if ! command -v bw &> /dev/null; then
        log_error "Bitwarden CLI (bw) not found. Install with: npm install -g @bitwarden/cli"
        exit 1
    fi
    log_success "Bitwarden CLI found"
    
    # Check openssl for secret generation
    if ! command -v openssl &> /dev/null; then
        log_error "openssl not found. Required for secret generation."
        exit 1
    fi
    log_success "OpenSSL found"
    
    # Check for .env.example template
    if [ ! -f "config/.env.example" ]; then
        log_error "config/.env.example not found. This is required as a template."
        exit 1
    fi
    log_success "Template file config/.env.example found"
}

# Authenticate with Bitwarden
authenticate_bitwarden() {
    log_header "BITWARDEN AUTHENTICATION"
    
    # Check if already authenticated
    if [ -n "$BW_SESSION" ] && bw sync --session "$BW_SESSION" &>/dev/null; then
        log_success "Already authenticated with Bitwarden"
        return
    fi
    
    # Unlock Bitwarden
    if [ -z "$BW_PASSWORD" ]; then
        log_info "Enter your Bitwarden master password:"
        read -s BW_PASSWORD
        export BW_PASSWORD
    fi
    
    log_info "Unlocking Bitwarden vault..."
    export BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$BW_SESSION" ]; then
        log_success "Bitwarden vault unlocked successfully"
    else
        log_error "Failed to unlock Bitwarden vault. Check your password."
        exit 1
    fi
    
    # Sync vault
    log_info "Syncing Bitwarden vault..."
    bw sync --session "$BW_SESSION" &>/dev/null
    log_success "Vault synchronized"
}

# Generate secret using openssl
generate_secret() {
    local type=$1
    local length=${2:-32}
    
    case $type in
        "hex")
            openssl rand -hex $length
            ;;
        "base64")
            openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
            ;;
        "password")
            # Generate strong password without problematic characters
            openssl rand -base64 32 | tr -d "=+/1Il0Oo" | cut -c1-$length
            ;;
        *)
            log_error "Unknown secret type: $type"
            exit 1
            ;;
    esac
}

# Get or generate secret
get_or_generate_secret() {
    local name=$1
    local secret_type=${2:-"password"}
    local length=${3:-32}
    
    # First try to get from Bitwarden
    local value=$(bw get password "$name" --session "$BW_SESSION" 2>/dev/null || echo "")
    
    if [ -n "$value" ] && [ "$value" != "BITWARDEN_SECRET_MISSING_$name" ]; then
        echo "$value"
    else
        # Generate new secret
        local generated_value=$(generate_secret "$secret_type" "$length")
        log_info "Generated new $secret_type secret for $name"
        
        # Store in Bitwarden for future use
        store_secret_in_bitwarden "$name" "$generated_value"
        
        echo "$generated_value"
    fi
}

# Store secret in Bitwarden
store_secret_in_bitwarden() {
    local name=$1
    local value=$2
    
    # Create item template
    local template='{
        "organizationId": null,
        "folderId": null,
        "type": 1,
        "name": "'$name'",
        "notes": "Auto-generated secret for Local AI Package - '$name'",
        "favorite": false,
        "fields": [],
        "login": {
            "username": "localai",
            "password": "'$value'"
        },
        "secureNote": null,
        "card": null,
        "identity": null
    }'
    
    # Store in Bitwarden
    echo "$template" | bw create item --session "$BW_SESSION" &>/dev/null
    if [ $? -eq 0 ]; then
        log_success "Stored $name in Bitwarden vault"
    else
        log_warning "Could not store $name in Bitwarden vault (may already exist)"
    fi
}

# Create .env file from template with secrets
populate_env_file() {
    log_header "POPULATING .env FILE"
    
    # Backup existing .env if it exists
    if [ -f .env ]; then
        local backup_name=".env.backup.$(date +%Y%m%d_%H%M%S)"
        cp .env "$backup_name"
        log_info "Backed up existing .env to $backup_name"
    fi
    
    # Start with empty .env
    > .env
    
    log_info "Populating secrets from Bitwarden and generating missing ones..."
    
    # Add header
    cat << 'EOF' >> .env
# Auto-populated .env file from Bitwarden vault
# Generated on $(date)
# DO NOT COMMIT THIS FILE TO VERSION CONTROL

EOF

    # Core Supabase secrets (these MUST be secure)
    echo "# Supabase Core Secrets" >> .env
    echo "POSTGRES_PASSWORD=$(get_or_generate_secret "localai_supabase_postgres_password" "password" 32)" >> .env
    echo "JWT_SECRET=$(get_or_generate_secret "localai_supabase_jwt_secret" "hex" 64)" >> .env
    echo "ANON_KEY=$(get_or_generate_secret "localai_supabase_anon_key")" >> .env
    echo "SERVICE_ROLE_KEY=$(get_or_generate_secret "localai_supabase_service_role_key")" >> .env
    echo "DASHBOARD_USERNAME=$(get_or_generate_secret "localai_supabase_dashboard_username" "password" 16)" >> .env
    echo "DASHBOARD_PASSWORD=$(get_or_generate_secret "localai_supabase_dashboard_password" "password" 24)" >> .env
    echo "POOLER_TENANT_ID=$(get_or_generate_secret "localai_supabase_pooler_tenant_id" "hex" 8)" >> .env
    echo "" >> .env
    
    # n8n secrets
    echo "# n8n Workflow Automation" >> .env
    echo "N8N_ENCRYPTION_KEY=$(get_or_generate_secret "localai_n8n_encryption_key" "hex" 32)" >> .env
    echo "N8N_USER_MANAGEMENT_JWT_SECRET=$(get_or_generate_secret "localai_n8n_jwt_secret" "hex" 32)" >> .env
    echo "" >> .env
    
    # Database and infrastructure
    echo "# Database and Infrastructure" >> .env
    local neo4j_password=$(get_or_generate_secret "localai_neo4j_password" "password" 24)
    echo "NEO4J_AUTH=neo4j/$neo4j_password" >> .env
    echo "CLICKHOUSE_PASSWORD=$(get_or_generate_secret "localai_clickhouse_password" "password" 24)" >> .env
    echo "MINIO_ROOT_PASSWORD=$(get_or_generate_secret "localai_minio_root_password" "base64" 24)" >> .env
    echo "GRAYLOG_PASSWORD=$(get_or_generate_secret "localai_graylog_password" "password" 24)" >> .env
    echo "RABBITMQ_USER=$(get_or_generate_secret "localai_rabbitmq_user" "password" 16)" >> .env
    echo "RABBITMQ_PASS=$(get_or_generate_secret "localai_rabbitmq_password" "password" 24)" >> .env
    echo "QDRANT_API_KEY=$(get_or_generate_secret "localai_qdrant_api_key" "hex" 32)" >> .env
    echo "" >> .env
    
    # Authentication and security
    echo "# Authentication and Security" >> .env
    echo "LANGFUSE_SALT=$(get_or_generate_secret "localai_langfuse_salt" "hex" 32)" >> .env
    echo "NEXTAUTH_SECRET=$(get_or_generate_secret "localai_nextauth_secret" "hex" 32)" >> .env
    echo "ENCRYPTION_KEY=$(get_or_generate_secret "localai_encryption_key" "hex" 32)" >> .env
    echo "SECRET_KEY_BASE=$(get_or_generate_secret "localai_secret_key_base" "hex" 64)" >> .env
    echo "VAULT_ENC_KEY=$(get_or_generate_secret "localai_vault_enc_key" "hex" 32)" >> .env
    echo "SEARXNG_SECRET_KEY=$(get_or_generate_secret "localai_searxng_secret_key" "hex" 32)" >> .env
    echo "LOCALAI_API_KEY=$(get_or_generate_secret "localai_localai_api_key" "hex" 32)" >> .env
    echo "GRAYLOG_PASSWORD_SECRET=$(get_or_generate_secret "localai_graylog_password_secret" "hex" 32)" >> .env
    echo "" >> .env
    
    # Optional AI service keys (these may be placeholders if not set)
    echo "# AI Services (Optional)" >> .env
    echo "OPENAI_API_KEY=$(get_or_generate_secret "localai_openai_api_key" "password" 51)" >> .env
    echo "SERPAPI_API_KEY=$(get_or_generate_secret "localai_serpapi_api_key" "password" 64)" >> .env
    echo "GRAPHRAG_API_KEY=$(get_or_generate_secret "localai_graphrag_api_key" "password" 32)" >> .env
    echo "CRAWL4AI_API_KEY=$(get_or_generate_secret "localai_crawl4ai_api_key" "password" 32)" >> .env
    echo "" >> .env
    
    # Monitoring and logging
    echo "# Monitoring and Logging" >> .env
    echo "LOGFLARE_PUBLIC_ACCESS_TOKEN=$(get_or_generate_secret "localai_logflare_public_token" "hex" 32)" >> .env
    echo "LOGFLARE_PRIVATE_ACCESS_TOKEN=$(get_or_generate_secret "localai_logflare_private_token" "hex" 32)" >> .env
    echo "" >> .env
    
    # Optional services
    echo "# Optional Services" >> .env
    echo "FLOWISE_USERNAME=$(get_or_generate_secret "localai_flowise_username" "password" 16)" >> .env
    echo "FLOWISE_PASSWORD=$(get_or_generate_secret "localai_flowise_password" "password" 24)" >> .env
    echo "" >> .env
    
    # Append standard configuration from template
    echo "# Standard Configuration (Non-sensitive)" >> .env
    cat config/.env.example | grep -E "^[A-Z_]+=([^y]|y[^o]|yo[^u]|you[^r])" | grep -v "^#" >> .env
    
    # Set proper permissions
    chmod 600 .env
    log_success ".env file created with proper permissions (600)"
}

# Validate the generated .env file
validate_env_file() {
    log_header "VALIDATING .env FILE"
    
    if [ ! -f .env ]; then
        log_error ".env file not found"
        return 1
    fi
    
    # Check for placeholder values
    local placeholders=$(grep -E "(your_|super-secret|PLACEHOLDER|MISSING)" .env || true)
    if [ -n "$placeholders" ]; then
        log_warning "Found potential placeholder values:"
        echo "$placeholders"
        log_warning "These should be replaced with actual values"
    else
        log_success "No placeholder values found"
    fi
    
    # Check critical secrets exist and have proper length
    local critical_secrets=(
        "POSTGRES_PASSWORD:20"
        "JWT_SECRET:64"
        "N8N_ENCRYPTION_KEY:32"
        "LANGFUSE_SALT:32"
        "NEXTAUTH_SECRET:32"
        "ENCRYPTION_KEY:32"
    )
    
    local validation_failed=false
    for item in "${critical_secrets[@]}"; do
        local var_name="${item%:*}"
        local min_length="${item#*:}"
        
        local value=$(grep "^${var_name}=" .env | cut -d'=' -f2- || echo "")
        if [ -z "$value" ]; then
            log_error "$var_name is missing"
            validation_failed=true
        elif [ ${#value} -lt $min_length ]; then
            log_error "$var_name is too short (${#value} chars, need at least $min_length)"
            validation_failed=true
        else
            log_success "$var_name is valid (${#value} chars)"
        fi
    done
    
    if [ "$validation_failed" = true ]; then
        log_error ".env validation failed"
        return 1
    fi
    
    log_success ".env file validation completed successfully"
    
    # Count total variables
    local total_vars=$(grep -c "^[A-Z_]*=" .env)
    log_info "Total environment variables: $total_vars"
}

# Main execution
main() {
    log_header "ENHANCED BITWARDEN .env POPULATION"
    
    check_prerequisites
    authenticate_bitwarden
    populate_env_file
    validate_env_file
    
    log_header "COMPLETION SUMMARY"
    log_success "✅ .env file populated successfully from Bitwarden"
    log_success "✅ All critical secrets validated"
    log_success "✅ File permissions set to 600"
    
    log_info "Next steps:"
    echo "  1. Review .env file for any placeholder values"
    echo "  2. Run validation: ./scripts/validate-env.sh"
    echo "  3. Start services: python tools/start_services_enhanced.py"
    
    log_warning "Remember to set BW_PASSWORD environment variable for automated runs"
}

# Execute main function
main "$@"