#!/bin/bash

# =============================================================================
# Cloudflare Terraform Deployment Script
# =============================================================================
# This script deploys the Local AI Package infrastructure to Cloudflare
# =============================================================================

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TERRAFORM_DIR="${SCRIPT_DIR}"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly LOG_FILE="${PROJECT_ROOT}/logs/terraform-deploy.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    log "ERROR: $1"
    exit 1
}

# Check if required tools are installed
check_dependencies() {
    echo -e "${BLUE}🔍 Checking dependencies...${NC}"
    
    local deps=("terraform" "jq")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            error_exit "Required tool '$dep' is not installed"
        fi
    done
    
    echo -e "${GREEN}✅ All dependencies found${NC}"
}

# Validate Terraform configuration
validate_terraform() {
    echo -e "${BLUE}🔍 Validating Terraform configuration...${NC}"
    
    cd "$TERRAFORM_DIR"
    
    if ! terraform fmt -check; then
        echo -e "${YELLOW}⚠️  Formatting issues found. Auto-fixing...${NC}"
        terraform fmt
    fi
    
    if ! terraform validate; then
        error_exit "Terraform configuration validation failed"
    fi
    
    echo -e "${GREEN}✅ Terraform configuration is valid${NC}"
}

# Initialize Terraform
init_terraform() {
    echo -e "${BLUE}🚀 Initializing Terraform...${NC}"
    
    cd "$TERRAFORM_DIR"
    
    terraform init -upgrade
    
    echo -e "${GREEN}✅ Terraform initialized${NC}"
}

# Plan Terraform deployment
plan_terraform() {
    echo -e "${BLUE}📋 Planning Terraform deployment...${NC}"
    
    cd "$TERRAFORM_DIR"
    
    # Check if terraform.tfvars exists
    if [[ ! -f "terraform.tfvars" ]]; then
        echo -e "${YELLOW}⚠️  terraform.tfvars not found. Please create it from terraform.tfvars.example${NC}"
        echo "Required variables:"
        echo "- cloudflare_api_token"
        echo "- cloudflare_account_id"
        echo "- domain_name (default: opendiscourse.net)"
        echo "- environment (default: prod)"
        error_exit "Missing terraform.tfvars file"
    fi
    
    terraform plan -out=tfplan
    
    echo -e "${GREEN}✅ Terraform plan created${NC}"
}

# Apply Terraform deployment
apply_terraform() {
    echo -e "${BLUE}🚀 Applying Terraform deployment...${NC}"
    
    cd "$TERRAFORM_DIR"
    
    # Apply with auto-approve if non-interactive
    if [[ "${CI:-false}" == "true" ]]; then
        terraform apply -auto-approve tfplan
    else
        terraform apply tfplan
    fi
    
    echo -e "${GREEN}✅ Terraform deployment completed${NC}"
}

# Show deployment outputs
show_outputs() {
    echo -e "${BLUE}📊 Deployment outputs:${NC}"
    
    cd "$TERRAFORM_DIR"
    
    terraform output -json > outputs.json
    
    echo -e "${GREEN}Domain:${NC} $(terraform output -raw domain)"
    echo -e "${GREEN}Zone ID:${NC} $(terraform output -raw zone_id)"
    
    echo -e "${BLUE}Service URLs:${NC}"
    terraform output -json services | jq -r 'to_entries[] | "  \(.key): \(.value)"'
    
    echo -e "${BLUE}R2 Buckets:${NC}"
    terraform output -json r2_buckets | jq -r 'to_entries[] | "  \(.key): \(.value)"'
    
    echo -e "${BLUE}D1 Database:${NC}"
    echo "  Name: $(terraform output -json d1_database | jq -r '.name')"
    echo "  ID: $(terraform output -json d1_database | jq -r '.id')"
}

# Update project configuration with Terraform outputs
update_project_config() {
    echo -e "${BLUE}🔧 Updating project configuration...${NC}"
    
    cd "$TERRAFORM_DIR"
    
    local domain=$(terraform output -raw domain)
    local zone_id=$(terraform output -raw zone_id)
    
    # Update .env.template with actual domain
    local env_template="${PROJECT_ROOT}/.env.template"
    if [[ -f "$env_template" ]]; then
        sed -i.bak "s/opendiscourse\.net/${domain}/g" "$env_template"
        echo -e "${GREEN}✅ Updated .env.template with domain: ${domain}${NC}"
    fi
    
    # Create Cloudflare configuration file
    cat > "${PROJECT_ROOT}/cloudflare-config.json" << EOF
{
  "domain": "${domain}",
  "zone_id": "${zone_id}",
  "services": $(terraform output -json services),
  "r2_buckets": $(terraform output -json r2_buckets),
  "d1_database": $(terraform output -json d1_database)
}
EOF
    
    echo -e "${GREEN}✅ Created cloudflare-config.json${NC}"
}

# Main deployment function
deploy() {
    echo -e "${BLUE}🚀 Starting Cloudflare deployment for Local AI Package${NC}"
    log "Starting Cloudflare deployment"
    
    check_dependencies
    validate_terraform
    init_terraform
    plan_terraform
    
    # Confirm deployment
    if [[ "${CI:-false}" != "true" ]]; then
        echo -e "${YELLOW}⚠️  Ready to deploy infrastructure to Cloudflare${NC}"
        read -p "Continue with deployment? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Deployment cancelled"
            exit 0
        fi
    fi
    
    apply_terraform
    show_outputs
    update_project_config
    
    echo -e "${GREEN}🎉 Cloudflare deployment completed successfully!${NC}"
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Update your server IP in the DNS records"
    echo "2. Run the main deployment script to start services"
    echo "3. Configure SSL certificates"
    
    log "Cloudflare deployment completed successfully"
}

# Destroy infrastructure
destroy() {
    echo -e "${YELLOW}⚠️  This will destroy ALL Cloudflare infrastructure!${NC}"
    
    if [[ "${CI:-false}" != "true" ]]; then
        read -p "Are you sure? (type 'yes' to confirm): " -r
        if [[ $REPLY != "yes" ]]; then
            echo "Destruction cancelled"
            exit 0
        fi
    fi
    
    cd "$TERRAFORM_DIR"
    terraform destroy -auto-approve
    
    echo -e "${GREEN}✅ Infrastructure destroyed${NC}"
}

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [COMMAND]

Commands:
    deploy      Deploy infrastructure to Cloudflare
    destroy     Destroy all Cloudflare infrastructure
    plan        Show deployment plan without applying
    output      Show current deployment outputs
    validate    Validate Terraform configuration
    help        Show this help message

Environment Variables:
    CI=true     Run in non-interactive mode

Examples:
    $0 deploy           # Deploy to Cloudflare
    $0 plan             # Show what would be deployed
    $0 output           # Show current outputs
    $0 destroy          # Destroy infrastructure

EOF
}

# Main script logic
main() {
    case "${1:-deploy}" in
        deploy)
            deploy
            ;;
        destroy)
            destroy
            ;;
        plan)
            check_dependencies
            validate_terraform
            init_terraform
            plan_terraform
            ;;
        output)
            show_outputs
            ;;
        validate)
            check_dependencies
            validate_terraform
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"