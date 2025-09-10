#!/bin/bash

# AI Tools Setup Script
# This script sets up the necessary directories and permissions for AI tools

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== AI Tools Setup ===${NC}"

# Create directories
DIRS=(
    "graphite/data"
    "graphite/logs"
    "libsql_data"
    "neo4j/data"
    "neo4j/logs"
    "crewai/agents"
    "crewai/tasks"
    "letta_data"
    "falkor_data"
    "graphrag_data"
    "llama_data"
    "crawl4ai_data"
)

echo -e "${GREEN}Creating directories...${NC}"
for dir in "${DIRS[@]}"; do
    echo "Creating $dir"
    mkdir -p "$dir"
done

# Set permissions
echo -e "\n${GREEN}Setting permissions...${NC}"
chmod -R 777 graphite libsql_data neo4j letta_data falkor_data graphrag_data llama_data crawl4ai_data

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Please edit the .env file with your configuration.${NC}"
fi

# Pull latest images
echo -e "\n${GREEN}Pulling latest Docker images...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.override.ai-tools.yml pull

echo -e "\n${GREEN}=== Setup Complete ===${NC}"
echo -e "To start all services, run: ${YELLOW}./ai_tools_manager.sh start${NC}"
echo -e "For more information, see: ${YELLOW}AI_TOOLS_README.md${NC}"
