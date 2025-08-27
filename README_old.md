# Self-hosted AI Package

**Self-hosted AI Package** is a comprehensive, production-ready Docker Compose template that bootstraps a fully featured Local AI and Low Code development environment. It includes Ollama for local LLMs, Open WebUI for chat interfaces, n8n for workflow automation, Supabase for database and authentication, and a complete suite of AI development tools.

This enhanced version features a **single-entrypoint orchestration script** (`start_services.py`) that provides comprehensive environment setup, service management, health monitoring, diagnostics, and remote deployment capabilities.

## Key Features

🚀 **Single Command Deployment** - One script handles everything: `python start_services.py up`  
🔧 **Automated Environment Setup** - Generates secure secrets and validates configuration  
📊 **Comprehensive Diagnostics** - Built-in health checks and connectivity testing  
🌐 **Remote Deployment** - Deploy to any server via SSH with automatic Docker setup  
📝 **Rich Logging** - Structured logs with rotation and detailed error reporting  
🔍 **Service Monitoring** - Real-time status and health checking for all services  
⚙️ **Flexible Configuration** - Support for CPU/GPU profiles and private/public environments

## Architecture Overview

The platform consists of interconnected services orchestrated through Docker Compose:

**Core Services:**
- **n8n** - Workflow automation and AI agent orchestration
- **Supabase** - PostgreSQL database, authentication, and vector storage
- **Ollama** - Local LLM serving (CPU/GPU support)
- **Open WebUI** - Chat interface for models and agents

**AI Development Tools:**
- **Flowise** - Visual AI agent builder
- **Langfuse** - LLM observability and analytics
- **Qdrant** - High-performance vector database
- **Neo4j** - Knowledge graph database for GraphRAG

**Infrastructure:**
- **Caddy** - Reverse proxy with automatic HTTPS
- **SearXNG** - Privacy-respecting search engine
- **Redis** - Caching and session storage
- **ClickHouse** - Analytics database

All services communicate via a unified Docker network with proper health checks and dependency management.

## Quick Start

### Prerequisites

- **Docker** (v20.10+) and **Docker Compose** (v2.0+)
- **Python 3.8+** (for the orchestration script)
- **Git** (for cloning and updates)
- **4GB+ RAM** (8GB+ recommended)
- **10GB+ free disk space**

### Installation

1. **Clone the repository:**
   ```bash
   git clone -b stable https://github.com/coleam00/local-ai-packaged.git
   cd local-ai-packaged
   ```

2. **Initialize environment and generate secrets:**
   ```bash
   python start_services.py init
   ```
   This creates a `.env` file with secure, randomly generated secrets for all services.

3. **Start all services:**
   ```bash
   python start_services.py up
   ```
   For GPU support:
   ```bash
   python start_services.py up --profile gpu-nvidia
   # or for AMD GPUs:
   python start_services.py up --profile gpu-amd
   ```

4. **Verify deployment:**
   ```bash
   python start_services.py status
   ```

5. **Access services:**
   - **n8n**: http://localhost:5678
   - **Open WebUI**: http://localhost:8080
   - **Flowise**: http://localhost:3001
   - **Supabase Studio**: http://localhost:8000
   - **Langfuse**: http://localhost:3000

## Orchestration Script Usage

The `start_services.py` script provides comprehensive service management:

### Available Commands

#### `init` - Environment Initialization
```bash
python start_services.py init [--force]
```
- Creates `.env` file with generated secrets
- Validates Docker installation
- Sets up required directories
- Use `--force` to overwrite existing configuration

#### `up` - Start Services
```bash
python start_services.py up [--profile PROFILE] [--environment ENV] [--no-cache]
```
- **Profiles**: `cpu` (default), `gpu-nvidia`, `gpu-amd`, `none`
- **Environments**: `private` (default), `public`
- **Options**: `--no-cache` for clean builds

#### `down` - Stop Services
```bash
python start_services.py down [--profile PROFILE] [--volumes]
```
- Gracefully stops all services
- Use `--volumes` to remove persistent data (irreversible!)

#### `restart` - Restart Services
```bash
python start_services.py restart [--profile PROFILE] [--environment ENV]
```
- Performs controlled restart with proper service ordering

#### `logs` - View Logs
```bash
python start_services.py logs [SERVICE] [--since TIME] [--follow] [--tail N]
```
Examples:
```bash
python start_services.py logs --follow          # Follow all logs
python start_services.py logs n8n --since 1h   # Last hour of n8n logs
python start_services.py logs --tail 200        # Last 200 lines
```

#### `status` - Health Check
```bash
python start_services.py status
```
Shows real-time status of all services with health indicators.

#### `test` - Diagnostics
```bash
python start_services.py test [--output FILE]
```
Runs comprehensive diagnostics including:
- Docker and environment validation
- Service health checks
- Network connectivity tests
- Supabase API validation
- Port conflict detection

#### `deploy-remote` - Remote Deployment
```bash
python start_services.py deploy-remote HOST [--user USER] [--ssh-key KEY] [--domain DOMAIN] [--dry-run]
```
Examples:
```bash
# Basic deployment
python start_services.py deploy-remote 192.168.1.100 --user ubuntu

# With custom SSH key and domain
python start_services.py deploy-remote my-server.com --ssh-key ~/.ssh/id_rsa --domain ai.example.com

# Dry run to see what would be done
python start_services.py deploy-remote 192.168.1.100 --dry-run
```

Features:
- Automatic Docker/Docker Compose installation
- File synchronization via rsync/scp
- Idempotent deployment (safe to run multiple times)
- Optional HTTPS setup with Let's Encrypt (when domain provided)

#### `destroy-remote` - Remove Remote Deployment
```bash
python start_services.py destroy-remote HOST [--user USER] [--ssh-key KEY] --confirm
```
⚠️ **Warning**: This completely removes the remote deployment. Backup data first!

## Environment Variables Reference

The system uses environment variables for configuration. Run `python start_services.py init` to automatically generate secure values.

### Core Service Variables

| Variable | Description | Required | Auto-Generated |
|----------|-------------|----------|----------------|
| `N8N_ENCRYPTION_KEY` | n8n data encryption key | ✅ | ✅ |
| `N8N_USER_MANAGEMENT_JWT_SECRET` | n8n JWT secret | ✅ | ✅ |
| `POSTGRES_PASSWORD` | PostgreSQL password | ✅ | ✅ |
| `JWT_SECRET` | Supabase JWT secret | ✅ | ✅ |
| `ANON_KEY` | Supabase anonymous key | ✅ | ✅ |
| `SERVICE_ROLE_KEY` | Supabase service role key | ✅ | ✅ |
| `DASHBOARD_USERNAME` | Supabase dashboard username | ✅ | ✅ |
| `DASHBOARD_PASSWORD` | Supabase dashboard password | ✅ | ✅ |

### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `FLOWISE_USERNAME` | Flowise login username | (unset) |
| `FLOWISE_PASSWORD` | Flowise login password | (unset) |
| `N8N_HOSTNAME` | Custom domain for n8n | localhost:5678 |
| `WEBUI_HOSTNAME` | Custom domain for Open WebUI | localhost:8080 |
| `LETSENCRYPT_EMAIL` | Email for Let's Encrypt certificates | internal |

### Environment Types

- **Private** (`--environment private`): Services accessible on localhost only
- **Public** (`--environment public`): Services accessible from any IP (use with Caddy/reverse proxy)

### GPU Profiles

- **CPU** (`--profile cpu`): CPU-only operation
- **GPU-NVIDIA** (`--profile gpu-nvidia`): NVIDIA GPU support with CUDA
- **GPU-AMD** (`--profile gpu-amd`): AMD GPU support with ROCm

## Logging and Monitoring

### Log Files

All orchestration logs are stored in the `logs/` directory:
- `orchestrator_YYYYMMDD_HHMMSS.log` - Detailed operation logs
- `diagnostics_YYYYMMDD_HHMMSS.json` - Diagnostic test results

### Service Logs

View service-specific logs:
```bash
python start_services.py logs n8n          # n8n logs only
python start_services.py logs --follow     # Follow all logs
python start_services.py logs --since 1h   # Last hour
```

### Health Monitoring

All services include health checks that verify:
- HTTP endpoint availability
- Database connectivity
- Internal service communication
- Resource availability

Monitor health status:
```bash
python start_services.py status    # Real-time status
python start_services.py test      # Comprehensive diagnostics
```

## Remote Deployment Guide

### Server Requirements

- **Operating System**: Ubuntu 20.04+ or similar Linux distribution
- **Resources**: 4GB+ RAM, 20GB+ disk space
- **Network**: SSH access, ports 80/443 open for HTTPS
- **User**: sudo privileges for Docker installation

### Deployment Process

1. **Prepare local environment:**
   ```bash
   python start_services.py init
   # Customize .env as needed
   ```

2. **Deploy to server:**
   ```bash
   python start_services.py deploy-remote your-server.com --user ubuntu --ssh-key ~/.ssh/id_rsa
   ```

3. **With custom domain (enables HTTPS):**
   ```bash
   python start_services.py deploy-remote your-server.com --domain ai.yoursite.com
   ```

### DNS Configuration

For custom domains, configure these A records:
```
n8n.yoursite.com        → your-server-ip
openwebui.yoursite.com  → your-server-ip
flowise.yoursite.com    → your-server-ip
supabase.yoursite.com   → your-server-ip
langfuse.yoursite.com   → your-server-ip
```

Then update your `.env` file:
```bash
N8N_HOSTNAME=n8n.yoursite.com
WEBUI_HOSTNAME=openwebui.yoursite.com
FLOWISE_HOSTNAME=flowise.yoursite.com
SUPABASE_HOSTNAME=supabase.yoursite.com
LANGFUSE_HOSTNAME=langfuse.yoursite.com
LETSENCRYPT_EMAIL=your-email@domain.com
```

## Troubleshooting

### Common Issues

#### 1. Port Conflicts
**Error**: "Port already in use"
**Solution**: 
```bash
python start_services.py test  # Check for conflicts
docker ps                      # See what's using ports
python start_services.py down  # Stop all services
```

#### 2. Docker Permission Issues
**Error**: "Permission denied accessing Docker"
**Solution**:
```bash
sudo usermod -aG docker $USER
# Log out and back in, or restart shell
```

#### 3. Insufficient Resources
**Error**: Services failing to start or being killed
**Solution**:
- Increase Docker memory allocation (Docker Desktop settings)
- Free up disk space
- Use `--profile none` to disable Ollama if not needed

#### 4. Environment File Issues
**Error**: "Missing required environment variables"
**Solution**:
```bash
python start_services.py init --force  # Regenerate .env
python start_services.py test          # Validate configuration
```

#### 5. Supabase Connection Issues
**Error**: Services can't connect to Supabase
**Solutions**:
- Ensure no special characters (especially `@`) in `POSTGRES_PASSWORD`
- Check Supabase containers are healthy: `python start_services.py status`
- Restart with proper ordering: `python start_services.py restart`

#### 6. Network Connectivity Issues
**Error**: Services can't reach each other
**Solution**:
```bash
docker network ls                    # Check networks exist
docker network inspect localai_default  # Inspect network
python start_services.py restart    # Recreate services
```

### GPU-Specific Issues

#### NVIDIA GPU
**Error**: "nvidia-container-runtime not found"
**Solution**:
1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Restart Docker service
3. Verify: `docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi`

#### AMD GPU
**Error**: ROCm support issues
**Solution**:
1. Ensure ROCm drivers are installed
2. Check device availability: `ls -la /dev/kfd /dev/dri`
3. Verify container access: `docker run --rm --device=/dev/kfd --device=/dev/dri rocm/pytorch:latest rocm-smi`

### Diagnostic Commands

Run comprehensive diagnostics:
```bash
python start_services.py test --output diagnostics.json
```

This checks:
- ✅ Docker installation and daemon status
- ✅ Environment variable validation
- ✅ Service health and connectivity
- ✅ Port availability
- ✅ Network configuration
- ✅ Supabase API accessibility

### Getting Help

1. **Check logs**: `python start_services.py logs --since 1h`
2. **Run diagnostics**: `python start_services.py test`
3. **Verify status**: `python start_services.py status`
4. **Community support**: [Local AI Community Forum](https://thinktank.ottomator.ai/c/local-ai/18)
5. **Report issues**: [GitHub Issues](https://github.com/coleam00/local-ai-packaged/issues)

## Security Considerations

### Production Deployment

For production use:

1. **Change default passwords**: All auto-generated secrets should be reviewed
2. **Enable HTTPS**: Use custom domains with Let's Encrypt
3. **Restrict access**: Use firewall rules to limit service access
4. **Regular updates**: Keep containers and host OS updated
5. **Backup data**: Regularly backup volumes and configuration

### Data Backup

Important data locations:
- **n8n workflows**: `docker volume inspect localai_n8n_storage`
- **Supabase data**: Supabase containers include database
- **Ollama models**: `docker volume inspect localai_ollama_storage`
- **Configuration**: `.env` file and `logs/` directory

Backup command example:
```bash
docker run --rm -v localai_n8n_storage:/data -v $(pwd):/backup alpine tar czf /backup/n8n_backup.tar.gz -C /data .
```

## Advanced Configuration

### Custom Domains and HTTPS

1. **Configure DNS** (see Remote Deployment section)
2. **Update environment variables** in `.env`
3. **Deploy with domain**:
   ```bash
   python start_services.py deploy-remote server.com --domain yoursite.com
   ```

### Service Dependencies

Services start in proper order with health check dependencies:
1. Core infrastructure (Redis, ClickHouse, MinIO)
2. Supabase services (Database, Kong, GoTrue)
3. AI services (Ollama, Qdrant, Neo4j)
4. Application services (n8n, Open WebUI, Flowise)
5. Reverse proxy (Caddy)

### Custom Models

Add custom Ollama models by modifying the init scripts or running:
```bash
docker exec -it ollama ollama pull your-model-name
```

## Important Links

- [Local AI Community Forum](https://thinktank.ottomator.ai/c/local-ai/18)
- [GitHub Project Board](https://github.com/users/coleam00/projects/2/views/1)
- [Original n8n AI Starter Kit](https://github.com/n8n-io/self-hosted-ai-starter-kit)
- [Open WebUI n8n Integration](https://openwebui.com/f/coleam/n8n_pipe/)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request with clear description

For major changes, please open an issue first to discuss the proposed changes.

### What’s included

✅ [**Self-hosted n8n**](https://n8n.io/) - Low-code platform with over 400
integrations and advanced AI components

✅ [**Supabase**](https://supabase.com/) - Open source database as a service -
most widely used database for AI agents

✅ [**Ollama**](https://ollama.com/) - Cross-platform LLM platform to install
and run the latest local LLMs

✅ [**Open WebUI**](https://openwebui.com/) - ChatGPT-like interface to
privately interact with your local models and N8N agents

✅ [**Flowise**](https://flowiseai.com/) - No/low code AI agent
builder that pairs very well with n8n

✅ [**Qdrant**](https://qdrant.tech/) - Open source, high performance vector
store with an comprehensive API. Even though you can use Supabase for RAG, this was
kept unlike Postgres since it's faster than Supabase so sometimes is the better option.

✅ [**Neo4j**](https://neo4j.com/) - Knowledge graph engine that powers tools like GraphRAG, LightRAG, and Graphiti 

✅ [**SearXNG**](https://searxng.org/) - Open source, free internet metasearch engine which aggregates 
results from up to 229 search services. Users are neither tracked nor profiled, hence the fit with the local AI package.

✅ [**Caddy**](https://caddyserver.com/) - Managed HTTPS/TLS for custom domains

✅ [**Langfuse**](https://langfuse.com/) - Open source LLM engineering platform for agent observability

## Prerequisites

Before you begin, make sure you have the following software installed:

- [Python](https://www.python.org/downloads/) - Required to run the setup script
- [Git/GitHub Desktop](https://desktop.github.com/) - For easy repository management
- [Docker/Docker Desktop](https://www.docker.com/products/docker-desktop/) - Required to run all services

## Installation

Clone the repository and navigate to the project directory:
```bash
git clone -b stable https://github.com/coleam00/local-ai-packaged.git
cd local-ai-packaged
```

Before running the services, you need to set up your environment variables for Supabase following their [self-hosting guide](https://supabase.com/docs/guides/self-hosting/docker#securing-your-services).

1. Make a copy of `.env.example` and rename it to `.env` in the root directory of the project
2. Set the following required environment variables:
   ```bash
   ############
   # N8N Configuration
   ############
   N8N_ENCRYPTION_KEY=
   N8N_USER_MANAGEMENT_JWT_SECRET=

   ############
   # Supabase Secrets
   ############
   POSTGRES_PASSWORD=
   JWT_SECRET=
   ANON_KEY=
   SERVICE_ROLE_KEY=
   DASHBOARD_USERNAME=
   DASHBOARD_PASSWORD=
   POOLER_TENANT_ID=

   ############
   # Neo4j Secrets
   ############   
   NEO4J_AUTH=

   ############
   # Langfuse credentials
   ############

   CLICKHOUSE_PASSWORD=
   MINIO_ROOT_PASSWORD=
   LANGFUSE_SALT=
   NEXTAUTH_SECRET=
   ENCRYPTION_KEY=  
   ```

> [!IMPORTANT]
> Make sure to generate secure random values for all secrets. Never use the example values in production.

3. Set the following environment variables if deploying to production, otherwise leave commented:
   ```bash
   ############
   # Caddy Config
   ############

   N8N_HOSTNAME=n8n.yourdomain.com
   WEBUI_HOSTNAME=:openwebui.yourdomain.com
   FLOWISE_HOSTNAME=:flowise.yourdomain.com
   SUPABASE_HOSTNAME=:supabase.yourdomain.com
   OLLAMA_HOSTNAME=:ollama.yourdomain.com
   SEARXNG_HOSTNAME=searxng.yourdomain.com
   NEO4J_HOSTNAME=neo4j.yourdomain.com
   LETSENCRYPT_EMAIL=your-email-address
   ```   

---

The project includes a `start_services.py` script that handles starting both the Supabase and local AI services. The script accepts a `--profile` flag to specify which GPU configuration to use.

### For Nvidia GPU users

```bash
python start_services.py --profile gpu-nvidia
```

> [!NOTE]
> If you have not used your Nvidia GPU with Docker before, please follow the
> [Ollama Docker instructions](https://github.com/ollama/ollama/blob/main/docs/docker.md).

### For AMD GPU users on Linux

```bash
python start_services.py --profile gpu-amd
```

### For Mac / Apple Silicon users

If you're using a Mac with an M1 or newer processor, you can't expose your GPU to the Docker instance, unfortunately. There are two options in this case:

1. Run the starter kit fully on CPU:
   ```bash
   python start_services.py --profile cpu
   ```

2. Run Ollama on your Mac for faster inference, and connect to that from the n8n instance:
   ```bash
   python start_services.py --profile none
   ```

   If you want to run Ollama on your mac, check the [Ollama homepage](https://ollama.com/) for installation instructions.

#### For Mac users running OLLAMA locally

If you're running OLLAMA locally on your Mac (not in Docker), you need to modify the OLLAMA_HOST environment variable in the n8n service configuration. Update the x-n8n section in your Docker Compose file as follows:

```yaml
x-n8n: &service-n8n
  # ... other configurations ...
  environment:
    # ... other environment variables ...
    - OLLAMA_HOST=host.docker.internal:11434
```

Additionally, after you see "Editor is now accessible via: http://localhost:5678/":

1. Head to http://localhost:5678/home/credentials
2. Click on "Local Ollama service"
3. Change the base URL to "http://host.docker.internal:11434/"

### For everyone else

```bash
python start_services.py --profile cpu
```

### The environment argument
The **start-services.py** script offers the possibility to pass one of two options for the environment argument, **private** (default environment) and **public**:
- **private:** you are deploying the stack in a safe environment, hence a lot of ports can be made accessible without having to worry about security
- **public:** the stack is deployed in a public environment, which means the attack surface should be made as small as possible. All ports except for 80 and 443 are closed

The stack initialized with
```bash
   python start_services.py --profile gpu-nvidia --environment private
   ```
equals the one initialized with
```bash
   python start_services.py --profile gpu-nvidia
   ```

## Deploying to the Cloud

### Prerequisites for the below steps

- Linux machine (preferably Unbuntu) with Nano, Git, and Docker installed

### Extra steps

Before running the above commands to pull the repo and install everything:

1. Run the commands as root to open up the necessary ports:
   - ufw enable
   - ufw allow 80 && ufw allow 443
   - ufw reload
   ---
   **WARNING**

   ufw does not shield ports published by docker, because the iptables rules configured by docker are analyzed before those configured by ufw. There is a solution to change this behavior, but that is out of scope for this project. Just make sure that all traffic runs through the caddy service via port 443. Port 80 should only be used to redirect to port 443.

   ---
2. Run the **start-services.py** script with the environment argument **public** to indicate you are going to run the package in a public environment. The script will make sure that all ports, except for 80 and 443, are closed down, e.g.

```bash
   python3 start_services.py --profile gpu-nvidia --environment public
   ```

3. Set up A records for your DNS provider to point your subdomains you'll set up in the .env file for Caddy
to the IP address of your cloud instance.

   For example, A record to point n8n to [cloud instance IP] for n8n.yourdomain.com


**NOTE**: If you are using a cloud machine without the "docker compose" command available by default, such as a Ubuntu GPU instance on DigitalOcean, run these commands before running start_services.py:

- DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\\" -f4)
- sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
- sudo chmod +x /usr/local/bin/docker-compose
- sudo mkdir -p /usr/local/lib/docker/cli-plugins
- sudo ln -s /usr/local/bin/docker-compose /usr/local/lib/docker/cli-plugins/docker-compose

## ⚡️ Quick start and usage

The main component of the self-hosted AI starter kit is a docker compose file
pre-configured with network and disk so there isn’t much else you need to
install. After completing the installation steps above, follow the steps below
to get started.

1. Open <http://localhost:5678/> in your browser to set up n8n. You’ll only
   have to do this once. You are NOT creating an account with n8n in the setup here,
   it is only a local account for your instance!
2. Open the included workflow:
   <http://localhost:5678/workflow/vTN9y2dLXqTiDfPT>
3. Create credentials for every service:
   
   Ollama URL: http://ollama:11434

   Postgres (through Supabase): use DB, username, and password from .env. IMPORTANT: Host is 'db'
   Since that is the name of the service running Supabase

   Qdrant URL: http://qdrant:6333 (API key can be whatever since this is running locally)

   Google Drive: Follow [this guide from n8n](https://docs.n8n.io/integrations/builtin/credentials/google/).
   Don't use localhost for the redirect URI, just use another domain you have, it will still work!
   Alternatively, you can set up [local file triggers](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.localfiletrigger/).
4. Select **Test workflow** to start running the workflow.
5. If this is the first time you’re running the workflow, you may need to wait
   until Ollama finishes downloading Llama3.1. You can inspect the docker
   console logs to check on the progress.
6. Make sure to toggle the workflow as active and copy the "Production" webhook URL!
7. Open <http://localhost:3000/> in your browser to set up Open WebUI.
You’ll only have to do this once. You are NOT creating an account with Open WebUI in the 
setup here, it is only a local account for your instance!
8. Go to Workspace -> Functions -> Add Function -> Give name + description then paste in
the code from `n8n_pipe.py`

   The function is also [published here on Open WebUI's site](https://openwebui.com/f/coleam/n8n_pipe/).

9. Click on the gear icon and set the n8n_url to the production URL for the webhook
you copied in a previous step.
10. Toggle the function on and now it will be available in your model dropdown in the top left! 

To open n8n at any time, visit <http://localhost:5678/> in your browser.
To open Open WebUI at any time, visit <http://localhost:3000/>.

With your n8n instance, you’ll have access to over 400 integrations and a
suite of basic and advanced AI nodes such as
[AI Agent](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/),
[Text classifier](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.text-classifier/),
and [Information Extractor](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.information-extractor/)
nodes. To keep everything local, just remember to use the Ollama node for your
language model and Qdrant as your vector store.

> [!NOTE]
> This starter kit is designed to help you get started with self-hosted AI
> workflows. While it’s not fully optimized for production environments, it
> combines robust components that work well together for proof-of-concept
> projects. You can customize it to meet your specific needs

## Upgrading

To update all containers to their latest versions (n8n, Open WebUI, etc.), run these commands:

```bash
# Stop all services
docker compose -p localai -f docker-compose.yml --profile <your-profile> down

# Pull latest versions of all containers
docker compose -p localai -f docker-compose.yml --profile <your-profile> pull

# Start services again with your desired profile
python start_services.py --profile <your-profile>
```

Replace `<your-profile>` with one of: `cpu`, `gpu-nvidia`, `gpu-amd`, or `none`.

Note: The `start_services.py` script itself does not update containers - it only restarts them or pulls them if you are downloading these containers for the first time. To get the latest versions, you must explicitly run the commands above.

## Troubleshooting

Here are solutions to common issues you might encounter:

### Supabase Issues

- **Supabase Pooler Restarting**: If the supabase-pooler container keeps restarting itself, follow the instructions in [this GitHub issue](https://github.com/supabase/supabase/issues/30210#issuecomment-2456955578).

- **Supabase Analytics Startup Failure**: If the supabase-analytics container fails to start after changing your Postgres password, delete the folder `supabase/docker/volumes/db/data`.

- **If using Docker Desktop**: Go into the Docker settings and make sure "Expose daemon on tcp://localhost:2375 without TLS" is turned on

- **Supabase Service Unavailable** - Make sure you don't have an "@" character in your Postgres password! If the connection to the kong container is working (the container logs say it is receiving requests from n8n) but n8n says it cannot connect, this is generally the problem from what the community has shared. Other characters might not be allowed too, the @ symbol is just the one I know for sure!

- **SearXNG Restarting**: If the SearXNG container keeps restarting, run the command "chmod 755 searxng" within the local-ai-packaged folder so SearXNG has the permissions it needs to create the uwsgi.ini file.

- **Files not Found in Supabase Folder** - If you get any errors around files missing in the supabase/ folder like .env, docker/docker-compose.yml, etc. this most likely means you had a "bad" pull of the Supabase GitHub repository when you ran the start_services.py script. Delete the supabase/ folder within the Local AI Package folder entirely and try again.

### GPU Support Issues

- **Windows GPU Support**: If you're having trouble running Ollama with GPU support on Windows with Docker Desktop:
  1. Open Docker Desktop settings
  2. Enable WSL 2 backend
  3. See the [Docker GPU documentation](https://docs.docker.com/desktop/features/gpu/) for more details

- **Linux GPU Support**: If you're having trouble running Ollama with GPU support on Linux, follow the [Ollama Docker instructions](https://github.com/ollama/ollama/blob/main/docs/docker.md).

## 👓 Recommended reading

n8n is full of useful content for getting started quickly with its AI concepts
and nodes. If you run into an issue, go to [support](#support).

- [AI agents for developers: from theory to practice with n8n](https://blog.n8n.io/ai-agents/)
- [Tutorial: Build an AI workflow in n8n](https://docs.n8n.io/advanced-ai/intro-tutorial/)
- [Langchain Concepts in n8n](https://docs.n8n.io/advanced-ai/langchain/langchain-n8n/)
- [Demonstration of key differences between agents and chains](https://docs.n8n.io/advanced-ai/examples/agent-chain-comparison/)
- [What are vector databases?](https://docs.n8n.io/advanced-ai/examples/understand-vector-databases/)

## 🎥 Video walkthrough

- [Cole's Guide to the Local AI Starter Kit](https://youtu.be/pOsO40HSbOo)

## 🛍️ More AI templates

For more AI workflow ideas, visit the [**official n8n AI template
gallery**](https://n8n.io/workflows/?categories=AI). From each workflow,
select the **Use workflow** button to automatically import the workflow into
your local n8n instance.

### Learn AI key concepts

- [AI Agent Chat](https://n8n.io/workflows/1954-ai-agent-chat/)
- [AI chat with any data source (using the n8n workflow too)](https://n8n.io/workflows/2026-ai-chat-with-any-data-source-using-the-n8n-workflow-tool/)
- [Chat with OpenAI Assistant (by adding a memory)](https://n8n.io/workflows/2098-chat-with-openai-assistant-by-adding-a-memory/)
- [Use an open-source LLM (via HuggingFace)](https://n8n.io/workflows/1980-use-an-open-source-llm-via-huggingface/)
- [Chat with PDF docs using AI (quoting sources)](https://n8n.io/workflows/2165-chat-with-pdf-docs-using-ai-quoting-sources/)
- [AI agent that can scrape webpages](https://n8n.io/workflows/2006-ai-agent-that-can-scrape-webpages/)

### Local AI templates

- [Tax Code Assistant](https://n8n.io/workflows/2341-build-a-tax-code-assistant-with-qdrant-mistralai-and-openai/)
- [Breakdown Documents into Study Notes with MistralAI and Qdrant](https://n8n.io/workflows/2339-breakdown-documents-into-study-notes-using-templating-mistralai-and-qdrant/)
- [Financial Documents Assistant using Qdrant and](https://n8n.io/workflows/2335-build-a-financial-documents-assistant-using-qdrant-and-mistralai/) [ Mistral.ai](http://mistral.ai/)
- [Recipe Recommendations with Qdrant and Mistral](https://n8n.io/workflows/2333-recipe-recommendations-with-qdrant-and-mistral/)

## Tips & tricks

### Accessing local files

The self-hosted AI starter kit will create a shared folder (by default,
located in the same directory) which is mounted to the n8n container and
allows n8n to access files on disk. This folder within the n8n container is
located at `/data/shared` -- this is the path you’ll need to use in nodes that
interact with the local filesystem.

**Nodes that interact with the local filesystem**

- [Read/Write Files from Disk](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.filesreadwrite/)
- [Local File Trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.localfiletrigger/)
- [Execute Command](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executecommand/)

## 📜 License

This project (originally created by the n8n team, link at the top of the README) is licensed under the Apache License 2.0 - see the
[LICENSE](LICENSE) file for details.
