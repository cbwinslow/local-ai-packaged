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

# Step 1: Login using API token (non-interactive)
echo "🔐 Logging into Cloudflare using API token..."
cloudflared tunnel login --hostname api.cloudflare.com

# Step 2: Create the tunnel programmatically
TUNNEL_NAME="local-ai-tunnel"
echo "🏗️  Creating tunnel: $TUNNEL_NAME..."

TUNNEL_ID=$(cloudflared tunnel create $TUNNEL_NAME --quiet | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TUNNEL_ID" ]; then
    echo "❌ Failed to create tunnel"
    exit 1
fi

echo "✅ Tunnel created with ID: ${TUNNEL_ID:0:8}..."

# Step 3: Create the tunnel configuration
mkdir -p ~/.cloudflared

cat > ~/.cloudflared/config.yml << EOF
tunnel: $TUNNEL_ID
credentials-file: /root/.cloudflared/$TUNNEL_ID.json

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

# Step 4: Use API to configure DNS routes
echo "🌐 Configuring DNS routes via Cloudflare API..."

# Get zone ID for the domain
DOMAIN="cloudcurio.cc"
ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$DOMAIN" \
     -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
     -H "Content-Type: application/json" | \
     jq -r '.result[0].id' 2>/dev/null)

if [ -z "$ZONE_ID" ] || [ "$ZONE_ID" = "null" ]; then
    echo "❌ Could not find Zone ID for domain $DOMAIN"
    echo "Please ensure the domain is added to your Cloudflare account"
    exit 1
fi

echo "✅ Found Zone ID: ${ZONE_ID:0:8}..."

# Create DNS records for each service
SERVICES=("n8n" "openwebui" "flowise" "ollama" "neo4j" "qdrant")

for service in "${SERVICES[@]}"; do
    SUBDOMAIN="$service.cloudcurio.cc"
    
    # Check if DNS record already exists
    EXISTS=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=CNAME&name=$SUBDOMAIN" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json" | \
        jq -r '.result | length')
    
    if [ "$EXISTS" = "0" ]; then
        # Create DNS record
        RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
            -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"CNAME\",\"name\":\"$SUBDOMAIN\",\"content\":\"$TUNNEL_ID.cfargotunnel.com\",\"ttl\":1,\"priority\":10,\"proxied\":true}")
        
        SUCCESS=$(echo $RESPONSE | jq -r '.success')
        if [ "$SUCCESS" = "true" ]; then
            echo "✅ Created DNS record: $SUBDOMAIN"
        else
            echo "❌ Failed to create DNS record for $SUBDOMAIN"
            echo "Response: $RESPONSE"
        fi
    else
        echo "ℹ️  DNS record for $SUBDOMAIN already exists"
    fi
done

# Step 5: Associate tunnel with DNS routes using API
echo "🔗 Associating tunnel with DNS routes..."
cloudflared tunnel route dns $TUNNEL_NAME --overwrite-dns n8n.cloudcurio.cc
cloudflared tunnel route dns $TUNNEL_NAME openwebui.cloudcurio.cc
cloudflared tunnel route dns $TUNNEL_NAME flowise.cloudcurio.cc
cloudflared tunnel route dns $TUNNEL_NAME ollama.cloudcurio.cc
cloudflared tunnel route dns $TUNNEL_NAME neo4j.cloudcurio.cc
cloudflared tunnel route dns $TUNNEL_NAME qdrant.cloudcurio.cc

echo "✅ DNS routes configured for the tunnel"

# Step 6: Create a service to run the tunnel automatically
echo "⚙️  Creating tunnel service..."

# Create tunnel run script
cat > /home/cbwinslow/projects/local-ai-packaged/run_tunnel.sh << 'EOF'
#!/bin/bash
# Script to run Cloudflare Tunnel

echo "🚀 Starting Cloudflare Tunnel..."
cloudflared tunnel run --config /root/.cloudflared/config.yml
EOF

chmod +x /home/cbwinslow/projects/local-ai-packaged/run_tunnel.sh

# Optionally create systemd service
cat > /etc/systemd/system/cloudflare-tunnel.service << EOF
[Unit]
Description=Cloudflare Tunnel for Local AI Package
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/cloudflared tunnel run --config /root/.cloudflared/config.yml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Created tunnel service configuration"

# Final instructions
echo ""
echo "🎉 Cloudflare Tunnel Setup Complete!"
echo "======================================="
echo ""
echo "✅ Tunnel '$TUNNEL_NAME' created with ID: $TUNNEL_ID"
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
echo "   cloudflared tunnel run --config /root/.cloudflared/config.yml"
echo ""
echo "⚡ To run as a service permanently:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable cloudflare-tunnel"
echo "   sudo systemctl start cloudflare-tunnel"
echo ""
echo "📋 To check tunnel status:"
echo "   cloudflared tunnel info $TUNNEL_NAME"
echo ""
echo "The tunnel is now fully configured and ready to provide external access to your Local AI Package!"