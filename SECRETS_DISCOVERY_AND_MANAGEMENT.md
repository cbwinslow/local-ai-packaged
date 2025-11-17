# Secrets Management and Discovery Documentation

## Overview
This document details all the secrets that were discovered, configured, and updated during the Local AI Package setup process.

## Historical Discovery: Secrets Found During Setup

During the initial configuration process, the following secrets were identified as needing updates in the `.env` and `supabase/docker/.env` files:

### Originally Identified Insecure Values (Now Fixed):
1. `DASHBOARD_PASSWORD` - Updated from "this_password_is_insecure_and_should_be_updated"
2. `POOLER_TENANT_ID` - Updated from "your-tenant-id" 
3. `NEO4J_AUTH` - Updated from "neo4j/password" (weak password)
4. `CLICKHOUSE_PASSWORD` - Updated from "super-secret-key-1" (placeholder)
5. `MINIO_ROOT_PASSWORD` - Updated from "super-secret-key-2" (placeholder)
6. `LANGFUSE_SALT` - Updated from "super-secret-key-3" (placeholder)
7. `VAULT_ENC_KEY` - Updated from "your-32-character-encryption-key" (placeholder)
8. `LOGFLARE_PUBLIC_ACCESS_TOKEN` - Updated from "your-super-secret-and-long-logflare-key-public" (placeholder)
9. `LOGFLARE_PRIVATE_ACCESS_TOKEN` - Updated from "your-super-secret-and-long-logflare-key-private" (placeholder)
10. `SMTP_PASS` - Updated from "fake_mail_password" (placeholder)
11. `SMTP_USER` - Updated from "fake_mail_user" (placeholder)

### Updated with Secure Generated Values:
All of the above mentioned insecure values were replaced with secure, randomly generated hexadecimal strings using `openssl rand -hex 32` for appropriate lengths.

## Current Secrets Configuration

### Primary Configuration Files:
1. `/home/cbwinslow/projects/local-ai-packaged/.env` - Main application secrets
2. `/home/cbwinslow/projects/local-ai-packaged/supabase/docker/.env` - Supabase-specific secrets

### Critical Secrets Currently Configured:

#### Authentication & Encryption:
- `N8N_ENCRYPTION_KEY` - Used for n8n workflow encryption
- `N8N_USER_MANAGEMENT_JWT_SECRET` - Used for n8n JWT token signing
- `JWT_SECRET` - General JWT signing secret
- `ANON_KEY` - Supabase anonymous key (JWT format)
- `SERVICE_ROLE_KEY` - Supabase service role key (JWT format)

#### Database Credentials:
- `POSTGRES_PASSWORD` - PostgreSQL database password
- `DASHBOARD_PASSWORD` - Supabase dashboard password
- `NEO4J_AUTH` - Neo4j authentication (format: username/password)

#### API Keys & Passwords:
- `CLICKHOUSE_PASSWORD` - ClickHouse database password
- `MINIO_ROOT_PASSWORD` - MinIO object storage root password
- `LANGFUSE_SALT` - Salt for Langfuse hashing
- `NEXTAUTH_SECRET` - NextAuth.js secret
- `ENCRYPTION_KEY` - General encryption key

#### Domain & Email Configuration:
- `N8N_HOSTNAME=n8n.cloudcurio.cc` - Domain for n8n
- `WEBUI_HOSTNAME=openwebui.cloudcurio.cc` - Domain for Open WebUI
- `FLOWISE_HOSTNAME=flowise.cloudcurio.cc` - Domain for Flowise
- `SUPABASE_HOSTNAME=supabase.cloudcurio.cc` - Domain for Supabase
- `OLLAMA_HOSTNAME=ollama.cloudcurio.cc` - Domain for Ollama
- `SEARXNG_HOSTNAME=searxng.cloudcurio.cc` - Domain for SearXNG
- `NEO4J_HOSTNAME=neo4j.cloudcurio.cc` - Domain for Neo4j
- `LETSENCRYPT_EMAIL=blaine.winslow@cloudcurio.cc` - Let's Encrypt email

## Security Updates Applied

### URL/Site Configuration Updates:
- `SITE_URL=https://openwebui.cloudcurio.cc` - Updated from localhost
- `API_EXTERNAL_URL=https://supabase.cloudcurio.cc` - Updated from localhost
- `SUPABASE_PUBLIC_URL=https://supabase.cloudcurio.cc` - Updated from localhost
- `SMTP_ADMIN_EMAIL=admin@cloudcurio.cc` - Updated from example.com

## Bitwarden Integration Preparation

### Secrets Suitable for Bitwarden Storage:
The following secrets from the .env files are ideal candidates for Bitwarden storage:

```
N8N_ENCRYPTION_KEY
N8N_USER_MANAGEMENT_JWT_SECRET
POSTGRES_PASSWORD
JWT_SECRET
ANON_KEY
SERVICE_ROLE_KEY
DASHBOARD_USERNAME
DASHBOARD_PASSWORD
POOLER_TENANT_ID
NEO4J_AUTH
CLICKHOUSE_PASSWORD
MINIO_ROOT_PASSWORD
LANGFUSE_SALT
NEXTAUTH_SECRET
ENCRYPTION_KEY
SECRET_KEY_BASE
VAULT_ENC_KEY
LOGFLARE_PUBLIC_ACCESS_TOKEN
LOGFLARE_PRIVATE_ACCESS_TOKEN
SMTP_USER
SMTP_PASS
SMTP_SENDER_NAME
```

## Verification Checklist

### To Verify Current Configuration:
```bash
# Check for any remaining placeholder or insecure values
grep -E "(insecure|password|secret|your-|fake_|super-secret)" .env supabase/docker/.env

# Verify all cloudcurio.cc domains are set
grep -E "cloudcurio\.cc" .env supabase/docker/.env

# Verify no localhost references remain for production URLs
grep "localhost" .env supabase/docker/.env
```

## Future Management Recommendations

### For Adding New Secrets via Bitwarden:
1. Use naming patterns that match the environment variable names:
   - Exact match: `N8N_ENCRYPTION_KEY`
   - Prefixed: `user.account.N8N_ENCRYPTION_KEY`
   - Suffix patterns: as needed

2. Store sensitive values in the `password` field of Bitwarden login items

3. Use the `setup_bitwarden_secrets.py` script to populate .env files from Bitwarden vault

### Automated Secret Rotation:
Consider implementing a scheduled rotation process:
1. Generate new secure values using `openssl rand -hex 32`
2. Update both Bitwarden vault and .env files
3. Restart affected services
4. Log rotation events

## Access Patterns for AI Agent Use

### To Retrieve Secrets Programmatically:
```bash
# For a single secret
SECRET_VALUE=$(bw get item "N8N_ENCRYPTION_KEY" --session $BW_SESSION | jq -r '.login.password')

# For multiple secrets
bw list items --search "cloudcurio" --session $BW_SESSION
```

### Security Verification:
The current configuration has all placeholder/insecure values replaced with secure, randomly generated values, and all domains properly set to the cloudcurio.cc ecosystem.