#!/bin/bash
set -e

# Set the domain
domain="opendiscourse.net"

# Generate a secure password for Traefik dashboard
TRAEFIK_PASSWORD=$(openssl rand -base64 16)
TRAEFIK_USER="admin"
TRAEFIK_AUTH=$(echo $(htpasswd -nb $TRAEFIK_USER $TRAEFIK_PASSWORD) | sed -e s/\\$/\\$\$/g)

# Update .env file
echo "# Traefik Configuration" > .env
echo "DOMAIN=${domain}" >> .env
echo "TRAEFIK_AUTH_USERS=${TRAEFIK_AUTH}" >> .env
echo "" >> .env

# Add service domains
echo "# Service Domains" >> .env
echo "TRAEFIK_HOST=traefik.${domain}" >> .env
echo "SUPABASE_HOST=supabase.${domain}" >> .env
echo "N8N_HOST=n8n.${domain}" >> .env
echo "FLOWISE_HOST=flowise.${domain}" >> .env
echo "WEBUI_HOST=webui.${domain}" >> .env
echo "NEO4J_HOST=neo4j.${domain}" >> .env
echo "LANGCHAIN_HOST=langchain.${domain}" >> .env
echo "" >> .env

# Add Let's Encrypt email
echo "# Let's Encrypt Configuration" >> .env
echo "LETSENCRYPT_EMAIL=admin@${domain}" >> .env
echo "" >> .env

# Add Cloudflare configuration if available
if [ -n "${CLOUDFLARE_EMAIL}" ] && [ -n "${CLOUDFLARE_API_KEY}" ]; then
    echo "# Cloudflare Configuration" >> .env
    echo "CLOUDFLARE_EMAIL=${CLOUDFLARE_EMAIL}" >> .env
    echo "CLOUDFLARE_API_KEY=${CLOUDFLARE_API_KEY}" >> .env
    echo "" >> .env
fi

# Add database configuration
echo "# Database Configuration" >> .env
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "POSTGRES_DB=opendiscourse" >> .env
echo "POSTGRES_USER=opendiscourse" >> .env
echo "" >> .env

# Add JWT configuration
echo "# JWT Configuration" >> .env
echo "JWT_SECRET=$(openssl rand -base64 32)" >> .env
echo "JWT_EXPIRES_IN=3600" >> .env
echo "" >> .env

# Add service secrets
echo "# Service Secrets" >> .env
echo "N8N_ENCRYPTION_KEY=$(openssl rand -base64 32)" >> .env
echo "N8N_JWT_SECRET=$(openssl rand -base64 32)" >> .env
echo "FLOWISE_USERNAME=admin" >> .env
echo "FLOWISE_PASSWORD=$(openssl rand -base64 16)" >> .env
echo "" >> .env

# Output the generated credentials
echo "Traefik dashboard credentials:"
echo "Username: ${TRAEFIK_USER}"
echo "Password: ${TRAEFIK_PASSWORD}"
echo ""
echo ".env file has been updated with the new configuration."
echo "Make sure to save the credentials in a secure location."
