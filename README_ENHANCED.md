# Enhanced Local AI Package

**Enhanced Local AI Package** is a comprehensive, self-hosted AI development environment that provides a complete stack for AI/ML development including:

- 🤖 **Ollama** for local LLMs
- 💬 **Open WebUI** for chat interfaces  
- 🔄 **N8N** for workflow automation
- 🗄️ **Supabase** for database, authentication, and APIs
- 📊 **Langfuse** for LLM observability
- 🔍 **SearXNG** for private search
- 📈 **Neo4j** for knowledge graphs
- 🧠 **Agentic Knowledge RAG Graph** for advanced AI workflows
- 🌐 **Next.js Frontend** for configuration and management
- 🚦 **Traefik** for reverse proxy and SSL management

## 🚀 One-Click Installation

We've created a comprehensive installer that handles all configuration and secret generation:

```bash
# Clone the repository
git clone https://github.com/cbwinslow/local-ai-packaged.git
cd local-ai-packaged

# Run the one-click installer
python3 install.py

# Start all services
python3 start_services.py
```

The installer will:
- ✅ Check system requirements
- 🔐 Generate secure secrets automatically
- 📋 Configure environment variables
- 🌐 Set up domain configurations (optional)
- 📦 Clone the agentic RAG component
- 🛠️ Prepare all necessary directories

## 🎯 What's New in This Enhanced Version

### 🚦 Traefik Instead of Caddy
- Modern reverse proxy with better Docker integration
- Automatic SSL with Let's Encrypt
- Advanced routing and middleware support
- Built-in dashboard and metrics

### 🧠 Agentic Knowledge RAG Graph
- Integrated knowledge graph capabilities
- RAG (Retrieval Augmented Generation) workflows
- Neo4j graph database integration
- Vector search with Qdrant

### 🌐 Next.js Management Interface
- Web-based configuration dashboard
- Service status monitoring
- OAuth integration with Supabase
- Modern, responsive UI

### 🔧 Enhanced Deployment Scripts
- Improved error handling and logging
- Better health checks and wait conditions
- Support for both local and remote deployment
- Comprehensive pre-flight checks

### 🐳 Better Docker Networking
- Proper service discovery
- Isolated networks for security
- Health checks for all services
- Improved inter-service communication

## 📋 System Requirements

- **Docker** 20.10+ with Docker Compose
- **Git** for repository cloning
- **Python 3.8+** for the installer scripts
- **4GB+ RAM** (8GB+ recommended)
- **20GB+ disk space**

### GPU Support (Optional)
- **NVIDIA GPU**: NVIDIA Docker runtime
- **AMD GPU**: ROCm support (Linux only)

## 🛠️ Installation & Setup

### Quick Start
```bash
# 1. Clone and enter directory
git clone https://github.com/cbwinslow/local-ai-packaged.git
cd local-ai-packaged

# 2. Run installer (interactive setup)
python3 install.py

# 3. Start services
python3 start_services.py

# 4. Access the dashboard
open http://localhost
```

### Advanced Installation Options

#### GPU Support
```bash
# NVIDIA GPU
python3 start_services.py --profile gpu-nvidia

# AMD GPU (Linux only)  
python3 start_services.py --profile gpu-amd

# CPU only
python3 start_services.py --profile cpu
```

#### Production Deployment
```bash
# Public environment (secure ports)
python3 start_services.py --environment public

# With custom domain
python3 install.py  # Configure domains during setup
python3 start_services.py --environment public
```

## 🌐 Service Access URLs

After deployment, services are available at:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend Dashboard** | `http://localhost` | Main management interface |
| **N8N Workflows** | `http://localhost/n8n` | Workflow automation |
| **Open WebUI** | `http://localhost/openwebui` | Chat with AI models |
| **Flowise** | `http://localhost/flowise` | Visual LLM workflows |
| **Supabase** | `http://localhost/supabase` | Database & auth |
| **Langfuse** | `http://localhost/langfuse` | LLM observability |
| **SearXNG** | `http://localhost/searxng` | Private search |
| **Neo4j** | `http://localhost/neo4j` | Graph database |
| **Agentic RAG** | `http://localhost/agentic` | Knowledge graph API |
| **Traefik Dashboard** | `http://localhost:8080` | Proxy management |

## 🔐 Security & Configuration

### Generated Secrets
The installer automatically generates secure secrets for:
- N8N encryption keys
- Supabase JWT tokens and API keys
- Database passwords
- Service authentication tokens
- SSL certificates (production)

### Environment Configuration
All configuration is managed through the `.env` file:
```bash
# Edit configuration
nano .env

# Restart services to apply changes
python3 start_services.py
```

### Production Considerations
- ✅ Change default passwords
- ✅ Configure proper domain names
- ✅ Set up SSL certificates
- ✅ Configure firewall rules
- ✅ Regular backups of data volumes

## 🚀 Usage Examples

### 1. Building AI Workflows
1. Access N8N at `http://localhost/n8n`
2. Create workflows combining:
   - Local LLMs via Ollama
   - Database operations via Supabase
   - Knowledge graph queries via Neo4j
   - Vector searches via Qdrant

### 2. Chat with AI Models
1. Visit Open WebUI at `http://localhost/openwebui`
2. Models are automatically available from Ollama
3. Chat with pre-installed models or download new ones

### 3. Knowledge Graph Operations
1. Access Neo4j browser at `http://localhost/neo4j`
2. Use the Agentic RAG API for programmatic access
3. Build knowledge graphs from your documents

### 4. Monitoring & Observability
1. View LLM usage in Langfuse at `http://localhost/langfuse`
2. Monitor system health via Traefik dashboard
3. Check service logs: `docker compose -p localai logs [service]`

## 🔧 Advanced Configuration

### Custom Domains
Configure in `.env`:
```bash
BASE_DOMAIN=yourdomain.com
N8N_HOSTNAME=n8n.yourdomain.com
WEBUI_HOSTNAME=chat.yourdomain.com
LETSENCRYPT_EMAIL=admin@yourdomain.com
```

### OAuth Integration
Configure Google OAuth in `.env`:
```bash
ENABLE_GOOGLE_SIGNUP=true
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

### Resource Limits
Customize Docker resources in `docker-compose.yml`:
```yaml
services:
  ollama-gpu:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          devices:
            - driver: nvidia
              count: 1
```

## 🛠️ Management Commands

```bash
# View all services
docker compose -p localai ps

# View logs
docker compose -p localai logs [service-name]

# Restart a service
docker compose -p localai restart [service-name]

# Stop all services
docker compose -p localai down

# Stop and remove volumes (⚠️ deletes data)
docker compose -p localai down -v

# Update containers
docker compose -p localai pull
docker compose -p localai up -d
```

## 🐛 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker
docker info

# Check logs
docker compose -p localai logs

# Reset everything
docker compose -p localai down -v
python3 start_services.py
```

#### Port Conflicts
```bash
# Find processes using ports
lsof -i :80
lsof -i :443

# Stop conflicting services
sudo systemctl stop apache2  # Example
```

#### Permission Issues
```bash
# Fix Traefik permissions
sudo chown -R $USER:$USER traefik/
chmod 600 traefik/letsencrypt/

# Fix SearXNG permissions
chmod 755 searxng/
```

#### Memory Issues
- Increase Docker memory limits
- Use CPU profile instead of GPU
- Close unnecessary applications

### Getting Help
1. 📋 Check the logs: `docker compose -p localai logs`
2. 🔍 Search existing issues on GitHub
3. 💬 Create a new issue with:
   - System information
   - Complete logs
   - Steps to reproduce

## 🔄 Updates & Maintenance

### Updating Services
```bash
# Pull latest images
docker compose -p localai pull

# Restart with new images
python3 start_services.py
```

### Backup Data
```bash
# Backup all volumes
docker run --rm -v localai_n8n_storage:/data -v $(pwd):/backup alpine tar czf /backup/n8n_backup.tar.gz -C /data .
# Repeat for other volumes...
```

### Health Monitoring
The enhanced version includes:
- Service health checks
- Automatic restarts on failure
- Traefik metrics and monitoring
- Resource usage tracking

## 📚 Documentation

- 📖 **N8N**: [docs.n8n.io](https://docs.n8n.io)
- 🗄️ **Supabase**: [supabase.com/docs](https://supabase.com/docs)
- 🤖 **Ollama**: [ollama.ai/docs](https://ollama.ai/docs)
- 🚦 **Traefik**: [doc.traefik.io](https://doc.traefik.io)
- 📊 **Langfuse**: [langfuse.com/docs](https://langfuse.com/docs)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original Local AI Package by [@coleam00](https://github.com/coleam00)
- N8N team for workflow automation
- Supabase team for the backend platform
- Ollama team for local LLM support
- All the open-source contributors

---

**Happy AI Development! 🚀**