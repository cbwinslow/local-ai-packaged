#!/bin/bash

# fix-supabase-env.sh - Secure environment variable generation
# This script is deprecated in favor of scripts/generate-secrets.sh
# It now calls the comprehensive secret generation script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}⚠️  This script is deprecated. Redirecting to comprehensive secret generation...${NC}"
echo -e "${BLUE}📝 Using scripts/generate-secrets.sh for secure secret generation${NC}"
echo ""

# Check if the comprehensive script exists
if [[ -f "scripts/generate-secrets.sh" ]]; then
    echo -e "${GREEN}✅ Found comprehensive secret generation script${NC}"
    echo -e "${BLUE}🚀 Executing scripts/generate-secrets.sh...${NC}"
    echo ""
    
    # Make sure it's executable
    chmod +x scripts/generate-secrets.sh
    
    # Execute the comprehensive script
    ./scripts/generate-secrets.sh "$@"
    
    echo ""
    echo -e "${GREEN}✅ Secret generation completed via comprehensive script${NC}"
    echo -e "${BLUE}ℹ️  For future use, run: ./scripts/generate-secrets.sh${NC}"
    
else
    echo -e "${RED}❌ Comprehensive secret generation script not found${NC}"
    echo -e "${YELLOW}💡 Please ensure scripts/generate-secrets.sh exists${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 All environment variables have been securely generated!${NC}"