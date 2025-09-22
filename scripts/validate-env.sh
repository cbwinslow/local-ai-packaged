#!/bin/bash

# validate-env.sh - Comprehensive .env file validation script
# Validates all environment variables against security and format requirements
# Based on ENV_VARIABLES_RULES.md and RULES.md specifications

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
ENV_FILE=".env"
PASSED_TESTS=0
FAILED_TESTS=0
TOTAL_TESTS=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

log_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Validation functions
validate_hex_string() {
    local var_name=$1
    local value=$2
    local min_length=${3:-32}
    ((TOTAL_TESTS++))

    if [[ ! "$value" =~ ^[0-9a-fA-F]+$ ]]; then
        log_error "$var_name: Must contain only hexadecimal characters (0-9, a-f, A-F)"
        return 1
    fi

    if [[ ${#value} -lt $min_length ]]; then
        log_error "$var_name: Must be at least $min_length hex characters (${#value} provided)"
        return 1
    fi

    log_success "$var_name: Valid hex string (${#value} chars)"
    return 0
}

validate_base64_filtered() {
    local var_name=$1
    local value=$2
    local min_length=${3:-12}
    ((TOTAL_TESTS++))

    if [[ ${#value} -lt $min_length ]]; then
        log_error "$var_name: Must be at least $min_length characters (${#value} provided)"
        return 1
    fi

    if [[ "$value" =~ [/+] ]]; then
        log_error "$var_name: Must not contain '/' or '+' characters"
        return 1
    fi

    log_success "$var_name: Valid filtered base64 (${#value} chars)"
    return 0
}

validate_jwt() {
    local var_name=$1
    local value=$2
    ((TOTAL_TESTS++))

    local parts
    IFS='.' read -ra parts <<< "$value"
    if [[ ${#parts[@]} -ne 3 ]]; then
        log_error "$var_name: Must have 3 parts separated by dots"
        return 1
    fi

    # Validate header is valid base64url
    if ! echo "${parts[0]}" | base64 -d &>/dev/null; then
        log_error "$var_name: Invalid JWT header (not valid base64)"
        return 1
    fi

    # Validate payload is valid base64url
    if ! echo "${parts[1]}" | base64 -d &>/dev/null; then
        log_error "$var_name: Invalid JWT payload (not valid base64)"
        return 1
    fi

    log_success "$var_name: Valid JWT format"
    return 0
}

validate_port() {
    local var_name=$1
    local value=$2
    ((TOTAL_TESTS++))

    if ! [[ "$value" =~ ^[0-9]+$ ]] || [[ "$value" -lt 1024 ]] || [[ "$value" -gt 65535 ]]; then
        log_error "$var_name: Must be a valid port number between 1024 and 65535"
        return 1
    fi

    log_success "$var_name: Valid port number ($value)"
    return 0
}

validate_url() {
    local var_name=$1
    local value=$2
    ((TOTAL_TESTS++))

    if [[ ! "$value" =~ ^https?:// ]]; then
        log_error "$var_name: Must start with http:// or https://"
        return 1
    fi

    log_success "$var_name: Valid URL format"
    return 0
}

validate_numeric_range() {
    local var_name=$1
    local value=$2
    local min_val=$3
    local max_val=$4
    ((TOTAL_TESTS++))

    if ! [[ "$value" =~ ^[0-9]+$ ]] || [[ "$value" -lt $min_val ]] || [[ "$value" -gt $max_val ]]; then
        log_error "$var_name: Must be between $min_val and $max_val"
        return 1
    fi

    log_success "$var_name: Valid numeric range ($value)"
    return 0
}

validate_not_placeholder() {
    local var_name=$1
    local value=$2
    ((TOTAL_TESTS++))

    if [[ "$value" =~ ^your- ]] || [[ "$value" =~ ^change-me ]] || [[ "$value" == "placeholder" ]]; then
        log_error "$var_name: Contains placeholder value that must be changed"
        return 1
    fi

    log_success "$var_name: Not a placeholder value"
    return 0
}

validate_variable_exists() {
    local var_name=$1
    local value=$2
    ((TOTAL_TESTS++))

    if [[ -z "$value" ]]; then
        log_error "$var_name: Variable is not set or empty"
        return 1
    fi

    log_success "$var_name: Variable is set"
    return 0
}

# Load environment variables
load_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file '$ENV_FILE' not found"
        exit 1
    fi

    # Source the .env file
    set -a
    source "$ENV_FILE"
    set +a

    log_info "Loaded environment variables from $ENV_FILE"
}

# Validate all secrets
validate_all_secrets() {
    log_header "ENVIRONMENT VARIABLE VALIDATION"

    # Core N8N secrets
    if [[ -n "$N8N_ENCRYPTION_KEY" ]]; then
        validate_variable_exists "N8N_ENCRYPTION_KEY" "$N8N_ENCRYPTION_KEY"
        validate_hex_string "N8N_ENCRYPTION_KEY" "$N8N_ENCRYPTION_KEY" 32
    fi

    if [[ -n "$N8N_USER_MANAGEMENT_JWT_SECRET" ]]; then
        validate_variable_exists "N8N_USER_MANAGEMENT_JWT_SECRET" "$N8N_USER_MANAGEMENT_JWT_SECRET"
        validate_hex_string "N8N_USER_MANAGEMENT_JWT_SECRET" "$N8N_USER_MANAGEMENT_JWT_SECRET" 32
    fi

    # PostgreSQL
    if [[ -n "$POSTGRES_PASSWORD" ]]; then
        validate_variable_exists "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD"
        validate_base64_filtered "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD" 24
    fi

    # JWT and Supabase
    if [[ -n "$JWT_SECRET" ]]; then
        validate_variable_exists "JWT_SECRET" "$JWT_SECRET"
        validate_hex_string "JWT_SECRET" "$JWT_SECRET" 32
    fi

    if [[ -n "$ANON_KEY" ]]; then
        validate_variable_exists "ANON_KEY" "$ANON_KEY"
        validate_jwt "ANON_KEY" "$ANON_KEY"
    fi

    if [[ -n "$SERVICE_ROLE_KEY" ]]; then
        validate_variable_exists "SERVICE_ROLE_KEY" "$SERVICE_ROLE_KEY"
        validate_jwt "SERVICE_ROLE_KEY" "$SERVICE_ROLE_KEY"
    fi

    # Dashboard credentials
    if [[ -n "$DASHBOARD_USERNAME" ]]; then
        validate_variable_exists "DASHBOARD_USERNAME" "$DASHBOARD_USERNAME"
        validate_hex_string "DASHBOARD_USERNAME" "$DASHBOARD_USERNAME" 8
    fi

    if [[ -n "$DASHBOARD_PASSWORD" ]]; then
        validate_variable_exists "DASHBOARD_PASSWORD" "$DASHBOARD_PASSWORD"
        validate_base64_filtered "DASHBOARD_PASSWORD" "$DASHBOARD_PASSWORD" 12
    fi

    # Pooler tenant ID
    if [[ -n "$POOLER_TENANT_ID" ]]; then
        validate_variable_exists "POOLER_TENANT_ID" "$POOLER_TENANT_ID"
        validate_numeric_range "POOLER_TENANT_ID" "$POOLER_TENANT_ID" 1000 9999
    fi

    # Neo4j
    if [[ -n "$NEO4J_AUTH" ]]; then
        validate_variable_exists "NEO4J_AUTH" "$NEO4J_AUTH"
        if [[ "$NEO4J_AUTH" =~ ^neo4j/ ]]; then
            local neo4j_pass="${NEO4J_AUTH#neo4j/}"
            validate_base64_filtered "NEO4J_PASSWORD" "$neo4j_pass" 12
        else
            ((TOTAL_TESTS++))
            log_error "NEO4J_AUTH: Must be in format 'neo4j/password'"
        fi
    fi

    # ClickHouse
    if [[ -n "$CLICKHOUSE_PASSWORD" ]]; then
        validate_variable_exists "CLICKHOUSE_PASSWORD" "$CLICKHOUSE_PASSWORD"
        validate_base64_filtered "CLICKHOUSE_PASSWORD" "$CLICKHOUSE_PASSWORD" 12
    fi

    # MinIO
    if [[ -n "$MINIO_ROOT_PASSWORD" ]]; then
        validate_variable_exists "MINIO_ROOT_PASSWORD" "$MINIO_ROOT_PASSWORD"
        validate_base64_filtered "MINIO_ROOT_PASSWORD" "$MINIO_ROOT_PASSWORD" 12
    fi

    # Langfuse
    if [[ -n "$LANGFUSE_SALT" ]]; then
        validate_variable_exists "LANGFUSE_SALT" "$LANGFUSE_SALT"
        validate_hex_string "LANGFUSE_SALT" "$LANGFUSE_SALT" 32
    fi

    if [[ -n "$NEXTAUTH_SECRET" ]]; then
        validate_variable_exists "NEXTAUTH_SECRET" "$NEXTAUTH_SECRET"
        validate_hex_string "NEXTAUTH_SECRET" "$NEXTAUTH_SECRET" 32
    fi

    if [[ -n "$ENCRYPTION_KEY" ]]; then
        validate_variable_exists "ENCRYPTION_KEY" "$ENCRYPTION_KEY"
        validate_hex_string "ENCRYPTION_KEY" "$ENCRYPTION_KEY" 32
    fi

    # Supabase additional keys
    if [[ -n "$SECRET_KEY_BASE" ]]; then
        validate_variable_exists "SECRET_KEY_BASE" "$SECRET_KEY_BASE"
        validate_hex_string "SECRET_KEY_BASE" "$SECRET_KEY_BASE" 64
    fi

    if [[ -n "$VAULT_ENC_KEY" ]]; then
        validate_variable_exists "VAULT_ENC_KEY" "$VAULT_ENC_KEY"
        validate_hex_string "VAULT_ENC_KEY" "$VAULT_ENC_KEY" 32
    fi

    # Logflare
    if [[ -n "$LOGFLARE_PUBLIC_ACCESS_TOKEN" ]]; then
        validate_variable_exists "LOGFLARE_PUBLIC_ACCESS_TOKEN" "$LOGFLARE_PUBLIC_ACCESS_TOKEN"
        validate_hex_string "LOGFLARE_PUBLIC_ACCESS_TOKEN" "$LOGFLARE_PUBLIC_ACCESS_TOKEN" 32
    fi

    if [[ -n "$LOGFLARE_PRIVATE_ACCESS_TOKEN" ]]; then
        validate_variable_exists "LOGFLARE_PRIVATE_ACCESS_TOKEN" "$LOGFLARE_PRIVATE_ACCESS_TOKEN"
        validate_hex_string "LOGFLARE_PRIVATE_ACCESS_TOKEN" "$LOGFLARE_PRIVATE_ACCESS_TOKEN" 32
    fi

    # Optional services
    if [[ -n "$FLOWISE_USERNAME" ]]; then
        validate_variable_exists "FLOWISE_USERNAME" "$FLOWISE_USERNAME"
        validate_hex_string "FLOWISE_USERNAME" "$FLOWISE_USERNAME" 8
    fi

    if [[ -n "$FLOWISE_PASSWORD" ]]; then
        validate_variable_exists "FLOWISE_PASSWORD" "$FLOWISE_PASSWORD"
        validate_base64_filtered "FLOWISE_PASSWORD" "$FLOWISE_PASSWORD" 12
    fi

    if [[ -n "$GRAFANA_ADMIN_PASSWORD" ]]; then
        validate_variable_exists "GRAFANA_ADMIN_PASSWORD" "$GRAFANA_ADMIN_PASSWORD"
        validate_base64_filtered "GRAFANA_ADMIN_PASSWORD" "$GRAFANA_ADMIN_PASSWORD" 12
    fi

    if [[ -n "$PROMETHEUS_PASSWORD" ]]; then
        validate_variable_exists "PROMETHEUS_PASSWORD" "$PROMETHEUS_PASSWORD"
        validate_base64_filtered "PROMETHEUS_PASSWORD" "$PROMETHEUS_PASSWORD" 12
    fi

    if [[ -n "$RABBITMQ_USER" ]]; then
        validate_variable_exists "RABBITMQ_USER" "$RABBITMQ_USER"
        validate_hex_string "RABBITMQ_USER" "$RABBITMQ_USER" 8
    fi

    if [[ -n "$RABBITMQ_PASSWORD" ]]; then
        validate_variable_exists "RABBITMQ_PASSWORD" "$RABBITMQ_PASSWORD"
        validate_base64_filtered "RABBITMQ_PASSWORD" "$RABBITMQ_PASSWORD" 12
    fi

    if [[ -n "$GRAYLOG_PASSWORD" ]]; then
        validate_variable_exists "GRAYLOG_PASSWORD" "$GRAYLOG_PASSWORD"
        validate_base64_filtered "GRAYLOG_PASSWORD" "$GRAYLOG_PASSWORD" 12
    fi

    if [[ -n "$QDRANT_API_KEY" ]]; then
        validate_variable_exists "QDRANT_API_KEY" "$QDRANT_API_KEY"
        validate_hex_string "QDRANT_API_KEY" "$QDRANT_API_KEY" 32
    fi

    if [[ -n "$SEARXNG_SECRET_KEY" ]]; then
        validate_variable_exists "SEARXNG_SECRET_KEY" "$SEARXNG_SECRET_KEY"
        validate_hex_string "SEARXNG_SECRET_KEY" "$SEARXNG_SECRET_KEY" 32
    fi

    if [[ -n "$LOCALAI_API_KEY" ]]; then
        validate_variable_exists "LOCALAI_API_KEY" "$LOCALAI_API_KEY"
        validate_hex_string "LOCALAI_API_KEY" "$LOCALAI_API_KEY" 32
    fi

    if [[ -n "$GRAYLOG_PASSWORD_SECRET" ]]; then
        validate_variable_exists "GRAYLOG_PASSWORD_SECRET" "$GRAYLOG_PASSWORD_SECRET"
        validate_hex_string "GRAYLOG_PASSWORD_SECRET" "$GRAYLOG_PASSWORD_SECRET" 32
    fi
}

# Check for placeholder values
check_placeholders() {
    log_header "PLACEHOLDER VALUE DETECTION"

    local placeholders_found=0

    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue

        # Remove quotes if present
        value=$(echo "$value" | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")

        if [[ "$value" =~ ^your- ]] || [[ "$value" =~ ^change-me ]] || [[ "$value" == "placeholder" ]]; then
            ((TOTAL_TESTS++))
            log_error "$key: Contains placeholder value '$value'"
            ((placeholders_found++))
        fi
    done < "$ENV_FILE"

    if [[ $placeholders_found -eq 0 ]]; then
        ((TOTAL_TESTS++))
        log_success "No placeholder values found in .env file"
    fi
}

# Main execution
main() {
    log_header "LOCAL AI PACKAGE .ENV VALIDATION"
    log_info "Validating environment variables against security rules..."
    log_info "Environment file: $ENV_FILE"

    # Check if .env exists
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file '$ENV_FILE' not found. Please create it first."
        exit 1
    fi

    # Load environment variables
    load_env_file

    # Run validations
    validate_all_secrets
    check_placeholders

    # Summary
    log_header "VALIDATION SUMMARY"
    echo "Total tests run: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"

    if [[ $FAILED_TESTS -eq 0 ]]; then
        log_success "All validations passed! Your .env file is compliant with security rules."
        exit 0
    else
        log_error "$FAILED_TESTS validation(s) failed. Please fix the issues above."
        exit 1
    fi
}

# Run main function
main "$@"