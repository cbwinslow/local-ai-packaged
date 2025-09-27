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

# log writes a timestamped, level-prefixed message to LOG_FILE and prints a colorized, level-prefixed message to stdout (sent to stderr when level is ERROR).
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

# backup_file creates a timestamped backup of the given file (appends `.backup.YYYYMMDD_HHMMSS`) if the file exists.
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        local backup="$file.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$file" "$backup"
        log INFO "Backed up $file to $backup"
    fi
}

# check_dependency verifies that a command is available; logs an error with an installation hint and exits if the command is missing, otherwise logs success.
check_dependency() {
    local dep="$1"
    local install_cmd="$2"
    command -v "$dep" >/dev/null 2>&1 || {
        log ERROR "$dep not found. $install_cmd"
        exit 1
    }
    log SUCCESS "$dep available"
}

# detect_environment detects the deployment environment and echoes one of: "proxmox" (if `pct` is available), "cloudflare" (if `cloudflared` is available), "local" (if `docker` is available), or "remote" otherwise.
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

# run_parallel runs multiple commands concurrently, waits for all to finish, and logs completion.
run_parallel() {
    local cmds=("$@")
    for cmd in "${cmds[@]}"; do
        ($cmd) &
    done
    wait
    log SUCCESS "Parallel tasks completed"
}

# rollback performs environment-specific rollback actions for the given target (local, proxmox, cloudflare, remote) and logs completion.
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

# self_heal checks for Docker services with status 'Exited' when TARGET is "local" and restarts any found, logging a WARN message.
self_heal() {
    if [ "$TARGET" = "local" ]; then
        local failed=$(docker compose ps | grep "Exited" | awk '{print $1}')
        if [ -n "$failed" ]; then
            log WARN "Restarting failed services: $failed"
            docker compose restart $failed
        fi
    fi
}