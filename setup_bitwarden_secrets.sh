#!/bin/bash

# Bitwarden Secrets Setup Script
# This script fetches secrets from Bitwarden vault and creates a .env file
# It searches for secrets using multiple naming patterns:
#   - Exact name (e.g., 'N8N_ENCRYPTION_KEY')
#   - user.account.<name> (e.g., 'user.account.N8N_ENCRYPTION_KEY')
#   - user.secret.<name> (e.g., 'user.secret.N8N_ENCRYPTION_KEY')
#   - machine.account.<name> (e.g., 'machine.account.N8N_ENCRYPTION_KEY')

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "Bitwarden Secrets Setup for Local AI Package"
echo "================================================"
echo ""

# Check if bw is installed
if ! command -v bw &> /dev/null; then
    echo -e "${RED}Error: Bitwarden CLI (bw) is not installed${NC}"
    echo ""
    echo "Please install it from: https://bitwarden.com/help/cli/"
    echo ""
    echo "Installation instructions:"
    echo "  Linux/Mac: npm install -g @bitwarden/cli"
    echo "  Or download from: https://github.com/bitwarden/clients/releases"
    exit 1
fi

echo -e "${GREEN}✓ Bitwarden CLI found${NC}"

# Check if .env.example exists
if [ ! -f ".env.example" ]; then
    echo -e "${RED}Error: .env.example not found${NC}"
    echo "Please run this script from the root of the local-ai-packaged repository"
    exit 1
fi

# Login to Bitwarden if not already logged in
echo ""
echo "Checking Bitwarden login status..."

if ! bw login --check &> /dev/null; then
    echo "Not logged in to Bitwarden. Please login:"
    echo ""
    echo "Options:"
    echo "  1. Login with email/password: bw login"
    echo "  2. Login with API key: bw login --apikey"
    echo ""
    read -p "Press enter after logging in..."
fi

# Unlock vault
echo ""
echo "Unlocking Bitwarden vault..."
if [ -z "$BW_SESSION" ]; then
    echo "Please enter your master password to unlock the vault:"
    export BW_SESSION=$(bw unlock --raw)
    if [ -z "$BW_SESSION" ]; then
        echo -e "${RED}Error: Failed to unlock Bitwarden vault${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Vault unlocked${NC}"

# Sync vault
echo "Syncing vault..."
bw sync --session "$BW_SESSION" > /dev/null
echo -e "${GREEN}✓ Vault synced${NC}"
echo ""

# Function to search for a secret in Bitwarden
get_secret() {
    local secret_name=$1
    local search_patterns=("$secret_name" "user.account.$secret_name" "user.secret.$secret_name" "machine.account.$secret_name")
    
    for pattern in "${search_patterns[@]}"; do
        # Try to get the item
        item=$(bw get item "$pattern" --session "$BW_SESSION" 2>/dev/null || echo "")
        if [ -n "$item" ]; then
            # Try to get password field first, then notes
            value=$(echo "$item" | jq -r '.login.password // .notes // empty' 2>/dev/null)
            if [ -n "$value" ] && [ "$value" != "null" ]; then
                echo "$value"
                return 0
            fi
        fi
    done
    
    echo ""
    return 1
}

# Backup existing .env if it exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}Backing up existing .env to .env.backup${NC}"
    cp .env .env.backup
fi

# Start with the .env.example as a template
cp .env.example .env

echo "Fetching secrets from Bitwarden vault..."
echo ""

# Arrays to track secrets
declare -a found_secrets
declare -a missing_secrets

# Function to fetch and update secret
fetch_and_update() {
    local secret_name=$1
    local is_required=$2
    
    echo -n "  Fetching ${secret_name}... "
    value=$(get_secret "$secret_name")
    
    if [ -n "$value" ]; then
        sed -i "s|^${secret_name}=.*|${secret_name}=${value}|" .env
        # Also handle commented lines for optional secrets
        sed -i "s|^# ${secret_name}=.*|${secret_name}=${value}|" .env
        echo -e "${GREEN}✓${NC}"
        found_secrets+=("$secret_name")
        return 0
    else
        echo -e "${RED}✗${NC}"
        if [ "$is_required" == "true" ]; then
            missing_secrets+=("$secret_name")
        fi
        return 1
    fi
}

# Required N8N secrets
echo -e "${YELLOW}N8N Configuration:${NC}"
fetch_and_update "N8N_ENCRYPTION_KEY" "true"
fetch_and_update "N8N_USER_MANAGEMENT_JWT_SECRET" "true"
echo ""

# Required Supabase secrets
echo -e "${YELLOW}Supabase Secrets:${NC}"
fetch_and_update "POSTGRES_PASSWORD" "true"
fetch_and_update "JWT_SECRET" "true"
fetch_and_update "ANON_KEY" "true"
fetch_and_update "SERVICE_ROLE_KEY" "true"
fetch_and_update "DASHBOARD_USERNAME" "true"
fetch_and_update "DASHBOARD_PASSWORD" "true"
fetch_and_update "POOLER_TENANT_ID" "true"
echo ""

# Required Neo4j secrets
echo -e "${YELLOW}Neo4j Secrets:${NC}"
fetch_and_update "NEO4J_AUTH" "true"
echo ""

# Required Langfuse secrets
echo -e "${YELLOW}Langfuse Credentials:${NC}"
fetch_and_update "CLICKHOUSE_PASSWORD" "true"
fetch_and_update "MINIO_ROOT_PASSWORD" "true"
fetch_and_update "LANGFUSE_SALT" "true"
fetch_and_update "NEXTAUTH_SECRET" "true"
fetch_and_update "ENCRYPTION_KEY" "true"
echo ""

# Optional additional secrets
echo -e "${YELLOW}Additional Secrets:${NC}"
fetch_and_update "SECRET_KEY_BASE" "false"
fetch_and_update "VAULT_ENC_KEY" "false"
echo ""

# Optional production secrets
echo -e "${YELLOW}Optional Production Configuration:${NC}"
fetch_and_update "N8N_HOSTNAME" "false"
fetch_and_update "WEBUI_HOSTNAME" "false"
fetch_and_update "FLOWISE_HOSTNAME" "false"
fetch_and_update "SUPABASE_HOSTNAME" "false"
fetch_and_update "OLLAMA_HOSTNAME" "false"
fetch_and_update "SEARXNG_HOSTNAME" "false"
fetch_and_update "NEO4J_HOSTNAME" "false"
fetch_and_update "LETSENCRYPT_EMAIL" "false"
echo ""

# Summary
echo "================================================"
echo "Summary"
echo "================================================"
echo ""
echo -e "${GREEN}Found secrets: ${#found_secrets[@]}${NC}"
echo -e "${RED}Missing required secrets: ${#missing_secrets[@]}${NC}"
echo ""

if [ ${#missing_secrets[@]} -gt 0 ]; then
    echo -e "${RED}⚠ WARNING: The following required secrets are missing:${NC}"
    for secret in "${missing_secrets[@]}"; do
        echo "  - $secret"
    done
    echo ""
    echo "Please add these secrets to your Bitwarden vault using one of these naming patterns:"
    echo "  - Exact name (e.g., 'N8N_ENCRYPTION_KEY')"
    echo "  - user.account.<name> (e.g., 'user.account.N8N_ENCRYPTION_KEY')"
    echo "  - user.secret.<name> (e.g., 'user.secret.N8N_ENCRYPTION_KEY')"
    echo "  - machine.account.<name> (e.g., 'machine.account.N8N_ENCRYPTION_KEY')"
    echo ""
    echo "Store the secret value in the 'Password' field of the Bitwarden item."
    echo ""
    echo -e "${YELLOW}The .env file has been created but is INCOMPLETE.${NC}"
    echo "Please add the missing secrets to Bitwarden and run this script again."
    exit 1
else
    echo -e "${GREEN}✓ All required secrets found and configured!${NC}"
    echo ""
    echo "The .env file has been created successfully."
    echo "You can now run: python start_services.py --profile <your-profile>"
    echo ""
fi

# Security reminder
echo "================================================"
echo -e "${YELLOW}Security Reminder:${NC}"
echo "  - The .env file is listed in .gitignore"
echo "  - Never commit the .env file to version control"
echo "  - Keep your Bitwarden master password secure"
echo "================================================"
