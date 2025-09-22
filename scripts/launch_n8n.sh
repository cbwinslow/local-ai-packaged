#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep '=' | xargs)
else
    echo "Error: .env file not found."
    exit 1
fi

echo "Launching n8n service..."

# Launch n8n-import first, then n8n
docker compose -f docker-compose.yml -f docker-compose.override.private.yml up -d n8n-import

# Wait a bit for import to complete
sleep 20

echo "n8n launched. Port: 9003 (localhost)"
echo "Logs: docker compose logs -f n8n"
