#!/bin/bash

# =============================================================================
# Production Deployment Script for Local AI Package
# =============================================================================
# This script deploys the Local AI Package with production-ready configurations
# including cloud integration, monitoring, and security best practices
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_TYPE="${1:-development}"
ENVIRONMENT="${2:-local}"

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}  Local AI Package - Production Deployment${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo

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

show_usage() {
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 [deployment_type] [environment]"
    echo
    echo -e "${YELLOW}Deployment Types:${NC}"
    echo "  development   - Local development setup"
    echo "  staging       - Staging environment"
    echo "  production    - Production deployment"
    echo
    echo -e "${YELLOW}Environments:${NC}"
    echo "  local         - Local Docker setup"
    echo "  cloud         - Cloud-based deployment"
    echo "  hybrid        - Hybrid local/cloud setup"
    echo
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 development local"
    echo "  $0 production cloud"
    echo "  $0 staging hybrid"
}

# Pre-deployment checks
check_prerequisites() {
    log_info "Performing pre-deployment checks..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check available disk space (minimum 10GB)
    available_space=$(df . | tail -1 | awk '{print $4}')
    if [ "$available_space" -lt 10485760 ]; then  # 10GB in KB
        log_warning "Less than 10GB disk space available"
    fi
    
    # Check available memory (minimum 4GB)
    available_memory=$(free -m | awk 'NR==2{print $7}')
    if [ "$available_memory" -lt 4096 ]; then
        log_warning "Less than 4GB memory available"
    fi
    
    log_success "Pre-deployment checks passed"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment for $DEPLOYMENT_TYPE deployment..."
    
    # Generate secrets if .env doesn't exist
    if [ ! -f .env ]; then
        log_info "Generating environment configuration..."
        if [ "$DEPLOYMENT_TYPE" = "production" ]; then
            ./scripts/enhanced-generate-secrets.sh --yes
        else
            ./scripts/enhanced-generate-secrets.sh --no
        fi
    else
        log_info "Using existing .env file"
    fi
    
    # Set deployment-specific variables
    case "$DEPLOYMENT_TYPE" in
        "development")
            export NODE_ENV=development
            export DEBUG_MODE=true
            export ENABLE_EXPERIMENTAL_FEATURES=true
            ;;
        "staging")
            export NODE_ENV=staging
            export DEBUG_MODE=false
            export ENABLE_EXPERIMENTAL_FEATURES=true
            ;;
        "production")
            export NODE_ENV=production
            export DEBUG_MODE=false
            export ENABLE_EXPERIMENTAL_FEATURES=false
            export ENABLE_TELEMETRY=true
            ;;
    esac
    
    log_success "Environment setup completed"
}

# Create networks
create_networks() {
    log_info "Creating Docker networks..."
    
    # Create main network
    if ! docker network ls | grep -q localai_default; then
        docker network create localai_default
        log_success "Created localai_default network"
    else
        log_info "Network localai_default already exists"
    fi
    
    # Create traefik network for production
    if [ "$DEPLOYMENT_TYPE" = "production" ] || [ "$DEPLOYMENT_TYPE" = "staging" ]; then
        if ! docker network ls | grep -q traefik-public; then
            docker network create traefik-public
            log_success "Created traefik-public network"
        else
            log_info "Network traefik-public already exists"
        fi
    fi
}

# Initialize data directories
initialize_data() {
    log_info "Initializing data directories..."
    
    # Create all necessary volume directories
    mkdir -p volumes/{postgres/data,qdrant/data,langfuse/{postgres,clickhouse/{data,logs},minio},ollama,flowise,open-webui,n8n,valkey,agentic}
    mkdir -p volumes/{mcp/{congress/{data,logs},federal/data,fec/data,neo4j-memory/data,postgres/data,vectorize/data,embeddings/cache,azure/{data,config},cloudflare/data,oci/{data,config},pluggedin/data,github/data,stackhawk/data,logs/data},neo4j/{data,logs,import,plugins,conf},memgraph/{data,logs,etc},falkordb/data}
    mkdir -p supabase/volumes/{db/{data,init-scripts},storage,functions,api}
    mkdir -p backups/{daily,weekly,monthly}
    mkdir -p logs/{application,system,error}
    
    # Set proper permissions
    chmod -R 755 volumes/
    chmod -R 755 supabase/volumes/
    chmod -R 755 backups/
    chmod -R 755 logs/
    
    log_success "Data directories initialized"
}

# Deploy based on type
deploy_services() {
    log_info "Deploying services for $DEPLOYMENT_TYPE environment..."
    
    case "$DEPLOYMENT_TYPE" in
        "development")
            deploy_development
            ;;
        "staging")
            deploy_staging
            ;;
        "production")
            deploy_production
            ;;
        *)
            log_error "Unknown deployment type: $DEPLOYMENT_TYPE"
            exit 1
            ;;
    esac
}

deploy_development() {
    log_info "Starting development deployment..."
    
    # Start core services first
    log_info "Starting core services..."
    docker compose up -d postgres redis qdrant
    
    # Wait for databases to be ready
    log_info "Waiting for databases to be ready..."
    sleep 30
    
    # Start Supabase
    log_info "Starting Supabase..."
    docker compose up -d db auth rest realtime storage imgproxy kong analytics studio meta functions
    
    # Start AI services
    log_info "Starting AI services..."
    docker compose up -d flowise open-webui n8n
    
    # Start MCP servers
    log_info "Starting MCP servers..."
    docker compose up -d mcp-congress-gov mcp-neo4j-agent-memory mcp-vectorize
    
    # Start monitoring
    log_info "Starting monitoring..."
    docker compose up -d langfuse-worker langfuse-web clickhouse minio
    
    log_success "Development deployment completed"
}

deploy_staging() {
    log_info "Starting staging deployment..."
    
    # Start with Traefik
    log_info "Starting Traefik..."
    docker compose -f docker-compose.traefik.yml up -d
    
    # Start all core services
    log_info "Starting all services..."
    docker compose up -d
    
    log_success "Staging deployment completed"
}

deploy_production() {
    log_info "Starting production deployment..."
    
    # Validate production configuration
    if [ ! -f .env ]; then
        log_error "No .env file found for production deployment"
        exit 1
    fi
    
    # Check for required production variables
    required_vars="POSTGRES_PASSWORD JWT_SECRET NEXTAUTH_SECRET"
    for var in $required_vars; do
        if ! grep -q "^${var}=" .env; then
            log_error "Required variable $var not found in .env"
            exit 1
        fi
    done
    
    # Start Traefik first
    log_info "Starting Traefik reverse proxy..."
    docker compose -f docker-compose.traefik.yml up -d
    
    # Wait for Traefik to be ready
    sleep 10
    
    # Start all services
    log_info "Starting all services..."
    docker compose up -d
    
    # Start monitoring
    log_info "Starting monitoring stack..."
    docker compose -f docker-compose.monitoring.yml up -d || log_warning "Monitoring stack not available"
    
    log_success "Production deployment completed"
}

# Validate deployment
validate_deployment() {
    log_info "Validating deployment..."
    
    # Check if services are running
    local failed_services=()
    local services=(postgres redis qdrant)
    
    case "$DEPLOYMENT_TYPE" in
        "staging"|"production")
            services+=(traefik)
            ;;
    esac
    
    for service in "${services[@]}"; do
        if ! docker compose ps | grep -q "$service.*Up"; then
            failed_services+=("$service")
        fi
    done
    
    if [ ${#failed_services[@]} -eq 0 ]; then
        log_success "All core services are running"
    else
        log_error "Failed services: ${failed_services[*]}"
        return 1
    fi
    
    # Test connectivity
    log_info "Testing service connectivity..."
    
    # Test PostgreSQL
    if docker compose exec -T postgres pg_isready -U postgres &>/dev/null; then
        log_success "PostgreSQL is ready"
    else
        log_warning "PostgreSQL connection test failed"
    fi
    
    # Test Redis
    if docker compose exec -T redis redis-cli ping | grep -q PONG; then
        log_success "Redis is ready"
    else
        log_warning "Redis connection test failed"
    fi
    
    log_success "Deployment validation completed"
}

# Setup monitoring
setup_monitoring() {
    if [ "$DEPLOYMENT_TYPE" = "production" ] || [ "$DEPLOYMENT_TYPE" = "staging" ]; then
        log_info "Setting up monitoring..."
        
        # Setup log rotation
        cat > /etc/logrotate.d/local-ai-package << EOF
$(pwd)/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
        
        # Setup backup cron job
        (crontab -l 2>/dev/null; echo "0 2 * * * cd $(pwd) && ./scripts/backup-restore-enhanced.sh backup incremental") | crontab -
        
        log_success "Monitoring setup completed"
    fi
}

# Setup cloud integration
setup_cloud_integration() {
    if [ "$ENVIRONMENT" = "cloud" ] || [ "$ENVIRONMENT" = "hybrid" ]; then
        log_info "Setting up cloud integration..."
        
        # Check cloud credentials
        local cloud_configured=false
        
        if [ -n "$CLOUDFLARE_API_TOKEN" ]; then
            log_info "Cloudflare integration available"
            cloud_configured=true
        fi
        
        if [ -n "$AZURE_CLIENT_ID" ]; then
            log_info "Azure integration available"
            cloud_configured=true
        fi
        
        if [ -n "$OCI_TENANCY_ID" ]; then
            log_info "Oracle OCI integration available"
            cloud_configured=true
        fi
        
        if [ "$cloud_configured" = true ]; then
            log_success "Cloud integration configured"
        else
            log_warning "No cloud credentials found - update .env file"
        fi
    fi
}

# Post deployment tasks
post_deployment() {
    log_info "Running post-deployment tasks..."
    
    # Create initial backup
    log_info "Creating initial backup..."
    ./scripts/backup-restore-enhanced.sh backup full || log_warning "Initial backup failed"
    
    # Run health checks
    log_info "Running health checks..."
    if [ -f "./scripts/health-check.sh" ]; then
        ./scripts/health-check.sh || log_warning "Health check script failed"
    fi
    
    log_success "Post-deployment tasks completed"
}

# Display access information
show_access_info() {
    echo
    echo -e "${GREEN}=============================================================================${NC}"
    echo -e "${GREEN}  Deployment Complete!${NC}"
    echo -e "${GREEN}=============================================================================${NC}"
    echo
    echo -e "${YELLOW}Access URLs:${NC}"
    
    case "$DEPLOYMENT_TYPE" in
        "development")
            echo "• Supabase Dashboard: http://localhost:8000"
            echo "• Neo4j Browser: http://localhost:7474"
            echo "• Flowise: http://localhost:3001"
            echo "• Open WebUI: http://localhost:8080"
            echo "• N8N: http://localhost:5678"
            ;;
        "staging"|"production")
            echo "• Main Application: https://localhost (via Traefik)"
            echo "• Traefik Dashboard: https://localhost:8080"
            echo "• Services available through reverse proxy"
            ;;
    esac
    
    echo
    echo -e "${YELLOW}Credentials:${NC}"
    if [ -f .env ]; then
        echo "• Supabase: admin / $(grep DASHBOARD_PASSWORD .env | cut -d'=' -f2)"
        echo "• Flowise: admin / $(grep FLOWISE_PASSWORD .env | cut -d'=' -f2)"
        echo "• Grafana: admin / $(grep GRAFANA_ADMIN_PASSWORD .env | cut -d'=' -f2)"
        echo "• Neo4j: neo4j / $(grep NEO4J_PASSWORD .env | cut -d'=' -f2)"
    fi
    
    echo
    echo -e "${YELLOW}Management Commands:${NC}"
    echo "• View logs: docker compose logs -f [service]"
    echo "• Stop services: docker compose down"
    echo "• Backup data: ./scripts/backup-restore-enhanced.sh backup full"
    echo "• Health check: ./scripts/health-check.sh"
    
    echo
    echo -e "${YELLOW}Important Notes:${NC}"
    echo "• All data is stored in ./volumes/ directory"
    echo "• Backup this directory regularly"
    echo "• Update API keys in .env file for external services"
    echo "• Monitor logs for any issues"
    
    if [ "$DEPLOYMENT_TYPE" = "production" ]; then
        echo
        echo -e "${RED}Production Security Reminders:${NC}"
        echo "• Never commit .env file to version control"
        echo "• Regularly rotate passwords and API keys"
        echo "• Keep Docker images updated"
        echo "• Monitor system resources and logs"
        echo "• Test backup and restore procedures"
    fi
    
    echo
    echo -e "${GREEN}Happy building! 🚀${NC}"
}

# Main execution
main() {
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_usage
        exit 0
    fi
    
    log_info "Starting deployment: $DEPLOYMENT_TYPE ($ENVIRONMENT)"
    
    check_prerequisites
    setup_environment
    create_networks
    initialize_data
    deploy_services
    validate_deployment
    setup_monitoring
    setup_cloud_integration
    post_deployment
    show_access_info
}

# Execute main function
main "$@"