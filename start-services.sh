#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: .env file not found. Please run traefik/update-env.sh first."
    exit 1
fi

# Create the traefik-public network if it doesn't exist
if ! docker network ls | grep -q traefik-public; then
    echo "Creating traefik-public network..."
    docker network create traefik-public
else
    echo "traefik-public network already exists, skipping creation."
fi

# Create necessary directories
mkdir -p traefik/letsencrypt traefik/logs traefik/config/dynamic

# Set proper permissions for Let's Encrypt
chmod 600 traefik/letsencrypt || true

# Start all services
echo "Starting all services with Docker Compose..."
docker-compose -f docker-compose.traefik.yml -f docker-compose.yml up -d

echo ""
echo "All services have been started!"
echo ""
echo "Access the services at:"
echo "- Traefik Dashboard: https://traefik.opendiscourse.net"
echo "- Supabase: https://supabase.opendiscourse.net"
echo "- n8n: https://n8n.opendiscourse.net"
echo "- Flowise: https://flowise.opendiscourse.net"
echo "- Web UI: https://webui.opendiscourse.net"
echo "- Neo4j: https://neo4j.opendiscourse.net"
echo ""
echo "Note: It may take a few minutes for all services to be fully available."
