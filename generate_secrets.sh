#!/bin/bash

# Secret Generator Script for Local AI Package
# This script generates secure random values for all required secrets
# You can copy these values into Bitwarden or directly into your .env file

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================"
echo "Secret Generator for Local AI Package"
echo "================================================"
echo ""
echo "This script generates secure random values for all required secrets."
echo "Copy these values into your Bitwarden vault or .env file."
echo ""

# Check if openssl is available
if ! command -v openssl &> /dev/null; then
    echo "Warning: openssl not found, using Python fallback"
    GENERATOR="python"
else
    GENERATOR="openssl"
fi

# Function to generate a random hex string
generate_secret() {
    if [ "$GENERATOR" = "openssl" ]; then
        openssl rand -hex 32
    else
        python3 -c "import secrets; print(secrets.token_hex(32))"
    fi
}

# Function to generate a strong password
generate_password() {
    if [ "$GENERATOR" = "openssl" ]; then
        openssl rand -base64 24 | tr -d "=+/" | cut -c1-24
    else
        python3 -c "import secrets; import string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24)))"
    fi
}

echo -e "${YELLOW}=== N8N Configuration ===${NC}"
echo ""
echo -e "${BLUE}N8N_ENCRYPTION_KEY:${NC}"
N8N_ENCRYPTION_KEY=$(generate_secret)
echo "$N8N_ENCRYPTION_KEY"
echo ""
echo -e "${BLUE}N8N_USER_MANAGEMENT_JWT_SECRET:${NC}"
N8N_USER_MANAGEMENT_JWT_SECRET=$(generate_secret)
echo "$N8N_USER_MANAGEMENT_JWT_SECRET"
echo ""

echo -e "${YELLOW}=== Supabase Secrets ===${NC}"
echo ""
echo -e "${BLUE}POSTGRES_PASSWORD:${NC}"
POSTGRES_PASSWORD=$(generate_password)
echo "$POSTGRES_PASSWORD"
echo ""
echo -e "${BLUE}JWT_SECRET:${NC}"
JWT_SECRET=$(generate_secret)
echo "$JWT_SECRET"
echo ""
echo -e "${BLUE}ANON_KEY:${NC}"
echo "Please generate using Supabase JWT generator:"
echo "https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys"
echo ""
echo -e "${BLUE}SERVICE_ROLE_KEY:${NC}"
echo "Please generate using Supabase JWT generator:"
echo "https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys"
echo ""
echo -e "${BLUE}DASHBOARD_USERNAME:${NC}"
echo "supabase (or choose your own)"
echo ""
echo -e "${BLUE}DASHBOARD_PASSWORD:${NC}"
DASHBOARD_PASSWORD=$(generate_password)
echo "$DASHBOARD_PASSWORD"
echo ""
echo -e "${BLUE}POOLER_TENANT_ID:${NC}"
echo "1000 (or any numeric value)"
echo ""

echo -e "${YELLOW}=== Neo4j Secrets ===${NC}"
echo ""
echo -e "${BLUE}NEO4J_AUTH:${NC}"
NEO4J_PASSWORD=$(generate_password)
echo "neo4j/$NEO4J_PASSWORD"
echo ""

echo -e "${YELLOW}=== Langfuse Credentials ===${NC}"
echo ""
echo -e "${BLUE}CLICKHOUSE_PASSWORD:${NC}"
CLICKHOUSE_PASSWORD=$(generate_secret)
echo "$CLICKHOUSE_PASSWORD"
echo ""
echo -e "${BLUE}MINIO_ROOT_PASSWORD:${NC}"
MINIO_ROOT_PASSWORD=$(generate_secret)
echo "$MINIO_ROOT_PASSWORD"
echo ""
echo -e "${BLUE}LANGFUSE_SALT:${NC}"
LANGFUSE_SALT=$(generate_secret)
echo "$LANGFUSE_SALT"
echo ""
echo -e "${BLUE}NEXTAUTH_SECRET:${NC}"
NEXTAUTH_SECRET=$(generate_secret)
echo "$NEXTAUTH_SECRET"
echo ""
echo -e "${BLUE}ENCRYPTION_KEY:${NC}"
ENCRYPTION_KEY=$(generate_secret)
echo "$ENCRYPTION_KEY"
echo ""

echo -e "${YELLOW}=== Additional Optional Secrets ===${NC}"
echo ""
echo -e "${BLUE}SECRET_KEY_BASE:${NC}"
SECRET_KEY_BASE=$(generate_secret)
echo "$SECRET_KEY_BASE"
echo ""
echo -e "${BLUE}VAULT_ENC_KEY:${NC}"
VAULT_ENC_KEY=$(generate_secret)
echo "$VAULT_ENC_KEY"
echo ""

echo "================================================"
echo -e "${GREEN}Secret Generation Complete!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Copy these values to your Bitwarden vault"
echo "2. For ANON_KEY and SERVICE_ROLE_KEY, use the Supabase JWT generator"
echo "3. Run: ./setup_bitwarden_secrets.sh (or .py) to fetch secrets"
echo "4. Or manually create .env file with these values"
echo ""
echo "================================================"
echo -e "${YELLOW}IMPORTANT SECURITY NOTES:${NC}"
echo "  - Store these secrets securely (Bitwarden recommended)"
echo "  - Never commit secrets to version control"
echo "  - Clear your terminal history if it stores commands"
echo "================================================"

# Option to save to a temporary file
echo ""
read -p "Save secrets to a temporary file? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    OUTFILE="/tmp/local-ai-secrets-$(date +%s).txt"
    {
        echo "# Generated secrets for Local AI Package"
        echo "# Generated on: $(date)"
        echo ""
        echo "# N8N Configuration"
        echo "N8N_ENCRYPTION_KEY=$N8N_ENCRYPTION_KEY"
        echo "N8N_USER_MANAGEMENT_JWT_SECRET=$N8N_USER_MANAGEMENT_JWT_SECRET"
        echo ""
        echo "# Supabase Secrets"
        echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
        echo "JWT_SECRET=$JWT_SECRET"
        echo "ANON_KEY=<GENERATE_WITH_SUPABASE_TOOL>"
        echo "SERVICE_ROLE_KEY=<GENERATE_WITH_SUPABASE_TOOL>"
        echo "DASHBOARD_USERNAME=supabase"
        echo "DASHBOARD_PASSWORD=$DASHBOARD_PASSWORD"
        echo "POOLER_TENANT_ID=1000"
        echo ""
        echo "# Neo4j Secrets"
        echo "NEO4J_AUTH=neo4j/$NEO4J_PASSWORD"
        echo ""
        echo "# Langfuse Credentials"
        echo "CLICKHOUSE_PASSWORD=$CLICKHOUSE_PASSWORD"
        echo "MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD"
        echo "LANGFUSE_SALT=$LANGFUSE_SALT"
        echo "NEXTAUTH_SECRET=$NEXTAUTH_SECRET"
        echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"
        echo ""
        echo "# Additional Optional Secrets"
        echo "SECRET_KEY_BASE=$SECRET_KEY_BASE"
        echo "VAULT_ENC_KEY=$VAULT_ENC_KEY"
    } > "$OUTFILE"
    
    echo -e "${GREEN}Secrets saved to: $OUTFILE${NC}"
    echo "Remember to delete this file after storing secrets securely!"
    echo "Command: rm $OUTFILE"
fi
