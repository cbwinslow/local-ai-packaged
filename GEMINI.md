# Instructions for Next AI Agent

## Overview
This file provides detailed instructions for the next AI agent taking over this Local AI Package project. The system is fully configured and operational, but there are specific instructions for ongoing management and potential enhancements.

## Current Status
The Local AI Package is fully operational with the following key achievements:
- All services running with 10+ hour uptime
- Security configuration complete (all insecure placeholders replaced)
- Cloudflare Tunnel configured for external access
- All cloudcurio.cc domains properly configured
- Services: n8n, Ollama, Open WebUI, Flowise, Qdrant, Neo4j, SearXNG, Supabase stack, etc.

## Critical Information

### 1. External Access
To enable external access to all services:
```bash
cloudflared tunnel run local-ai-tunnel
```
Once running, services will be available at:
- https://n8n.cloudcurio.cc
- https://openwebui.cloudcurio.cc
- https://flowise.cloudcurio.cc
- https://ollama.cloudcurio.cc
- https://neo4j.cloudcurio.cc
- https://qdrant.cloudcurio.cc
- https://searxng.cloudcurio.cc
- https://supabase.cloudcurio.cc
- https://langfuse.cloudcurio.cc

### 2. Service Locations
- Project: `/home/cbwinslow/projects/local-ai-packaged/`
- Secrets: Retrieved from `/home/cbwinslow/.env` (contains Cloudflare API credentials)
- Tunnel config: `~/.cloudflared/config.yml`
- Main services: Docker containers (check with `docker ps`)

### 3. Security Configuration
- All .env files have secure, random-generated values
- No default/insecure passwords remain
- Cloudflare Tunnel handles SSL termination
- Services are only accessible through tunnel (secure by default)

## Ongoing Management Tasks

### Monitoring
- Check service health: `bash /home/cbwinslow/projects/local-ai-packaged/check_services_health.sh`
- View Docker container status: `docker ps`
- Monitor tunnel access by checking logs when tunnel is running

### Potential Enhancements

#### 1. Langfuse Service Activation
Langfuse is configured in the tunnel but needs to be started separately. The Docker Compose file defines langfuse-web and langfuse-worker services that may need to be activated separately if full Langfuse functionality is needed.

#### 2. Automated Tunnel Deployment
Consider setting up a systemd service or cron job to automatically restart the tunnel if it goes down:
```bash
# Example systemd service file could be created at /etc/systemd/system/cloudflare-tunnel.service
```

#### 3. Backup Strategy
- Docker volumes need to be backed up for persistent data
- Configuration files should be version controlled
- Secrets in Bitwarden should be regularly audited

### 3. Scaling Considerations
- Resource usage should be monitored as all services consume CPU/RAM
- Consider GPU acceleration for Ollama if needed
- Database performance monitoring for high-load scenarios

## Known Issues / Limitations

### 1. Port Conflicts
- Ports 80/443 are in use by other services (Traefik, NextCloud AIO)
- Workaround: Cloudflare Tunnel bypasses the need for direct port access
- Do NOT attempt to change other system services on ports 80/443

### 2. Tunnel Connectivity
- The tunnel must be actively running to provide external access
- If tunnel goes down, services are still accessible internally
- Consider setting up tunnel health checks/automatic restart

### 3. Domain Configuration
- All services configured for cloudcurio.cc domains
- Changing domains would require regenerating certificates and DNS updates

## Troubleshooting

### If Services Go Down
```bash
# Check if containers are running
docker ps

# Check logs for specific service
docker logs <service-name> --tail 50

# Restart services using the project script
cd /home/cbwinslow/projects/local-ai-packaged
python3 start_services.py --profile cpu
```

### If Tunnel Fails
```bash
# Check tunnel configuration
cloudflared tunnel info local-ai-tunnel

# Verify credentials file exists
ls -la /home/cbwinslow/.cloudflared/921d7ec0-08a3-4bb5-a0fe-959fcef03629.json

# Test tunnel configuration
cloudflared tunnel run --config ~/.cloudflared/config.yml
```

### If External Access Doesn't Work
1. Verify tunnel is running: `cloudflared tunnel run local-ai-tunnel`
2. Check DNS propagation: The CNAME records should point to the tunnel
3. Verify network connectivity to Cloudflare edge nodes

## Repository Information
- The project has all necessary files for operation
- Includes test frameworks in the `tests/` directory
- Documentation files provide full system understanding
- Ready for Git synchronization

## Git Repository Setup
The project is ready to be pushed to GitHub with all configurations complete and operational.