#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep '=' | xargs)
else
    echo "Error: .env file not found."
    exit 1
fi

echo "Launching Ollama service..."

# Launch Ollama CPU version (default for local)
docker compose -f docker-compose.yml -f docker-compose.override.private.yml up -d ollama-cpu

echo "Ollama launched. Port: 9019 (localhost)"
echo "Logs: docker compose logs -f ollama-cpu"
echo "To use GPU, edit script to use ollama-gpu instead"
