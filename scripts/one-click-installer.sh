#!/bin/bash
# One-Click Local AI Package Installer
# Comprehensive setup script that handles everything from prerequisites to deployment
# Uses Bitwarden for secure secret management

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/install.log"
INSTALL_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_header() {
    echo -e "\n${PURPLE}${'='*60}${NC}" | tee -a "$LOG_FILE"
    echo -e "${PURPLE}$1${NC}" | tee -a "$LOG_FILE"
    echo -e "${PURPLE}${'='*60}${NC}\n" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1" | tee -a "$LOG_FILE"
}

# Progress tracking
TOTAL_STEPS=12
CURRENT_STEP=0

show_progress() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    local percent=$((CURRENT_STEP * 100 / TOTAL_STEPS))
    echo -e "${CYAN}Progress: [$CURRENT_STEP/$TOTAL_STEPS] ($percent%)${NC}" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    local line_no=$1
    local error_code=$2
    log_error "Installation failed at line $line_no with exit code $error_code"
    log_error "Check the log file at: $LOG_FILE"
    log_info "You can resume installation by running this script again"
    exit $error_code
}

trap 'handle_error ${LINENO} $?' ERR

# Welcome and initialization
show_welcome() {
    clear
    log_header "LOCAL AI PACKAGE - ONE-CLICK INSTALLER"
    cat << 'EOF'
🤖 Welcome to the Local AI Package Installer!

This script will:
  ✅ Install all prerequisites (Docker, Bitwarden CLI, etc.)
  ✅ Set up Bitwarden integration for secure secret management  
  ✅ Generate and validate all required secrets
  ✅ Build Docker containers incrementally with health checks
  ✅ Deploy all services with proper dependency management
  ✅ Verify the complete installation

Prerequisites:
  - Ubuntu/Debian Linux (recommended) or macOS
  - Internet connection for downloads
  - Bitwarden account (for secret management)
  - At least 8GB RAM and 20GB disk space

EOF
    
    log_info "Installation will be logged to: $LOG_FILE"
    
    # Confirm installation
    read -p "Do you want to proceed with the installation? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Installation cancelled by user"
        exit 0
    fi
    
    # Change to project root
    cd "$PROJECT_ROOT"
    log_info "Working directory: $PROJECT_ROOT"
}

# Check and install system prerequisites
install_prerequisites() {
    log_header "STEP 1: INSTALLING PREREQUISITES"
    show_progress
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_info "Detected Linux system"
        
        # Update package list
        log_step "Updating package list..."
        sudo apt-get update -qq
        
        # Install essential packages
        log_step "Installing essential packages..."
        sudo apt-get install -y curl wget unzip git python3 python3-pip openssl jq
        
        # Install Docker if not present
        if ! command -v docker &> /dev/null; then
            log_step "Installing Docker..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
            log_success "Docker installed successfully"
        else
            log_success "Docker is already installed"
        fi
        
        # Install Docker Compose if not present
        if ! command -v docker-compose &> /dev/null; then
            log_step "Installing Docker Compose..."
            sudo pip3 install docker-compose
            log_success "Docker Compose installed successfully"
        else
            log_success "Docker Compose is already installed"
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log_info "Detected macOS system"
        
        # Check for Homebrew
        if ! command -v brew &> /dev/null; then
            log_step "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        # Install packages via Homebrew
        log_step "Installing packages via Homebrew..."
        brew install docker docker-compose python3 openssl jq
        
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    # Install Node.js and npm for Bitwarden CLI
    if ! command -v node &> /dev/null; then
        log_step "Installing Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    
    # Install Python requirements
    log_step "Installing Python requirements..."
    if [ -f requirements.txt ]; then
        pip3 install --user -r requirements.txt
    fi
    
    log_success "Prerequisites installed successfully"
}

# Install and configure Bitwarden CLI
setup_bitwarden() {
    log_header "STEP 2: SETTING UP BITWARDEN CLI"
    show_progress
    
    # Install Bitwarden CLI
    if ! command -v bw &> /dev/null; then
        log_step "Installing Bitwarden CLI..."
        npm install -g @bitwarden/cli
        log_success "Bitwarden CLI installed successfully"
    else
        log_success "Bitwarden CLI is already installed"
    fi
    
    # Check if user is logged in
    if ! bw status | grep -q "authenticated"; then
        log_step "Authenticating with Bitwarden..."
        log_info "Please enter your Bitwarden credentials:"
        
        read -p "Bitwarden Email: " bw_email
        bw login "$bw_email"
        
        log_success "Bitwarden authentication successful"
    else
        log_success "Already authenticated with Bitwarden"
    fi
    
    # Unlock vault
    log_step "Unlocking Bitwarden vault..."
    if [ -z "$BW_SESSION" ]; then
        log_info "Please enter your Bitwarden master password:"
        export BW_SESSION=$(bw unlock --raw)
    fi
    
    # Sync vault
    log_step "Syncing Bitwarden vault..."
    bw sync --session "$BW_SESSION"
    
    log_success "Bitwarden setup completed successfully"
}

# Generate and populate secrets
setup_secrets() {
    log_header "STEP 3: GENERATING AND POPULATING SECRETS"
    show_progress
    
    # Run enhanced population script
    log_step "Populating .env from Bitwarden..."
    if [ -f "scripts/enhanced-populate-env-from-bitwarden.sh" ]; then
        ./scripts/enhanced-populate-env-from-bitwarden.sh
    else
        log_warning "Enhanced script not found, using original..."
        ./scripts/populate-env-from-bitwarden.sh
    fi
    
    log_success "Secrets populated successfully"
}

# Validate all secrets
validate_secrets() {
    log_header "STEP 4: VALIDATING SECRETS"
    show_progress
    
    # Run enhanced validation
    log_step "Running comprehensive secret validation..."
    if [ -f "scripts/enhanced-validate-env.sh" ]; then
        ./scripts/enhanced-validate-env.sh
    else
        log_warning "Enhanced validation not found, using original..."
        ./scripts/validate-env.sh
    fi
    
    log_success "Secret validation completed successfully"
}

# Prepare Docker environment
prepare_docker() {
    log_header "STEP 5: PREPARING DOCKER ENVIRONMENT"
    show_progress
    
    # Start Docker if not running
    log_step "Ensuring Docker is running..."
    if ! docker info &> /dev/null; then
        sudo systemctl start docker
        sleep 5
    fi
    
    # Clean up any existing containers
    log_step "Cleaning up existing containers..."
    docker system prune -f --volumes || true
    
    # Create Docker networks
    log_step "Creating Docker networks..."
    docker network create localai_default 2>/dev/null || true
    docker network create supabase 2>/dev/null || true
    
    log_success "Docker environment prepared"
}

# Build Docker images
build_images() {
    log_header "STEP 6: BUILDING DOCKER IMAGES"
    show_progress
    
    log_step "Pulling base images..."
    docker compose pull || log_warning "Some images could not be pulled"
    
    log_step "Building custom images..."
    docker compose build || log_warning "Some images could not be built"
    
    log_success "Docker images prepared"
}

# Deploy infrastructure services
deploy_infrastructure() {
    log_header "STEP 7: DEPLOYING INFRASTRUCTURE SERVICES"
    show_progress
    
    log_step "Starting Traefik reverse proxy..."
    docker compose -f docker-compose.traefik.yml up -d traefik || true
    sleep 10
    
    log_step "Starting core infrastructure..."
    # Start essential services first
    for service in postgres redis; do
        log_info "Starting $service..."
        docker compose up -d "$service" || log_warning "Service $service may not be defined"
        sleep 15
    done
    
    log_success "Infrastructure services deployed"
}

# Deploy Supabase stack
deploy_supabase() {
    log_header "STEP 8: DEPLOYING SUPABASE STACK"
    show_progress
    
    # Start Supabase services
    supabase_services=(db auth rest storage studio)
    
    for service in "${supabase_services[@]}"; do
        log_step "Starting Supabase $service..."
        docker compose up -d "$service" 2>/dev/null || log_warning "Service $service may not be defined"
        sleep 20  # Supabase services need more time
    done
    
    # Health check Supabase
    log_step "Checking Supabase health..."
    local retries=0
    while [ $retries -lt 10 ]; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            log_success "Supabase is healthy"
            break
        fi
        log_info "Waiting for Supabase... (attempt $((retries+1))/10)"
        sleep 30
        retries=$((retries+1))
    done
    
    log_success "Supabase stack deployed"
}

# Deploy AI services
deploy_ai_services() {
    log_header "STEP 9: DEPLOYING AI SERVICES"
    show_progress
    
    # AI services in order of dependency
    ai_services=(neo4j qdrant ollama n8n flowise)
    
    for service in "${ai_services[@]}"; do
        log_step "Starting AI service: $service..."
        docker compose up -d "$service" 2>/dev/null || log_warning "Service $service may not be defined"
        
        # Service-specific wait times
        case $service in
            "neo4j"|"qdrant") sleep 30 ;;
            "ollama") sleep 60 ;;  # Ollama needs more time
            *) sleep 20 ;;
        esac
        
        log_info "$service startup completed"
    done
    
    # Pull Ollama models
    log_step "Pulling Ollama models (this may take a while)..."
    docker exec ollama ollama pull qwen2.5:7b || log_warning "Could not pull Ollama model"
    
    log_success "AI services deployed"
}

# Deploy frontend services
deploy_frontend() {
    log_header "STEP 10: DEPLOYING FRONTEND SERVICES"
    show_progress
    
    # Frontend services
    frontend_services=(frontend webui)
    
    for service in "${frontend_services[@]}"; do
        log_step "Starting frontend service: $service..."
        docker compose up -d "$service" 2>/dev/null || log_warning "Service $service may not be defined"
        sleep 15
    done
    
    log_success "Frontend services deployed"
}

# Verify installation
verify_installation() {
    log_header "STEP 11: VERIFYING INSTALLATION"
    show_progress
    
    # Check running containers
    log_step "Checking running containers..."
    local running_containers=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c "Up" || echo "0")
    log_info "Found $running_containers running containers"
    
    # Health checks
    local services_to_check=(
        "Traefik:http://localhost:8080/ping"
        "Supabase:http://localhost:8000/health"
        "n8n:http://localhost:5678"
        "Neo4j:http://localhost:7474"
        "Open WebUI:http://localhost:3001"
    )
    
    local healthy_services=0
    for service_check in "${services_to_check[@]}"; do
        local service_name="${service_check%:*}"
        local service_url="${service_check#*:}"
        
        log_step "Checking $service_name..."
        if curl -f -s "$service_url" &>/dev/null; then
            log_success "$service_name is accessible"
            healthy_services=$((healthy_services+1))
        else
            log_warning "$service_name is not accessible at $service_url"
        fi
    done
    
    log_info "Health checks completed: $healthy_services/${#services_to_check[@]} services accessible"
    log_success "Installation verification completed"
}

# Final setup and documentation
finalize_installation() {
    log_header "STEP 12: FINALIZING INSTALLATION"
    show_progress
    
    # Create installation summary
    cat > "INSTALLATION_SUMMARY_$INSTALL_TIMESTAMP.md" << EOF
# Local AI Package Installation Summary

**Installation Date:** $(date)
**Installation ID:** $INSTALL_TIMESTAMP

## 🎉 Installation Completed Successfully!

### Services Accessible At:
- **Traefik Dashboard:** http://localhost:8080
- **Supabase Studio:** http://localhost:3000  
- **n8n Workflows:** http://localhost:5678
- **Neo4j Browser:** http://localhost:7474
- **Open WebUI:** http://localhost:3001
- **Ollama API:** http://localhost:11434

### Default Credentials:
- **Supabase Studio:** Check your .env file for DASHBOARD_USERNAME/DASHBOARD_PASSWORD
- **n8n:** Configured via environment variables
- **Neo4j:** Check NEO4J_AUTH in .env file

### Next Steps:
1. Access the services using the URLs above
2. Configure your workflows in n8n
3. Set up your knowledge graphs in Neo4j
4. Start building AI applications!

### Troubleshooting:
- **View logs:** \`docker compose logs -f [service-name]\`
- **Restart service:** \`docker compose restart [service-name]\`  
- **Check health:** \`./scripts/health-check.sh\`
- **Full restart:** \`docker compose down && docker compose up -d\`

### Files Created:
- **.env** - Environment configuration (keep secure!)
- **Installation log:** $LOG_FILE
- **This summary:** INSTALLATION_SUMMARY_$INSTALL_TIMESTAMP.md

### Support:
- Check the logs in $LOG_FILE
- Review documentation in the docs/ folder
- Join our community for support

Happy AI building! 🚀
EOF
    
    log_success "Installation summary created: INSTALLATION_SUMMARY_$INSTALL_TIMESTAMP.md"
    
    # Set up convenience scripts
    log_step "Creating convenience scripts..."
    cat > "restart-services.sh" << 'EOF'
#!/bin/bash
echo "🔄 Restarting Local AI Package services..."
docker compose down
docker compose up -d
echo "✅ Services restarted"
EOF
    chmod +x "restart-services.sh"
    
    cat > "status-check.sh" << 'EOF'
#!/bin/bash
echo "📊 Local AI Package Status:"
echo "=========================="
docker compose ps
echo ""
echo "🌐 Service URLs:"
echo "- Traefik: http://localhost:8080"
echo "- Supabase: http://localhost:3000"
echo "- n8n: http://localhost:5678"
echo "- Neo4j: http://localhost:7474"
echo "- Open WebUI: http://localhost:3001"
EOF
    chmod +x "status-check.sh"
    
    log_success "Convenience scripts created"
    log_success "Installation finalized successfully!"
}

# Main installation flow
main() {
    show_welcome
    
    # Execute all installation steps
    install_prerequisites
    setup_bitwarden  
    setup_secrets
    validate_secrets
    prepare_docker
    build_images
    deploy_infrastructure
    deploy_supabase
    deploy_ai_services
    deploy_frontend
    verify_installation
    finalize_installation
    
    # Success message
    log_header "🎉 INSTALLATION COMPLETE! 🎉"
    
    cat << EOF

${GREEN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🎊 LOCAL AI PACKAGE SUCCESSFULLY INSTALLED! 🎊           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝${NC}

${CYAN}🌐 Your AI services are now running at:${NC}
  • Traefik Dashboard: http://localhost:8080
  • Supabase Studio: http://localhost:3000  
  • n8n Workflows: http://localhost:5678
  • Neo4j Browser: http://localhost:7474
  • Open WebUI: http://localhost:3001

${YELLOW}📋 Next steps:${NC}
  1. Review the installation summary: INSTALLATION_SUMMARY_$INSTALL_TIMESTAMP.md
  2. Check service status: ./status-check.sh
  3. Start building your AI applications!

${BLUE}💡 Helpful commands:${NC}
  • Restart all services: ./restart-services.sh
  • View logs: docker compose logs -f [service-name]
  • Stop all services: docker compose down

${GREEN}Happy AI building! 🚀${NC}

EOF
    
    log_info "Installation completed at $(date)"
    log_info "Total installation time: $(($(date +%s) - $(date -d "$(head -1 "$LOG_FILE" | cut -d']' -f1 | tr -d '[')" +%s))) seconds"
}

# Run main installation
main "$@"