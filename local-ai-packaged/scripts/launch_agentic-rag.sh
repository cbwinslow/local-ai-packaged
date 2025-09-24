#!/bin/bash

set -e

# Change to scripts directory
cd "$(dirname "$0")"

# Source and validate environment
source ./validate_env.sh

# Check if agentic-rag is already running on port 8000
if lsof -i :8000 > /dev/null 2>&1; then
    echo "Agentic RAG backend is already running on port 8000."
    exit 1
fi

# Note: Ensure dependencies are running
echo "Note: This script assumes neo4j, qdrant, and postgres are already running."

# Change to agentic-rag directory
cd ../agentic-knowledge-rag-graph

# Install dependencies with Poetry
poetry install

# Launch backend in background
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

echo "Agentic RAG backend launched successfully on port 8000. Logs in backend.log."