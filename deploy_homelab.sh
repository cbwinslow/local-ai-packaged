#!/bin/bash
# Deploy to Homelab Server via Tailscale IP 100.90.23.59
# Usage: bash deploy_homelab.sh [pull|up|down]

SERVER_IP="100.90.23.59"
PROJECT_DIR="/opt/local-ai-packaged"

case "$1" in
  pull)
    echo "Pulling latest code to server..."
    ssh $SERVER_IP "cd $PROJECT_DIR && git pull origin main"
    ;;
  up)
    echo "Deploying and starting on server..."
    ssh $SERVER_IP "cd $PROJECT_DIR && ./scripts/enhanced-generate-secrets.sh && docker compose up -d --build"
    ;;
  down)
    echo "Stopping on server..."
    ssh $SERVER_IP "cd $PROJECT_DIR && docker compose down -v"
    ;;
  *)
    echo "Usage: bash deploy_homelab.sh [pull|up|down]"
    exit 1
    ;;
esac
