acon#!/bin/bash
set -e

# Load environment variables from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep '=' | xargs)
else
    echo "Error: .env file not found."
    exit 1
fi

echo "Launching Postgres service..."

# Launch Postgres using Docker Compose with private override
docker compose -f docker-compose.yml -f docker-compose.override.private.yml up -d postgres

echo "Postgres launched. Port: 5433 (localhost)"
echo "Logs: docker compose logs -f postgres"
