#!/bin/bash

# update-secrets-from-bitwarden.sh - Retrieve API keys from Bitwarden and update .env
# Prerequisites: Bitwarden CLI (bw) installed and logged in (bw login)
# Usage: bash scripts/update-secrets-from-bitwarden.sh [item_search_terms...]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if Bitwarden CLI is available and logged in
if ! command -v bw &> /dev/null; then
