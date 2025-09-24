#!/bin/zsh
# Launch Qdrant service for Local AI Packaged

set -e

# Validate env
source ../validate_env.sh || exit 1

# Run Qdrant container
docker run -d \
  --name local-ai-qdrant \
  -p 6333:6333 \
  -e QDRANT__SERVICE__API_KEY=$QDRANT_API_KEY \
  -v qdrant-data:/qdrant/storage \
  qdrant/qdrant:latest

echo "Qdrant launched on port 6333..."
sleep 5
docker logs local-ai-qdrant

# Health check
if curl -f http://localhost:6333/healthz; then
  echo "✓ Qdrant ready (dashboard at http://localhost:6333/dashboard)."
else
  echo "✗ Qdrant not ready. Check logs."
  exit 1
fi