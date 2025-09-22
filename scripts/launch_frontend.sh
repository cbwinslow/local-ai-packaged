#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep '=' | xargs)
else
    echo "Error: .env file not found."
    exit 1
fi

echo "Launching frontend..."

# Launch frontend
docker compose -f docker-compose.yml -f docker-compose.override.private.yml up -d frontend

echo "Frontend launched. Port: 3000 (localhost)"
echo "Logs: docker compose logs -f frontend"
