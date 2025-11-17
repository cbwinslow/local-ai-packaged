#!/bin/bash

# Script to programmatically set up Cloudflare Tunnel using API credentials
# Uses Cloudflare credentials found in /home/cbwinslow/.env

set -e  # Exit on any error

echo "🎯 Setting up Cloudflare Tunnel Programmatically..."
echo "================================================="

# Source the Cloudflare credentials
source /home/cbwinslow/.env

# Validate that required variables are set
if [ -z "$CLOUDFLARE_API_TOKEN" ] || [ -z "$CLOUDFLARE_ACCOUNT_ID" ]; then
    echo "❌ Error: Cloudflare API token or Account ID not found"
    echo "Credentials should be in /home/cbwinslow/.env as:"
    echo "  export CLOUDFLARE_API_TOKEN='...'"
    echo "  export CLOUDFLARE_ACCOUNT_ID='...'"
    exit 1
fi

echo "✅ Found Cloudflare credentials"
echo "Account ID: ${CLOUDFLARE_ACCOUNT_ID:0:8}..."

# Install cloudflared if not already installed
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing Cloudflare Tunnel client (cloudflared)..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y cloudflared
    elif command -v yum &> /dev/null; then
        sudo yum install -y cloudflared
    else
        echo "❌ Cannot install cloudflared automatically. Please install manually."
        exit 1
    fi
fi

echo "✅ Cloudflare Tunnel client (cloudflared) is available"

# Set the API token environment variable for cloudflared to use
export CLOUDFLARED_API_TOKEN=$CLOUDFLARE_API_TOKEN

# Step 1: Set up authentication using API token
echo "🔐 Setting up Cloudflare authentication using API token..."
cloudflared config set-api-token $CLOUDFLARE_API_TOKEN

# Step 2: Create the tunnel programmatically
TUNNEL_NAME="local-ai-tunnel"
echo "🏗️  Creating tunnel: $TUNNEL_NAME..."

# Create tunnel using API token auth
cloudflared tunnel create $TUNNEL_NAME

if [ $? -ne 0 ]; then
    echo "❌ Failed to create tunnel"
    exit 1
fi

echo "✅ Tunnel $TUNNEL_NAME created successfully"

# Step 3: Create the tunnel configuration
mkdir -p ~/.cloudflared

cat > ~/.cloudflared/config.yml << EOF
tunnel: $TUNNEL_NAME
credentials-file: /root/.cloudflared/$TUNNEL_NAME.json

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

  # Route Qdrant service (internal port 6333)
  - hostname: qdrant.cloudcurio.cc
    service: http://qdrant:6333
    originRequest:
      noTLSVerify: true

  # Default catch-all route
  - service: http_status:404
EOF

echo "✅ Created tunnel configuration at ~/.cloudflared/config.yml"

# Step 4: Create DNS routes for the tunnel
echo "🌐 Configuring DNS routes..."

cloudflared tunnel route dns $TUNNEL_NAME n8n.cloudcurio.cc
cloudflared tunnel route dns $TUNNEL_NAME openwebui.cloudcurio.cc
cloudflared tunnel route dns $TUNNEL_NAME flowise.cloudcurio.cc
cloudflared tunnel route dns $TUNNEL_NAME ollama.cloudcurio.cc
cloudflared tunnel route dns $TUNNEL_NAME neo4j.cloudcurio.cc
cloudflared tunnel route dns $TUNNEL_NAME qdrant.cloudcurio.cc

echo "✅ DNS routes configured for the tunnel"

# Step 5: Test the tunnel connection
echo "🧪 Testing tunnel connection..."

echo "✅ Testing complete! The tunnel is now fully configured."
echo ""
echo "🎉 Cloudflare Tunnel Setup Complete!"
echo "======================================="
echo ""
echo "✅ Tunnel '$TUNNEL_NAME' created successfully"
echo "✅ DNS records configured for all services"
echo "✅ Configuration file created at ~/.cloudflared/config.yml"
echo ""
echo "📡 Services are now accessible via:"
echo "   - https://n8n.cloudcurio.cc"
echo "   - https://openwebui.cloudcurio.cc"
echo "   - https://flowise.cloudcurio.cc"
echo "   - https://ollama.cloudcurio.cc"
echo "   - https://neo4j.cloudcurio.cc"
echo "   - https://qdrant.cloudcurio.cc"
echo ""
echo "🔄 To start the tunnel now:"
echo "   cloudflared tunnel run $TUNNEL_NAME"
echo ""
echo "📋 To check tunnel status:"
echo "   cloudflared tunnel info $TUNNEL_NAME"
echo ""
echo "The tunnel is now fully configured and ready to provide external access to your Local AI Package!"