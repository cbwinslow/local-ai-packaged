#!/bin/bash
# Enhanced .env validation script for Bitwarden-populated secrets
# Validates all environment variables against security and format requirements
# Includes checks for missing secrets, placeholder values, and proper formats

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Enhanced validation functions
validate_variable_exists() {
    local var_name=$1
    local value=$2
    ((TOTAL_TESTS++))

    if [[ -z "$value" ]]; then
        log_error "$var_name: Variable is empty or undefined"
        return 1
    fi

    log_success "$var_name: Variable exists and has value"
    return 0
}

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

    # Check for problematic characters that might cause issues
    if [[ "$value" =~ [\"\'\ ] ]]; then
        log_error "$var_name: Contains problematic characters (quotes or spaces)"
        return 1
    fi

    log_success "$var_name: Valid password/token (${#value} chars)"
    return 0
}

validate_jwt_format() {
    local var_name=$1
    local value=$2
    ((TOTAL_TESTS++))

    # Check if it has 3 parts separated by dots (JWT format)
    local parts_count=$(echo "$value" | grep -o '\.' | wc -l)
    if [[ $parts_count -ne 2 ]]; then
        log_warning "$var_name: Not in JWT format (3 parts separated by dots)"
    fi

    # Check minimum length
    if [[ ${#value} -lt 100 ]]; then
        log_error "$var_name: JWT token too short (${#value} chars, should be > 100)"
        return 1
    fi

    log_success "$var_name: Valid JWT format (${#value} chars)"
    return 0
}

validate_neo4j_auth() {
    local var_name=$1
    local value=$2
    ((TOTAL_TESTS++))

    if [[ ! "$value" =~ ^[a-zA-Z0-9_]+/[a-zA-Z0-9_@#\$%\^!\-]+$ ]]; then
        log_error "$var_name: Must be in format 'username/password'"
        return 1
    fi

    local password_part="${value#*/}"
    if [[ ${#password_part} -lt 8 ]]; then
        log_error "$var_name: Password part too short (${#password_part} chars, need at least 8)"
        return 1
    fi

    log_success "$var_name: Valid Neo4j auth format"
    return 0
}

# Check for Bitwarden-related issues
check_bitwarden_secrets() {
    log_header "BITWARDEN SECRET VALIDATION"

    # Check for missing secret indicators
    local missing_secrets=$(grep -E "(BITWARDEN_SECRET_MISSING|PLACEHOLDER|your_|super-secret)" .env 2>/dev/null | wc -l)
    if [[ $missing_secrets -gt 0 ]]; then
        log_error "Found $missing_secrets missing or placeholder secrets:"
        grep -E "(BITWARDEN_SECRET_MISSING|PLACEHOLDER|your_|super-secret)" .env 2>/dev/null | while read line; do
            log_error "  $line"
        done
        return 1
    else
        log_success "No missing or placeholder secrets found"
    fi

    # Validate critical secrets exist and have proper format
    local critical_secrets=(
        "POSTGRES_PASSWORD:password:20"
        "JWT_SECRET:hex:64"
        "ANON_KEY:jwt:100"
        "SERVICE_ROLE_KEY:jwt:100"
        "N8N_ENCRYPTION_KEY:hex:32"
        "N8N_USER_MANAGEMENT_JWT_SECRET:hex:32"
        "LANGFUSE_SALT:hex:32"
        "NEXTAUTH_SECRET:hex:32"
        "ENCRYPTION_KEY:hex:32"
        "SECRET_KEY_BASE:hex:64"
        "VAULT_ENC_KEY:hex:32"
        "NEO4J_AUTH:neo4j:1"
    )

    local validation_failed=false
    for item in "${critical_secrets[@]}"; do
        local var_name="${item%%:*}"
        local var_type="${item#*:}"
        local var_type="${var_type%:*}"
        local min_length="${item##*:}"
        
        # Get value from .env
        local value=$(grep "^${var_name}=" .env 2>/dev/null | cut -d'=' -f2- || echo "")
        
        if [[ -z "$value" ]]; then
            log_error "$var_name: Critical secret is missing"
            validation_failed=true
            continue
        fi
        
        # Validate based on type
        case $var_type in
            "hex")
                if ! validate_hex_string "$var_name" "$value" "$min_length"; then
                    validation_failed=true
                fi
                ;;
            "password")
                if ! validate_base64_filtered "$var_name" "$value" "$min_length"; then
                    validation_failed=true
                fi
                ;;
            "jwt")
                if ! validate_jwt_format "$var_name" "$value"; then
                    validation_failed=true
                fi
                ;;
            "neo4j")
                if ! validate_neo4j_auth "$var_name" "$value"; then
                    validation_failed=true
                fi
                ;;
        esac
    done

    if [[ "$validation_failed" = true ]]; then
        log_error "Critical secret validation failed"
        return 1
    fi

    log_success "All critical secrets validated successfully"
    return 0
}

# Validate service-specific requirements
validate_service_requirements() {
    log_header "SERVICE REQUIREMENT VALIDATION"

    # Source .env file for validation
    set -a
    source .env 2>/dev/null || {
        log_error "Cannot source .env file"
        return 1
    }
    set +a

    # Supabase requirements
    if [[ -n "$POSTGRES_PASSWORD" ]]; then
        validate_variable_exists "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD"
        validate_base64_filtered "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD" 20
    fi

    if [[ -n "$JWT_SECRET" ]]; then
        validate_variable_exists "JWT_SECRET" "$JWT_SECRET"
        validate_hex_string "JWT_SECRET" "$JWT_SECRET" 64
    fi

    # n8n requirements
    if [[ -n "$N8N_ENCRYPTION_KEY" ]]; then
        validate_variable_exists "N8N_ENCRYPTION_KEY" "$N8N_ENCRYPTION_KEY"
        validate_hex_string "N8N_ENCRYPTION_KEY" "$N8N_ENCRYPTION_KEY" 32
    fi

    if [[ -n "$N8N_USER_MANAGEMENT_JWT_SECRET" ]]; then
        validate_variable_exists "N8N_USER_MANAGEMENT_JWT_SECRET" "$N8N_USER_MANAGEMENT_JWT_SECRET"
        validate_hex_string "N8N_USER_MANAGEMENT_JWT_SECRET" "$N8N_USER_MANAGEMENT_JWT_SECRET" 32
    fi

    # Neo4j requirements
    if [[ -n "$NEO4J_AUTH" ]]; then
        validate_variable_exists "NEO4J_AUTH" "$NEO4J_AUTH"
        validate_neo4j_auth "NEO4J_AUTH" "$NEO4J_AUTH"
    fi

    # Other critical services
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
}

# Check for security issues
validate_security_requirements() {
    log_header "SECURITY VALIDATION"

    # Check file permissions
    local perm=$(stat -c "%a" .env 2>/dev/null || echo "000")
    if [[ "$perm" != "600" ]]; then
        log_error ".env file permissions are $perm, should be 600"
        log_info "Fix with: chmod 600 .env"
    else
        log_success ".env file has correct permissions (600)"
    fi

    # Check for common weak passwords
    local weak_patterns=(
        "password"
        "123456"
        "admin"
        "secret"
        "changeme"
    )

    local weak_found=false
    for pattern in "${weak_patterns[@]}"; do
        if grep -qi "$pattern" .env; then
            log_warning "Potentially weak secret detected containing: $pattern"
            weak_found=true
        fi
    done

    if [[ "$weak_found" = false ]]; then
        log_success "No common weak password patterns detected"
    fi
}

# Main validation function
main() {
    log_header "ENHANCED .env VALIDATION"
    
    # Check if .env file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error ".env file not found!"
        log_info "Run: ./scripts/enhanced-populate-env-from-bitwarden.sh"
        exit 1
    fi

    log_success ".env file found"

    # Run validation checks
    check_bitwarden_secrets
    validate_service_requirements  
    validate_security_requirements

    # Final summary
    log_header "VALIDATION SUMMARY"
    
    local total_vars=$(grep -c "^[A-Z_]*=" .env)
    log_info "Total environment variables: $total_vars"
    log_info "Tests passed: $PASSED_TESTS"
    log_info "Tests failed: $FAILED_TESTS"
    log_info "Total tests: $TOTAL_TESTS"

    if [[ $FAILED_TESTS -eq 0 ]]; then
        log_success "🎉 ALL VALIDATIONS PASSED!"
        log_success "Your .env file is ready for deployment"
        return 0
    else
        log_error "❌ VALIDATION FAILED!"
        log_error "Please fix the issues above before proceeding"
        return 1
    fi
}

# Execute main function
main "$@"