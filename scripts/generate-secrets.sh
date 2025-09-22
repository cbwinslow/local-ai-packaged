#!/bin/bash

# generate-secrets.sh - Generate secure secrets for all environment variables
# This script provides individual functions to create secret values for each variable
# following the restrictions and guidelines from README.md and ENV_VARIABLES_RULES.md

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to generate hex string of specified length
generate_hex() {
    local length=$1
    openssl rand -hex $((length / 2))
}

# Function to generate filtered base64 string (no /+=)
generate_base64_filtered() {
    local length=$1
    openssl rand -base64 $length | tr -d '/+=' | cut -c1-$length
}

# Function to generate JWT token
generate_jwt() {
    local role=$1
    local jwt_secret=$2
    local timestamp=$(date +%s)
    local header='{"alg":"HS256","typ":"JWT"}'
    local payload="{\"iss\":\"supabase\",\"ref\":\"localai\",\"role\":\"$role\",\"iat\":$timestamp,\"sub\":\"localai\"}"

    # Base64url encode header and payload
    local header_b64=$(echo -n "$header" | base64 | tr -d '=' | sed 's/+/-/g' | sed 's/\//_/g')
    local payload_b64=$(echo -n "$payload" | base64 | tr -d '=' | sed 's/+/-/g' | sed 's/\//_/g')

    # Create signature
    local message="$header_b64.$payload_b64"
    local signature=$(echo -n "$message" | openssl dgst -sha256 -hmac "$jwt_secret" -binary | base64 | tr -d '=' | sed 's/+/-/g' | sed 's/\//_/g')

    printf "%s.%s" "$message" "$signature"
}

# Individual secret generation functions

generate_n8n_encryption_key() {
    generate_hex 32
}

generate_n8n_user_management_jwt_secret() {
    generate_hex 32
}

generate_postgres_password() {
    generate_base64_filtered 32
}

generate_jwt_secret() {
    generate_hex 32
}

generate_anon_key() {
    local jwt_secret=$1
    generate_jwt "anon" "$jwt_secret"
}

generate_service_role_key() {
    local jwt_secret=$1
    generate_jwt "service_role" "$jwt_secret"
}

generate_dashboard_username() {
    generate_hex 8
}

generate_dashboard_password() {
    generate_base64_filtered 24
}

generate_pooler_tenant_id() {
    shuf -i 1000-9999 -n 1
}

generate_neo4j_password() {
    generate_base64_filtered 24
}

generate_clickhouse_password() {
    generate_base64_filtered 24
}

generate_minio_root_password() {
    generate_base64_filtered 24
}

generate_langfuse_salt() {
    generate_hex 32
}

generate_nextauth_secret() {
    generate_hex 32
}

generate_encryption_key() {
    generate_hex 32
}

generate_secret_key_base() {
    generate_hex 64
}

generate_vault_enc_key() {
    generate_hex 32
}

generate_logflare_public_access_token() {
    generate_hex 32
}

generate_logflare_private_access_token() {
    generate_hex 32
}

generate_flowise_username() {
    generate_hex 8
}

generate_flowise_password() {
    generate_base64_filtered 24
}

generate_grafana_admin_password() {
    generate_base64_filtered 24
}

generate_prometheus_password() {
    generate_base64_filtered 24
}

generate_rabbitmq_user() {
    generate_hex 8
}

generate_rabbitmq_password() {
    generate_base64_filtered 24
}

generate_graylog_password() {
    generate_base64_filtered 24
}

generate_qdrant_api_key() {
    generate_hex 32
}

generate_searxng_secret_key() {
    generate_hex 32
}

generate_localai_api_key() {
    generate_hex 32
}

generate_graylog_password_secret() {
    generate_hex 32
}

# Main function to generate all secrets
generate_all_secrets() {
    # Check if output is being redirected (not a terminal)
    if [[ -t 1 ]]; then
        echo -e "${YELLOW}Generating all secrets...${NC}"
    fi

    # Generate JWT_SECRET first as it's needed for JWT tokens
    JWT_SECRET=$(generate_jwt_secret)

    echo "N8N_ENCRYPTION_KEY=$(generate_n8n_encryption_key)"
    echo "N8N_USER_MANAGEMENT_JWT_SECRET=$(generate_n8n_user_management_jwt_secret)"
    echo "POSTGRES_PASSWORD=$(generate_postgres_password)"
    echo "JWT_SECRET=$JWT_SECRET"
    echo "ANON_KEY=\"$(generate_anon_key "$JWT_SECRET")\""
    echo "SERVICE_ROLE_KEY=\"$(generate_service_role_key "$JWT_SECRET")\""
    echo "DASHBOARD_USERNAME=$(generate_dashboard_username)"
    echo "DASHBOARD_PASSWORD=$(generate_dashboard_password)"
    echo "POOLER_TENANT_ID=$(generate_pooler_tenant_id)"
    echo "NEO4J_AUTH=neo4j/$(generate_neo4j_password)"
    echo "CLICKHOUSE_PASSWORD=$(generate_clickhouse_password)"
    echo "MINIO_ROOT_PASSWORD=$(generate_minio_root_password)"
    echo "LANGFUSE_SALT=$(generate_langfuse_salt)"
    echo "NEXTAUTH_SECRET=$(generate_nextauth_secret)"
    echo "ENCRYPTION_KEY=$(generate_encryption_key)"
    echo "SECRET_KEY_BASE=$(generate_secret_key_base)"
    echo "VAULT_ENC_KEY=$(generate_vault_enc_key)"
    echo "LOGFLARE_PUBLIC_ACCESS_TOKEN=$(generate_logflare_public_access_token)"
    echo "LOGFLARE_PRIVATE_ACCESS_TOKEN=$(generate_logflare_private_access_token)"
    echo "FLOWISE_USERNAME=$(generate_flowise_username)"
    echo "FLOWISE_PASSWORD=$(generate_flowise_password)"
    echo "GRAFANA_ADMIN_PASSWORD=$(generate_grafana_admin_password)"
    echo "PROMETHEUS_PASSWORD=$(generate_prometheus_password)"
    echo "RABBITMQ_USER=$(generate_rabbitmq_user)"
    echo "RABBITMQ_PASSWORD=$(generate_rabbitmq_password)"
    echo "GRAYLOG_PASSWORD=$(generate_graylog_password)"
    echo "QDRANT_API_KEY=$(generate_qdrant_api_key)"
    echo "SEARXNG_SECRET_KEY=$(generate_searxng_secret_key)"
    echo "LOCALAI_API_KEY=$(generate_localai_api_key)"
    echo "GRAYLOG_PASSWORD_SECRET=$(generate_graylog_password_secret)"

    if [[ -t 1 ]]; then
        echo -e "${GREEN}✅ All secrets generated${NC}"
    fi
}

# If script is run directly, generate all secrets
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    generate_all_secrets
fi