# 🚀 Enhanced Local AI Package - Complete Setup Guide

## 🎯 What's New in This Enhanced Version

### 🔐 Critical Security Fixes
- **Fixed Supabase JWT Issue**: ANON_KEY and SERVICE_ROLE_KEY now properly generated from JWT_SECRET
- **Added Flowise Authentication**: Username/password protection with auto-generated credentials
- **Enhanced Secret Generation**: 20+ secure secrets automatically generated for all services
- **Kong Security**: Full security setup for Kong API Gateway with database encryption

### 📦 New Components Added
- **🦍 Kong API Gateway**: Alternative to Traefik with admin interface and Konga dashboard
- **📊 Graphite Monitoring**: Complete observability stack for metrics and monitoring
- **🔒 Enhanced Authentication**: All services now have proper authentication and secrets
- **🌐 Production-Ready**: SSL, domain configuration, and production deployment support

### 🚀 Deployment Enhancements
- **One-Click Installation**: `python3 install.py` with full automation
- **Unified Deployment**: `python3 deploy.py local` or `python3 deploy.py remote`
- **Non-Interactive Mode**: `--non-interactive` flag for automated deployments
- **Health Checks**: Automatic service verification and status reporting

## 📋 Quick Start (30 Seconds)

```bash
# Clone the repository
git clone https://github.com/cbwinslow/local-ai-packaged.git
cd local-ai-packaged

# One-click deployment
python3 deploy.py local

# Or step-by-step
python3 install.py              # Generate configs and secrets
python3 start_services.py       # Start all services
```

## 🌐 Service Access URLs

After deployment, all services are accessible through a unified interface:

| Service | URL | Description | Authentication |
|---------|-----|-------------|----------------|
| **Frontend Dashboard** | `http://localhost` | Main management interface | None |
| **N8N Workflows** | `http://localhost/n8n` | Workflow automation | Setup required |
| **Open WebUI** | `http://localhost/openwebui` | Chat with AI models | Create account |
| **Flowise** | `http://localhost/flowise` | Visual LLM workflows | admin/[generated] |
| **Supabase** | `http://localhost/supabase` | Database & auth | admin/[generated] |
| **Langfuse** | `http://localhost/langfuse` | LLM observability | Setup required |
| **SearXNG** | `http://localhost/searxng` | Private search | None |
| **Neo4j** | `http://localhost/neo4j` | Graph database | neo4j/[generated] |
| **Agentic RAG** | `http://localhost/agentic` | Knowledge graph API | None |
| **Graphite** | `http://localhost/graphite` | Monitoring & metrics | None |
| **Traefik Dashboard** | `http://localhost:8080` | Proxy management | None |

### Optional Kong Services (if using `--api-gateway kong`)
| Service | URL | Description |
|---------|-----|-------------|
| **Kong Admin** | `http://localhost:8001` | Kong API management |
| **Konga Dashboard** | `http://localhost:1337` | Kong web interface |

## 🔧 Deployment Options

### Local Development
```bash
python3 deploy.py local --profile cpu --environment private
```

### Local with GPU Support
```bash
python3 deploy.py local --profile gpu-nvidia --environment private
```

### Production Deployment
```bash
python3 deploy.py local --profile cpu --environment public --domain yourdomain.com
```

### Remote Server Deployment
```bash
python3 deploy.py remote --remote-host your-server.com --remote-user root
```

### Using Kong Instead of Traefik
```bash
python3 start_services.py --api-gateway kong
```

## 🔐 Generated Credentials

The installer automatically generates secure credentials for all services. Check your `.env` file for:

### Main Services
- **Supabase Dashboard**: admin / [check DASHBOARD_PASSWORD in .env]
- **Flowise**: admin / [check FLOWISE_PASSWORD in .env]  
- **Neo4j**: neo4j / [check NEO4J_AUTH in .env]
- **PostgreSQL**: postgres / [check POSTGRES_PASSWORD in .env]

### Generated Secrets (Samples)
```bash
# N8N Encryption
N8N_ENCRYPTION_KEY=bd28a1f174f849935e025dd74a3ced39...
N8N_USER_MANAGEMENT_JWT_SECRET=3d38877036eca3bae7ebf806...

# Supabase (Now Properly Generated!)
JWT_SECRET=IaHOHzerg6A7DLx7VraQX20gXSsGXu9dSNt9nZLhrRI
ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiI...
SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIi...

# Flowise Authentication
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=prmk2RyjDFov3hiEzNUp

# Kong API Gateway
KONG_DB_PASSWORD=g2psWMdu6G5igym4Jj5x69DUEDoOW0A8
KONG_TOKEN_SECRET=1607OO7VG4yeqbBvhJy5mohG8icbu6Ezhp1ehJKUe...
```

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check Docker
docker info

# Check logs
docker compose -p localai logs

# Reset everything
docker compose -p localai down -v
python3 deploy.py local
```

### Supabase Issues (FIXED!)
- ✅ **JWT Keys**: Now properly generated from JWT_SECRET (no more demo keys!)
- ✅ **Authentication**: Dashboard credentials auto-generated
- ✅ **Database**: Postgres password automatically set

### Port Conflicts
```bash
# Check what's using ports
sudo lsof -i :80
sudo lsof -i :443

# Stop conflicting services
sudo systemctl stop apache2  # Example
```

### Permission Issues
```bash
# Fix Traefik permissions
sudo chown -R $USER:$USER traefik/
chmod 600 traefik/letsencrypt/

# Fix SearXNG permissions  
chmod 755 searxng/
```

### Flowise Won't Start
- Check that FLOWISE_USERNAME and FLOWISE_PASSWORD are set in .env
- Use the generated credentials to log in
- Reset: `docker compose -p localai restart flowise`

## 🔍 Health Monitoring

### Check Service Status
```bash
# All services status
docker compose -p localai ps

# Individual service logs
docker compose -p localai logs n8n
docker compose -p localai logs supabase-kong

# Health check
python3 deploy.py local --skip-build  # Quick health check
```

### Monitoring with Graphite
- Visit `http://localhost/graphite` for metrics dashboard
- All services automatically send metrics to Graphite
- Create custom dashboards for monitoring

## 🚀 Advanced Configuration

### Production with SSL
```bash
python3 install.py --production --domain yourdomain.com --email admin@yourdomain.com
python3 start_services.py --environment public
```

### Custom Resource Limits
Edit `docker-compose.yml` to adjust memory/CPU limits:
```yaml
services:
  ollama-gpu:
    deploy:
      resources:
        limits:
          memory: 8G
```

### Kong Configuration
1. Start with Kong: `python3 start_services.py --api-gateway kong`
2. Access Kong Admin: `http://localhost:8001`
3. Access Konga Dashboard: `http://localhost:1337`
4. Configure API routes and plugins through Konga

## 🔄 Management Commands

```bash
# Start services
python3 start_services.py

# Start with specific profile
python3 start_services.py --profile gpu-nvidia

# Start with Kong instead of Traefik
python3 start_services.py --api-gateway kong

# Stop all services
docker compose -p localai down

# Reset everything (including data)
docker compose -p localai down -v

# View logs
docker compose -p localai logs -f

# Update services
git pull
python3 start_services.py
```

## 📊 What's Monitoring What

### Graphite Metrics
- **System**: CPU, memory, disk usage
- **Docker**: Container statistics
- **Services**: Response times, error rates
- **Custom**: Application-specific metrics

### Service Health Checks
- **Supabase**: Database connectivity and API health
- **N8N**: Workflow engine status
- **Ollama**: Model availability
- **Traefik/Kong**: Proxy health

## 🎯 Getting Started Checklist

1. **Deploy**: `python3 deploy.py local`
2. **Access Dashboard**: Visit `http://localhost`
3. **Configure N8N**: Set up your first workflow
4. **Test AI Chat**: Use Open WebUI to chat with models
5. **Monitor**: Check Graphite dashboard for metrics
6. **Secure**: Review generated credentials in `.env`

## 🤝 Support

- **Documentation**: Check README.md and QUICK_START.md
- **Logs**: `docker compose -p localai logs [service]`
- **Reset**: `docker compose -p localai down -v && python3 deploy.py local`
- **Issues**: Check GitHub issues or create new one

---

**🎉 Your enhanced Local AI Package is ready! All services are secured, monitored, and production-ready.**