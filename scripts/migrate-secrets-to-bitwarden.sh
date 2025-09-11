#!/bin/bash
# One-time migration: Store current .env secrets in Bitwarden
# After running, clear sensitive values from .env
# Requires: Bitwarden CLI (bw) and existing .env with secrets

set -e

echo "🔄 Migrating secrets from .env to Bitwarden..."

# Check prerequisites
if ! command -v bw &> /dev/null; then
    echo "❌ Bitwarden CLI (bw) not found. Install first: wget -qO- https://downloads.bitwarden.com/cli/Bitwarden_Installer.sh | bash"
    exit 1
fi

if [ ! -f .env ]; then
    echo "❌ .env file not found. Run fix-supabase-env.sh first to generate secrets."
    exit 1
fi

# Source current .env properly (ignores comments and warnings)
export $(grep -v '^#' .env | grep -v '^WARNING:' | cut -d= -f1)

# Authenticate Bitwarden
echo "🔐 Authenticating with Bitwarden..."
bw login
export BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD)

# Function to create secret in Bitwarden
create_secret() {
    local name=$1
    local value=$2
    local notes=$3
    
    if [ -z "$value" ] || [ "$value" = "your_"* ] || [ "$value" = "super-secret-key" ]; then
        echo "⏭️  Skipping placeholder: $name"
        return
    fi
    
    # Check if secret already exists
    if bw get password "$name" >/dev/null 2>&1; then
        echo "ℹ️  Secret already exists: $name"
        return
    fi
    
    echo -n "$value" | bw encode | bw create login "$name" --notes "$notes"
    echo "✅ Created: $name"
}

# Create organization if not exists (manual step recommended)
echo "📁 Ensure 'Local AI Package' organization exists in Bitwarden web interface"
echo "Press Enter to continue with secret creation..."
read

# Migrate Supabase secrets
echo "📦 Migrating Supabase secrets..."
create_secret "localai_supabase_postgres_password" "$POSTGRES_PASSWORD" "PostgreSQL master password for Supabase"
create_secret "localai_supabase_jwt_secret" "$JWT_SECRET" "JWT signing secret for Supabase auth (256-bit)"
create_secret "localai_supabase_anon_key" "$ANON_KEY" "Public anonymous key for client-side Supabase access"
create_secret "localai_supabase_service_role_key" "$SERVICE_ROLE_KEY" "Service role key for server-side Supabase operations"
create_secret "localai_supabase_dashboard_username" "$DASHBOARD_USERNAME" "Supabase Studio dashboard username"
create_secret "localai_supabase_dashboard_password" "$DASHBOARD_PASSWORD" "Supabase Studio dashboard password"
create_secret "localai_supabase_pooler_tenant_id" "$POOLER_TENANT_ID" "Supavisor connection pooler tenant ID"

# n8n secrets
echo "📦 Migrating n8n secrets..."
create_secret "localai_n8n_encryption_key" "$N8N_ENCRYPTION_KEY" "n8n data encryption key"
create_secret "localai_n8n_jwt_secret" "$N8N_USER_MANAGEMENT_JWT_SECRET" "n8n user management JWT secret"

# Database/Storage
echo "📦 Migrating database/storage secrets..."
create_secret "localai_neo4j_password" "$(echo "$NEO4J_AUTH" | cut -d'/' -f2)" "Neo4j database password"
create_secret "localai_clickhouse_password" "$CLICKHOUSE_PASSWORD" "ClickHouse analytics database password"
create_secret "localai_minio_root_password" "$MINIO_ROOT_PASSWORD" "MinIO S3-compatible storage root password"
create_secret "localai_graylog_password" "$GRAYLOG_PASSWORD" "Graylog logging system password"
create_secret "localai_rabbitmq_user" "$RABBITMQ_USER" "RabbitMQ message queue username"
create_secret "localai_rabbitmq_password" "$RABBITMQ_PASS" "RabbitMQ message queue password"
create_secret "localai_flowise_username" "$FLOWISE_USERNAME" "Flowise AI workflow username"
create_secret "localai_flowise_password" "$FLOWISE_PASSWORD" "Flowise AI workflow password"
create_secret "localai_localai_api_key" "$LOCALAI_API_KEY" "LocalAI inference API key"

# Auth/Monitoring
echo "📦 Migrating auth/monitoring secrets..."
create_secret "localai_nextauth_secret" "$NEXTAUTH_SECRET" "NextAuth.js session secret"
create_secret "localai_langfuse_salt" "$LANGFUSE_SALT" "Langfuse tracing salt"
create_secret "localai_logflare_public_token" "$LOGFLARE_PUBLIC_ACCESS_TOKEN" "Logflare analytics public access token"
create_secret "localai_logflare_private_token" "$LOGFLARE_PRIVATE_ACCESS_TOKEN" "Logflare analytics private access token"

# AI Services (if populated)
if [[ "$OPENAI_API_KEY" != "your_"* ]]; then
    echo "📦 Migrating AI service secrets..."
    create_secret "localai_openai_api_key" "$OPENAI_API_KEY" "OpenAI GPT API key"
fi
if [[ "$SERPAPI_API_KEY" != "your_"* ]]; then
    create_secret "localai_serpapi_api_key" "$SERPAPI_API_KEY" "SerpAPI web search key"
fi
if [[ "$GRAPHRAG_API_KEY" != "your_"* ]]; then
    create_secret "localai_graphrag_api_key" "$GRAPHRAG_API_KEY" "GraphRAG indexing API key"
fi
if [[ "$CRAWL4AI_API_KEY" != "your_"* ]]; then
    create_secret "localai_crawl4ai_api_key" "$CRAWL4AI_API_KEY" "Crawl4AI web scraping API key"
fi

# Encryption keys
create_secret "localai_encryption_key" "$ENCRYPTION_KEY" "General application encryption key"
create_secret "localai_secret_key_base" "$SECRET_KEY_BASE" "Supavisor secret key base"
create_secret "localai_vault_enc_key" "$VAULT_ENC_KEY" "Supavisor vault encryption key"
create_secret "localai_searxng_secret_key" "$SEARXNG_SECRET_KEY" "SearXNG search engine secret key"

echo ""
echo "🎉 Migration complete!"
echo "📊 Total secrets created: $(bw list items | jq 'length')"
echo ""
echo "🚨 NEXT STEPS:"
echo "1. Verify secrets in Bitwarden web interface"
echo "2. Clear sensitive values from .env: sed -i '/^(POSTGRES_PASSWORD|JWT_SECRET|ANON_KEY|N8N_)/d' .env"
echo "3. Test population: ./scripts/populate-env-from-bitwarden.sh"
echo "4. Test deployment: source .env && python tools/start_services.py --profile cpu"
echo "5. Secure .env: chmod 600 .env"
echo ""
echo "🔒 Security: Remove this script after migration or restrict permissions"
echo "💡 For teams: Assign collection access in Bitwarden organization settings"