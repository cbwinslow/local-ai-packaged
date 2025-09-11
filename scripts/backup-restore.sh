#!/bin/bash

# ========================================================================================
# Local AI Package - Comprehensive Backup and Restore System
# ========================================================================================
# This script provides complete backup and restore functionality for all data
# Includes databases, configurations, volumes, and application data
# ========================================================================================

set -euo pipefail

# Color codes
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(dirname "$SCRIPT_DIR")"
readonly BACKUP_DIR="${ROOT_DIR}/backups"
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)
readonly LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# Backup configuration
DEFAULT_RETENTION_DAYS=30
COMPRESSION_LEVEL=6

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}ℹ️  $*${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $*${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $*${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $*${NC}" | tee -a "$LOG_FILE"
}

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

COMMANDS:
    backup      Create a complete backup of all data
    restore     Restore from a backup
    list        List available backups
    cleanup     Remove old backups based on retention policy
    verify      Verify backup integrity

OPTIONS:
    --retention-days DAYS   Number of days to keep backups (default: $DEFAULT_RETENTION_DAYS)
    --backup-name NAME      Specific backup name to restore
    --include COMPONENTS    Comma-separated list of components to include
    --exclude COMPONENTS    Comma-separated list of components to exclude
    --compression LEVEL     Compression level 1-9 (default: $COMPRESSION_LEVEL)
    --dry-run              Show what would be done without executing
    --force                Force operations without confirmation
    --help                 Show this help message

COMPONENTS:
    databases    PostgreSQL, Redis, Neo4j, ClickHouse, MinIO
    configs      Environment files, Docker configurations
    volumes      Docker volumes and persistent data
    logs         Application and system logs
    models       AI models and embeddings
    all          All components (default)

EXAMPLES:
    $0 backup                                    # Full backup
    $0 backup --include databases,configs        # Backup only databases and configs
    $0 restore --backup-name backup_20240101     # Restore specific backup
    $0 cleanup --retention-days 7               # Clean backups older than 7 days
    $0 list                                      # List all available backups

EOF
}

# Parse command line arguments
parse_arguments() {
    COMMAND=""
    RETENTION_DAYS="$DEFAULT_RETENTION_DAYS"
    BACKUP_NAME=""
    INCLUDE_COMPONENTS="all"
    EXCLUDE_COMPONENTS=""
    DRY_RUN=false
    FORCE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            backup|restore|list|cleanup|verify)
                COMMAND="$1"
                shift
                ;;
            --retention-days)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            --backup-name)
                BACKUP_NAME="$2"
                shift 2
                ;;
            --include)
                INCLUDE_COMPONENTS="$2"
                shift 2
                ;;
            --exclude)
                EXCLUDE_COMPONENTS="$2"
                shift 2
                ;;
            --compression)
                COMPRESSION_LEVEL="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    if [[ -z "$COMMAND" ]]; then
        error "No command specified"
        show_usage
        exit 1
    fi
}

# Initialize backup environment
init_backup_env() {
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR/logs"
    
    # Create backup metadata
    cat > "$BACKUP_DIR/backup_${TIMESTAMP}.metadata" << EOF
{
    "timestamp": "$TIMESTAMP",
    "date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "user": "$(whoami)",
    "components": "$INCLUDE_COMPONENTS",
    "excluded": "$EXCLUDE_COMPONENTS",
    "compression": "$COMPRESSION_LEVEL",
    "version": "2.0.0"
}
EOF
}

# Check if component should be backed up
should_backup_component() {
    local component="$1"
    
    # Check excludes first
    if [[ "$EXCLUDE_COMPONENTS" =~ $component ]]; then
        return 1
    fi
    
    # Check includes
    if [[ "$INCLUDE_COMPONENTS" == "all" ]] || [[ "$INCLUDE_COMPONENTS" =~ $component ]]; then
        return 0
    fi
    
    return 1
}

# Backup PostgreSQL databases
backup_postgresql() {
    if ! should_backup_component "databases"; then
        return 0
    fi
    
    info "Backing up PostgreSQL databases..."
    
    local backup_file="$BACKUP_DIR/postgresql_${TIMESTAMP}.sql.gz"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would backup PostgreSQL to $backup_file"
        return 0
    fi
    
    # Get database connection details from .env
    local db_password=$(grep "^POSTGRES_PASSWORD=" .env | cut -d'=' -f2)
    
    if docker-compose ps postgres | grep -q "Up"; then
        PGPASSWORD="$db_password" docker-compose exec -T postgres pg_dumpall -U postgres | gzip -"$COMPRESSION_LEVEL" > "$backup_file"
        success "PostgreSQL backup completed: $backup_file"
    else
        warning "PostgreSQL container not running, skipping database backup"
    fi
}

# Backup Redis
backup_redis() {
    if ! should_backup_component "databases"; then
        return 0
    fi
    
    info "Backing up Redis..."
    
    local backup_file="$BACKUP_DIR/redis_${TIMESTAMP}.rdb.gz"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would backup Redis to $backup_file"
        return 0
    fi
    
    if docker-compose ps redis | grep -q "Up"; then
        docker-compose exec -T redis redis-cli BGSAVE
        sleep 5  # Wait for background save to complete
        docker-compose exec -T redis cat /data/dump.rdb | gzip -"$COMPRESSION_LEVEL" > "$backup_file"
        success "Redis backup completed: $backup_file"
    else
        warning "Redis container not running, skipping Redis backup"
    fi
}

# Backup Neo4j
backup_neo4j() {
    if ! should_backup_component "databases"; then
        return 0
    fi
    
    info "Backing up Neo4j..."
    
    local backup_file="$BACKUP_DIR/neo4j_${TIMESTAMP}.tar.gz"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would backup Neo4j to $backup_file"
        return 0
    fi
    
    if docker-compose ps neo4j | grep -q "Up"; then
        # Stop Neo4j for consistent backup
        docker-compose stop neo4j
        tar -czf "$backup_file" -C "$ROOT_DIR" neo4j/data neo4j/logs
        docker-compose start neo4j
        success "Neo4j backup completed: $backup_file"
    else
        warning "Neo4j container not running, skipping Neo4j backup"
    fi
}

# Backup Docker volumes
backup_volumes() {
    if ! should_backup_component "volumes"; then
        return 0
    fi
    
    info "Backing up Docker volumes..."
    
    local volumes_file="$BACKUP_DIR/volumes_${TIMESTAMP}.tar.gz"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would backup Docker volumes to $volumes_file"
        return 0
    fi
    
    # Get list of project volumes
    local volumes=$(docker volume ls --filter "name=localai" --format "{{.Name}}")
    
    if [[ -n "$volumes" ]]; then
        # Create temporary container to access volumes
        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "$BACKUP_DIR":/backup \
            alpine:latest sh -c "
            apk add --no-cache tar gzip
            cd /
            for volume in $volumes; do
                echo 'Backing up volume: \$volume'
                docker run --rm -v \$volume:/volume -v /backup:/backup alpine:latest \
                    tar -czf /backup/volume_\${volume}_${TIMESTAMP}.tar.gz -C /volume .
            done
        "
        success "Docker volumes backup completed"
    else
        warning "No Docker volumes found for project"
    fi
}

# Backup configuration files
backup_configs() {
    if ! should_backup_component "configs"; then
        return 0
    fi
    
    info "Backing up configuration files..."
    
    local configs_file="$BACKUP_DIR/configs_${TIMESTAMP}.tar.gz"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would backup configurations to $configs_file"
        return 0
    fi
    
    # Backup important configuration files
    tar -czf "$configs_file" \
        --exclude="*.log" \
        --exclude="node_modules" \
        --exclude=".git" \
        --exclude="venv" \
        --exclude=".venv" \
        .env* \
        docker-compose*.yml \
        pyproject.toml \
        prompts/ \
        scripts/ \
        config/ \
        2>/dev/null || true
    
    success "Configuration backup completed: $configs_file"
}

# Backup logs
backup_logs() {
    if ! should_backup_component "logs"; then
        return 0
    fi
    
    info "Backing up logs..."
    
    local logs_file="$BACKUP_DIR/logs_${TIMESTAMP}.tar.gz"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would backup logs to $logs_file"
        return 0
    fi
    
    if [[ -d "logs" ]]; then
        tar -czf "$logs_file" logs/
        success "Logs backup completed: $logs_file"
    else
        warning "No logs directory found"
    fi
}

# Backup AI models
backup_models() {
    if ! should_backup_component "models"; then
        return 0
    fi
    
    info "Backing up AI models..."
    
    local models_file="$BACKUP_DIR/models_${TIMESTAMP}.tar.gz"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would backup AI models to $models_file"
        return 0
    fi
    
    # Check for model directories in Docker volumes
    if docker volume ls | grep -q ollama_storage; then
        docker run --rm -v ollama_storage:/models -v "$BACKUP_DIR":/backup alpine:latest \
            tar -czf /backup/models_ollama_${TIMESTAMP}.tar.gz -C /models .
        success "Ollama models backup completed"
    fi
    
    # Backup other model directories if they exist
    local model_dirs=("models" ".cache/huggingface")
    for dir in "${model_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            tar -czf "$BACKUP_DIR/models_$(basename "$dir")_${TIMESTAMP}.tar.gz" "$dir"
            success "$(basename "$dir") models backup completed"
        fi
    done
}

# Create full backup
create_backup() {
    info "Starting full backup process..."
    
    init_backup_env
    
    # Stop services for consistent backup (optional)
    if [[ "$FORCE" == "true" ]]; then
        info "Stopping services for consistent backup..."
        docker-compose stop
    fi
    
    # Backup all components
    backup_postgresql
    backup_redis
    backup_neo4j
    backup_volumes
    backup_configs
    backup_logs
    backup_models
    
    # Restart services if they were stopped
    if [[ "$FORCE" == "true" ]]; then
        info "Restarting services..."
        docker-compose start
    fi
    
    # Create backup manifest
    create_backup_manifest
    
    success "Backup completed successfully!"
    info "Backup location: $BACKUP_DIR"
    info "Backup timestamp: $TIMESTAMP"
}

# Create backup manifest
create_backup_manifest() {
    local manifest_file="$BACKUP_DIR/backup_${TIMESTAMP}.manifest"
    
    {
        echo "# Local AI Package Backup Manifest"
        echo "# Created: $(date)"
        echo "# Timestamp: $TIMESTAMP"
        echo ""
        echo "Files in this backup:"
        ls -la "$BACKUP_DIR"/*"$TIMESTAMP"* | while read -r line; do
            echo "$line"
        done
        echo ""
        echo "Total backup size: $(du -sh "$BACKUP_DIR" | cut -f1)"
    } > "$manifest_file"
    
    success "Backup manifest created: $manifest_file"
}

# List available backups
list_backups() {
    info "Available backups:"
    echo ""
    
    if [[ ! -d "$BACKUP_DIR" ]] || [[ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]]; then
        warning "No backups found in $BACKUP_DIR"
        return 0
    fi
    
    # Group backups by timestamp
    local timestamps=$(ls "$BACKUP_DIR"/*.metadata 2>/dev/null | sed 's/.*backup_\([0-9_]*\)\.metadata/\1/' | sort -r)
    
    for timestamp in $timestamps; do
        local metadata_file="$BACKUP_DIR/backup_${timestamp}.metadata"
        if [[ -f "$metadata_file" ]]; then
            local date=$(jq -r '.date' "$metadata_file" 2>/dev/null || echo "Unknown")
            local components=$(jq -r '.components' "$metadata_file" 2>/dev/null || echo "Unknown")
            local size=$(du -sh "$BACKUP_DIR"/*"$timestamp"* 2>/dev/null | awk '{total+=$1} END {print total "B"}' || echo "Unknown")
            
            echo -e "${GREEN}📦 Backup: $timestamp${NC}"
            echo "  📅 Date: $date"
            echo "  🗂️  Components: $components"
            echo "  📊 Size: $size"
            echo "  📁 Files:"
            ls "$BACKUP_DIR"/*"$timestamp"* 2>/dev/null | sed 's/^/    /' || echo "    No files found"
            echo ""
        fi
    done
}

# Restore from backup
restore_backup() {
    if [[ -z "$BACKUP_NAME" ]]; then
        error "No backup name specified. Use --backup-name option."
        exit 1
    fi
    
    local backup_metadata="$BACKUP_DIR/backup_${BACKUP_NAME}.metadata"
    
    if [[ ! -f "$backup_metadata" ]]; then
        error "Backup not found: $BACKUP_NAME"
        exit 1
    fi
    
    info "Restoring from backup: $BACKUP_NAME"
    
    # Confirmation
    if [[ "$FORCE" != "true" ]]; then
        echo -e "${YELLOW}⚠️  This will overwrite current data. Are you sure? (y/N)${NC}"
        read -r confirmation
        if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
            info "Restore cancelled"
            exit 0
        fi
    fi
    
    # Stop services
    info "Stopping services..."
    docker-compose down
    
    # Restore components
    restore_postgresql
    restore_redis
    restore_neo4j
    restore_volumes
    restore_configs
    
    # Start services
    info "Starting services..."
    docker-compose up -d
    
    success "Restore completed successfully!"
}

# Restore PostgreSQL
restore_postgresql() {
    local backup_file="$BACKUP_DIR/postgresql_${BACKUP_NAME}.sql.gz"
    
    if [[ ! -f "$backup_file" ]]; then
        warning "PostgreSQL backup not found, skipping"
        return 0
    fi
    
    info "Restoring PostgreSQL..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would restore PostgreSQL from $backup_file"
        return 0
    fi
    
    # Start PostgreSQL container
    docker-compose up -d postgres
    sleep 10
    
    # Restore database
    zcat "$backup_file" | docker-compose exec -T postgres psql -U postgres
    success "PostgreSQL restored"
}

# Restore Redis
restore_redis() {
    local backup_file="$BACKUP_DIR/redis_${BACKUP_NAME}.rdb.gz"
    
    if [[ ! -f "$backup_file" ]]; then
        warning "Redis backup not found, skipping"
        return 0
    fi
    
    info "Restoring Redis..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would restore Redis from $backup_file"
        return 0
    fi
    
    # Stop Redis and restore data
    docker-compose stop redis
    zcat "$backup_file" | docker run --rm -i -v redis_data:/data alpine:latest sh -c "cat > /data/dump.rdb"
    docker-compose start redis
    success "Redis restored"
}

# Restore Neo4j
restore_neo4j() {
    local backup_file="$BACKUP_DIR/neo4j_${BACKUP_NAME}.tar.gz"
    
    if [[ ! -f "$backup_file" ]]; then
        warning "Neo4j backup not found, skipping"
        return 0
    fi
    
    info "Restoring Neo4j..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would restore Neo4j from $backup_file"
        return 0
    fi
    
    # Extract Neo4j data
    tar -xzf "$backup_file" -C "$ROOT_DIR"
    success "Neo4j restored"
}

# Restore Docker volumes
restore_volumes() {
    local volumes_pattern="$BACKUP_DIR/volume_*_${BACKUP_NAME}.tar.gz"
    
    if ! ls $volumes_pattern >/dev/null 2>&1; then
        warning "No volume backups found, skipping"
        return 0
    fi
    
    info "Restoring Docker volumes..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would restore Docker volumes"
        return 0
    fi
    
    for volume_backup in $volumes_pattern; do
        local volume_name=$(basename "$volume_backup" | sed "s/volume_\(.*\)_${BACKUP_NAME}.tar.gz/\1/")
        info "Restoring volume: $volume_name"
        
        # Create volume if it doesn't exist
        docker volume create "$volume_name" >/dev/null 2>&1 || true
        
        # Restore volume data
        docker run --rm -v "$volume_name":/volume -v "$BACKUP_DIR":/backup alpine:latest \
            tar -xzf "/backup/$(basename "$volume_backup")" -C /volume
    done
    
    success "Docker volumes restored"
}

# Restore configurations
restore_configs() {
    local backup_file="$BACKUP_DIR/configs_${BACKUP_NAME}.tar.gz"
    
    if [[ ! -f "$backup_file" ]]; then
        warning "Configuration backup not found, skipping"
        return 0
    fi
    
    info "Restoring configurations..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would restore configurations from $backup_file"
        return 0
    fi
    
    tar -xzf "$backup_file" -C "$ROOT_DIR"
    success "Configurations restored"
}

# Clean old backups
cleanup_backups() {
    info "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
    
    local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y%m%d)
    local deleted_count=0
    
    for backup_file in "$BACKUP_DIR"/backup_*; do
        if [[ -f "$backup_file" ]]; then
            local backup_date=$(basename "$backup_file" | sed 's/backup_\([0-9]\{8\}\).*/\1/')
            
            if [[ "$backup_date" < "$cutoff_date" ]]; then
                if [[ "$DRY_RUN" == "true" ]]; then
                    info "DRY RUN: Would delete $backup_file"
                else
                    rm -f "$BACKUP_DIR"/*"$backup_date"*
                    info "Deleted backup: $backup_date"
                fi
                ((deleted_count++))
            fi
        fi
    done
    
    if [[ $deleted_count -eq 0 ]]; then
        info "No old backups to clean up"
    else
        success "Cleaned up $deleted_count old backup(s)"
    fi
}

# Verify backup integrity
verify_backup() {
    if [[ -z "$BACKUP_NAME" ]]; then
        error "No backup name specified. Use --backup-name option."
        exit 1
    fi
    
    info "Verifying backup integrity: $BACKUP_NAME"
    
    local backup_files=("$BACKUP_DIR"/*"$BACKUP_NAME"*)
    local verified_count=0
    local failed_count=0
    
    for file in "${backup_files[@]}"; do
        if [[ -f "$file" ]]; then
            info "Verifying: $(basename "$file")"
            
            case "$file" in
                *.gz)
                    if gzip -t "$file" 2>/dev/null; then
                        success "✓ $(basename "$file")"
                        ((verified_count++))
                    else
                        error "✗ $(basename "$file") - corrupted"
                        ((failed_count++))
                    fi
                    ;;
                *.tar.gz)
                    if tar -tzf "$file" >/dev/null 2>&1; then
                        success "✓ $(basename "$file")"
                        ((verified_count++))
                    else
                        error "✗ $(basename "$file") - corrupted"
                        ((failed_count++))
                    fi
                    ;;
                *)
                    success "✓ $(basename "$file") - skipped verification"
                    ((verified_count++))
                    ;;
            esac
        fi
    done
    
    info "Verification complete: $verified_count verified, $failed_count failed"
    
    if [[ $failed_count -eq 0 ]]; then
        success "Backup integrity verified successfully"
        return 0
    else
        error "Backup integrity check failed"
        return 1
    fi
}

# Main execution
main() {
    cd "$ROOT_DIR"
    
    case "$COMMAND" in
        backup)
            create_backup
            ;;
        restore)
            restore_backup
            ;;
        list)
            list_backups
            ;;
        cleanup)
            cleanup_backups
            ;;
        verify)
            verify_backup
            ;;
        *)
            error "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
}

# Parse arguments and execute
parse_arguments "$@"
main