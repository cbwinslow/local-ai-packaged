#!/bin/bash
set -e

# Create necessary directories
mkdir -p ./certs ./letsencrypt ./logs

# Generate a random password for Traefik dashboard
TRAEFIK_PASSWORD=$(openssl rand -base64 16)
TRAEFIK_USER=admin
TRAEFIK_AUTH=$(echo $(htpasswd -nb $TRAEFIK_USER $TRAEFIK_PASSWORD) | sed -e s/\\$/\\$\$/g)

# Create .env file
cat > .env <<EOL
# Traefik Configuration
DOMAIN=yourdomain.com  # Replace with your domain
TRAEFIK_AUTH_USERS=$TRAEFIK_AUTH

# Cloudflare Configuration (for DNS challenge)
CLOUDFLARE_EMAIL=your-email@example.com  # Replace with your Cloudflare email
CLOUDFLARE_API_KEY=your-cloudflare-api-key  # Replace with your Cloudflare API key

# Let's Encrypt Configuration
ACME_EMAIL=your-email@example.com  # Replace with your email for Let's Encrypt

# Network Configuration
TRAEFIK_NETWORK=traefik-public
EOL

echo "Traefik environment has been configured."
echo "Dashboard username: $TRAEFIK_USER"
echo "Dashboard password: $TRAEFIK_PASSWORD"
echo "Please save these credentials in a secure location."
echo "Review and update the .env file with your actual domain and Cloudflare credentials."
