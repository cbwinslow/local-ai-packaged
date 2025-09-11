# Local AI Package - Complete Setup Guide

This guide provides comprehensive, step-by-step instructions to set up and run the Local AI Package on your system.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Services](#running-the-services)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

## System Requirements

- **OS**: Linux/macOS/Windows (WSL2 recommended for Windows)
- **CPU**: x86_64/ARM64 with AVX2 support
- **RAM**: Minimum 16GB (32GB recommended for optimal performance)
- **Storage**: 50GB+ free space (SSD recommended)
- **Docker**: 20.10.0+
- **Docker Compose**: 2.0.0+
- **Python**: 3.10+
- **Git**: Latest stable version

## Prerequisites

1. **Install Docker and Docker Compose**
   ```bash
   # For Ubuntu/Debian
   sudo apt update
   sudo apt install -y docker.io docker-compose
   sudo systemctl enable --now docker
   sudo usermod -aG docker $USER
   newgrp docker  # Or log out and back in
   ```

2. **Install Python 3.10**
   ```bash
   # For Ubuntu/Debian
   sudo apt update
   sudo apt install -y python3.10 python3.10-venv python3-pip
   ```

3. **Install UV Package Manager**
   ```bash
   curl -sSf https://astral.sh/uv/install.sh | sh
   echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/coleam00/local-ai-packaged.git
   cd local-ai-packaged
   ```

2. **Set Up Python Environment**
   ```bash
   uv venv .venv --python=3.10
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Python Dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```

## Configuration

1. **Copy and Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   nano .env  # or use your preferred editor
   ```

   Key configurations to update:
   - `POSTGRES_PASSWORD`: Strong password for PostgreSQL
   - `SUPABASE_JWT_SECRET`: Generate with `openssl rand -base64 32`
   - `N8N_ENCRYPTION_KEY`: Generate with `openssl rand -base64 32`
   - `OLLAMA_HOST`: Set to your host IP if accessing remotely

2. **Initialize Supabase**
   ```bash
   docker-compose run --rm supabase init
   ```

## Running the Services

1. **Start All Services**
   ```bash
   docker-compose up -d
   ```

2. **Verify Services**
   ```bash
   docker-compose ps
   ```

3. **Access the Services**
   - **n8n**: http://localhost:5678
   - **Supabase Studio**: http://localhost:3000
   - **Open WebUI**: http://localhost:3001
   - **Flowise**: http://localhost:3002
   - **Neo4j Browser**: http://localhost:7474
   - **SearXNG**: http://localhost:8080

## Verification

1. **Test n8n**
   - Open http://localhost:5678
   - You should see the n8n dashboard

2. **Test Supabase**
   - Open http://localhost:3000
   - Log in with the credentials from your .env file

3. **Test Open WebUI**
   - Open http://localhost:3001
   - You should see the chat interface

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check which process is using a port
   sudo lsof -i :3000
   
   # Or on Windows
   netstat -ano | findstr :3000
   ```

2. **Docker Issues**
   ```bash
   # Check logs for a specific service
   docker-compose logs -f service_name
   
   # Rebuild and restart a specific service
   docker-compose up -d --build service_name
   ```

3. **Database Issues**
   ```bash
   # Reset the database (WARNING: This will delete all data)
   docker-compose down -v
   docker-compose up -d
   ```

## Maintenance

### Updating the Repository

```bash
git pull origin main
docker-compose down
docker-compose pull
docker-compose up -d
```

### Backing Up Data

```bash
# Create a backup of important data
mkdir -p backups
# Backup PostgreSQL
docker exec -t postgres pg_dumpall -c -U postgres > backups/postgres_backup_$(date +%Y-%m-%d).sql
# Backup configuration files
tar -czvf backups/config_backup_$(date +%Y-%m-%d).tar.gz .env config/
```

### Monitoring

```bash
# View resource usage
docker stats

# View logs for all services
docker-compose logs -f

# View resource usage for a specific container
docker stats container_name
```

## Next Steps

1. **Configure Authentication**
   - Set up OAuth providers in Supabase
   - Configure JWT tokens for API access

2. **Deploy Models**
   - Pull and deploy your preferred LLM models in Ollama
   - Configure model endpoints in n8n and Open WebUI

3. **Set Up Backups**
   - Configure automated database backups
   - Set up volume backups for persistent data

For more detailed information, refer to the [official documentation](https://github.com/coleam00/local-ai-packaged/tree/main/docs).
