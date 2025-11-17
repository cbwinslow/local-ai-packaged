# Access Summary for Local AI Package

## Current Status
- All services are **RUNNING** (confirmed by docker ps)
- Services are accessible **internally** within Docker network
- External access via **Cloudflare Tunnels** (pending manual setup)

## Cloudflare Tunnel Setup
1. Run: `cloudflared tunnel login`
2. Run: `cloudflared tunnel create local-ai-tunnel`
3. Add DNS routes in Cloudflare dashboard
4. Start: `cloudflared tunnel run local-ai-tunnel`

## Services Accessible Internally
- n8n: `http://n8n:5678`
- Open WebUI: `http://open-webui:8080`
- Ollama: `http://ollama:11434`
- Flowise: `http://flowise:3001`
- Qdrant: `http://qdrant:6333`
- Neo4j: `http://localai-neo4j-1:7474`

## Monitoring
- Check health: `bash check_services_health.sh`
- View logs: `docker logs <service_name>`

## Port Conflicts
- Ports 80/443 are used by Traefik and NextCloud AIO
- Caddy reverse proxy cannot start on standard ports
- Cloudflare Tunnels provide secure external access without direct port access
