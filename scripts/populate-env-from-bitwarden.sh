#!/bin/bash
# Populate .env from Bitwarden vault
# Requires: Bitwarden CLI (bw) authenticated with BW_SESSION

set -e

echo "🔐 Populating .env from Bitwarden..."

# Check if Bitwarden CLI is available
if ! command -v bw &> /dev/null; then
    echo "❌ Bitwarden CLI (bw) not found. Install with: wget -qO- https://downloads.bitwarden.com/cli/Bitwarden_Installer.sh | bash"
    exit 1
fi

# Unlock Bitwarden if not already unlocked
if [ -z "$BW_SESSION" ]; then
    echo "🔓 Unlocking Bitwarden vault..."
    BW_PASSWORD=${BW_PASSWORD:-$(read -s -p "Enter Bitwarden master password: " password; echo $password)}
    export BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD)
    echo
fi

# Backup existing .env if it exists
[ -f .env ] && cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Clear .env and repopulate only with retrieved secrets
> .env

# Function to get secret safely
get_secret() {
    local name=$1
    local value=$(bw get password "$name" 2>/dev/null || echo "")
    if [ -z "$value" ]; then
        echo "WARNING: Secret '$name' not found in Bitwarden. Using placeholder."
        echo "$name=BITWARDEN_SECRET_MISSING_$name"
    else
        echo "$name=$value"
    fi
}

# Critical Supabase secrets
echo "# Supabase Secrets (auto-populated from Bitwarden)" >> .env
echo $(get_secret "localai_supabase_postgres_password") >> .env
echo $(get_secret "localai_supabase_jwt_secret") >> .env
echo $(get_secret "localai_supabase_anon_key") >> .env
echo $(get_secret "localai_supabase_service_role_key") >> .env
echo $(get_secret "localai_supabase_dashboard_username") >> .env
echo $(get_secret "localai_supabase_dashboard_password") >> .env
echo "POOLER_TENANT_ID=$(get_secret "localai_supabase_pooler_tenant_id")" >> .env

# n8n secrets
echo "" >> .env
echo "# n8n Secrets" >> .env
echo $(get_secret "localai_n8n_encryption_key") >> .env
echo $(get_secret "localai_n8n_jwt_secret") >> .env

# Database/Storage
echo "" >> .env
echo "# Database/Storage Secrets" >> .env
echo "NEO4J_AUTH=neo4j/$(get_secret "localai_neo4j_password")" >> .env
echo $(get_secret "localai_clickhouse_password") >> .env
echo $(get_secret "localai_minio_root_password") >> .env
echo $(get_secret "localai_graylog_password") >> .env
echo "RABBITMQ_USER=$(get_secret "localai_rabbitmq_user")" >> .env
echo "RABBITMQ_PASS=$(get_secret "localai_rabbitmq_password")" >> .env
echo $(get_secret "localai_flowise_username") >> .env
echo $(get_secret "localai_flowise_password") >> .env
echo $(get_secret "localai_localai_api_key") >> .env

# AI Services (placeholders if not set)
echo "" >> .env
echo "# AI Services (populate from Bitwarden as needed)" >> .env
echo "OPENAI_API_KEY=$(get_secret "localai_openai_api_key")" >> .env
echo "SERPAPI_API_KEY=$(get_secret "localai_serpapi_api_key")" >> .env
echo "GRAPHRAG_API_KEY=$(get_secret "localai_graphrag_api_key")" >> .env
echo "CRAWL4AI_API_KEY=$(get_secret "localai_crawl4ai_api_key")" >> .env

# Auth/Monitoring
echo "" >> .env
echo "# Auth/Monitoring" >> .env
echo $(get_secret "localai_nextauth_secret") >> .env
echo $(get_secret "localai_langfuse_salt") >> .env
echo $(get_secret "localai_logflare_public_token") >> .env
echo $(get_secret "localai_logflare_private_token") >> .env

# Add standard config (non-sensitive) - complete from .env.example
echo "" >> .env
echo "# Standard Configuration (from .env.example)" >> .env
cat << 'EOF' >> .env
# Database
POSTGRES_HOST=db
POSTGRES_DB=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres

# Supavisor
POOLER_PROXY_PORT_TRANSACTION=6543
POOLER_DEFAULT_POOL_SIZE=20
POOLER_MAX_CLIENT_CONN=100
POOLER_DB_POOL_SIZE=5

# Frontend
FRONTEND_TITLE=Local AI Package
FRONTEND_DESCRIPTION=Self-hosted AI Development Environment

# Auth
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

# Studio
STUDIO_DEFAULT_ORGANIZATION=Default Organization
STUDIO_DEFAULT_PROJECT=Default Project
STUDIO_PORT=3000
SUPABASE_PUBLIC_URL=http://localhost:8000
IMGPROXY_ENABLE_WEBP_DETECTION=true

# Functions
FUNCTIONS_VERIFY_JWT=false

# Logs
DOCKER_SOCKET_LOCATION=/var/run/docker.sock
GOOGLE_PROJECT_ID=GOOGLE_PROJECT_ID
GOOGLE_PROJECT_NUMBER=GOOGLE_PROJECT_NUMBER

# API
PGRST_DB_SCHEMAS=public,storage,graphql_public

# Kong
KONG_HTTP_PORT=8000
KONG_HTTPS_PORT=8443

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j

# libSQL
LIBSQL_URL=http://libsql:8080

# CrewAI
CREWAI_MODEL=gpt-4
CREWAI_TEMPERATURE=0.7
CREWAI_MAX_TOKENS=4000

# Letta
LETTA_STORAGE_PATH=/data
LETTA_MAX_MEMORY_ITEMS=10000

# GraphRAG
GRAPHRAG_STORAGE_PATH=/data
GRAPHRAG_EMBEDDING_MODEL=text-embedding-ada-002

# Falkor
FALKOR_URL=redis://falkor:6379
FALKOR_MAX_CONNECTIONS=100

# MCP Crawl4AI
CRAWL4AI_STORAGE_PATH=/data
CRAWL4AI_MAX_DEPTH=3
CRAWL4AI_MAX_PAGES=100

# Service Ports
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

echo "✅ .env populated from Bitwarden successfully!"
echo "📋 Total secrets retrieved: $(grep -v '^#' .env | grep '=' | wc -l)"
echo "🔍 Verify: source .env && echo 'Supabase JWT length:' \${#JWT_SECRET}"
echo "⚠️  Remember to set BW_PASSWORD environment variable for automated runs"