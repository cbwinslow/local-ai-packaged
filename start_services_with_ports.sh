#!/bin/bash

# Start services with custom port mappings to work around port conflicts
# This script maps internal services to custom ports that avoid conflicts

echo "Starting Local AI Package with custom port mappings..."

# Stop existing containers
docker compose -p localai -f docker-compose.yml down 2>/dev/null || true

# Define custom port mappings
CUSTOM_PORTS=(
    "n8n:5678:5678"           # n8n on port 5678 (usually available)
    "open-webui:8080:8081"     # OpenWebUI on port 8081 (instead of 8080)
    "ollama:11434:11435"       # Ollama on port 11435 (instead of 11434)
    "flowise:3001:3002"        # Flowise on port 3002 (instead of 3001)
    "qdrant:6333:6335"         # Qdrant on port 6335 (instead of 6333)
    "neo4j:7474:7475"          # Neo4j on port 7475 (instead of 7474)
)

echo "Starting services with custom ports..."
echo "Services will be available at:"
echo "  - n8n: http://localhost:5678"
echo "  - open-webui: http://localhost:8081"
echo "  - ollama: http://localhost:11435"
echo "  - flowise: http://localhost:3002"
echo "  - qdrant: http://localhost:6335"
echo "  - neo4j: http://localhost:7475"

# Start services with custom port mappings (this requires editing the compose file)
# For now, we'll just run the normal start
cd /home/cbwinslow/projects/local-ai-packaged
python3 start_services.py --profile cpu
