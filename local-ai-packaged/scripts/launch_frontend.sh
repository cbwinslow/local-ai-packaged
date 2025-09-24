#!/bin/bash

set -e

# Change to scripts directory
cd "$(dirname "$0")"

# Source and validate environment
source ./validate_env.sh

# Check if frontend is already running on port 3000
if lsof -i :3000 > /dev/null 2>&1; then
    echo "Frontend is already running on port 3000."
    exit 1
fi

# Note: Ensure backend is running before launching frontend
echo "Note: This script assumes the backend (agentic-rag) is already running on port 8000."

# Change to frontend directory
cd ../frontend

# Install dependencies
npm ci

# Launch frontend in background
nohup npm run dev -- -p 3000 > frontend.log 2>&1 &

echo "Frontend launched successfully on port 3000. Logs in frontend.log."