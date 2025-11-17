# Cloudflare Tunnel Configuration for Local AI Package

# Run the following commands to set up Cloudflare Tunnel:

# 1. Login to Cloudflare (first time only)
# cloudflared tunnel login

# 2. Create a tunnel
# cloudflared tunnel create local-ai-tunnel

# 3. Create this configuration file at ~/.cloudflared/config.yml:
tunnel: local-ai-tunnel
credentials-file: /root/.cloudflared/local-ai-tunnel.json

# 4. Add your domain routes to Cloudflare DNS
# cloudflared tunnel route dns local-ai-tunnel n8n.cloudcurio.cc
# cloudflared tunnel route dns local-ai-tunnel openwebui.cloudcurio.cc
# cloudflared tunnel route dns local-ai-tunnel flowise.cloudcurio.cc
# cloudflared tunnel route dns local-ai-tunnel ollama.cloudcurio.cc
# cloudflared tunnel route dns local-ai-tunnel neo4j.cloudcurio.cc

ingress:
  # Route n8n service
  - hostname: n8n.cloudcurio.cc
    service: http://n8n:5678
    originRequest:
      # Skip certificate verification for internal service
      noTLSVerify: true

  # Route Open WebUI service  
  - hostname: openwebui.cloudcurio.cc
    service: http://open-webui:8080
    originRequest:
      noTLSVerify: true

  # Route Flowise service
  - hostname: flowise.cloudcurio.cc
    service: http://flowise:3001
    originRequest:
      noTLSVerify: true

  # Route Ollama service
  - hostname: ollama.cloudcurio.cc
    service: http://ollama:11434
    originRequest:
      noTLSVerify: true

  # Route Neo4j service
  - hostname: neo4j.cloudcurio.cc
    service: http://localai-neo4j-1:7474
    originRequest:
      noTLSVerify: true

  # Default catch-all route
  - service: http_status:404