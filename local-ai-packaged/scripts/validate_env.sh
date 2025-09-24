#!/bin/bash

# Validate required environment variables for the RAG platform
# Source the .env file and check if all required vars are set

set -euo pipefail

# Source the .env file
if [[ -f .env ]]; then
    source .env
else
    echo "Error: .env file not found. Please create .env from .env.example."
    exit 1
fi

# List of required environment variables
required_vars=(
    POSTGRES_PASSWORD
    POSTGRES_DB
    POSTGRES_USER
    NEO4J_PASSWORD
    QDRANT_URL
    OLLAMA_MODEL
    OLLAMA_HOST
    OLLAMA_PORT
    N8N_BASIC_AUTH_USER
    N8N_BASIC_AUTH_PASSWORD
    SUPABASE_URL
    SUPABASE_ANON_KEY
    SUPABASE_SERVICE_ROLE_KEY
    SECRET_KEY
)

# Function to check if a variable is set
check_var() {
    local var_name="$1"
    if [[ -z "${!var_name:-}" ]]; then
        echo "Error: Required environment variable '$var_name' is not set in .env"
        exit 1
    fi
}

# Check each required variable
for var in "${required_vars[@]}"; do
    check_var "$var"
done

echo "All required environment variables are set correctly."