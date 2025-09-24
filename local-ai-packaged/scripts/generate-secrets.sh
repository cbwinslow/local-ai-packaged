#!/bin/bash

# Secure secrets generator for bare metal deployment
# Generates random secrets for Neo4j, Postgres, Supabase JWT, Twitter Bearer (placeholder)
# Output: Prints secrets; appends to .env.secrets for Ansible Vault integration
# Usage: ./scripts/generate-secrets.sh
# Ensure executable: chmod +x scripts/generate-secrets.sh

set -euo pipefail

SECRETS_FILE=".env.secrets"

echo "# Generated secrets (load into Ansible Vault or secure store)" > "$SECRETS_FILE"

# Neo4j password: 32-char alphanumeric + special
NEO4J_PW=$(openssl rand -base64 24 | tr -d /=+ | cut -c1-32)
echo "vault_neo4j_password: $NEO4J_PW" >> "$SECRETS_FILE"
echo "Generated Neo4j password: $NEO4J_PW"

# Postgres password: 32-char alphanumeric + special
POSTGRES_PW=$(openssl rand -base64 24 | tr -d /=+ | cut -c1-32)
echo "vault_postgres_password: $POSTGRES_PW" >> "$SECRETS_FILE"
echo "Generated Postgres password: $POSTGRES_PW"

# Supabase JWT secret: 64-char hex
SUPABASE_JWT=$(openssl rand -hex 32)
echo "vault_supabase_jwt_secret: $SUPABASE_JWT" >> "$SECRETS_FILE"
echo "Generated Supabase JWT secret: $SUPABASE_JWT"

# Twitter Bearer Token: Placeholder (generate real via Twitter Dev Portal; use vault for storage)
TWITTER_BEARER="TWITTER_BEARER_PLACEHOLDER_$(openssl rand -hex 16)"
echo "vault_twitter_bearer_token: $TWITTER_BEARER" >> "$SECRETS_FILE"
echo "Generated Twitter Bearer placeholder: $TWITTER_BEARER (replace with real token)"

echo "Secrets generated and saved to $SECRETS_FILE. Secure this file and integrate with Ansible Vault (e.g., ansible-vault encrypt_string)."
echo "Remove from git: echo '.env.secrets' >> .gitignore"