# 🚀 Quick Start Guide - Enhanced Local AI Package

## Prerequisites

Before getting started, ensure you have:

- **Docker** 20.10+ with Docker Compose
- **Git** for repository cloning  
- **Python 3.8+** for the installer scripts
- **4GB+ RAM** (8GB+ recommended)
- **20GB+ disk space**

## 🎯 30-Second Quick Start

```bash
# Clone and enter the repository
git clone https://github.com/cbwinslow/local-ai-packaged.git
cd local-ai-packaged

# Run the one-click installer
python3 install.py

# Start all services  
python3 start_services.py

# Open your browser
open http://localhost
```

## 📋 What the Installer Does

The `install.py` script automatically:

1. ✅ **Checks requirements** (Docker, Git, Python)
2. ✅ **Generates secure secrets** for all services
3. ✅ **Creates .env file** with proper configuration
4. ✅ **Sets up directories** for persistent data
5. ✅ **Configures networking** for service communication
6. ✅ **Prepares SSL certificates** for production use

## 🔧 Installation Options

### Basic Installation
```bash
python3 install.py
# Follow prompts, use defaults for local development
```

### Production Installation
```bash
python3 install.py
# When prompted:
# - Answer "y" for production domains
# - Enter your domain name
# - Enter your email for SSL certificates
```

### With GPU Support
```bash
# For NVIDIA GPUs
python3 start_services.py --profile gpu-nvidia

# For AMD GPUs (Linux only)
python3 start_services.py --profile gpu-amd
```

### Public Deployment
```bash
# Secure configuration for cloud deployment
python3 start_services.py --environment public
```

## 🌐 Service Access

After installation, access your services:

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost | Main control panel |
| **N8N** | http://localhost/n8n | Workflow automation |
| **Chat UI** | http://localhost/openwebui | Talk to your AI |
| **Flowise** | http://localhost/flowise | Visual AI workflows |
| **Database** | http://localhost/supabase | Data management |
| **Analytics** | http://localhost/langfuse | AI observability |
| **Graph DB** | http://localhost/neo4j | Knowledge graphs |
| **RAG API** | http://localhost/agentic | Advanced AI features |

## 🛠️ Common Commands

```bash
# View all running services
docker compose -p localai ps

# Check service logs
docker compose -p localai logs [service-name]

# Restart a specific service
docker compose -p localai restart [service-name]

# Stop all services
docker compose -p localai down

# Update to latest versions
docker compose -p localai pull
python3 start_services.py
```

## 🐛 Quick Troubleshooting

### Services Won't Start
```bash
# Check Docker is running
docker info

# Check logs for errors
docker compose -p localai logs

# Reset everything
docker compose -p localai down -v
python3 start_services.py
```

### Can't Access Services
```bash
# Check Traefik is running
curl http://localhost:8080/ping

# Verify network connectivity
docker network ls | grep localai
```

### Port Conflicts
```bash
# Find what's using port 80/443
sudo lsof -i :80
sudo lsof -i :443

# Stop conflicting services
sudo systemctl stop apache2  # Example
```

## 🔐 Security Notes

- **Secrets are auto-generated** - Save them securely!
- **Default passwords changed** - Check your .env file
- **SSL enabled in production** - Use real domains
- **Firewall configured** - Only necessary ports open

## 📊 Resource Usage

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 20GB
- **Network**: Broadband

### Recommended for Production
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Disk**: 50GB+ SSD
- **Network**: High-speed internet

## 🎯 Next Steps

1. **Explore the Dashboard** - http://localhost
2. **Create your first workflow** - N8N at http://localhost/n8n
3. **Chat with AI models** - Open WebUI at http://localhost/openwebui
4. **Monitor performance** - Langfuse at http://localhost/langfuse
5. **Build knowledge graphs** - Neo4j at http://localhost/neo4j

## 📞 Getting Help

- **Documentation**: Check README_ENHANCED.md
- **Logs**: `docker compose -p localai logs`
- **Issues**: GitHub repository issues
- **Community**: Discussion forums

## 🔄 Updates

```bash
# Pull latest code
git pull origin main

# Update containers
docker compose -p localai pull

# Restart services
python3 start_services.py
```

---

**Ready to build amazing AI applications? Start exploring your new Local AI Package! 🚀**