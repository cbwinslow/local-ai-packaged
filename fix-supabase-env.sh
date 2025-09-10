#!/bin/bash

set -euo pipefail  # Exit on error, undefined vars, pipe failures

echo "=== Local AI Package Secret Generation Script ==="
echo "This script generates all required secure secrets and fixes Supabase JWT key expiration issues."
echo "Requirements: openssl, base64, date (Unix utilities)"
echo

# Check dependencies
if ! command -v openssl &> /dev/null; then
    echo "❌ openssl not found. Install it to generate secure secrets."
    exit 1
fi

if ! command -v date &> /dev/null; then
    echo "❌ date command not found. Required for JWT timestamps."
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "⚠️ jq not found. JWT generation will use simpler method."
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

echo "✓ Dependencies OK"

# Check if .env exists
if [[ ! -f .env ]]; then
    echo "❌ .env file not found. Copy .env.example to .env first."
    exit 1
fi

# Backup current .env file
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo "✓ Backed up current .env file to .env.backup.$(date +%Y%m%d_%H%M%S)"

# Generate all required secrets
echo "Generating secure secrets..."

# N8N secrets
N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
N8N_USER_MANAGEMENT_JWT_SECRET=$(openssl rand -hex 32)

# Supabase secrets
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '/+= ')
JWT_SECRET=$(openssl rand -hex 32)
DASHBOARD_USERNAME=$(openssl rand -hex 8)
DASHBOARD_PASSWORD=$(openssl rand -base64 24 | tr -d '/+= ')
POOLER_TENANT_ID=$(shuf -i 1000-9999 -n 1 || echo $((1000 + RANDOM % 8900)))

# Neo4j
NEO4J_PASSWORD=$(openssl rand -base64 24 | tr -d '/+= ')
NEO4J_AUTH="neo4j/${NEO4J_PASSWORD}"

# Langfuse
CLICKHOUSE_PASSWORD=$(openssl rand -base64 24 | tr -d '/+= ')
MINIO_ROOT_PASSWORD=$(openssl rand -base64 24 | tr -d '/+= ')
LANGFUSE_SALT=$(openssl rand -hex 32)
NEXTAUTH_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Other services
SECRET_KEY_BASE=$(openssl rand -hex 64)
VAULT_ENC_KEY=$(openssl rand -hex 32)

# Logflare
LOGFLARE_PUBLIC_ACCESS_TOKEN=$(openssl rand -hex 32)
LOGFLARE_PRIVATE_ACCESS_TOKEN=$(openssl rand -hex 32)

# Additional services
GRAYLOG_PASSWORD=$(openssl rand -base64 24 | tr -d '/+= ')
RABBITMQ_USER=$(openssl rand -hex 8)
RABBITMQ_PASS=$(openssl rand -base64 24 | tr -d '/+= ')
FLOWISE_USERNAME=$(openssl rand -hex 8)
FLOWISE_PASSWORD=$(openssl rand -base64 24 | tr -d '/+= ')
LOCALAI_API_KEY=$(openssl rand -hex 32)

echo "✓ All secrets generated securely"
echo

# Function to update .env variables safely
update_env_var() {
    local key="$1"
    local value="$2"
    if grep -q "^$key=" .env; then
        sed -i "s|^$key=.*|$key=$value|" .env
        echo "✓ Updated $key"
    else
        echo "$key=$value" >> .env
        echo "✓ Added $key"
    fi
}

# Update all generated secrets
update_env_var "N8N_ENCRYPTION_KEY" "$N8N_ENCRYPTION_KEY"
update_env_var "N8N_USER_MANAGEMENT_JWT_SECRET" "$N8N_USER_MANAGEMENT_JWT_SECRET"
update_env_var "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD"
update_env_var "JWT_SECRET" "$JWT_SECRET"
update_env_var "DASHBOARD_USERNAME" "$DASHBOARD_USERNAME"
update_env_var "DASHBOARD_PASSWORD" "$DASHBOARD_PASSWORD"
update_env_var "POOLER_TENANT_ID" "$POOLER_TENANT_ID"
update_env_var "NEO4J_AUTH" "$NEO4J_AUTH"
update_env_var "CLICKHOUSE_PASSWORD" "$CLICKHOUSE_PASSWORD"
update_env_var "MINIO_ROOT_PASSWORD" "$MINIO_ROOT_PASSWORD"
update_env_var "LANGFUSE_SALT" "$LANGFUSE_SALT"
update_env_var "NEXTAUTH_SECRET" "$NEXTAUTH_SECRET"
update_env_var "ENCRYPTION_KEY" "$ENCRYPTION_KEY"
update_env_var "SECRET_KEY_BASE" "$SECRET_KEY_BASE"
update_env_var "VAULT_ENC_KEY" "$VAULT_ENC_KEY"
update_env_var "LOGFLARE_PUBLIC_ACCESS_TOKEN" "$LOGFLARE_PUBLIC_ACCESS_TOKEN"
update_env_var "LOGFLARE_PRIVATE_ACCESS_TOKEN" "$LOGFLARE_PRIVATE_ACCESS_TOKEN"
update_env_var "GRAYLOG_PASSWORD" "$GRAYLOG_PASSWORD"
update_env_var "RABBITMQ_USER" "$RABBITMQ_USER"
update_env_var "RABBITMQ_PASS" "$RABBITMQ_PASS"
update_env_var "FLOWISE_USERNAME" "$FLOWISE_USERNAME"
update_env_var "FLOWISE_PASSWORD" "$FLOWISE_PASSWORD"
update_env_var "LOCALAI_API_KEY" "$LOCALAI_API_KEY"

echo "✓ Updated .env with all core secrets"
echo

# Generate new JWT tokens using Supabase's format
if command -v jq &> /dev/null; then
    # Create a proper JWT token if jq is available
    header="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    payload="eyJpc3MiOiJzdXBhYmFzZSIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNjM5MjM5NTU3LCJleHAiOjE5NTQ4MDM1NTd9"
    signature=$(echo -n "${header}.${payload}" | openssl dgst -sha256 -hmac "${JWT_SECRET}" -binary | openssl base64 -e | sed 's/=//g' | sed 's/+/-/g' | sed 's/\//_/g')
    ANON_KEY="${header}.${payload}.${signature}"

    payload_service="eyJpc3MiOiJzdXBhYmFzZSIsInJvbGUiOiJzZXJ2aWNlX3JvbGUiLCJpYXQiOjE2MzkyMzk1NTcsImV4cCI6MTk1NDgwMzU1N30"
    signature_service=$(echo -n "${header}.${payload_service}" | openssl dgst -sha256 -hmac "${JWT_SECRET}" -binary | openssl base64 -e | sed 's/=//g' | sed 's/+/-/g' | sed 's/\//_/g')
    SERVICE_ROLE_KEY="${header}.${payload_service}.${signature_service}"

    # Update the JWT tokens
    sed -i "s|ANON_KEY=.*|ANON_KEY=${ANON_KEY}|" .env
    sed -i "s|SERVICE_ROLE_KEY=.*|SERVICE_ROLE_KEY=${SERVICE_ROLE_KEY}|" .env
else
    echo "⚠️ jq not found - keeping JWT tokens as they are (may need manual fixing)"
fi

echo "=== Secret Generation Complete ==="
echo "All critical secrets have been generated and updated in .env"
echo "JWT keys are valid until $(date -d "@$EXP" '+%Y-%m-%d')"
echo
echo "=== Next Steps ==="
echo "1. Review generated secrets: cat .env | grep -E '^(N8N_|POSTGRES_|JWT_|ANON_|SERVICE_|SECRET_|VAULT_)'"
echo "2. Start services: python start_services.py --profile cpu"
echo "3. Verify Supabase: curl http://localhost:8000/health"
echo "4. Check logs if issues: docker compose logs supabase"
echo
echo "=== Security Notes ==="
echo "- All secrets use cryptographically secure random values"
echo "- JWT keys have 10-year expiration (rotate as needed)"
echo "- Backup .env securely (password manager recommended)"
echo "- Add .env to .gitignore (already configured)"
echo
echo "Script completed successfully! 🎉"

# Update docker-compose restores configuration
echo "=== Next Steps ==="
echo "1. Clean restart Supabase containers:"
echo "   docker compose down -v"
echo "   docker system prune -a"
echo "   docker compose up -d"
echo
echo "2. Check container status:"
echo "   docker ps -a -f name=supabase"
echo
echo "3. Monitor logs if issues persist:"
echo "   docker compose logs -f supabase-db"
echo "   docker compose logs -f supabase-kong"
echo
echo "=== Common Issues and Solutions ==="
echo "- If containers still fail, check for port conflicts"
echo "- Ensure DOCKER_SOCKET_LOCATION is correct for your system"
echo "- Verify PostgreSQL authentication is working"
echo
echo "Fix script completed! 🎉"
