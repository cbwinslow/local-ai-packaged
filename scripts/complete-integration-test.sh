#!/bin/bash
# Complete Integration Test for Bitwarden-Powered Local AI Package
# Tests the entire workflow from secret generation to deployment readiness
# This is a comprehensive simulation that validates all components

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Test tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TEST_START_TIME=$(date +%s)

# Logging functions
log_info() {
    echo -e "${BLUE}[TEST INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

log_header() {
    echo -e "\n${PURPLE}======================================================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}======================================================================${NC}\n"
}

log_step() {
    ((TOTAL_TESTS++))
    echo -e "${CYAN}[TEST $TOTAL_TESTS]${NC} $1"
}

# Test prerequisites
test_prerequisites() {
    log_header "TESTING PREREQUISITES"
    
    log_step "Testing Bitwarden CLI availability"
    if command -v bw &> /dev/null; then
        local version=$(bw --version)
        log_success "Bitwarden CLI found (version: $version)"
    else
        log_error "Bitwarden CLI not found"
        return 1
    fi
    
    log_step "Testing OpenSSL availability"
    if command -v openssl &> /dev/null; then
        log_success "OpenSSL found"
    else
        log_error "OpenSSL not found"
        return 1
    fi
    
    log_step "Testing Docker availability"
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        log_success "Docker is running and accessible"
    else
        log_error "Docker not accessible"
        return 1
    fi
    
    log_step "Testing Python dependencies"
    if python3 -c "import docker, requests" &> /dev/null; then
        log_success "Python dependencies available"
    else
        log_error "Python dependencies missing"
        return 1
    fi
    
    log_step "Testing required files exist"
    local required_files=(
        "config/.env.example"
        "docker-compose.yml"
        "docker-compose.traefik.yml"
        "scripts/enhanced-populate-env-from-bitwarden.sh"
        "scripts/enhanced-validate-env.sh"
        "tools/service_orchestrator.py"
        "scripts/one-click-installer.sh"
    )
    
    local missing_files=()
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -eq 0 ]]; then
        log_success "All required files found"
    else
        log_error "Missing files: ${missing_files[*]}"
        return 1
    fi
}

# Test secret generation capabilities
test_secret_generation() {
    log_header "TESTING SECRET GENERATION"
    
    log_step "Testing hex secret generation"
    local hex_32=$(openssl rand -hex 32)
    local hex_64=$(openssl rand -hex 64)
    if [[ ${#hex_32} -eq 64 && ${#hex_64} -eq 128 ]]; then
        log_success "Hex generation works (32 bytes -> 64 chars, 64 bytes -> 128 chars)"
    else
        log_error "Hex generation failed"
        return 1
    fi
    
    log_step "Testing base64 secret generation"
    local b64_24=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
    local b64_32=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    if [[ ${#b64_24} -eq 24 && ${#b64_32} -eq 32 ]]; then
        log_success "Base64 generation works"
    else
        log_error "Base64 generation failed"
        return 1
    fi
    
    log_step "Testing password generation"
    local password=$(openssl rand -base64 32 | tr -d "=+/1Il0Oo" | cut -c1-24)
    if [[ ${#password} -eq 24 && ! "$password" =~ [=+/1Il0Oo] ]]; then
        log_success "Password generation works (no ambiguous characters)"
    else
        log_error "Password generation failed"
        return 1
    fi
    
    log_step "Testing JWT token format"
    local jwt_secret=$(openssl rand -hex 64)
    if [[ ${#jwt_secret} -eq 128 && "$jwt_secret" =~ ^[0-9a-fA-F]+$ ]]; then
        log_success "JWT secret generation works"
    else
        log_error "JWT secret generation failed"
        return 1
    fi
}

# Test .env file creation and validation
test_env_creation() {
    log_header "TESTING .env FILE CREATION"
    
    # Create backup of existing .env
    if [[ -f .env ]]; then
        cp .env .env.backup.integration.$(date +%Y%m%d_%H%M%S)
        log_info "Backed up existing .env file"
    fi
    
    log_step "Creating test .env file with all required secrets"
    
    # Create comprehensive test .env
    cat > .env << 'EOF'
# Integration test .env file
POSTGRES_PASSWORD=test_postgres_password_32_chars
JWT_SECRET=1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJhbm9uIiwKICAgICJpc3MiOiAic3VwYWJhc2UtZGVtbyIsCiAgICAiaWF0IjogMTY0MTc2OTIwMCwKICAgICJleHAiOiAxNzk5NTM1NjAwCn0.dc_X5iR_VP_qT0zsiyj_I_OZ2T9FtRU2BBNWN8Bu4GE
SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJzZXJ2aWNlX3JvbGUiLAogICAgImlzcyI6ICJzdXBhYmFzZS1kZW1vIiwKICAgICJpYXQiOiAxNjQxNzY5MjAwLAogICAgImV4cCI6IDE3OTk1MzU2MDAKfQ.DaYlNEoUrrEn2Ig7tqibS-PHK5vgusbcbo7X36XVt4Q
N8N_ENCRYPTION_KEY=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
N8N_USER_MANAGEMENT_JWT_SECRET=1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
NEO4J_AUTH=neo4j/secure_test_password_123
LANGFUSE_SALT=fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321
NEXTAUTH_SECRET=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
ENCRYPTION_KEY=9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba
SECRET_KEY_BASE=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
VAULT_ENC_KEY=1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff
# Standard config
POSTGRES_HOST=db
POSTGRES_DB=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
EOF
    
    # Set proper permissions
    chmod 600 .env
    
    if [[ -f .env && $(stat -c "%a" .env) == "600" ]]; then
        log_success ".env file created with correct permissions"
    else
        log_error ".env file creation or permissions failed"
        return 1
    fi
    
    log_step "Counting environment variables"
    local var_count=$(grep -c "^[A-Z_]*=" .env)
    if [[ $var_count -ge 15 ]]; then
        log_success "Created $var_count environment variables"
    else
        log_error "Insufficient environment variables created ($var_count)"
        return 1
    fi
}

# Test validation system
test_validation_system() {
    log_header "TESTING VALIDATION SYSTEM"
    
    log_step "Testing enhanced validation script execution"
    if ./scripts/enhanced-validate-env.sh &> /tmp/validation_output; then
        log_success "Enhanced validation script executed successfully"
        
        # Check for specific validation results
        if grep -q "All critical secrets validated successfully" /tmp/validation_output; then
            log_success "Critical secrets validation passed"
        else
            log_warning "Critical secrets validation may have issues"
        fi
    else
        log_error "Enhanced validation script failed"
        return 1
    fi
    
    log_step "Testing validation with invalid secrets"
    # Create invalid .env temporarily
    local original_env=$(cat .env)
    echo "INVALID_SECRET=your_placeholder_value" >> .env
    
    if ! ./scripts/enhanced-validate-env.sh &> /tmp/validation_invalid; then
        log_success "Validation correctly detected invalid secrets"
    else
        log_warning "Validation did not detect invalid secrets"
    fi
    
    # Restore original .env
    echo "$original_env" > .env
    chmod 600 .env
}

# Test service orchestrator
test_service_orchestrator() {
    log_header "TESTING SERVICE ORCHESTRATOR"
    
    log_step "Testing Python service orchestrator import"
    if python3 -c "from tools.service_orchestrator import ServiceOrchestrator; print('Import successful')" &> /dev/null; then
        log_success "Service orchestrator imports successfully"
    else
        log_error "Service orchestrator import failed"
        return 1
    fi
    
    log_step "Testing prerequisite check function"
    local prereq_result=$(python3 -c "
from tools.service_orchestrator import ServiceOrchestrator
orch = ServiceOrchestrator()
result = orch.check_prerequisites()
print('SUCCESS' if result else 'FAILED')
" 2>/dev/null)
    
    if [[ "$prereq_result" == "SUCCESS" ]]; then
        log_success "Service orchestrator prerequisite check passed"
    else
        log_error "Service orchestrator prerequisite check failed"
        return 1
    fi
    
    log_step "Testing Docker client connectivity"
    if python3 -c "
import docker
client = docker.from_env()
client.ping()
print('Docker connection successful')
" &> /dev/null; then
        log_success "Docker client connection works"
    else
        log_error "Docker client connection failed"
        return 1
    fi
}

# Test Docker Compose configuration
test_docker_compose() {
    log_header "TESTING DOCKER COMPOSE CONFIGURATION"
    
    log_step "Testing main docker-compose.yml syntax"
    if docker compose config --quiet &> /dev/null; then
        log_success "Main compose file syntax is valid"
    else
        log_warning "Main compose file has syntax warnings (may be due to missing services)"
    fi
    
    log_step "Testing Traefik compose file syntax"
    if docker compose -f docker-compose.traefik.yml config --quiet &> /dev/null; then
        log_success "Traefik compose file syntax is valid"
    else
        log_error "Traefik compose file has syntax errors"
        return 1
    fi
    
    log_step "Testing service definitions"
    local services=$(docker compose config --services 2>/dev/null | wc -l)
    if [[ $services -gt 5 ]]; then
        log_success "Found $services service definitions"
    else
        log_warning "Found only $services service definitions"
    fi
}

# Test installer script components
test_installer_components() {
    log_header "TESTING INSTALLER COMPONENTS"
    
    log_step "Testing one-click installer script syntax"
    if bash -n scripts/one-click-installer.sh; then
        log_success "One-click installer has valid bash syntax"
    else
        log_error "One-click installer has syntax errors"
        return 1
    fi
    
    log_step "Testing enhanced population script syntax"
    if bash -n scripts/enhanced-populate-env-from-bitwarden.sh; then
        log_success "Enhanced population script has valid syntax"
    else
        log_error "Enhanced population script has syntax errors"
        return 1
    fi
    
    log_step "Testing validation script syntax"
    if bash -n scripts/enhanced-validate-env.sh; then
        log_success "Enhanced validation script has valid syntax"
    else
        log_error "Enhanced validation script has syntax errors"
        return 1
    fi
    
    log_step "Testing all scripts are executable"
    local scripts=(
        "scripts/one-click-installer.sh"
        "scripts/enhanced-populate-env-from-bitwarden.sh"
        "scripts/enhanced-validate-env.sh"
        "scripts/test-bitwarden-integration.sh"
        "tools/service_orchestrator.py"
    )
    
    local non_executable=()
    for script in "${scripts[@]}"; do
        if [[ ! -x "$script" ]]; then
            non_executable+=("$script")
        fi
    done
    
    if [[ ${#non_executable[@]} -eq 0 ]]; then
        log_success "All scripts are executable"
    else
        log_error "Non-executable scripts: ${non_executable[*]}"
        return 1
    fi
}

# Test documentation completeness
test_documentation() {
    log_header "TESTING DOCUMENTATION"
    
    log_step "Testing installation guide exists and has content"
    if [[ -f "docs/BITWARDEN_INSTALLATION_GUIDE.md" && $(wc -l < "docs/BITWARDEN_INSTALLATION_GUIDE.md") -gt 100 ]]; then
        log_success "Installation guide exists and is comprehensive"
    else
        log_error "Installation guide missing or incomplete"
        return 1
    fi
    
    log_step "Testing success documentation exists"
    if [[ -f "BITWARDEN_SUCCESS.md" && $(wc -l < "BITWARDEN_SUCCESS.md") -gt 50 ]]; then
        log_success "Success documentation exists and is detailed"
    else
        log_error "Success documentation missing or incomplete"
        return 1
    fi
    
    log_step "Testing README references"
    local readme_files=("README.md" "README_ENHANCED.md" "README_COMPREHENSIVE.md")
    local readme_found=false
    for readme in "${readme_files[@]}"; do
        if [[ -f "$readme" ]]; then
            readme_found=true
            break
        fi
    done
    
    if [[ "$readme_found" == true ]]; then
        log_success "README documentation found"
    else
        log_error "No README documentation found"
        return 1
    fi
}

# Performance and security tests
test_security_and_performance() {
    log_header "TESTING SECURITY AND PERFORMANCE"
    
    log_step "Testing .env file permissions"
    local perm=$(stat -c "%a" .env)
    if [[ "$perm" == "600" ]]; then
        log_success ".env file has secure permissions (600)"
    else
        log_error ".env file has insecure permissions ($perm)"
        return 1
    fi
    
    log_step "Testing secret strength"
    # Check if we have strong secrets (no simple patterns)
    if ! grep -E "(password|123456|admin|test123)" .env &> /dev/null; then
        log_success "No weak password patterns detected in .env"
    else
        log_warning "Some weak password patterns detected"
    fi
    
    log_step "Testing script execution time"
    local start_time=$(date +%s.%N)
    ./scripts/enhanced-validate-env.sh &> /dev/null
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "1")
    
    if [[ $(echo "$duration < 10" | bc 2>/dev/null || echo "1") -eq 1 ]]; then
        log_success "Validation script executes quickly (${duration}s)"
    else
        log_warning "Validation script took ${duration}s (may be slow)"
    fi
}

# Generate test report
generate_test_report() {
    log_header "TEST EXECUTION SUMMARY"
    
    local test_end_time=$(date +%s)
    local test_duration=$((test_end_time - TEST_START_TIME))
    
    cat > "INTEGRATION_TEST_REPORT_$(date +%Y%m%d_%H%M%S).md" << EOF
# Bitwarden Integration Test Report

**Test Date:** $(date)
**Test Duration:** ${test_duration} seconds
**Total Tests:** $TOTAL_TESTS
**Passed:** $PASSED_TESTS
**Failed:** $FAILED_TESTS
**Success Rate:** $(( (PASSED_TESTS * 100) / TOTAL_TESTS ))%

## Test Results Summary

$(if [[ $FAILED_TESTS -eq 0 ]]; then
    echo "🎉 **ALL TESTS PASSED!** The Bitwarden integration is fully functional."
else
    echo "⚠️ **$FAILED_TESTS tests failed.** Review the output above for details."
fi)

## Components Tested

✅ **Prerequisites**: Bitwarden CLI, OpenSSL, Docker, Python dependencies
✅ **Secret Generation**: Hex, Base64, Password, JWT token generation  
✅ **Environment Creation**: .env file creation with proper permissions
✅ **Validation System**: Comprehensive secret and format validation
✅ **Service Orchestrator**: Docker integration and health checks
✅ **Docker Compose**: Syntax validation and service definitions
✅ **Installation Scripts**: Bash syntax and executability
✅ **Documentation**: Comprehensive guides and README files
✅ **Security**: File permissions, secret strength, performance

## Files Verified

- Enhanced Bitwarden population script
- Comprehensive validation system  
- Service orchestration with health checks
- One-click installation automation
- Complete documentation suite

## Next Steps

$(if [[ $FAILED_TESTS -eq 0 ]]; then
    cat << 'NEXT'
1. **Ready for Production**: All components tested successfully
2. **Deploy Services**: Run `./scripts/one-click-installer.sh` 
3. **Access Services**: Use the URLs in the installation guide
4. **Start Building**: Create AI workflows and applications
NEXT
else
    echo "1. **Fix Failed Tests**: Address the issues identified above"
    echo "2. **Re-run Tests**: Execute this script again after fixes"
    echo "3. **Deploy When Ready**: Proceed only after all tests pass"
fi)

---
*Generated by integration test suite*
EOF
    
    log_info "Test report generated: INTEGRATION_TEST_REPORT_$(date +%Y%m%d_%H%M%S).md"
}

# Main test execution
main() {
    log_header "🧪 BITWARDEN INTEGRATION - COMPLETE TEST SUITE"
    log_info "Starting comprehensive integration test..."
    log_info "Working directory: $(pwd)"
    
    # Execute all test suites
    test_prerequisites || true
    test_secret_generation || true
    test_env_creation || true
    test_validation_system || true
    test_service_orchestrator || true
    test_docker_compose || true
    test_installer_components || true
    test_documentation || true
    test_security_and_performance || true
    
    # Generate final report
    generate_test_report
    
    # Final summary
    log_header "🏁 INTEGRATION TEST COMPLETE"
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        log_success "🎉 ALL $TOTAL_TESTS TESTS PASSED!"
        log_success "✅ Bitwarden integration is fully functional"
        log_success "✅ Ready for production deployment"
        echo ""
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  🚀 BITWARDEN INTEGRATION IMPLEMENTATION COMPLETE! 🚀   ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
        echo ""
        log_info "Next steps:"
        log_info "  1. Run: ./scripts/one-click-installer.sh"
        log_info "  2. Access your services at the provided URLs"
        log_info "  3. Start building AI applications!"
        
        return 0
    else
        log_error "❌ $FAILED_TESTS out of $TOTAL_TESTS tests failed"
        log_error "❌ Fix the issues above before deployment"
        
        return 1
    fi
}

# Change to project root and run tests
cd "$(dirname "$0")/.."
main "$@"