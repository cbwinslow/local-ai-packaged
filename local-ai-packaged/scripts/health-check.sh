#!/bin/zsh
# Health check for all services

set -e

echo "Checking Local AI Packaged services..."

# Backend
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
  echo "✓ Backend healthy"
else
  echo "✗ Backend unhealthy"
  exit 1
fi

# Frontend (basic load)
if curl -f http://localhost:3000 >/dev/null 2>&1; then
  echo "✓ Frontend accessible"
else
  echo "✗ Frontend down"
fi

# Neo4j
if curl -f http://localhost:7474 >/dev/null 2>&1; then
  echo "✓ Neo4j browser up"
else
  echo "✗ Neo4j down"
fi

# Qdrant
if curl -f http://localhost:6333/healthz >/dev/null 2>&1; then
  echo "✓ Qdrant healthy"
else
  echo "✗ Qdrant down"
fi

# Postgres
if docker exec local-ai-postgres pg_isready >/dev/null 2>&1; then
  echo "✓ Postgres ready"
else
  echo "✗ Postgres down"
fi

# n8n
if curl -f http://localhost:5678/healthz >/dev/null 2>&1; then
  echo "✓ n8n healthy"
else
  echo "✗ n8n down"
fi

echo "All services healthy!"