# Secure Secrets Management with Bitwarden/Cloudflare

## Overview
This project uses Bitwarden as the primary secrets manager for all API keys, database credentials, and service tokens. This ensures repeatability without regeneration—once stored, secrets can be retrieved consistently across environments. Cloudflare Secrets is used for production deployments. Local .env files are populated from Bitwarden for development.

**Key Principles:**
- No secret regeneration during normal operations
- All secrets stored in Bitwarden vault with secure naming conventions
- Scripts pull secrets dynamically using Bitwarden CLI
- .env.example serves as template; actual .env is .gitignore'd and populated on-demand
- Rotate only when compromised or per policy (annual)

## Critical Secrets Inventory
The following secrets must be stored in Bitwarden:

### Supabase (Folder: "Local AI Package/Supabase")
- `SUPABASE_POSTGRES_PASSWORD`: PostgreSQL master password
- `SUPABASE_JWT_SECRET`: JWT signing secret (256-bit)
- `SUPABASE_ANON_KEY`: Public anon key for client access
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key for admin operations
- `SUPABASE_DASHBOARD_PASSWORD`: Studio dashboard password
- `SUPABASE_POOLER_TENANT_ID`: Connection pooler tenant ID

### n8n (Folder: "Local AI Package/n8n")
- `N8N_ENCRYPTION_KEY`: Data encryption key
- `N8N_USER_MANAGEMENT_JWT_SECRET`: User auth JWT secret

### Database/Storage (Folder: "Local AI Package/Storage")
- `NEO4J_PASSWORD`: Neo4j database password
- `CLICKHOUSE_PASSWORD`: ClickHouse analytics password
- `MINIO_ROOT_PASSWORD`: MinIO S3 storage password
- `GRAYLOG_PASSWORD`: Graylog logging password
- `RABBITMQ_PASSWORD`: Message queue password

### AI Services (Folder: "Local AI Package/AI APIs")
- `OPENAI_API_KEY`: OpenAI GPT access
- `SERPAPI_API_KEY`: Web search API
- `GRAPHRAG_API_KEY`: GraphRAG indexing
- `CRAWL4AI_API_KEY`: Web crawling
- `LOCALAI_API_KEY`: Local AI inference

### Auth/Monitoring (Folder: "Local AI Package/Auth")
- `NEXTAUTH_SECRET`: NextAuth session secret
- `LANGFUSE_SALT`: Tracing salt
- `LOGFLARE_PUBLIC_ACCESS_TOKEN`: Log analytics public
- `LOGFLARE_PRIVATE_ACCESS_TOKEN`: Log analytics private

**Naming Convention:** Use `projectname_service_variablename` format (e.g., `localai_supabase_jwt_secret`)

## Setup Instructions

### 1. Install Bitwarden CLI
```bash
# Ubuntu/Debian
wget -qO- https://downloads.bitwarden.com/cli/Bitwarden_Installer.sh | bash
# Or via snap
sudo snap install bw
```

### 2. Authenticate Bitwarden CLI
```bash
# Login (2FA required)
bw login
# Unlock vault
bw unlock --passwordenv BW_PASSWORD
# Set session key for scripts
export BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD)
```

### 3. Create Secrets Organization (if team deployment)
- In Bitwarden web: Create organization "Local AI Package"
- Add collections matching folders above
- Assign members with appropriate access

### 4. Store Initial Secrets
For each secret from current .env:
```bash
# Example for Supabase JWT
echo -n "a88def8ee7e5675ccda45a2efe8cffc1355126fbcd097e91616b4b522cdd23a3" | bw encode | bw create login "localai_supabase_jwt_secret" --organizationid YOUR_ORG_ID
# Repeat for all secrets listed in inventory
```

**One-time migration script:**
```bash
#!/bin/bash
# migrate-secrets-to-bitwarden.sh
source .env
bw login  # Interactive
export BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD)

# Supabase
bw create login "localai_supabase_postgres_password" --password "$POSTGRES_PASSWORD"
bw create login "localai_supabase_jwt_secret" --password "$JWT_SECRET"
# ... continue for all variables

echo "Migration complete. Remove secrets from .env and use retrieval scripts."
```

### 5. Populate .env from Bitwarden (Repeatable Process)
Create `scripts/populate-env-from-bitwarden.sh`:
```bash
#!/bin/bash
# Requires: bw CLI authenticated

export BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD)

# Function to retrieve secret
get_secret() {
  local name=$1
  bw get password "$name" 2>/dev/null || echo "SECRET_NOT_FOUND_$name"
}

# Populate critical secrets
echo "POSTGRES_PASSWORD=$(get_secret localai_supabase_postgres_password)" >> .env
echo "JWT_SECRET=$(get_secret localai_supabase_jwt_secret)" >> .env
echo "ANON_KEY=$(get_secret localai_supabase_anon_key)" >> .env
# ... add all inventory items

echo ".env populated from Bitwarden. Run: source .env"
```

Usage:
```bash
chmod +x scripts/populate-env-from-bitwarden.sh
./scripts/populate-env-from-bitwarden.sh
source .env
```

### 6. Integrate with Deployment Scripts
Update `scripts/deploy-legislative-ai.sh` and `tools/start_services.py`:
```bash
# At script start
if [ -f scripts/populate-env-from-bitwarden.sh ]; then
  ./scripts/populate-env-from-bitwarden.sh
  source .env
else
  echo "WARNING: Using local .env - run populate script first"
  source .env
fi
```

For production (Cloudflare):
- Use Cloudflare Workers Secrets API
- Store in `wrangler.toml` secrets section
- Retrieve via `env.SECRET_NAME` in serverless functions

### 7. Bitwarden Security Best Practices
- Enable 2FA and YubiKey for vault access
- Use password manager autofill for CLI login
- Set vault timeout (e.g., 30 minutes)
- Audit access logs weekly
- Backup vault export (encrypted) to secure offsite location
- Never store .env in version control (already .gitignore'd)

## Cloudflare Secrets for Production
For public deployments:
1. Install Wrangler CLI: `npm i -g wrangler`
2. Add to `wrangler.toml`:
   ```
   [[secrets]]
   name = "SUPABASE_JWT_SECRET"
   ```
3. Set: `wrangler secret put SUPABASE_JWT_SECRET`
4. Access in code: `env.SUPABASE_JWT_SECRET`

## Recovery Process
If .env lost:
1. Run `populate-env-from-bitwarden.sh`
2. Verify: `source .env && echo $JWT_SECRET | wc -c` (should be 64+ chars)
3. Deploy: `./scripts/deploy-legislative-ai.sh`

## Migration from Current Setup
1. Run migration script above to store all existing .env secrets
2. Clear sensitive values from .env (replace with placeholders)
3. Test retrieval: `./scripts/populate-env-from-bitwarden.sh && source .env && curl -H "apikey: $ANON_KEY" http://localhost:8000/health`
4. Commit updated scripts/docs (no secrets)

## Security Notes
- Bitwarden CLI sessions expire—reauthenticate as needed
- Use environment variables for BW_PASSWORD in CI/CD
- Audit: `bw list collections --organizationid ORG_ID`
- Never expose BW_SESSION in logs
- For shared teams: Use collections with role-based access

## Next Steps
- Install Bitwarden CLI and authenticate
- Run migration script for current secrets
- Test population script
- Update deployment scripts to use new process
- Verify Supabase works with retrieved credentials