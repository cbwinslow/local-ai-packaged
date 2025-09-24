#!/bin/bash

set -e

# Change to scripts directory
cd "$(dirname "$0")"

# Source and validate environment
source ./validate_env.sh

# Check if Postgres is already running
if docker ps --filter name=postgres --format "{{.Names}}" | grep -q "^postgres$"; then
    echo "Postgres container is already running."
    exit 1
fi

# Launch Postgres
docker run -d \
    --name postgres \
    --env-file ../.env \
    -p 5432:5432 \
    -v postgres-data:/var/lib/postgresql/data \
    supabase/postgres:15.1.0.147

echo "Postgres launched successfully on port 5432."