#!/bin/bash

set -e

# Change to scripts directory
cd "$(dirname "$0")"

# Source and validate environment
source ./validate_env.sh

# Check if Neo4j is already running
if docker ps --filter name=neo4j --format "{{.Names}}" | grep -q "^neo4j$"; then
    echo "Neo4j container is already running."
    exit 1
fi

# Launch Neo4j
docker run -d \
    --name neo4j \
    --env-file ../.env \
    -p 7474:7474 \
    -p 7687:7687 \
    -v neo4j-data:/data \
    neo4j:5.20

echo "Neo4j launched successfully on ports 7474 (HTTP) and 7687 (Bolt)."