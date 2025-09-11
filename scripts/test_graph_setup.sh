#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print section headers
section() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

# Function to print success message
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error message
error() {
    echo -e "${RED}❌ $1${NC}"
}

section "Setting up and testing graph databases"

# Check if .env file exists
if [ ! -f .env ]; then
    error ".env file not found. Please create one from .env.example"
    exit 1
fi

# Load environment variables
section "Loading environment variables"
set -a
# shellcheck source=/dev/null
source .env
set +a

# Install required Python packages
section "Installing required Python packages"
pip install -r scripts/requirements-graph-test.txt

# Start the services
section "Starting Docker services"
docker compose -f docker-compose.mcp.yml up -d neo4j memgraph

# Wait for services to be ready
section "Waiting for services to be ready"
sleep 10

# Test Neo4j connection
section "Testing Neo4j connection"
if docker exec -i neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD}" --address=bolt://localhost:17687 "SHOW DATABASES;" &> /dev/null; then
    success "Neo4j connection successful"
    
    # Test basic operations
    section "Testing Neo4j operations"
    if docker exec -i neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD}" --address=bolt://localhost:17687 "
        CREATE (n:TestNode {name: 'Test', value: 123});
        MATCH (n:TestNode) RETURN n;
        MATCH (n:TestNode) DELETE n;
    " &> /dev/null; then
        success "Neo4j operations successful"
    else
        error "Neo4j operations failed"
    fi
else
    error "Neo4j connection failed"
fi

# Test Memgraph connection
section "Testing Memgraph connection"
if docker exec -i memgraph mgconsole --use-ssl=False --host=localhost --port=17688 --username='' --password='' --command="SHOW STORAGE INFO;" &> /dev/null; then
    success "Memgraph connection successful"
    
    # Test basic operations
    section "Testing Memgraph operations"
    if docker exec -i memgraph mgconsole --use-ssl=False --host=localhost --port=17688 --username='' --password='' --command="
        CREATE (n:TestNode {name: 'Test', value: 123});
        MATCH (n:TestNode) RETURN n;
        MATCH (n:TestNode) DELETE n;
    " &> /dev/null; then
        success "Memgraph operations successful"
    else
        error "Memgraph operations failed"
    fi
else
    error "Memgraph connection failed"
fi

# Run Python tests
section "Running Python tests"
python3 scripts/test_graph_connections.py

# Print connection details
section "Test complete"
echo -e "${GREEN}Neo4j Browser: http://localhost:17474"
echo "Neo4j Bolt: bolt://localhost:17687"
echo "Memgraph Lab: http://localhost:13000"
echo "Memgraph Bolt: bolt://localhost:17688"
echo "Memgraph Query Monitoring: http://localhost:17444${NC}"
