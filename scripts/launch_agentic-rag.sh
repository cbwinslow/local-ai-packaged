#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep '=' | xargs)
else
    echo "Error: .env file not found."
    exit 1
fi

echo "Launching agentic-rag service..."

# Launch agentic-rag
docker compose -f docker-compose.yml -f docker-compose.override.private.yml up -d agentic-rag

echo "Agentic RAG launched. Port: 8000 (localhost)"
echo "Logs: docker compose logs -f agentic-rag"
