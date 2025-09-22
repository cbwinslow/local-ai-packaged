#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep '=' | xargs)
else
    echo "Error: .env file not found."
    exit 1
fi

echo "Launching Qdrant service..."

# Launch Qdrant
docker compose -f docker-compose.yml -f docker-compose.override.private.yml up -d qdrant

echo "Qdrant launched. Port: 6333 (localhost)"
echo "Logs: docker compose logs -f qdrant"
