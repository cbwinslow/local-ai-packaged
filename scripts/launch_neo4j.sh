#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep '=' | xargs)
else
    echo "Error: .env file not found."
    exit 1
fi

echo "Launching Neo4J service..."

# Neo4J is not in the main compose, so use docker run for community edition
docker run -d \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -v $PWD/neo4j/data:/data \
    -e "NEO4J_AUTH=$NEO4J_USER/$NEO4J_PASSWORD" \
    -e "NEO4J_dbms.security.procedures.unrestricted=apoc.*" \
    neo4j:5.22.0-community

echo "Neo4J launched. Browser: http://localhost:7474 (user: neo4j, pass from .env)"
echo "Bolt port: 7687"
echo "Logs: docker logs -f neo4j"
