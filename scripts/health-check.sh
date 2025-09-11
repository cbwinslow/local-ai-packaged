#!/bin/bash

# ========================================================================================
# Local AI Package - Comprehensive Health Check Script
# ========================================================================================
# This script performs comprehensive health checks on all services and components
# Provides detailed status reporting and recommendations for issues
# ========================================================================================

set -euo pipefail

# Color codes
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(dirname "$SCRIPT_DIR")"
readonly LOG_FILE="logs/health-check-$(date +%Y%m%d_%H%M%S).log"
readonly TIMEOUT=10

# Ensure logs directory exists
mkdir -p "$(dirname "$LOG_FILE")"

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

# Health check results
declare -a PASSED_CHECKS=()
declare -a FAILED_CHECKS=()
declare -a WARNING_CHECKS=()

# Add result to appropriate array
add_result() {
    local status="$1"
    local check_name="$2"
    local message="$3"
    
    case "$status" in
        "PASS")
            PASSED_CHECKS+=("$check_name: $message")
            success "$check_name: $message"
            ;;
        "FAIL")
            FAILED_CHECKS+=("$check_name: $message")
            error "$check_name: $message"
            ;;
        "WARN")
            WARNING_CHECKS+=("$check_name: $message")
            warning "$check_name: $message"
            ;;
    esac
}

# Check if URL is accessible
check_url() {
    local url="$1"
    local service_name="$2"
    local expected_code="${3:-200}"
    
    info "Checking $service_name at $url..."
    
    if curl -s -f --max-time "$TIMEOUT" "$url" >/dev/null 2>&1; then
        add_result "PASS" "$service_name" "Accessible at $url"
        return 0
    else
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$url" 2>/dev/null || echo "000")
        add_result "FAIL" "$service_name" "Not accessible at $url (HTTP $status_code)"
        return 1
    fi
}

# Check if port is open
check_port() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    
    info "Checking $service_name port $port..."
    
    if nc -z -w "$TIMEOUT" "$host" "$port" 2>/dev/null; then
        add_result "PASS" "$service_name" "Port $port is open"
        return 0
    else
        add_result "FAIL" "$service_name" "Port $port is not accessible"
        return 1
    fi
}

# Check Docker service status
check_docker_service() {
    local service_name="$1"
    
    info "Checking Docker service $service_name..."
    
    if docker-compose ps "$service_name" 2>/dev/null | grep -q "Up"; then
        local status=$(docker-compose ps "$service_name" | tail -n 1 | awk '{print $3}')
        add_result "PASS" "$service_name" "Container running ($status)"
        return 0
    else
        add_result "FAIL" "$service_name" "Container not running or not found"
        return 1
    fi
}

# Check environment variables
check_environment() {
    info "Checking environment configuration..."
    
    if [[ ! -f ".env" ]]; then
        add_result "FAIL" "Environment" ".env file not found"
        return 1
    fi
    
    local required_vars=(
        "POSTGRES_PASSWORD"
        "JWT_SECRET"
        "N8N_ENCRYPTION_KEY"
        "NEXTAUTH_SECRET"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env || grep -q "^${var}=your-" .env; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -eq 0 ]]; then
        add_result "PASS" "Environment" "All required variables are set"
    else
        add_result "FAIL" "Environment" "Missing variables: ${missing_vars[*]}"
    fi
}

# Check Docker system
check_docker_system() {
    info "Checking Docker system..."
    
    if ! command -v docker >/dev/null 2>&1; then
        add_result "FAIL" "Docker" "Docker command not found"
        return 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        add_result "FAIL" "Docker" "Docker daemon not running"
        return 1
    fi
    
    # Check Docker Compose
    if ! docker-compose version >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
        add_result "FAIL" "Docker Compose" "Docker Compose not available"
        return 1
    fi
    
    add_result "PASS" "Docker" "Docker system is healthy"
}

# Check system resources
check_system_resources() {
    info "Checking system resources..."
    
    # Check disk space
    local available_space=$(df "$ROOT_DIR" | awk 'NR==2 {print $4}')
    local available_gb=$((available_space / 1024 / 1024))
    
    if [[ $available_gb -lt 2 ]]; then
        add_result "FAIL" "Disk Space" "Only ${available_gb}GB available"
    elif [[ $available_gb -lt 5 ]]; then
        add_result "WARN" "Disk Space" "Low disk space: ${available_gb}GB available"
    else
        add_result "PASS" "Disk Space" "${available_gb}GB available"
    fi
    
    # Check memory
    local available_memory=$(free -g | awk 'NR==2{print $7}')
    if [[ $available_memory -lt 1 ]]; then
        add_result "WARN" "Memory" "Low available memory: ${available_memory}GB"
    else
        add_result "PASS" "Memory" "${available_memory}GB available"
    fi
}

# Check core infrastructure
check_infrastructure() {
    info "Checking core infrastructure services..."
    
    # Check Traefik
    check_url "http://localhost:80" "Traefik"
    
    # Check databases
    check_port "localhost" "5432" "PostgreSQL"
    check_port "localhost" "6379" "Redis"
    
    # Check Supabase
    check_url "http://localhost:8000/health" "Supabase API"
}

# Check AI services
check_ai_services() {
    info "Checking AI services..."
    
    # Check N8N
    check_url "http://localhost:5678" "N8N"
    
    # Check Flowise
    check_url "http://localhost:3002" "Flowise"
    
    # Check Open WebUI
    check_url "http://localhost:8081" "Open WebUI"
    
    # Check Langfuse
    check_url "http://localhost:3004" "Langfuse"
}

# Check databases
check_databases() {
    info "Checking database services..."
    
    # Check Qdrant
    check_url "http://localhost:6333" "Qdrant"
    
    # Check Neo4j
    check_url "http://localhost:7474" "Neo4j"
    
    # Check ClickHouse
    check_port "localhost" "8123" "ClickHouse"
    
    # Check MinIO
    check_port "localhost" "9001" "MinIO"
}

# Check monitoring
check_monitoring() {
    info "Checking monitoring services..."
    
    # Check Grafana
    check_url "http://localhost:3003" "Grafana"
    
    # Check Prometheus
    check_url "http://localhost:9090" "Prometheus"
}

# Check applications
check_applications() {
    info "Checking application services..."
    
    # Check Frontend
    check_url "http://localhost:3005" "Frontend"
    
    # Check Dashboard
    check_url "http://localhost:3006" "Dashboard"
    
    # Check SearXNG
    check_url "http://localhost:8082" "SearXNG"
    
    # Check Agentic RAG
    check_url "http://localhost:8001" "Agentic RAG"
}

# Generate comprehensive report
generate_report() {
    local total_checks=$((${#PASSED_CHECKS[@]} + ${#FAILED_CHECKS[@]} + ${#WARNING_CHECKS[@]}))
    local pass_rate=$((${#PASSED_CHECKS[@]} * 100 / total_checks))
    
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                          Health Check Report                                    ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${BLUE}📊 Summary:${NC}"
    echo "  Total Checks: $total_checks"
    echo "  Passed: ${#PASSED_CHECKS[@]}"
    echo "  Failed: ${#FAILED_CHECKS[@]}"
    echo "  Warnings: ${#WARNING_CHECKS[@]}"
    echo "  Pass Rate: ${pass_rate}%"
    echo ""
    
    if [[ ${#PASSED_CHECKS[@]} -gt 0 ]]; then
        echo -e "${GREEN}✅ Passed Checks:${NC}"
        for check in "${PASSED_CHECKS[@]}"; do
            echo "  ✓ $check"
        done
        echo ""
    fi
    
    if [[ ${#WARNING_CHECKS[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Warnings:${NC}"
        for check in "${WARNING_CHECKS[@]}"; do
            echo "  ⚠ $check"
        done
        echo ""
    fi
    
    if [[ ${#FAILED_CHECKS[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Failed Checks:${NC}"
        for check in "${FAILED_CHECKS[@]}"; do
            echo "  ✗ $check"
        done
        echo ""
        
        echo -e "${RED}🔧 Troubleshooting Steps:${NC}"
        echo "1. Check if services are running: docker-compose ps"
        echo "2. Review service logs: docker-compose logs <service-name>"
        echo "3. Restart failed services: docker-compose restart <service-name>"
        echo "4. Check environment configuration: cat .env"
        echo "5. Verify port availability: netstat -tuln | grep <port>"
        echo "6. Re-run startup script: ./scripts/start-all-services.sh"
        echo ""
    fi
    
    # Overall status
    if [[ ${#FAILED_CHECKS[@]} -eq 0 ]]; then
        if [[ ${#WARNING_CHECKS[@]} -eq 0 ]]; then
            echo -e "${GREEN}🎉 All systems are healthy and operational!${NC}"
        else
            echo -e "${YELLOW}⚠️  Systems are operational with minor warnings.${NC}"
        fi
        echo -e "${GREEN}✅ Local AI Package is ready for use.${NC}"
    else
        echo -e "${RED}🚨 Some systems have issues that need attention.${NC}"
        echo -e "${YELLOW}🔧 Please address the failed checks before proceeding.${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}📋 Report saved to: $LOG_FILE${NC}"
    echo -e "${BLUE}📅 Report generated: $(date)${NC}"
}

# Show banner
show_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        Local AI Package Health Check                            ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

# Main execution
main() {
    show_banner
    
    cd "$ROOT_DIR"
    
    info "Starting comprehensive health check..."
    info "Results will be saved to: $LOG_FILE"
    echo ""
    
    # Run all health checks
    check_docker_system
    check_environment
    check_system_resources
    check_infrastructure
    check_ai_services
    check_databases
    check_monitoring
    check_applications
    
    # Generate report
    generate_report
    
    # Exit with appropriate code
    if [[ ${#FAILED_CHECKS[@]} -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# Execute main function
main "$@"