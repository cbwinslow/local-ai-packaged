#!/bin/bash

# Environment Variables Validation Script
# This script validates all required environment variables and service prerequisites

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validation functions
validate_hex_string() {
    local value="$1"
    local min_length="${2:-32}"
    if [[ ! "$value" =~ ^[0-9a-fA-F]+$ ]] || [[ ${#value} -lt $min_length ]]; then
        echo -e "${RED}❌ Invalid hex string: must be at least $min_length hex characters${NC}"
        return 1
    fi
    return 0
}

validate_base64_filtered() {
    local value="$1"
    local min_length="${2:-12}"
    if [[ ${#value} -lt $min_length ]] || [[ "$value" =~ [/+] ]]; then
        echo -e "${RED}❌ Invalid filtered base64: must be at least $min_length chars, no / or +${NC}"
        return 1
    fi
    return 0
}

validate_url() {
    local value="$1"
    if [[ ! "$value" =~ ^https?:// ]]; then
        echo -e "${RED}❌ Invalid URL: must start with http:// or https://${NC}"
        return 1
    fi
    return 0
}

validate_jwt() {
    local value="$1"
    local parts
    IFS='.' read -ra parts <<< "$value"
    if [[ ${#parts[@]} -ne 3 ]]; then
        echo -e "${RED}❌ Invalid JWT: must have 3 parts separated by dots${NC}"
        return 1
    fi
    return 0
}

validate_port() {
    local value="$1"
    if ! [[ "$value" =~ ^[0-9]+$ ]] || [[ "$value" -lt 1024 ]] || [[ "$value" -gt 65535 ]]; then
        echo -e "${RED}❌ Invalid port: must be between 1024 and 65535${NC}"
        return 1
    fi
    return 0
}

validate_boolean() {
    local value="$1"
    if [[ "$value" != "true" ]] && [[ "$value" != "false" ]]; then
        echo -e "${RED}❌ Invalid boolean: must be 'true' or 'false'${NC}"
        return 1
    fi
    return 0
}

# Check if variable is set and not empty
check_required_var() {
    local var_name="$1"
    local var_value="${!var_name:-}"
    if [[ -z "$var_value" ]]; then
        echo -e "${RED}❌ Required variable $var_name is not set${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ $var_name is set${NC}"
    return 0
}

# Check if variable is set (optional)
check_optional_var() {
    local var_name="$1"
    local var_value="${!var_name:-}"
    if [[ -z "$var_value" ]]; then
        echo -e "${YELLOW}⚠️  Optional variable $var_name is not set${NC}"
        return 0
    fi
    echo -e "${GREEN}✓ $var_name is set${NC}"
    return 0
}

# Validate specific variable types
validate_env_var() {
    local var_name="$1"
    local var_type="$2"
    local var_value="${!var_name:-}"

    if [[ -z "$var_value" ]]; then
        return 0  # Skip validation if not set
    fi

    case "$var_type" in
        "hex_32")
            validate_hex_string "$var_value" 32 || return 1
            ;;
        "hex_64")
            validate_hex_string "$var_value" 64 || return 1
            ;;
        "base64_filtered")
            validate_base64_filtered "$var_value" || return 1
            ;;
        "url")
            validate_url "$var_value" || return 1
            ;;
        "jwt")
            validate_jwt "$var_value" || return 1
            ;;
        "port")
            validate_port "$var_value" || return 1
            ;;
        "boolean")
            validate_boolean "$var_value" || return 1
            ;;
        "neo4j_auth")
            if [[ ! "$var_value" =~ / ]]; then
                echo -e "${RED}❌ Invalid Neo4j auth: must contain '/'${NC}"
                return 1
            fi
            ;;
        "json_array")
            if ! echo "$var_value" | jq . >/dev/null 2>&1; then
                echo -e "${RED}❌ Invalid JSON array${NC}"
                return 1
            fi
            ;;
    esac
    return 0
}

# Check if Docker service is running
check_service_running() {
    local service_name="$1"
    if docker compose ps "$service_name" --format json | jq -r '.[0].State' 2>/dev/null | grep -q "running"; then
        echo -e "${GREEN}✓ Service $service_name is running${NC}"
        return 0
    else
        echo -e "${RED}❌ Service $service_name is not running${NC}"
        return 1
    fi
}

# Check if Docker service is healthy
check_service_healthy() {
    local service_name="$1"
    if docker compose ps "$service_name" --format json | jq -r '.[0].Health' 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✓ Service $service_name is healthy${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Service $service_name health check pending${NC}"
        return 0
    fi
}

# Main validation function
validate_deployment_prerequisites() {
    local service_name="$1"
    local phase="$2"
    shift 2

    echo -e "${BLUE}🔍 Validating prerequisites for $service_name (Phase $phase)${NC}"

    # Check .env file exists
    if [[ ! -f .env ]]; then
        echo -e "${RED}❌ .env file not found. Run setup first.${NC}"
        exit 1
    fi

    # Load environment variables
    set -a
    source .env
    set +a

    local validation_failed=0

    # Validate required variables for this service
    case "$service_name" in
        "postgres")
            check_required_var "POSTGRES_PASSWORD" || validation_failed=1
            check_required_var "POSTGRES_USER" || validation_failed=1
            check_required_var "POSTGRES_DB" || validation_failed=1
            validate_env_var "POSTGRES_PASSWORD" "base64_filtered" || validation_failed=1
            ;;
        "redis")
            # Redis has no required env vars
            ;;
        "minio")
            check_required_var "MINIO_ROOT_PASSWORD" || validation_failed=1
            validate_env_var "MINIO_ROOT_PASSWORD" "base64_filtered" || validation_failed=1
            ;;
        "clickhouse")
            check_required_var "CLICKHOUSE_PASSWORD" || validation_failed=1
            validate_env_var "CLICKHOUSE_PASSWORD" "base64_filtered" || validation_failed=1
            ;;
        "qdrant")
            check_optional_var "QDRANT_API_KEY"
            validate_env_var "QDRANT_API_KEY" "hex_32" || validation_failed=1
            ;;
        "neo4j")
            check_required_var "NEO4J_AUTH" || validation_failed=1
            validate_env_var "NEO4J_AUTH" "neo4j_auth" || validation_failed=1
            ;;
        "ollama")
            # Ollama has no required env vars
            ;;
        "n8n")
            check_required_var "N8N_ENCRYPTION_KEY" || validation_failed=1
            check_required_var "N8N_USER_MANAGEMENT_JWT_SECRET" || validation_failed=1
            check_required_var "POSTGRES_PASSWORD" || validation_failed=1
            validate_env_var "N8N_ENCRYPTION_KEY" "hex_32" || validation_failed=1
            validate_env_var "N8N_USER_MANAGEMENT_JWT_SECRET" "hex_32" || validation_failed=1
            # Check postgres dependency
            check_service_running "postgres" || validation_failed=1
            ;;
        "flowise")
            check_optional_var "FLOWISE_USERNAME"
            check_optional_var "FLOWISE_PASSWORD"
            validate_env_var "FLOWISE_PASSWORD" "base64_filtered" || validation_failed=1
            ;;
        "open-webui")
            # Open WebUI has no required env vars
            ;;
        "langfuse-web"|"langfuse-worker")
            check_required_var "LANGFUSE_SALT" || validation_failed=1
            check_required_var "CLICKHOUSE_PASSWORD" || validation_failed=1
            check_required_var "MINIO_ROOT_PASSWORD" || validation_failed=1
            check_required_var "POSTGRES_PASSWORD" || validation_failed=1
            validate_env_var "LANGFUSE_SALT" "hex_32" || validation_failed=1
            # Check dependencies
            check_service_running "postgres" || validation_failed=1
            check_service_running "clickhouse" || validation_failed=1
            check_service_running "minio" || validation_failed=1
            check_service_running "redis" || validation_failed=1
            ;;
        "agentic-rag")
            check_required_var "NEO4J_AUTH" || validation_failed=1
            check_required_var "POSTGRES_PASSWORD" || validation_failed=1
            validate_env_var "NEO4J_AUTH" "neo4j_auth" || validation_failed=1
            # Check dependencies
            check_service_running "postgres" || validation_failed=1
            check_service_running "qdrant" || validation_failed=1
            check_service_running "neo4j" || validation_failed=1
            ;;
        "frontend")
            check_required_var "NEXTAUTH_SECRET" || validation_failed=1
            check_required_var "ANON_KEY" || validation_failed=1
            check_required_var "POSTGRES_PASSWORD" || validation_failed=1
            validate_env_var "NEXTAUTH_SECRET" "hex_32" || validation_failed=1
            validate_env_var "ANON_KEY" "jwt" || validation_failed=1
            # Check postgres dependency
            check_service_running "postgres" || validation_failed=1
            ;;
        "graylog")
            check_optional_var "GRAYLOG_PASSWORD_SECRET"
            check_optional_var "GRAYLOG_PASSWORD"
            validate_env_var "GRAYLOG_PASSWORD" "base64_filtered" || validation_failed=1
            # Check dependencies
            check_service_running "mongo" || validation_failed=1
            check_service_running "opensearch" || validation_failed=1
            ;;
        "rabbitmq")
            check_optional_var "RABBITMQ_USER"
            check_optional_var "RABBITMQ_PASS"
            validate_env_var "RABBITMQ_PASS" "base64_filtered" || validation_failed=1
            ;;
        "localai")
            check_optional_var "LOCALAI_API_KEY"
            validate_env_var "LOCALAI_API_KEY" "hex_32" || validation_failed=1
            ;;
        *)
            echo -e "${YELLOW}⚠️  No specific validation rules for $service_name${NC}"
            ;;
    esac

    # Check phase prerequisites
    case "$phase" in
        1)  # Infrastructure
            echo -e "${BLUE}📦 Phase 1: Infrastructure services${NC}"
            ;;
        2)  # Core AI
            echo -e "${BLUE}🤖 Phase 2: Core AI services${NC}"
            # Should have infrastructure running
            ;;
        3)  # Applications
            echo -e "${BLUE}🚀 Phase 3: Application services${NC}"
            # Should have infrastructure and core AI running
            ;;
        4)  # Monitoring
            echo -e "${BLUE}📊 Phase 4: Monitoring services${NC}"
            ;;
    esac

    if [[ $validation_failed -eq 1 ]]; then
        echo -e "${RED}❌ Validation failed for $service_name${NC}"
        return 1
    else
        echo -e "${GREEN}✅ All validations passed for $service_name${NC}"
        return 0
    fi
}

# Export functions for use in other scripts
export -f validate_hex_string
export -f validate_base64_filtered
export -f validate_url
export -f validate_jwt
export -f validate_port
export -f validate_boolean
export -f check_required_var
export -f check_optional_var
export -f validate_env_var
export -f check_service_running
export -f check_service_healthy
export -f validate_deployment_prerequisites</content>