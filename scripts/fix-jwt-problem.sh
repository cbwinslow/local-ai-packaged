#!/bin/bash
set -euo pipefail

echo "=== Fix Supabase JWT Token Issues ==="
echo "This script fixes the YAML parsing problems caused by special characters in JWT tokens"
echo

# Backup current .env
cp .env .env.before-jwt-fix

# Generate clean JWT secret (lowercase hex only)
JWT_SECRET=$(openssl rand -hex 32 | tr '[A-Z]' '[a-z]')

# Generate clean JWT tokens using base64url encoding (no problematic characters)
header_base64=$(echo -n '{"alg":"HS256","typ":"JWT"}' | openssl base64 -e | tr '+/' '-_' | tr -d '=' | tr -d '\n')
payload_anon=$(echo -n '{"iss":"supabase","role":"anon","iat":1639239557,"exp":1954803557}' | openssl base64 -e | tr '+/' '-_' | tr -d '=' | tr -d '\n')
payload_service=$(echo -n '{"iss":"supabase","role":"service_role","iat":1639239557,"exp":1954803557}' | openssl base64 -e | tr '+/' '-_' | tr -d '=' | tr -d '\n')

signature_anon=$(echo -n "${header_base64}.${payload_anon}" | openssl dgst -sha256 -hmac "${JWT_SECRET}" -binary | openssl base64 -e | tr '+/' '-_' | tr -d '=' | tr -d '\n')
signature_service=$(echo -n "${header_base64}.${payload_service}" | openssl dgst -sha256 -hmac "${JWT_SECRET}" -binary | openssl base64 -e | tr '+/' '-_' | tr -d '=' | tr -d '\n')

ANON_KEY="${header_base64}.${payload_anon}.${signature_anon}"
SERVICE_ROLE_KEY="${header_base64}.${payload_service}.${signature_service}"

# Generate clean dashboard credentials
DASHBOARD_USERNAME="dashboard_user"
DASHBOARD_PASSWORD=$(openssl rand -hex 16 | tr '[A-Z]' '[a-z]')

echo "Generated clean JWT tokens:"
echo "  JWT_SECRET: ${JWT_SECRET}"
echo "  ANON_KEY: ${ANON_KEY}"
echo "  SERVICE_ROLE_KEY: ${SERVICE_ROLE_KEY}"
echo "  DASHBOARD_USERNAME: ${DASHBOARD_USERNAME}"
echo "  DASHBOARD_PASSWORD: ${DASHBOARD_PASSWORD}"
echo

# Update .env file
sed -i "s/JWT_SECRET=.*/JWT_SECRET=${JWT_SECRET}/" .env
sed -i "s/ANON_KEY=.*/ANON_KEY=${ANON_KEY}/" .env
sed -i "s/SERVICE_ROLE_KEY=.*/SERVICE_ROLE_KEY=${SERVICE_ROLE_KEY}/" .env
sed -i "s/DASHBOARD_USERNAME=.*/DASHBOARD_USERNAME=${DASHBOARD_USERNAME}/" .env
sed -i "s/DASHBOARD_PASSWORD=.*/DASHBOARD_PASSWORD=${DASHBOARD_PASSWORD}/" .env

echo "✓ Updated .env with clean JWT tokens"
echo
echo "=== Next Steps ==="
echo "1. Stop current Supabase containers:"
echo "   docker compose down"
echo
echo "2. Start Supabase containers:"
echo "   docker compose up -d"
echo
echo "3. Check that Kong loads properly:"
echo "   docker logs supabase-kong"
echo
echo "4. Check that Auth service starts:"
echo "   docker logs supabase-auth"
echo
echo "JWT token fix completed! 🎉"
