#!/bin/bash

# =============================================================================
# Production-Grade Backup and Restore System for Local AI Package
# =============================================================================
# This script provides industry-standard backup and restore capabilities
# with support for cloud storage (Cloudflare R2, Oracle OCI, Azure Blob)
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="${PWD}/backups"
VOLUMES_DIR="${PWD}/volumes"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE=$(date +%Y%m%d)

# Load environment variables if available
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

show_usage() {
    echo -e "${BLUE}Local AI Package - Backup & Restore System${NC}"
    echo -e "${BLUE}============================================================================${NC}"
    echo
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 backup [full|incremental|databases|volumes]"
    echo "  $0 restore <backup_file> [--confirm]"
    echo "  $0 list"
    echo "  $0 clean [--older-than-days=30]"
    echo "  $0 cloud-backup [cloudflare|oracle|azure]"
    echo "  $0 cloud-restore <provider> <backup_name>"
    echo
    echo -e "${YELLOW}Commands:${NC}"
    echo "  backup          Create a backup (default: full)"
    echo "  restore         Restore from a backup file"
    echo "  list            List available backups"
    echo "  clean           Clean old backups"
    echo "  cloud-backup    Upload backup to cloud storage"
    echo "  cloud-restore   Download and restore from cloud"
    echo
    echo -e "${YELLOW}Backup Types:${NC}"
    echo "  full            Complete system backup (all data + config)"
    echo "  incremental     Only changed files since last backup"
    echo "  databases       Only database files"
    echo "  volumes         Only Docker volumes"
    echo
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 backup full"
    echo "  $0 restore backup_20240101_120000.tar.gz --confirm"
    echo "  $0 cloud-backup cloudflare"
    echo "  $0 clean --older-than-days=7"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if running as appropriate user
    if [ "$EUID" -eq 0 ]; then
        log_warning "Running as root - this may cause permission issues"
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running or not accessible"
        exit 1
    fi
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly,manual}
    
    log_success "Prerequisites check passed"
}

get_backup_size() {
    local backup_file="$1"
    if [ -f "$backup_file" ]; then
        du -h "$backup_file" | cut -f1
    else
        echo "Unknown"
    fi
}

# =============================================================================
# BACKUP FUNCTIONS
# =============================================================================

backup_databases() {
    local backup_path="$1"
    log_info "Backing up databases..."
    
    mkdir -p "$backup_path/databases"
    
    # PostgreSQL backup
    if docker ps --format '{{.Names}}' | grep -q postgres; then
        log_info "Backing up PostgreSQL..."
        docker exec postgres pg_dumpall -U postgres > "$backup_path/databases/postgres_dump_$TIMESTAMP.sql"
        log_success "PostgreSQL backup completed"
    fi
    
    # Neo4j backup
    if docker ps --format '{{.Names}}' | grep -q neo4j; then
        log_info "Backing up Neo4j..."
        docker exec neo4j neo4j-admin database dump neo4j --to-path=/tmp/
        docker cp neo4j:/tmp/neo4j.dump "$backup_path/databases/neo4j_dump_$TIMESTAMP.dump"
        log_success "Neo4j backup completed"
    fi
    
    # Supabase backup
    if docker ps --format '{{.Names}}' | grep -q supabase-db; then
        log_info "Backing up Supabase..."
        docker exec supabase-db pg_dumpall -U postgres > "$backup_path/databases/supabase_dump_$TIMESTAMP.sql"
        log_success "Supabase backup completed"
    fi
    
    # Redis/Valkey backup
    if docker ps --format '{{.Names}}' | grep -q redis; then
        log_info "Backing up Redis/Valkey..."
        docker exec redis redis-cli --rdb /tmp/redis_backup.rdb
        docker cp redis:/tmp/redis_backup.rdb "$backup_path/databases/redis_backup_$TIMESTAMP.rdb"
        log_success "Redis backup completed"
    fi
}

backup_volumes() {
    local backup_path="$1"
    log_info "Backing up Docker volumes..."
    
    mkdir -p "$backup_path/volumes"
    
    # Use tar with compression for volume backup
    if [ -d "$VOLUMES_DIR" ]; then
        tar -czf "$backup_path/volumes/docker_volumes_$TIMESTAMP.tar.gz" -C "$VOLUMES_DIR" .
        log_success "Docker volumes backed up"
    else
        log_warning "Volumes directory not found: $VOLUMES_DIR"
    fi
}

backup_configuration() {
    local backup_path="$1"
    log_info "Backing up configuration files..."
    
    mkdir -p "$backup_path/config"
    
    # Backup docker-compose files
    cp docker-compose*.yml "$backup_path/config/" 2>/dev/null || true
    cp .env.example "$backup_path/config/" 2>/dev/null || true
    
    # Backup Supabase config
    if [ -d "supabase" ]; then
        cp -r supabase "$backup_path/config/"
    fi
    
    # Backup MCP server configs
    if [ -d "mcp-servers" ]; then
        find mcp-servers -name "*.json" -o -name "*.yml" -o -name "*.yaml" | xargs cp --parents -t "$backup_path/config/" 2>/dev/null || true
    fi
    
    # Backup scripts
    if [ -d "scripts" ]; then
        cp -r scripts "$backup_path/config/"
    fi
    
    log_success "Configuration files backed up"
}

backup_full() {
    local backup_type="${1:-manual}"
    local backup_name="full_backup_$TIMESTAMP"
    local backup_path="$BACKUP_DIR/$backup_type/$backup_name"
    
    log_info "Starting full backup to: $backup_path"
    
    mkdir -p "$backup_path"
    
    # Create backup metadata
    cat > "$backup_path/backup_info.json" << EOF
{
    "backup_type": "full",
    "timestamp": "$TIMESTAMP",
    "date": "$DATE",
    "hostname": "$(hostname)",
    "docker_version": "$(docker --version)",
    "backup_script_version": "2.0.0"
}
EOF
    
    # Backup databases
    backup_databases "$backup_path"
    
    # Backup volumes
    backup_volumes "$backup_path"
    
    # Backup configuration
    backup_configuration "$backup_path"
    
    # Create compressed archive
    log_info "Creating compressed archive..."
    cd "$BACKUP_DIR/$backup_type"
    tar -czf "${backup_name}.tar.gz" "$backup_name"
    rm -rf "$backup_name"
    
    local backup_size=$(get_backup_size "${backup_name}.tar.gz")
    log_success "Full backup completed: ${backup_name}.tar.gz (${backup_size})"
    
    # Create symlink to latest backup
    ln -sf "${backup_name}.tar.gz" "latest_full_backup.tar.gz"
    
    echo "$BACKUP_DIR/$backup_type/${backup_name}.tar.gz"
}

backup_incremental() {
    local backup_type="${1:-manual}"
    local backup_name="incremental_backup_$TIMESTAMP"
    local backup_path="$BACKUP_DIR/$backup_type/$backup_name"
    local last_backup_file="$BACKUP_DIR/$backup_type/latest_full_backup.tar.gz"
    
    log_info "Starting incremental backup..."
    
    if [ ! -f "$last_backup_file" ]; then
        log_warning "No previous full backup found. Creating full backup instead."
        backup_full "$backup_type"
        return
    fi
    
    mkdir -p "$backup_path"
    
    # Find files newer than last backup
    local last_backup_time=$(stat -c %Y "$last_backup_file")
    
    # Backup only changed files
    find "$VOLUMES_DIR" -newer "$last_backup_file" -type f | tar -czf "$backup_path/changed_files_$TIMESTAMP.tar.gz" -T -
    
    # Always backup databases for incremental
    backup_databases "$backup_path"
    
    # Create compressed archive
    cd "$BACKUP_DIR/$backup_type"
    tar -czf "${backup_name}.tar.gz" "$backup_name"
    rm -rf "$backup_name"
    
    local backup_size=$(get_backup_size "${backup_name}.tar.gz")
    log_success "Incremental backup completed: ${backup_name}.tar.gz (${backup_size})"
}

backup_databases_only() {
    local backup_type="${1:-manual}"
    local backup_name="databases_backup_$TIMESTAMP"
    local backup_path="$BACKUP_DIR/$backup_type/$backup_name"
    
    log_info "Starting databases-only backup..."
    
    mkdir -p "$backup_path"
    backup_databases "$backup_path"
    
    cd "$BACKUP_DIR/$backup_type"
    tar -czf "${backup_name}.tar.gz" "$backup_name"
    rm -rf "$backup_name"
    
    local backup_size=$(get_backup_size "${backup_name}.tar.gz")
    log_success "Database backup completed: ${backup_name}.tar.gz (${backup_size})"
}

# =============================================================================
# RESTORE FUNCTIONS
# =============================================================================

restore_backup() {
    local backup_file="$1"
    local confirm="$2"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    if [ "$confirm" != "--confirm" ]; then
        echo -e "${RED}WARNING: This will overwrite existing data!${NC}"
        echo "Add --confirm flag to proceed with restore"
        exit 1
    fi
    
    log_info "Starting restore from: $backup_file"
    
    # Stop services before restore
    log_info "Stopping services..."
    docker compose down || log_warning "Some services may already be stopped"
    
    # Create restore directory
    local restore_dir="/tmp/restore_$TIMESTAMP"
    mkdir -p "$restore_dir"
    
    # Extract backup
    log_info "Extracting backup..."
    tar -xzf "$backup_file" -C "$restore_dir"
    
    # Find the actual backup directory
    local backup_content_dir=$(find "$restore_dir" -maxdepth 1 -type d -name "*backup*" | head -1)
    
    if [ -z "$backup_content_dir" ]; then
        log_error "Invalid backup file structure"
        rm -rf "$restore_dir"
        exit 1
    fi
    
    # Restore volumes
    if [ -d "$backup_content_dir/volumes" ]; then
        log_info "Restoring volumes..."
        rm -rf "$VOLUMES_DIR"
        mkdir -p "$VOLUMES_DIR"
        tar -xzf "$backup_content_dir/volumes/docker_volumes_"*.tar.gz -C "$VOLUMES_DIR"
        log_success "Volumes restored"
    fi
    
    # Restore configuration
    if [ -d "$backup_content_dir/config" ]; then
        log_info "Restoring configuration..."
        cp "$backup_content_dir/config/"*.yml . 2>/dev/null || true
        if [ -d "$backup_content_dir/config/supabase" ]; then
            rm -rf supabase
            cp -r "$backup_content_dir/config/supabase" .
        fi
        log_success "Configuration restored"
    fi
    
    # Start services
    log_info "Starting services..."
    docker compose up -d
    
    # Wait for services to be ready
    sleep 10
    
    # Restore databases
    if [ -d "$backup_content_dir/databases" ]; then
        log_info "Restoring databases..."
        
        # Restore PostgreSQL
        if [ -f "$backup_content_dir/databases/postgres_dump_"*.sql ]; then
            docker exec -i postgres psql -U postgres < "$backup_content_dir/databases/postgres_dump_"*.sql
            log_success "PostgreSQL restored"
        fi
        
        # Restore Supabase
        if [ -f "$backup_content_dir/databases/supabase_dump_"*.sql ]; then
            docker exec -i supabase-db psql -U postgres < "$backup_content_dir/databases/supabase_dump_"*.sql
            log_success "Supabase restored"
        fi
    fi
    
    # Cleanup
    rm -rf "$restore_dir"
    
    log_success "Restore completed successfully!"
}

# =============================================================================
# CLOUD BACKUP FUNCTIONS
# =============================================================================

cloud_backup_cloudflare() {
    local backup_file="$1"
    log_info "Uploading to Cloudflare R2..."
    
    if [ -z "$CLOUDFLARE_API_TOKEN" ] || [ -z "$CLOUDFLARE_ACCOUNT_ID" ]; then
        log_error "Cloudflare credentials not configured"
        exit 1
    fi
    
    # This would use rclone or aws cli configured for Cloudflare R2
    log_warning "Cloudflare R2 upload not implemented yet - configure rclone or aws cli"
}

cloud_backup_oracle() {
    local backup_file="$1"
    log_info "Uploading to Oracle Cloud Storage..."
    
    if [ -z "$OCI_TENANCY_ID" ]; then
        log_error "Oracle OCI credentials not configured"
        exit 1
    fi
    
    log_warning "Oracle OCI upload not implemented yet - configure oci cli"
}

cloud_backup_azure() {
    local backup_file="$1"
    log_info "Uploading to Azure Blob Storage..."
    
    if [ -z "$AZURE_CLIENT_ID" ]; then
        log_error "Azure credentials not configured"
        exit 1
    fi
    
    log_warning "Azure Blob upload not implemented yet - configure az cli"
}

# =============================================================================
# MAINTENANCE FUNCTIONS
# =============================================================================

list_backups() {
    log_info "Available backups:"
    echo
    
    for backup_type in daily weekly monthly manual; do
        local backup_dir="$BACKUP_DIR/$backup_type"
        if [ -d "$backup_dir" ] && [ "$(ls -A $backup_dir)" ]; then
            echo -e "${YELLOW}$backup_type backups:${NC}"
            for backup in "$backup_dir"/*.tar.gz; do
                if [ -f "$backup" ]; then
                    local size=$(get_backup_size "$backup")
                    local date=$(stat -c %y "$backup" | cut -d' ' -f1)
                    echo "  $(basename "$backup") (${size}, $date)"
                fi
            done
            echo
        fi
    done
}

clean_old_backups() {
    local days="${1:-30}"
    log_info "Cleaning backups older than $days days..."
    
    local count=0
    while read backup; do
        log_info "Removing old backup: $(basename "$backup")"
        rm "$backup"
        ((count++))
    done < <(find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$days)
    
    log_success "Cleaned $count old backup(s)"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    local command="$1"
    shift
    
    case "$command" in
        "backup")
            check_prerequisites
            local backup_type="${1:-full}"
            case "$backup_type" in
                "full") backup_full "manual" ;;
                "incremental") backup_incremental "manual" ;;
                "databases") backup_databases_only "manual" ;;
                "volumes") 
                    local backup_path="$BACKUP_DIR/manual/volumes_backup_$TIMESTAMP"
                    mkdir -p "$backup_path"
                    backup_volumes "$backup_path"
                    cd "$BACKUP_DIR/manual"
                    tar -czf "volumes_backup_$TIMESTAMP.tar.gz" "volumes_backup_$TIMESTAMP"
                    rm -rf "volumes_backup_$TIMESTAMP"
                    ;;
                *) log_error "Invalid backup type: $backup_type"; show_usage; exit 1 ;;
            esac
            ;;
        "restore")
            check_prerequisites
            restore_backup "$@"
            ;;
        "list")
            list_backups
            ;;
        "clean")
            local days=30
            if [[ "$1" =~ --older-than-days=([0-9]+) ]]; then
                days="${BASH_REMATCH[1]}"
            fi
            clean_old_backups "$days"
            ;;
        "cloud-backup")
            local provider="$1"
            local backup_file="$2"
            case "$provider" in
                "cloudflare") cloud_backup_cloudflare "$backup_file" ;;
                "oracle") cloud_backup_oracle "$backup_file" ;;
                "azure") cloud_backup_azure "$backup_file" ;;
                *) log_error "Invalid cloud provider: $provider"; exit 1 ;;
            esac
            ;;
        "cloud-restore")
            log_warning "Cloud restore not implemented yet"
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"