# Secure Secrets Management

## Overview

The Local AI Package uses Bitwarden as the primary secrets manager for API keys, database credentials, and service tokens. This ensures repeatability—secrets are stored once and retrieved consistently across environments. Cloudflare Secrets is used for production deployments. Local .env files are populated from Bitwarden for development.

**Key Principles**:
- No secret regeneration during normal operations.
- All secrets stored in Bitwarden vault with secure naming conventions (e.g., "Local AI Package/Supabase").
- Scripts pull secrets dynamically using Bitwarden CLI.
- `.env.example` serves as template; actual `.env` is `.gitignore`'d and populated on-demand.
- Rotate only when compromised or per policy (annual).

For detailed var rules, see [Environment Variables Rules](ENV_VARIABLES_RULES.md). For deployment integration, see [Deployment](deployment.md). For services using these vars, see [Services](services.md).

## Critical Secrets Inventory

Secrets are organized by category. Store in Bitwarden using naming: `localai_[category]_[var_name]` (e.g., `localai_supabase_jwt_secret`). Full list from `.env.example`.

### Secrets Table

| Category | Variable | Type | Length/Format | Security Level | Generation Example | Notes |
|----------|----------|------|---------------|----------------|-------------------|-------|
| **Application** | NODE_ENV | String | development/production/test | Low | Manual | Defaults to development. |
| | PORT | Integer | 1024-65535 | Low | Manual | Defaults to 3000. |
| **Supabase** | NEXT_PUBLIC_SUPABASE_URL | URL | http(s)://host:port | Low | Manual | e.g., http://localhost:5432. Validate: starts with http(s)://. |
| | NEXT_PUBLIC_SUPABASE_ANON_KEY | JWT Token | Valid JWT | High | Supabase CLI | Client access; validate JWT format (3 parts separated by .). |
| | SUPABASE_SERVICE_ROLE_KEY | JWT Token | Valid JWT | Critical | Supabase CLI | Admin key; validate JWT. |
| **Authentication** | JWT_SECRET | Hex | 64 chars (32 bytes) | Critical | `openssl rand -hex 32` | JWT signing; validate hex length. |
| | NEXTAUTH_SECRET | Hex | 64 chars | High | `openssl rand -hex 32` | Session encryption; validate hex. |
| | NEXTAUTH_URL | URL | http(s)://host:port | Low | Manual | e.g., http://localhost:3000. |
| **Database** | DATABASE_URL | Postgres URI | postgresql://user:pass@host:port/db | High | Constructed | Validate format; no special chars in pass. |
| | POSTGRES_PASSWORD | String (base64 filtered) | 24+ chars, no /+ | High | `openssl rand -base64 32 | tr -d '/+='` | Master password; validate no special chars. |
| | POSTGRES_VERSION | String | e.g., 16-alpine | Low | Manual | Defaults to 16-alpine. |
| | POSTGRES_HOST | String | Hostname | Low | Manual | Defaults to db. |
| | POSTGRES_DB | String | Database name | Low | Manual | Defaults to postgres. |
| | POSTGRES_USER | String | Username | Low | Manual | Defaults to postgres. |
| | POSTGRES_PORT | Integer | 1024-65535 | Low | Manual | Defaults to 5432. |
| **AI/ML** | OPENAI_API_KEY | String | Starts with 'sk-' | High | OpenAI dashboard | Optional; validate prefix. |
| | ANTHROPIC_API_KEY | String | Starts with 'sk-ant-' | High | Anthropic dashboard | Optional. |
| **Vector DBs** | QDRANT_URL | URL | http(s)://host:port | Low | Manual | Defaults to http://localhost:6333. |
| | QDRANT_API_KEY | String | 32+ chars | Medium | `openssl rand -hex 32` | Optional. |
| **Monitoring** | GRAFANA_ADMIN_PASSWORD | String | 12+ chars | Medium | `openssl rand -base64 24 | tr -d '/+='` | Defaults admin; change for prod. |
| | PROMETHEUS_PASSWORD | String | 12+ chars | Medium | `openssl rand -base64 24 | tr -d '/+='` | Optional. |
| **External** | LINEAR_API_KEY | String | Starts with 'lin_api_' | High | Linear dashboard | Optional. |
| | GITHUB_TOKEN | String | Starts with 'ghp_' or 'github_pat_' | High | GitHub settings | Optional. |
| **Security** | ENCRYPTION_KEY | Hex | 64 chars | Critical | `openssl rand -hex 32` | General encryption. |
| | CORS_ORIGIN | URL/Wildcard | http(s)://host or * | Low | Manual | Defaults http://localhost:3000. |
| **Feature Flags** | ENABLE_EXPERIMENTAL_FEATURES | Boolean | true/false | Low | Manual | Defaults false. |
| | ENABLE_ANALYTICS | Boolean | true/false | Low | Manual | Defaults false. |
| **n8n** | N8N_ENCRYPTION_KEY | Hex | 64 chars | High | `openssl rand -hex 32` | Workflow encryption. |
| | N8N_USER_MANAGEMENT_JWT_SECRET | Hex | 64 chars | High | `openssl rand -hex 32` | User auth. |
| | N8N_HOSTNAME | String | Hostname | Low | Manual | Defaults localhost. |
| **Flowise** | FLOWISE_USERNAME | Hex | 16 chars | Medium | `openssl rand -hex 8` | Defaults random. |
| | FLOWISE_PASSWORD | String | 12+ chars | Medium | `openssl rand -base64 24 | tr -d '/+='` | Defaults random. |
| | FLOWISE_HOSTNAME | String | Hostname | Low | Manual | Defaults localhost. |
| **Open WebUI** | WEBUI_HOSTNAME | String | Hostname | Low | Manual | Defaults localhost. |
| **Langfuse** | LANGFUSE_SALT | Hex | 64 chars | High | `openssl rand -hex 32` | Tracing salt. |
| | LANGFUSE_HOSTNAME | String | Hostname | Low | Manual | Defaults localhost. |
| | LANGFUSE_INIT_* | String | Various | Low | Manual | Initial org/project/user setup (optional). |
| | TELEMETRY_ENABLED | Boolean | true/false | Low | Manual | Defaults true. |
| | CLICKHOUSE_* | Various | See table | Medium | Manual | Analytics DB. |
| | REDIS_* | Various | See table | Low | Manual | Cache config. |
| **SearxNG** | SEARXNG_HOSTNAME | String | Hostname | Low | Manual | Defaults localhost. |
| | SEARXNG_UWSGI_* | Integer | 1-16 | Low | Manual | Workers/threads; defaults 4. |
| **Agentic RAG** | AGENTIC_HOSTNAME | String | Hostname | Low | Manual | Defaults localhost. |
| **Frontend** | FRONTEND_HOSTNAME | String | Hostname | Low | Manual | Defaults localhost. |
| **Supabase Tokens** | SERVICE_ROLE_KEY | JWT Token | Valid JWT | Critical | Supabase CLI | Admin key. |
| | DASHBOARD_USERNAME | Hex | 16 chars | Medium | `openssl rand -hex 8` | Studio login. |
| | DASHBOARD_PASSWORD | String | 12+ chars | Medium | `openssl rand -base64 24 | tr -d '/+='` | Studio password. |
| | POOLER_TENANT_ID | Integer | 1000-9999 | Low | `shuf -i 1000-9999 -n 1` | Connection pooler. |
| **Other** | SECRET_KEY_BASE | Hex | 128 chars | Critical | `openssl rand -hex 64` | General secret. |
| | VAULT_ENC_KEY | Hex | 64 chars | Critical | `openssl rand -hex 32` | Vault encryption. |
| | POOLER_DB_POOL_SIZE | Integer | Positive int | Low | Manual | Defaults 5. |
| | LOGFLARE_*_ACCESS_TOKEN | Hex | 64 chars | Medium | `openssl rand -hex 32` | Log analytics. |
| | GRAYLOG_PASSWORD_SECRET | String | 32+ chars | Medium | Manual/random | Logging secret. |
| | GRAYLOG_PASSWORD | String | 12+ chars | Medium | `openssl rand -base64 24 | tr -d '/+='` | Logging access. |
| | OPENSEARCH_HOSTS | JSON Array | ["http://host:port"] | Low | Manual | Defaults ["http://opensearch:9200"]. |
| | RABBITMQ_USER/PASS | String | 12+ chars | Medium | `openssl rand -hex 8` / base64 | Queue credentials. |
| | LOCALAI_API_KEY | Hex | 64 chars | Medium | `openssl rand -hex 32` | Local inference. |
| | ENVIRONMENT | String | private/public | Low | Manual | Defaults private. |
| | DOCKER_PROJECT_NAME | String | localai | Low | Manual | Defaults localai. |

## Setup Instructions

### 1. Install Bitwarden CLI
```bash
# Ubuntu/Debian
wget -qO- https://downloads.bitwarden.com/cli/Bitwarden_Installer.sh | bash
# macOS: brew install bitwarden-cli
# Windows: choco install bitwarden-cli
```

### 2. Authenticate Bitwarden CLI
```bash
bw login  # Interactive with 2FA
export BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD)  # Set BW_PASSWORD env var
```

### 3. Create Organization (Team Deployments)
- In Bitwarden web UI: Create org "Local AI Package".
- Add collections: Supabase, n8n, Databases, AI Services, Auth/Monitoring.
- Assign members with role-based access.

### 4. Store Initial Secrets (One-Time Migration)
For existing `.env` values:
```bash
#!/bin/bash
# scripts/migrate-secrets-to-bitwarden.sh
source .env || true
bw login  # If not logged in
export BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD)

# Supabase
bw create login "localai_supabase_postgres_password" --password "$POSTGRES_PASSWORD" --organizationid $ORG_ID
bw create login "localai_supabase_jwt_secret" --password "$JWT_SECRET" --organizationid $ORG_ID
# Repeat for all table vars (replace $ORG_ID with your org ID)

echo "Migration complete. Clear sensitive values from .env (replace with placeholders)."
```

Run: `./scripts/migrate-secrets-to-bitwarden.sh`.

### 5. Populate .env from Bitwarden (Repeatable)
```bash
#!/bin/bash
# scripts/populate-env-from-bitwarden.sh
export BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD)

get_secret() {
  local name="$1"
  bw get password "localai_$name" 2>/dev/null || echo "PLACEHOLDER_$name"
}

# Clear and populate .env
> .env

# Application
echo "NODE_ENV=development" >> .env
echo "PORT=3000" >> .env

# Supabase
echo "NEXT_PUBLIC_SUPABASE_URL=$(get_secret supabase_url)" >> .env
echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=$(get_secret supabase_anon_key)" >> .env
echo "SUPABASE_SERVICE_ROLE_KEY=$(get_secret supabase_service_role_key)" >> .env

# Authentication
echo "JWT_SECRET=$(get_secret auth_jwt_secret)" >> .env
echo "NEXTAUTH_SECRET=$(get_secret auth_nextauth_secret)" >> .env
echo "NEXTAUTH_URL=http://localhost:3000" >> .env

# Database
echo "DATABASE_URL=postgresql://postgres:$(get_secret database_postgres_password)@postgres:5432/postgres" >> .env
echo "POSTGRES_PASSWORD=$(get_secret database_postgres_password)" >> .env
echo "POSTGRES_VERSION=16-alpine" >> .env

# AI/ML
echo "OPENAI_API_KEY=$(get_secret ai_openai_key)" >> .env
echo "ANTHROPIC_API_KEY=$(get_secret ai_anthropic_key)" >> .env

# Vector Databases
echo "QDRANT_URL=http://qdrant:6333" >> .env
echo "QDRANT_API_KEY=$(get_secret vector_qdrant_key)" >> .env

# Monitoring
echo "GRAFANA_ADMIN_PASSWORD=$(get_secret monitoring_grafana_password)" >> .env
echo "PROMETHEUS_PASSWORD=$(get_secret monitoring_prometheus_password)" >> .env

# External Services
echo "LINEAR_API_KEY=$(get_secret external_linear_key)" >> .env
echo "GITHUB_TOKEN=$(get_secret external_github_token)" >> .env

# Security
echo "ENCRYPTION_KEY=$(get_secret security_encryption_key)" >> .env
echo "CORS_ORIGIN=http://localhost:3000" >> .env

# Feature Flags
echo "ENABLE_EXPERIMENTAL_FEATURES=false" >> .env
echo "ENABLE_ANALYTICS=false" >> .env

# n8n
echo "N8N_ENCRYPTION_KEY=$(get_secret n8n_encryption_key)" >> .env
echo "N8N_USER_MANAGEMENT_JWT_SECRET=$(get_secret n8n_jwt_secret)" >> .env
echo "N8N_HOSTNAME=localhost" >> .env

# Flowise
echo "FLOWISE_USERNAME=$(get_secret flowise_username)" >> .env
echo "FLOWISE_PASSWORD=$(get_secret flowise_password)" >> .env
echo "FLOWISE_HOSTNAME=localhost" >> .env

# Open WebUI
echo "WEBUI_HOSTNAME=localhost" >> .env

# Langfuse
echo "LANGFUSE_SALT=$(get_secret langfuse_salt)" >> .env
echo "LANGFUSE_HOSTNAME=localhost" >> .env
# Add LANGFUSE_INIT_* if set

# ClickHouse
echo "CLICKHOUSE_PASSWORD=$(get_secret clickhouse_password)" >> .env

# MinIO
echo "MINIO_ROOT_PASSWORD=$(get_secret minio_root_password)" >> .env

# SearxNG
echo "SEARXNG_HOSTNAME=localhost" >> .env
echo "SEARXNG_UWSGI_WORKERS=4" >> .env
echo "SEARXNG_UWSGI_THREADS=4" >> .env

# Agentic RAG
echo "AGENTIC_HOSTNAME=localhost" >> .env

# Frontend
echo "FRONTEND_HOSTNAME=localhost" >> .env
echo "SUPABASE_HOSTNAME=localhost" >> .env

# Neo4j
echo "NEO4J_PASSWORD=$(get_secret neo4j_password)" >> .env

# Graylog
echo "GRAYLOG_PASSWORD_SECRET=$(get_secret graylog_password_secret)" >> .env
echo "GRAYLOG_PASSWORD=$(get_secret graylog_password)" >> .env

# OpenSearch
echo "OPENSEARCH_HOSTS=[\"http://opensearch:9200\"]" >> .env

# RabbitMQ
echo "RABBITMQ_USER=guest" >> .env
echo "RABBITMQ_PASS=guest" >> .env

# LocalAI
echo "LOCALAI_API_KEY=$(get_secret localai_api_key)" >> .env

# Environment
echo "ENVIRONMENT=private" >> .env
echo "DOCKER_PROJECT_NAME=localai" >> .env

echo ".env populated from Bitwarden. Run: source .env"
```

Run: `./scripts/populate-env-from-bitwarden.sh && source .env`.

### 6. Integrate with Deployment and Launch Scripts

Modify scripts to use population (e.g., in start-all-services.sh, deploy-legislative-ai.sh):
```bash
# At script start
if [ -f scripts/populate-env-from-bitwarden.sh ]; then
  ./scripts/populate-env-from-bitwarden.sh
  source .env
else
  warning "Using local .env - run populate script first"
  source .env
fi
```

### 7. Bitwarden Security Best Practices

- **Authentication**: Enable 2FA/YubiKey; use password manager for CLI.
- **Session Management**: Vault timeout 30 min; re-authenticate for long sessions.
- **Access Control**: Use collections for RBAC (e.g., devs read-only for prod secrets).
- **Auditing**: Review access logs weekly (`bw list items --organizationid $ORG_ID`).
- **Backup**: Export encrypted vault to secure offsite; test restore.
- **.env Handling**: chmod 600 .env; never commit (gitignore'd).
- **Special Characters**: Avoid @ / + in passwords (breaks URLs/JWT); use filtered base64.

### 8. Cloudflare Secrets for Production

For serverless/prod:
1. Install Wrangler: `npm i -g wrangler`.
2. wrangler.toml:
   ```
   name = "local-ai-api"
   [[secrets]]
   name = "SUPABASE_JWT_SECRET"
   ```
3. Set secrets:
   ```bash
   wrangler secret put SUPABASE_JWT_SECRET
   ```
4. Access in code: `env.SUPABASE_JWT_SECRET`.

Integrate with deployment: Call wrangler in CI/CD.

### 9. Validation and Troubleshooting

Validate .env:
```bash
./scripts/validate_env.sh  # Checks lengths, formats, placeholders
```

Common issues:
- **Invalid Hex/JWT**: "Invalid hex string" or "JWT must have 3 parts".
  - **Solution**: Regenerate: `openssl rand -hex 32`; re-populate.
- **BW_SESSION Expired**: "Unlock failed".
  - **Solution**: Re-run `bw unlock --raw`.
- **Missing Vars**: "PLACEHOLDER_*" in .env.
  - **Solution**: Store in Bitwarden; re-run populate.
- **Special Chars in Passwords**: URL/JWT parse errors.
  - **Solution**: Regenerate without @ / + / =; use tr -d.
- **Validation Fails**: See [Environment Variables Rules](ENV_VARIABLES_RULES.md) for formats.

Test: `source .env && curl -H "apikey: $ANON_KEY" http://localhost:8000/health` (Supabase).

## Next Steps

1. Install/authenticate Bitwarden CLI.
2. Migrate existing secrets to vault.
3. Test population script.
4. Update launch/deployment scripts.
5. Verify services with populated .env.

This ensures secure, consistent secret management.