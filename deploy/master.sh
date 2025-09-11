#!/bin/bash
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/utils.sh"
# Master Deployment Script for Local AI Packaged Repository
# Unified script integrating all deployment options: local, Proxmox, Cloudflare, remote server.
# Usage: ./deploy/master.sh [-t target] [-c config.json] [-i] [-d] [-h]
# Targets: local (default, Docker Compose), proxmox (VM provisioning), cloudflare (tunnel + DNS), remote (SSH deploy)
# Requires: bash, jq (for JSON config), docker (local), pct/qm (Proxmox), cloudflared (Cloudflare), ssh/rsync (remote)

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Defaults
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_FILE="${CONFIG_FILE:-$SCRIPT_DIR/config.json}"
TARGET="${TARGET:-$(detect_environment)}"
INTERACTIVE=false
DRY_RUN=false
LOG_FILE="$REPO_ROOT/deploy_$(date +%Y%m%d_%H%M%S).log"

# Execute pre/post deploy hooks from config
execute_pre_post_hooks() {
    local phase="$1"  # pre_deploy or post_deploy
    local hooks=$(echo "$TARGET_CONFIG" | jq -r ".${phase} // empty" | jq -r '.[]')
    if [ -z "$hooks" ]; then
        log INFO "No $phase hooks defined for $TARGET"
        return
    fi
    log INFO "Executing $phase hooks..."
    echo "$hooks" | while IFS= read -r hook; do
        if [ -n "$hook" ]; then
            log INFO "Running: $hook"
            if [ "$DRY_RUN" = true ]; then
                log INFO "[DRY RUN] Skipped: $hook"
            else
                eval "$hook" || log WARN "Hook '$hook' failed, continuing..."
            fi
        fi
    done
}

# Validate dependencies (using utils)
validate_deps() {
    log INFO "Validating dependencies..."
    check_dependency "jq" "Install with: sudo apt install jq"
    case "$TARGET" in
        local)
            check_dependency "docker" "Install Docker: https://docs.docker.com/engine/install/"
            check_dependency "docker compose" "Install Docker Compose plugin: sudo apt install docker-compose-plugin"
            ;;
        proxmox)
            check_dependency "pct" "Install Proxmox tools on host"
            check_dependency "qm" "Install Proxmox tools on host"
            ;;
        cloudflare)
            check_dependency "cloudflared" "Download from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/local/"
            ;;
        remote)
            check_dependency "ssh" "OpenSSH is required"
            check_dependency "rsync" "Install rsync: sudo apt install rsync"
            ;;
    esac
    log SUCCESS "Dependencies validated"
}

# Load config (JSON)
load_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log ERROR "Config file $CONFIG_FILE not found. Create from config.example.json."
        exit 1
    fi
    # Load target-specific config
    TARGET_CONFIG=$(jq -r ".environments[\"$TARGET\"]" "$CONFIG_FILE")
    if [ "$TARGET_CONFIG" = "null" ]; then
        log ERROR "No config for target '$TARGET' in $CONFIG_FILE"
        exit 1
    fi
    # Export key vars from config (e.g., host, user, etc.)
    eval "$(echo "$TARGET_CONFIG" | jq -r 'to_entries | map("\(.key | ascii_upcase)=\(.value | tostring)") | join("\n")')"
    # Source .env as fallback for global secrets
    if [ -f "$REPO_ROOT/.env" ]; then
        source "$REPO_ROOT/.env"
        log INFO "Loaded .env config"
    fi
    log SUCCESS "Config loaded for $TARGET from $CONFIG_FILE"
}

# Interactive mode
interactive_setup() {
    if [ "$INTERACTIVE" = true ]; then
        log INFO "Interactive mode enabled"
        echo -e "${YELLOW}Select target environment:${NC}"
        echo "1) local (Docker Compose)"
        echo "2) proxmox (VM on Proxmox)"
        echo "3) cloudflare (Tunnel + local services)"
        echo "4) remote (SSH to server)"
        read -p "Choice (1-4) [default:1]: " choice
        case "$choice" in
            2) TARGET="proxmox" ;;
            3) TARGET="cloudflare" ;;
            4) TARGET="remote" ;;
            *) TARGET="local" ;;
        esac
        # Prompt for config values if needed, e.g., Proxmox IP, Cloudflare token, remote host
        case "$TARGET" in
            proxmox)
                read -p "Proxmox host IP: " PROXMOX_HOST
                read -s -p "Proxmox password: " PROXMOX_PASS
                ;;
            cloudflare)
                read -s -p "Cloudflare API token: " CF_TOKEN
                ;;
            remote)
                read -p "Remote host (user@ip): " REMOTE_HOST
                read -s -p "SSH private key path [~/.ssh/id_rsa]: " SSH_KEY
                SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}
                ;;
        esac
    fi
}

# Deploy functions (modular, integrate existing scripts)

# Local deployment (config-driven with Docker Compose)
deploy_local() {
    log INFO "Starting local deployment..."
    # Backup key files
    backup_file "$REPO_ROOT/.env"
    backup_file "$REPO_ROOT/docker-compose.yml"
    # Execute pre_deploy hooks (e.g., setup_env.sh)
    execute_pre_post_hooks "pre_deploy"
    # Core deployment
    cd "$REPO_ROOT"
    if [ "$DRY_RUN" = false ]; then
        local services=$(echo "$TARGET_CONFIG" | jq -r '.services | join(" ")')
        run_parallel "docker compose pull $services" "docker compose build --pull $services"  # Parallel pull/build if needed
        docker compose up -d $services
    fi
    # Execute post_deploy hooks (e.g., deploy-legislative-ai.sh)
    execute_pre_post_hooks "post_deploy"
    # Basic health check
    sleep 30
    if docker compose ps | grep -q "running"; then
        log SUCCESS "Local services up"
    else
        log ERROR "Some services failed to start"
        docker compose logs
        exit 1
    fi
}

# Proxmox deployment (provision VM, config-driven)
deploy_proxmox() {
    log INFO "Starting Proxmox deployment..."
    local VM_ID=$(pct nextid)
    local VM_NAME="local-ai-$(date +%s)"
    # Use config for resources/template
    local MEMORY=$(echo "$TARGET_CONFIG" | jq -r '.vm_resources.memory')
    local CORES=$(echo "$TARGET_CONFIG" | jq -r '.vm_resources.cores')
    local DISK=$(echo "$TARGET_CONFIG" | jq -r '.vm_resources.disk')
    local TEMPLATE=$(echo "$TARGET_CONFIG" | jq -r '.vm_template')
    local NETWORK=$(echo "$TARGET_CONFIG" | jq -r '.network')
    # Create LXC (or qm for KVM)
    pct create "$VM_ID" "$TEMPLATE" \
        --hostname "$VM_NAME" \
        --memory "$MEMORY" \
        --cores "$CORES" \
        --net0 "name=eth0,bridge=$NETWORK,ip=dhcp" \
        --rootfs "local-lvm:$DISK" \
        --unprivileged 1
    pct start "$VM_ID"
    sleep 60
    # Pre-deploy hooks inside VM (e.g., install deps)
    pct exec "$VM_ID" -- bash -c "$(echo "$TARGET_CONFIG" | jq -r '.pre_deploy[] | "\(.)\;"' | tr -d '\n')"
    # Rsync repo
    rsync -avz --delete "$REPO_ROOT/" "root@$host:/opt/local-ai/"  # Use config host/user
    # Post-deploy: recursive master.sh
    pct exec "$VM_ID" -- bash -c "$(echo "$TARGET_CONFIG" | jq -r '.post_deploy[]')"
    log SUCCESS "Proxmox VM $VM_ID deployed at $host"
}

# Cloudflare deployment (local + tunnel, config-driven)
deploy_cloudflare() {
    log INFO "Starting Cloudflare deployment..."
    deploy_local  # Base local deploy
    local TUNNEL_NAME=$(echo "$TARGET_CONFIG" | jq -r '.tunnel_name')
    cloudflared tunnel create "$TUNNEL_NAME" || true
    local TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
    local HOSTNAME=$(echo "$TARGET_CONFIG" | jq -r '.host')
    cloudflared tunnel route dns "$TUNNEL_ID" "$HOSTNAME"
    # Generate config from ingress_rules
    local CONFIG_CONTENT=$(echo "$TARGET_CONFIG" | jq -r --arg tid "$TUNNEL_ID" '
        "tunnel: \($tid)\ncredentials-file: /root/.cloudflared/\($tid).json\ningress:\n" +
        (.ingress_rules | map("- hostname: \(.hostname)\n  service: \(.service)") | join("\n")) +
        "\n- service: http_status:404"
    ')
    echo -e "$CONFIG_CONTENT" > ~/.cloudflared/config.yml
    # Run tunnel
    nohup cloudflared tunnel --config ~/.cloudflared/config.yml run "$TUNNEL_ID" > /var/log/cloudflared.log 2>&1 &
    # Post hooks
    execute_pre_post_hooks "post_deploy"
    log SUCCESS "Cloudflare tunnel active on $HOSTNAME"
}

# Remote deployment (rsync + SSH, config-driven)
deploy_remote() {
    log INFO "Starting remote deployment..."
    local DEPLOY_PATH=$(echo "$TARGET_CONFIG" | jq -r '.deploy_path')
    local SSH_KEY_PATH=$(echo "$TARGET_CONFIG" | jq -r '.ssh_key')
    # Rsync repo
    rsync -avz --delete -e "ssh -i $SSH_KEY_PATH" "$REPO_ROOT/" "$host:$DEPLOY_PATH/"
    # Pre-deploy via SSH
    ssh -i "$SSH_KEY_PATH" "$host" "$(echo "$TARGET_CONFIG" | jq -r '.pre_deploy[] | "\(.)\;"' | tr -d '\n')"
    # Run master.sh recursively
    ssh -i "$SSH_KEY_PATH" "$host" "cd $DEPLOY_PATH && ./deploy/master.sh -t local -c config.json --non-interactive"
    # Post-deploy
    ssh -i "$SSH_KEY_PATH" "$host" "$(echo "$TARGET_CONFIG" | jq -r '.post_deploy[] | "\(.)\;"' | tr -d '\n')"
    log SUCCESS "Remote deployment to $host complete"
}

# Rollback (using utils)
rollback() {
    log WARN "Rolling back deployment for $TARGET..."
    ::rollback "$TARGET"
    log INFO "Rollback complete"
}

# Main CLI parsing
while getopts "t:c:idhn" opt; do
    case $opt in
        t) TARGET="$OPTARG" ;;
        c) CONFIG_FILE="$OPTARG" ;;
        i) INTERACTIVE=true ;;
        d) DRY_RUN=true; log INFO "Dry run mode" ;;
        n) NON_INTERACTIVE=true ;;  # For recursive calls
        h)
            echo "Usage: $0 [-t target] [-c config.json] [-i interactive] [-d dry-run] [-n non-interactive] [-h help]"
            echo "Targets: local, proxmox, cloudflare, remote"
            echo "Example: $0 -t local -c deploy/config.json"
            echo "One-click: $0  # defaults to local"
            exit 0 ;;
        \?) log ERROR "Invalid option: -$OPTARG"; exit 1 ;;
    esac
done

# Skip interactive if non-interactive
if [ "$NON_INTERACTIVE" = true ]; then
    INTERACTIVE=false
fi

# Trap for rollback on error
trap 'log ERROR "Deployment failed. Attempting rollback..."; rollback; exit 1' ERR

# Run phases
log INFO "Starting master deployment for target: $TARGET"
validate_deps
load_config
interactive_setup

# Execute target-specific deploy
case "$TARGET" in
    local) deploy_local ;;
    proxmox) deploy_proxmox ;;
    cloudflare) deploy_cloudflare ;;
    remote) deploy_remote ;;
    *) log ERROR "Unknown target: $TARGET"; exit 1 ;;
esac

# Post-deployment verification (config-driven health checks)
run_health_checks() {
    log INFO "Running health checks..."
    sleep 10
    if [ "$DRY_RUN" = false ]; then
        local health_checks=$(echo "$TARGET_CONFIG" | jq -r '.health_checks // {} | to_entries[] | "\(.key): \(.value)"')
        if [ -n "$health_checks" ]; then
            echo "$health_checks" | while IFS=: read -r service check; do
                log INFO "Checking $service..."
                if eval "$check"; then
                    log SUCCESS "$service healthy"
                else
                    log ERROR "$service unhealthy"
                    rollback
                    exit 1
                fi
            done
        else
            # Fallback basic check
            case "$TARGET" in
                local) docker compose ps | grep -q running || { log ERROR "Services not running"; rollback; exit 1; } ;;
                proxmox) pct status "$VM_ID" | grep -q running || { log ERROR "VM not running"; rollback; exit 1; } ;;
                cloudflare) pgrep cloudflared >/dev/null || { log ERROR "Tunnel not running"; rollback; exit 1; } ;;
                remote) ssh -i "$SSH_KEY_PATH" "$host" "docker ps | grep Up" || { log ERROR "Remote services not up"; rollback; exit 1; } ;;
            esac
        fi
        log SUCCESS "All health checks passed"
    fi
}

run_health_checks

# Self-heal if enabled
self_heal

log SUCCESS "Deployment complete! Logs: $LOG_FILE"
echo -e "${GREEN}Access your deployment:${NC}"
case "$TARGET" in
    local) echo "  - Frontend: http://localhost:3000" ;;
    proxmox) echo "  - VM Console: https://$PROXMOX_HOST:8006" ;;
    cloudflare) echo "  - Via tunnel: https://${CF_DOMAIN:-localai.example.com}" ;;
    remote) echo "  - On $REMOTE_HOST: ssh $REMOTE_HOST" ;;
esac