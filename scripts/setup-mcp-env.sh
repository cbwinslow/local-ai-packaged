#!/bin/bash

# This script sets up the environment variables needed for MCP services

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Generate random passwords if not set
if ! grep -q "NEO4J_PASSWORD=" .env; then
    echo "NEO4J_PASSWORD=$(openssl rand -base64 32)" >> .env
fi

if ! grep -q "VECTORIZE_API_KEY=" .env; then
    echo "VECTORIZE_API_KEY=$(openssl rand -hex 32)" >> .env
fi

# Prompt for required API keys
if ! grep -q "CONGRESS_GOV_API_KEY=" .env; then
    echo "CONGRESS_GOV_API_KEY=your_congress_gov_api_key_here" >> .env
    echo "Please update CONGRESS_GOV_API_KEY in the .env file"
fi

if ! grep -q "STACKHAWK_API_KEY=" .env; then
    echo "STACKHAWK_API_KEY=your_stackhawk_api_key_here" >> .env
    echo "Please update STACKHAWK_API_KEY in the .env file"
fi

if ! grep -q "PINECONE_API_KEY=" .env; then
    echo "PINECONE_API_KEY=your_pinecone_api_key_here" >> .env
    echo "Please update PINECONE_API_KEY in the .env file"
fi

if ! grep -q "PINECONE_ENVIRONMENT=" .env; then
    echo "PINECONE_ENVIRONMENT=your_pinecone_environment" >> .env
    echo "Please update PINECONE_ENVIRONMENT in the .env file"
fi

if ! grep -q "PINECONE_INDEX=" .env; then
    echo "PINECONE_INDEX=your_pinecone_index" >> .env
    echo "Please update PINECONE_INDEX in the .env file"
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

echo "MCP environment setup complete. Please review the .env file and update the API keys as needed."
