#!/bin/bash

# ========================================================================================
# Local AI Package - Idempotent Launch Script
# ========================================================================================
# This script provides a complete, idempotent startup solution for the Local AI Package
# Can be run multiple times safely - will only perform necessary actions
# Handles dependencies, conflicts, health checks, and automated recovery
# ========================================================================================

set -euo pipefail

# Version and metadata
SCRIPT_VERSION="2.0.0"
LAUNCH_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m' # No Color

# Configuration
readonly DEFAULT_PROFILE="cpu"
readonly DEFAULT_ENVIRONMENT="private"
readonly MAX_STARTUP_WAIT=300
readonly HEALTH_CHECK_RETRIES=10
readonly HEALTH_CHECK_DELAY=30

# Global variables
PROFILE=""
ENVIRONMENT=""
SERVICES_TO_START=""
SKIP_HEALTH_CHECKS=false
FORCE_RECREATE=false
VERBOSE=false
DRY_RUN=false

# Logging setup
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/launch_${LAUNCH_TIMESTAMP}.log"
mkdir -p "$LOG_DIR"

# Logging functions
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

info() {
    log "INFO" "$@"
    echo -e "${BLUE}ℹ️  $*${NC}"
}

success() {
    log "SUCCESS" "$@"
    echo -e "${GREEN}✅ $*${NC}"
}

warning() {
    log "WARNING" "$@"
    echo -e "${YELLOW}⚠️  $*${NC}"
}

error() {
    log "ERROR" "$@"
    echo -e "${RED}❌ $*${NC}"
}

debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        log "DEBUG" "$@"
        echo -e "${PURPLE}🔍 $*${NC}"
    fi
}

# Banner and version info
show_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                          Local AI Package Launch Script                         ║"
    echo "║                                Version $SCRIPT_VERSION                                ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    info "Launching Local AI Package - Comprehensive Government Data Analysis Platform"
    info "Timestamp: $LAUNCH_TIMESTAMP"
    info "Working Directory: $ROOT_DIR"
    echo ""
}

# Usage information
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Idempotent launch script for the Local AI Package. Can be run multiple times safely.

OPTIONS:
    -p, --profile PROFILE       Hardware profile: cpu, gpu-nvidia, gpu-amd (default: $DEFAULT_PROFILE)
    -e, --environment ENV       Environment: private, public (default: $DEFAULT_ENVIRONMENT)
    -s, --services SERVICES     Comma-separated list of specific services to start
    --skip-health-checks        Skip health checks after startup
    --force-recreate           Force recreation of all containers
    --verbose                  Enable verbose logging
    --dry-run                  Show what would be done without executing
    -h, --help                 Show this help message

PROFILES:
    cpu         - CPU-only inference (default)
    gpu-nvidia  - NVIDIA GPU acceleration
    gpu-amd     - AMD GPU acceleration

ENVIRONMENTS:
    private     - Development mode with all ports exposed to localhost
    public      - Production mode with only 80/443 exposed via Traefik

EXAMPLES:
    $0                                    # Start with defaults (cpu, private)
    $0 -p gpu-nvidia -e public            # GPU acceleration in production mode
    $0 -s "supabase,n8n,flowise"         # Start only specific services
    $0 --force-recreate --verbose         # Force rebuild with detailed logging
    $0 --dry-run -p gpu-amd               # Preview AMD GPU setup

EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--profile)
                PROFILE="$2"
                shift 2
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -s|--services)
                SERVICES_TO_START="$2"
                shift 2
                ;;
            --skip-health-checks)
                SKIP_HEALTH_CHECKS=true
                shift
                ;;
            --force-recreate)
                FORCE_RECREATE=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
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
    
    # Set defaults
    PROFILE="${PROFILE:-$DEFAULT_PROFILE}"
    ENVIRONMENT="${ENVIRONMENT:-$DEFAULT_ENVIRONMENT}"
    
    # Validate arguments
    case "$PROFILE" in
        cpu|gpu-nvidia|gpu-amd) ;;
        *) error "Invalid profile: $PROFILE"; exit 1 ;;
    esac
    
    case "$ENVIRONMENT" in
        private|public) ;;
        *) error "Invalid environment: $ENVIRONMENT"; exit 1 ;;
    esac
}

# Check system requirements
check_system_requirements() {
    info "Checking system requirements..."
    
    local requirements_met=true
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        requirements_met=false
    elif ! docker info &> /dev/null; then
        error "Docker is not running or not accessible"
        requirements_met=false
    else
        local docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        success "Docker $docker_version is running"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed"
        requirements_met=false
    else
        success "Docker Compose is available"
    fi
    
    # Check available ports
    local required_ports=()
    if [[ "$ENVIRONMENT" == "private" ]]; then
        required_ports=(80 443 3000 5432 6379 8000)
    else
        required_ports=(80 443)
    fi
    
    for port in "${required_ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            warning "Port $port is already in use - will attempt to resolve conflicts"
        fi
    done
    
    # Check GPU requirements
    if [[ "$PROFILE" == "gpu-nvidia" ]]; then
        if ! command -v nvidia-smi &> /dev/null; then
            error "NVIDIA drivers not found for GPU profile"
            requirements_met=false
        elif ! docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi &> /dev/null; then
            error "Docker GPU support not available"
            requirements_met=false
        else
            success "NVIDIA GPU support available"
        fi
    elif [[ "$PROFILE" == "gpu-amd" ]]; then
        if [[ ! -d "/dev/dri" ]]; then
            error "AMD GPU devices not found"
            requirements_met=false
        else
            success "AMD GPU devices available"
        fi
    fi
    
    # Check disk space
    local available_space=$(df "$ROOT_DIR" | awk 'NR==2 {print $4}')
    local required_space=5242880  # 5GB in KB
    
    if [[ "$available_space" -lt "$required_space" ]]; then
        error "Insufficient disk space: $(($available_space/1024/1024))GB available, 5GB required"
        requirements_met=false
    else
        success "Sufficient disk space available: $(($available_space/1024/1024))GB"
    fi
    
    if [[ "$requirements_met" != "true" ]]; then
        error "System requirements not met"
        exit 1
    fi
    
    success "All system requirements satisfied"
}

# Setup environment and secrets
setup_environment() {
    info "Setting up environment and secrets..."
    
    cd "$ROOT_DIR"
    
    # Create .env if it doesn't exist
    if [[ ! -f .env ]]; then
        if [[ -f .env.template ]]; then
            info "Creating .env from template"
            cp .env.template .env
        elif [[ -f .env.example ]]; then
            info "Creating .env from example"
            cp .env.example .env
        else
            error ".env file not found and no template available"
            exit 1
        fi
    fi
    
    # Generate secrets if needed
    if [[ -f scripts/generate-secrets.sh ]]; then
        info "Checking and generating secrets..."
        if [[ "$DRY_RUN" != "true" ]]; then
            bash scripts/generate-secrets.sh
        else
            info "DRY RUN: Would generate secrets"
        fi
    fi
    
    # Set environment-specific variables
    if ! grep -q "ENVIRONMENT=" .env; then
        echo "ENVIRONMENT=$ENVIRONMENT" >> .env
    else
        sed -i "s/^ENVIRONMENT=.*/ENVIRONMENT=$ENVIRONMENT/" .env
    fi
    
    if ! grep -q "DOCKER_PROJECT_NAME=" .env; then
        echo "DOCKER_PROJECT_NAME=localai" >> .env
    fi
    
    success "Environment setup complete"
}

# Resolve port conflicts
resolve_port_conflicts() {
    info "Resolving port conflicts..."
    
    if [[ -f scripts/port-conflict-resolver.sh ]]; then
        if [[ "$DRY_RUN" != "true" ]]; then
            bash scripts/port-conflict-resolver.sh resolve "$ENVIRONMENT"
        else
            info "DRY RUN: Would resolve port conflicts for $ENVIRONMENT"
        fi
    else
        warning "Port conflict resolver not found - manual resolution may be needed"
    fi
    
    success "Port conflict resolution complete"
}

# Prepare Docker Compose configuration
prepare_compose_config() {
    info "Preparing Docker Compose configuration..."
    
    # Base compose files
    local compose_files=("-f" "docker-compose.yml")
    
    # Add Traefik
    if [[ -f "docker-compose.traefik.yml" ]]; then
        compose_files+=("-f" "docker-compose.traefik.yml")
    fi
    
    # Add monitoring
    if [[ -f "docker-compose.monitoring.yml" ]]; then
        compose_files+=("-f" "docker-compose.monitoring.yml")
    fi
    
    # Add MCP services
    if [[ -f "docker-compose.mcp.yml" ]]; then
        compose_files+=("-f" "docker-compose.mcp.yml")
    fi
    
    # Add Supabase
    if [[ -f "supabase/docker/docker-compose.yml" ]]; then
        compose_files+=("-f" "supabase/docker/docker-compose.yml")
    fi
    
    # Add environment-specific overrides
    local override_file="docker-compose.override.${ENVIRONMENT}.yml"
    if [[ -f "$override_file" ]]; then
        compose_files+=("-f" "$override_file")
    fi
    
    # Add generated overrides if they exist
    local generated_override="docker-compose.override.${ENVIRONMENT}.generated.yml"
    if [[ -f "$generated_override" ]]; then
        compose_files+=("-f" "$generated_override")
    fi
    
    # Export for use in other functions
    export COMPOSE_FILES="${compose_files[*]}"
    
    debug "Compose files: ${compose_files[*]}"
    success "Docker Compose configuration prepared"
}

# Pull latest images
pull_images() {
    info "Pulling latest Docker images..."
    
    if [[ "$DRY_RUN" != "true" ]]; then
        docker-compose ${COMPOSE_FILES} pull --ignore-pull-failures
    else
        info "DRY RUN: Would pull latest images"
    fi
    
    success "Image pull complete"
}

# Stop existing services
stop_existing_services() {
    info "Stopping existing services..."
    
    if [[ "$DRY_RUN" != "true" ]]; then
        # Stop by project name to ensure we get all related containers
        docker-compose --project-name localai down --remove-orphans 2>/dev/null || true
        
        # Also stop any containers that might be running from previous sessions
        docker stop $(docker ps -q --filter "label=com.docker.compose.project=localai") 2>/dev/null || true
        
        if [[ "$FORCE_RECREATE" == "true" ]]; then
            info "Force recreate enabled - removing volumes and networks"
            docker-compose --project-name localai down -v --remove-orphans 2>/dev/null || true
            docker system prune -f --volumes 2>/dev/null || true
        fi
    else
        info "DRY RUN: Would stop existing services"
    fi
    
    success "Existing services stopped"
}

# Start core infrastructure services
start_infrastructure() {
    info "Starting core infrastructure services..."
    
    local infrastructure_services=(
        "traefik"
        "postgres"
        "redis"
        "neo4j"
        "qdrant"
        "clickhouse"
        "minio"
    )
    
    if [[ "$DRY_RUN" != "true" ]]; then
        for service in "${infrastructure_services[@]}"; do
            if docker-compose ${COMPOSE_FILES} config --services | grep -q "^${service}$"; then
                info "Starting $service..."
                docker-compose ${COMPOSE_FILES} up -d "$service"
                
                # Wait for service to be healthy
                local retries=0
                while [[ $retries -lt 30 ]]; do
                    if docker-compose ${COMPOSE_FILES} ps "$service" | grep -q "Up"; then
                        success "$service is running"
                        break
                    fi
                    sleep 2
                    ((retries++))
                done
                
                if [[ $retries -eq 30 ]]; then
                    warning "$service may not have started properly"
                fi
            fi
        done
    else
        info "DRY RUN: Would start infrastructure services: ${infrastructure_services[*]}"
    fi
    
    success "Infrastructure services started"
}

# Start Supabase services
start_supabase() {
    info "Starting Supabase services..."
    
    if [[ "$DRY_RUN" != "true" ]]; then
        # Initialize Supabase if directory exists
        if [[ -d "supabase" ]]; then
            cd supabase
            
            # Update submodule if needed
            if [[ -d ".git" ]]; then
                git submodule update --init --recursive 2>/dev/null || true
            fi
            
            # Copy environment variables
            if [[ -f "../.env" ]]; then
                cp "../.env" "docker/.env"
            fi
            
            cd docker
            docker-compose up -d --wait
            cd "$ROOT_DIR"
            
            # Wait for Supabase to be ready
            local retries=0
            while [[ $retries -lt 60 ]]; do
                if curl -s http://localhost:8000/health >/dev/null 2>&1; then
                    success "Supabase is ready"
                    break
                fi
                sleep 5
                ((retries++))
            done
            
            if [[ $retries -eq 60 ]]; then
                warning "Supabase health check timeout"
            fi
        fi
    else
        info "DRY RUN: Would start Supabase services"
    fi
    
    success "Supabase startup complete"
}

# Start AI services
start_ai_services() {
    info "Starting AI services..."
    
    local ai_services=(
        "ollama-${PROFILE}"
        "ollama-pull-llama-${PROFILE}"
        "n8n"
        "flowise"
        "open-webui"
        "langfuse-web"
        "langfuse-worker"
    )
    
    if [[ "$DRY_RUN" != "true" ]]; then
        # Set the appropriate profile
        export COMPOSE_PROFILES="$PROFILE"
        
        for service in "${ai_services[@]}"; do
            if docker-compose ${COMPOSE_FILES} config --services | grep -q "^${service}$"; then
                info "Starting $service..."
                docker-compose ${COMPOSE_FILES} up -d "$service"
            fi
        done
        
        # Wait for key services to be ready
        info "Waiting for AI services to initialize..."
        sleep 30
    else
        info "DRY RUN: Would start AI services with profile $PROFILE: ${ai_services[*]}"
    fi
    
    success "AI services started"
}

# Start application services
start_applications() {
    info "Starting application services..."
    
    local app_services=(
        "searxng"
        "agentic-rag"
        "frontend"
        "dashboard"
    )
    
    if [[ "$DRY_RUN" != "true" ]]; then
        for service in "${app_services[@]}"; do
            if docker-compose ${COMPOSE_FILES} config --services | grep -q "^${service}$"; then
                info "Starting $service..."
                docker-compose ${COMPOSE_FILES} up -d "$service"
            fi
        done
    else
        info "DRY RUN: Would start application services: ${app_services[*]}"
    fi
    
    success "Application services started"
}

# Start monitoring services
start_monitoring() {
    info "Starting monitoring services..."
    
    local monitoring_services=(
        "grafana"
        "prometheus"
    )
    
    if [[ "$DRY_RUN" != "true" ]]; then
        for service in "${monitoring_services[@]}"; do
            if docker-compose ${COMPOSE_FILES} config --services | grep -q "^${service}$"; then
                info "Starting $service..."
                docker-compose ${COMPOSE_FILES} up -d "$service"
            fi
        done
    else
        info "DRY RUN: Would start monitoring services: ${monitoring_services[*]}"
    fi
    
    success "Monitoring services started"
}

# Health checks
perform_health_checks() {
    if [[ "$SKIP_HEALTH_CHECKS" == "true" ]]; then
        warning "Skipping health checks as requested"
        return
    fi
    
    info "Performing comprehensive health checks..."
    
    local health_check_urls=(
        "http://localhost:80:Traefik"
        "http://localhost:8000:Supabase API"
        "http://localhost:5678:N8N"
        "http://localhost:3000:Frontend"
        "http://localhost:6333:Qdrant"
    )
    
    if [[ "$ENVIRONMENT" == "private" ]]; then
        health_check_urls+=(
            "http://localhost:3001:Flowise"
            "http://localhost:8080:Open WebUI"
            "http://localhost:7474:Neo4j"
            "http://localhost:3003:Grafana"
        )
    fi
    
    local failed_checks=()
    
    for url_service in "${health_check_urls[@]}"; do
        local url="${url_service%:*}"
        local service="${url_service#*:}"
        
        info "Checking $service at $url..."
        
        local retries=0
        local check_passed=false
        
        while [[ $retries -lt $HEALTH_CHECK_RETRIES ]]; do
            if curl -s -f "$url" >/dev/null 2>&1; then
                success "$service is healthy"
                check_passed=true
                break
            fi
            
            debug "Health check attempt $((retries + 1)) for $service failed"
            sleep $HEALTH_CHECK_DELAY
            ((retries++))
        done
        
        if [[ "$check_passed" != "true" ]]; then
            failed_checks+=("$service")
            warning "$service health check failed"
        fi
    done
    
    if [[ ${#failed_checks[@]} -eq 0 ]]; then
        success "All health checks passed"
    else
        warning "Failed health checks: ${failed_checks[*]}"
        info "Services may still be starting up - check logs if issues persist"
    fi
}

# Display service status and access information
show_service_status() {
    info "Service Status and Access Information"
    echo ""
    
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                            Service Access Information                            ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Core services
    echo -e "${WHITE}Core Services:${NC}"
    echo "  🌐 Frontend Application      : http://localhost:3000"
    echo "  🗄️  Supabase API Gateway     : http://localhost:8000"
    echo "  📊 Supabase Studio          : http://localhost:3001"
    echo "  🔄 N8N Workflow Automation   : http://localhost:5678"
    echo "  🤖 Flowise AI Workflows     : http://localhost:3002"
    echo "  💬 Open WebUI Chat Interface : http://localhost:8081"
    echo ""
    
    # Databases
    echo -e "${WHITE}Databases:${NC}"
    echo "  🐘 PostgreSQL               : localhost:5432"
    echo "  🔴 Redis Cache               : localhost:6379"
    echo "  🕸️  Neo4j Graph Database     : http://localhost:7474"
    echo "  🔍 Qdrant Vector Database    : http://localhost:6333"
    echo "  📈 ClickHouse Analytics      : http://localhost:8123"
    echo ""
    
    # Monitoring
    echo -e "${WHITE}Monitoring & Observability:${NC}"
    echo "  📊 Grafana Dashboards       : http://localhost:3003"
    echo "  📈 Prometheus Metrics       : http://localhost:9090"
    echo "  🔬 Langfuse LLM Observability: http://localhost:3004"
    echo ""
    
    # Storage & Search
    echo -e "${WHITE}Storage & Search:${NC}"
    echo "  🪣 MinIO S3 Storage         : http://localhost:9001"
    echo "  🔍 SearXNG Search Engine    : http://localhost:8082"
    echo ""
    
    # Management
    echo -e "${WHITE}Management:${NC}"
    echo "  📱 System Dashboard         : http://localhost:3006"
    echo "  🚦 Traefik Dashboard        : http://localhost:8080"
    echo ""
    
    if [[ "$ENVIRONMENT" == "public" ]]; then
        echo -e "${YELLOW}Note: In public mode, only ports 80 and 443 are exposed externally.${NC}"
        echo -e "${YELLOW}All services are accessible through Traefik reverse proxy.${NC}"
        echo ""
    fi
    
    echo -e "${GREEN}🎉 Local AI Package is ready for government data analysis!${NC}"
    echo ""
    
    # Show next steps
    echo -e "${WHITE}Next Steps:${NC}"
    echo "1. 🔐 Set up API keys in the dashboard: http://localhost:3006"
    echo "2. 📊 Configure data sources and ingestion schedules"
    echo "3. 🤖 Create AI workflows in N8N: http://localhost:5678"
    echo "4. 🔍 Start analyzing government data with the tools provided"
    echo "5. 📈 Monitor system performance in Grafana: http://localhost:3003"
    echo ""
    
    # Show logs location
    echo -e "${WHITE}Useful Commands:${NC}"
    echo "  📋 View logs: docker-compose logs -f"
    echo "  🔄 Restart service: docker-compose restart <service>"
    echo "  🛑 Stop all: docker-compose down"
    echo "  💾 Backup data: ./scripts/backup-data.sh"
    echo ""
    
    info "Launch log saved to: $LOG_FILE"
}

# Error handling and cleanup
cleanup_on_exit() {
    local exit_code=$?
    
    if [[ $exit_code -ne 0 ]]; then
        error "Launch script failed with exit code $exit_code"
        warning "Check logs at $LOG_FILE for details"
        
        if [[ "$DRY_RUN" != "true" ]]; then
            warning "Attempting to stop any partially started services..."
            docker-compose --project-name localai down 2>/dev/null || true
        fi
    fi
}

# Main execution function
main() {
    trap cleanup_on_exit EXIT
    
    show_banner
    parse_arguments "$@"
    
    info "Starting Local AI Package with profile: $PROFILE, environment: $ENVIRONMENT"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        warning "DRY RUN MODE - No actual changes will be made"
    fi
    
    # Execute startup sequence
    check_system_requirements
    setup_environment
    resolve_port_conflicts
    prepare_compose_config
    
    if [[ "$DRY_RUN" != "true" ]]; then
        pull_images
        stop_existing_services
        start_infrastructure
        start_supabase
        start_ai_services
        start_applications
        start_monitoring
        perform_health_checks
        show_service_status
    else
        info "DRY RUN: All startup steps would be executed"
        info "Configuration files that would be used: $COMPOSE_FILES"
    fi
    
    success "Local AI Package launch completed successfully!"
    
    # Save completion status
    echo "LAUNCH_STATUS=SUCCESS" >> "$LOG_FILE"
    echo "LAUNCH_PROFILE=$PROFILE" >> "$LOG_FILE"
    echo "LAUNCH_ENVIRONMENT=$ENVIRONMENT" >> "$LOG_FILE"
    echo "LAUNCH_TIMESTAMP=$LAUNCH_TIMESTAMP" >> "$LOG_FILE"
}

# Execute main function with all arguments
main "$@"