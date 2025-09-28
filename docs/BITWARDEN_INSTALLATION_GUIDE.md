# Bitwarden-Powered One-Click Installation Guide

This guide provides complete instructions for setting up the Local AI Package using Bitwarden for secure secret management and automated deployment.

## Overview

The enhanced installation system provides:

- **Secure Secret Management**: All sensitive credentials stored and retrieved from Bitwarden
- **Automated Secret Generation**: Missing secrets auto-generated using cryptographically secure methods
- **Service-by-Service Deployment**: Incremental container builds with comprehensive health checks
- **One-Click Installation**: Complete automation from prerequisites to running services
- **Comprehensive Validation**: All secrets and services verified before and after deployment

## Prerequisites

Before starting, ensure you have:

- **Operating System**: Ubuntu/Debian Linux (recommended) or macOS
- **Hardware**: Minimum 8GB RAM, 20GB free disk space, internet connection
- **Bitwarden Account**: Free account at [bitwarden.com](https://bitwarden.com)
- **User Permissions**: Ability to install packages and run Docker

## Quick Start (One-Click Installation)

For users who want the complete automated experience:

```bash
# Clone the repository
git clone https://github.com/cbwinslow/local-ai-packaged.git
cd local-ai-packaged

# Run the one-click installer
./scripts/one-click-installer.sh
```

The installer will:
1. Install all prerequisites (Docker, Bitwarden CLI, etc.)
2. Guide you through Bitwarden authentication
3. Generate and populate all secrets
4. Build and deploy all services with health checks
5. Verify the complete installation

**Estimated time**: 15-30 minutes depending on internet speed and hardware.

## Step-by-Step Installation

For users who prefer manual control:

### Step 1: Install Prerequisites

```bash
# Update system packages
sudo apt-get update

# Install essential tools
sudo apt-get install -y curl wget unzip git python3 python3-pip openssl jq

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Node.js for Bitwarden CLI
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Bitwarden CLI
npm install -g @bitwarden/cli

# Install Python dependencies
pip3 install docker requests
```

### Step 2: Set Up Bitwarden

```bash
# Login to Bitwarden (first time only)
bw login your-email@example.com

# Unlock vault and export session
export BW_SESSION=$(bw unlock --raw)

# Sync vault
bw sync
```

### Step 3: Populate Secrets

```bash
# Use enhanced script for automatic secret generation
./scripts/enhanced-populate-env-from-bitwarden.sh

# Or use original script
./scripts/populate-env-from-bitwarden.sh
```

This will:
- Retrieve existing secrets from Bitwarden
- Generate missing secrets using `openssl rand`
- Store new secrets back in Bitwarden vault
- Create a complete `.env` file with proper permissions

### Step 4: Validate Configuration

```bash
# Run comprehensive validation
./scripts/enhanced-validate-env.sh

# Or run original validation
./scripts/validate-env.sh
```

Validation checks:
- All required secrets are present
- Secrets meet format requirements (hex, base64, JWT, etc.)
- No placeholder values remain
- File permissions are secure (600)

### Step 5: Deploy Services

```bash
# Option A: Use service orchestrator (recommended)
python3 tools/service_orchestrator.py

# Option B: Use existing deployment script
python3 tools/start_services_enhanced.py

# Option C: Manual Docker Compose
docker compose up -d
```

The orchestrator will:
- Deploy infrastructure services first (Postgres, Redis, Traefik)
- Start Supabase stack with health checks
- Deploy AI services (n8n, Ollama, Neo4j, etc.)
- Launch frontend services
- Verify all services are running correctly

## Service URLs

After successful deployment, access your services at:

| Service | URL | Purpose |
|---------|-----|---------|
| Traefik Dashboard | http://localhost:8080 | Reverse proxy management |
| Supabase Studio | http://localhost:3000 | Database and auth management |
| n8n | http://localhost:5678 | Workflow automation |
| Neo4j Browser | http://localhost:7474 | Graph database interface |
| Open WebUI | http://localhost:3001 | AI chat interface |
| Qdrant | http://localhost:6333 | Vector database |
| Ollama API | http://localhost:11434 | Local LLM API |

## Troubleshooting

### Common Issues

**1. Bitwarden Authentication Issues**
```bash
# Re-authenticate
bw logout
bw login your-email@example.com
export BW_SESSION=$(bw unlock --raw)
```

**2. Secret Validation Failures**
```bash
# Regenerate secrets
./scripts/enhanced-populate-env-from-bitwarden.sh
./scripts/enhanced-validate-env.sh
```

**3. Docker Permission Issues**
```bash
# Add user to docker group and restart session
sudo usermod -aG docker $USER
# Log out and log back in
```

**4. Service Health Check Failures**
```bash
# Check service logs
docker compose logs -f [service-name]

# Restart specific service
docker compose restart [service-name]

# Full restart
docker compose down && docker compose up -d
```

**5. Port Conflicts**
```bash
# Check what's using ports
sudo netstat -tlnp | grep :8080

# Stop conflicting services or modify ports in docker-compose.yml
```

### Diagnostic Commands

```bash
# Check all container status
docker compose ps

# View all logs
docker compose logs -f

# Check service health
./status-check.sh  # Created by installer

# Restart all services
./restart-services.sh  # Created by installer

# Full system check
./scripts/health-check.sh --check-all
```

## Security Notes

- **Secret Storage**: All sensitive data is stored in Bitwarden vault
- **File Permissions**: `.env` file set to 600 (owner read/write only)
- **No Version Control**: `.env` file excluded from git commits
- **Key Rotation**: Regenerate secrets periodically using the population script
- **Access Control**: Use Bitwarden organizations for team access control

## Backup and Recovery

### Backup Secrets
```bash
# Export secrets from Bitwarden
bw export --format json --session $BW_SESSION > backup.json

# Backup .env file
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
```

### Recovery
```bash
# Restore from Bitwarden
./scripts/enhanced-populate-env-from-bitwarden.sh

# Or restore from backup
cp .env.backup.YYYYMMDD_HHMMSS .env
```

## Advanced Configuration

### Custom Service Profiles

```bash
# Deploy with GPU support
python3 tools/service_orchestrator.py --profile gpu

# Deploy specific services only
python3 tools/service_orchestrator.py --services-only postgres redis n8n
```

### Environment Customization

Edit `.env` after population to customize:
- Service ports
- Resource limits
- Feature flags
- External service URLs

### Production Deployment

For production use:
1. Use strong master password for Bitwarden
2. Enable Bitwarden organization with access controls
3. Configure proper domain names and SSL certificates
4. Set up monitoring and alerting
5. Implement regular backup procedures

## Development and Testing

### Testing the Installation

```bash
# Test secret generation and validation
./scripts/test-bitwarden-integration.sh

# Test service orchestration
python3 -c "
from tools.service_orchestrator import ServiceOrchestrator
orch = ServiceOrchestrator()
print('Prerequisites OK:', orch.check_prerequisites())
"
```

### Adding New Services

1. Add service definition to `docker-compose.yml`
2. Add required secrets to Bitwarden population script
3. Add validation rules to validation script
4. Update service orchestrator with health checks
5. Test the complete flow

## Support and Documentation

- **Project Repository**: https://github.com/cbwinslow/local-ai-packaged
- **Issue Tracking**: GitHub Issues
- **Documentation**: `docs/` folder in repository
- **Community**: Join our Discord/Slack for support

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request with detailed description

---

**Note**: This installation system is designed for self-hosted, privacy-focused AI development. All processing happens locally, and your data never leaves your infrastructure.