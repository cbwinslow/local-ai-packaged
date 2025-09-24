#!/bin/bash

set -e

# Change to scripts directory
cd "$(dirname "$0")"

# Source and validate environment
source ./validate_env.sh

# Check if Ollama is already running
if docker ps --filter name=ollama --format "{{.Names}}" | grep -q "^ollama$"; then
    echo "Ollama container is already running."
    exit 1
fi

# Launch Ollama
docker run -d \
    --name ollama \
    --env-file ../.env \
    -p 11434:11434 \
    ollama/ollama

# Pull the specified model
docker exec ollama ollama pull "$OLLAMA_MODEL"

echo "Ollama launched successfully on port 11434 with model $OLLAMA_MODEL."