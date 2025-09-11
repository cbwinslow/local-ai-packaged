#!/bin/bash

# This script helps set up the environment for the political document analysis system

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Political Document Analysis Setup ===${NC}\n"

# Check if .env exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file already exists. Backing up to .env.backup.$(date +%Y%m%d_%H%M%S)${NC}"
    cp .env ".env.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}Created .env file from .env.example${NC}"
    else
        echo -e "${YELLOW}Warning: .env.example not found. Creating a new .env file.${NC}"
        touch .env
    fi
fi

# Function to set or update an environment variable
set_env_var() {
    local var_name=$1
    local prompt=$2
    local default_value=$3
    local is_secret=$4
    
    # Check if the variable already exists in .env
    local current_value=$(grep -E "^${var_name}=" .env | cut -d '=' -f2- || echo "")
    
    if [ -n "$current_value" ] && [ "$current_value" != "your-${var_name,,}" ]; then
        if [ "$is_secret" = true ]; then
            echo -e "${GREEN}${var_name} is already set (value hidden)${NC}"
        else
            echo -e "${GREEN}${var_name} is already set to: ${current_value}${NC}"
        fi
        return
    fi
    
    echo -n "${prompt} [${default_value}]: "
    read -r value
    value=${value:-$default_value}
    
    # Escape special characters for sed
    local escaped_value=$(printf '%s\n' "$value" | sed -e 's/[\/&]/\\&/g')
    
    # Update or add the variable
    if grep -q "^${var_name}=" .env; then
        sed -i "s/^${var_name}=.*/${var_name}=${escaped_value}/" .env
    else
        echo "${var_name}=${value}" >> .env
    fi
    
    if [ "$is_secret" = true ]; then
        echo -e "${GREEN}Set ${var_name} (value hidden)${NC}"
    else
        echo -e "${GREEN}Set ${var_name} to: ${value}${NC}"
    fi
}

# Set domain configuration
set_env_var "DOMAIN" "Enter your domain (e.g., opendiscourse.net)" "opendiscourse.net" false
set_env_var "LETSENCRYPT_EMAIL" "Enter your email for Let's Encrypt" "admin@${DOMAIN:-example.com}" false

# Database configuration
set_env_var "POSTGRES_PASSWORD" "Enter a password for PostgreSQL" "$(openssl rand -base64 32)" true
set_env_var "POSTGRES_USER" "Enter PostgreSQL username" "opendiscourse" false
set_env_var "POSTGRES_DB" "Enter PostgreSQL database name" "opendiscourse" false

# JWT Configuration
set_env_var "JWT_SECRET" "Enter a secret for JWT tokens" "$(openssl rand -base64 32)" true
set_env_var "NEXTAUTH_SECRET" "Enter a secret for NextAuth" "$(openssl rand -base64 32)" true

# Service credentials
set_env_var "N8N_ENCRYPTION_KEY" "Enter encryption key for n8n" "$(openssl rand -base64 32)" true
set_env_var "N8N_JWT_SECRET" "Enter JWT secret for n8n" "$(openssl rand -base64 32)" true
set_env_var "FLOWISE_PASSWORD" "Enter password for Flowise" "$(openssl rand -base64 16)" true

# Neo4j
set_env_var "NEO4J_PASSWORD" "Enter password for Neo4j" "$(openssl rand -base64 32)" true

# External services
set_env_var "CONGRESS_GOV_API_KEY" "Enter your Congress.gov API key" "" true
set_env_var "OPENAI_API_KEY" "Enter your OpenAI API key (optional)" "" true

# Set permissions
chmod 600 .env

echo -e "\n${GREEN}=== Setup Complete ===${NC}"
echo -e "\nNext steps:"
echo "1. Review the .env file and update any additional settings"
echo "2. Start the services with: docker-compose up -d"
echo "3. Access the services using the URLs in the .env file"
echo -e "\nFor more information, see the documentation in the docs/ directory."
