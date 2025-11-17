#!/bin/bash

# Health check script for Local AI Package services

echo "Local AI Package - Service Health Check"
echo "======================================"

SERVICES=("n8n" "open-webui" "ollama" "flowise" "qdrant" "localai-neo4j-1" "searxng")

for service in "${SERVICES[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "^$service$"; then
        echo "✅ $service is RUNNING"
        # Get the container ID to check more details
        CONTAINER_ID=$(docker ps -q --filter name=$service)
        if [ ! -z "$CONTAINER_ID" ]; then
            HEALTH=$(docker inspect --format='{{json .State.Health}}' $CONTAINER_ID 2>/dev/null | grep -o '"Status":"[^"]*"' | cut -d'"' -f4)
            if [ "$HEALTH" = "healthy" ] || [ "$HEALTH" = "" ]; then
                echo "   Status: HEALTHY"
            else
                echo "   Status: $HEALTH"
            fi
        fi
    else
        echo "❌ $service is NOT RUNNING"
    fi
done

echo ""
echo "Current port usage for key services:"
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "(n8n|open-webui|ollama|flowise|qdrant|neo4j)"
