#!/bin/bash

set -e

# Change to scripts directory
cd "$(dirname "$0")"

# Source and validate environment
source ./validate_env.sh

# Check if n8n is already running
if docker ps --filter name=n8n --format "{{.Names}}" | grep -q "^n8n$"; then
    echo "n8n container is already running."
    exit 1
fi

# Launch n8n
docker run -d \
    --name n8n \
    --env-file ../.env \
    -p 5678:5678 \
    n8nio/n8n

echo "n8n launched successfully on port 5678."