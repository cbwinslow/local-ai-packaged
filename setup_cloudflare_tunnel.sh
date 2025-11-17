#!/bin/bash

# Cloudflare Tunnel Setup Script for Local AI Package
# This script sets up Cloudflare Tunnels to make your services accessible externally
# even when ports 80/443 are occupied by other services

set -e  # Exit on any error

echo "Setting up Cloudflare Tunnel for Local AI Package..."

# Create the Cloudflare Tunnel configuration
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: local-ai-tunnel
credentials-file: /root/.cloudflared/local-ai-tunnel.json

ingress:
  # Route n8n service (internal port 5678)
  - hostname: n8n.cloudcurio.cc
    service: http://n8n:5678
    originRequest:
      noTLSVerify: true

  # Route Open WebUI service (internal port 8080)  
  - hostname: openwebui.cloudcurio.cc
    service: http://open-webui:8080
    originRequest:
      noTLSVerify: true

  # Route Flowise service (internal port 3001)
  - hostname: flowise.cloudcurio.cc
    service: http://flowise:3001
    originRequest:
      noTLSVerify: true

  # Route Ollama API (internal port 11434)
  - hostname: ollama.cloudcurio.cc
    service: http://ollama:11434
    originRequest:
      noTLSVerify: true

  # Route Neo4j service (internal port 7474)
  - hostname: neo4j.cloudcurio.cc
    service: http://localai-neo4j-1:7474
    originRequest:
      noTLSVerify: true

  # Default catch-all route
  - service: http_status:404
EOF

echo "Configuration file created at ~/.cloudflared/config.yml"

echo ""
echo "To complete the setup, follow these steps:"
echo ""
echo "1. Create your Cloudflare Tunnel:"
echo "   cloudflared tunnel create local-ai-tunnel"
echo ""
echo "2. Configure the tunnel route in Cloudflare DNS portal:"
echo "   - Go to dash.cloudflare.com"
echo "   - Navigate to Zero Trust > Networks > Tunnels"
echo "   - Find your 'local-ai-tunnel'"
echo "   - Go to Public Hostnames and add these routes:"
echo "     - n8n.cloudcurio.cc -> local-ai-tunnel"
echo "     - openwebui.cloudcurio.cc -> local-ai-tunnel" 
echo "     - flowise.cloudcurio.cc -> local-ai-tunnel"
echo "     - ollama.cloudcurio.cc -> local-ai-tunnel"
echo "     - neo4j.cloudcurio.cc -> local-ai-tunnel"
echo ""
echo "3. Start the Cloudflare Tunnel:"
echo "   cloudflared tunnel run local-ai-tunnel"
echo ""
echo "Note: The tunnel will connect to your Docker containers via their internal names."
echo "Make sure the Docker containers are on the default bridge network or accessible via DNS resolution."
echo ""
echo "Once running, your services will be accessible via:"
echo "  - https://n8n.cloudcurio.cc"
echo "  - https://openwebui.cloudcurio.cc"
echo "  - https://flowise.cloudcurio.cc"
echo "  - https://ollama.cloudcurio.cc"
echo "  - https://neo4j.cloudcurio.cc"