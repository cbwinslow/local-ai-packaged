#!/bin/bash

# fix-supabase-env.sh - Generate secure environment variables for Supabase

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Generating Supabase environment variables...${NC}"

# Generate random values
POSTGRES_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -hex 32)
ANON_KEY=$(openssl rand -hex 32)
SERVICE_ROLE_KEY=$(openssl rand -hex 32)
DASHBOARD_USERNAME="admin"
DASHBOARD_PASSWORD=$(openssl rand -base64 12)

# Timestamps for JWT expiration prevention
TIMESTAMP=$(date +%s)

# Update .env file
cat >> .env << EOF
# Supabase Secrets
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
JWT_SECRET=${JWT_SECRET}
ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvY2FsLWFpLXBhY2thZ2VkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjU2OTg3MjAsInN1YiI6ImxvY2FsLWFpLXBhY2thZ2VkIn0.$(echo -n ${ANON_KEY} | base64 | tr -d '=' | sed 's/+/-/g' | sed 's/\//_/' | cut -c1-22)
SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzIsIsInJlZiI6ImxvY2FsLWFpLXBhY2thZ2VkIiwicm9sZSI6InNlcnZpY2UiLCJpYXQiOjE3MjU2OTg3MjAsInN1YiI6ImxvY2FsLWFpLXBhY2thZ2VkIn0.$(echo -n ${SERVICE_ROLE_KEY} | base64 | tr -d '=' | sed 's/+/-/g' | sed 's/\//_/' | cut -c1-22)
DASHBOARD_USERNAME=${DASHBOARD_USERNAME}
DASHBOARD_PASSWORD=${DASHBOARD_PASSWORD}
EOF

echo -e "${GREEN}✅ Supabase environment variables generated and added to .env${NC}"

# Verify .env
if grep -q "POSTGRES_PASSWORD=" .env; then
  echo -e "${GREEN}✅ .env file updated successfully${NC}"
else
  echo -e "${RED}❌ Failed to update .env file${NC}"
  exit 1
fi

# Optional: Restart Supabase if running
if docker compose -f supabase/docker/docker-compose.yml ps | grep -q "Up"; then
  echo -e "${YELLOW}Restarting Supabase...${NC}"
  docker compose -f supabase/docker/docker-compose.yml down
  docker compose -f supabase/docker/docker-compose.yml up -d
  sleep 10
  echo -e "${GREEN}✅ Supabase restarted${NC}"
fi

echo -e "${GREEN}✅ Setup complete. Verify with: docker compose -f supabase/docker/docker-compose.yml ps${NC}"