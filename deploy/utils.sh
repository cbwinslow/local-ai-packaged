#!/bin/bash
# Shared Utilities for Deployment Scripts
# Source this in other scripts: source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/utils.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global vars (override in caller)
LOG_FILE="${LOG_FILE:-/tmp/deploy.log}"

# Logging function
log() {
    local level="$1"
    shift
    local msg="$*"
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') [$level] $msg" | tee -a "$LOG_FILE"
    case "$level" in
        ERROR) echo -e "${RED}ERROR: $msg${NC}" >&2 ;;
        WARN) echo -e "${YELLOW}WARN: $msg${NC}" ;;
        INFO) echo -e "${BLUE}INFO: $msg${NC}" ;;
        SUCCESS) echo -e "${GREEN}SUCCESS: $msg${NC}" ;;
    esac
}

# Backup function
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        local backup="$file.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$file" "$backup"
        log INFO "Backed up $file to $backup"
    fi
}

# Dependency check function (enhanced validation)
check_dependency() {
    local dep="$1"
    local install_cmd="$2"
    command -v "$dep" >/dev/null 2>&1 || {
        log ERROR "$dep not found. $install_cmd"
        exit 1
    }
    log SUCCESS "$dep available"
}

# Auto-detect environment
detect_environment() {
    if command -v pct >/dev/null 2>&1; then
        echo "proxmox"
    elif command -v cloudflared >/dev/null 2>&1; then
        echo "cloudflare"
    elif command -v docker >/dev/null 2>&1; then
        echo "local"
    else
        echo "remote"
    fi
}

# Parallel execution helper (for pulls, etc.)
run_parallel() {
    local cmds=("$@")
    for cmd in "${cmds[@]}"; do
        ($cmd) &
    done
    wait
    log SUCCESS "Parallel tasks completed"
}

# Rollback helper (extendable)
rollback() {
    local target="$1"
    case "$target" in
        local) cd "$REPO_ROOT" && docker compose down -v ;;
        proxmox) pct stop "$VM_ID" && pct destroy "$VM_ID" 2>/dev/null || true ;;
        cloudflare) pkill cloudflared 2>/dev/null || true ;;
        remote) ssh -i "$SSH_KEY_PATH" "$host" "cd $DEPLOY_PATH && ./deploy/master.sh -t local --rollback" 2>/dev/null || true ;;
    esac
    log WARN "Rollback for $target complete"
}

# Self-healing: check and restart failed services (Docker example)
self_heal() {
    if [ "$TARGET" = "local" ]; then
        local failed=$(docker compose ps | grep "Exited" | awk '{print $1}')
        if [ -n "$failed" ]; then
            log WARN "Restarting failed services: $failed"
            docker compose restart $failed
        fi
    fi
}