# Quick Start: Bitwarden Secrets Setup

This is a quick reference guide. For detailed instructions, see [BITWARDEN_SETUP.md](BITWARDEN_SETUP.md).

## Prerequisites

```bash
# Install Bitwarden CLI
npm install -g @bitwarden/cli

# Verify installation
bw --version
```

## Step 1: Generate and Store Secrets in Bitwarden

### Option A: Use the Secret Generator Script (Easiest)

```bash
# Generate all secrets at once
./generate_secrets.sh
```

This will generate all required secrets and display them. Copy each value into Bitwarden.

### Option B: Generate Manually

```bash
# Generate secrets individually
openssl rand -hex 32  # Use for most secrets

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**Required Secrets to Create:**
1. N8N_ENCRYPTION_KEY
2. N8N_USER_MANAGEMENT_JWT_SECRET
3. POSTGRES_PASSWORD
4. JWT_SECRET
5. ANON_KEY (use Supabase JWT generator)
6. SERVICE_ROLE_KEY (use Supabase JWT generator)
7. DASHBOARD_USERNAME
8. DASHBOARD_PASSWORD
9. POOLER_TENANT_ID
10. NEO4J_AUTH (format: `username/password`)
11. CLICKHOUSE_PASSWORD
12. MINIO_ROOT_PASSWORD
13. LANGFUSE_SALT
14. NEXTAUTH_SECRET
15. ENCRYPTION_KEY

**How to Store in Bitwarden:**
1. Go to [vault.bitwarden.com](https://vault.bitwarden.com)
2. Click "+ Add Item"
3. Name: Use the exact secret name (e.g., `N8N_ENCRYPTION_KEY`)
4. Password: Paste your generated secret value
5. Save

**Supabase JWT Keys:**
Generate at: https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys

## Step 2: Run Setup Script

### Local Development

```bash
# Option A: Bash script (Linux/Mac)
cd local-ai-packaged
./setup_bitwarden_secrets.sh

# Option B: Python script (Cross-platform)
cd local-ai-packaged
python setup_bitwarden_secrets.py
```

The script will:
- ✓ Check Bitwarden CLI installation
- ✓ Login/unlock your vault
- ✓ Fetch all secrets
- ✓ Create .env file
- ✓ Validate required secrets

## Step 3: Deploy Services

```bash
# Choose your profile:
python start_services.py --profile cpu          # CPU only
python start_services.py --profile gpu-nvidia   # NVIDIA GPU
python start_services.py --profile gpu-amd      # AMD GPU
python start_services.py --profile none         # External Ollama
```

## GitHub Actions (CI/CD)

### One-Time Setup

1. Create machine account in Bitwarden (recommended) or use personal account
2. In GitHub: Settings → Secrets and variables → Actions
3. Add secrets:
   - `BW_CLIENTID` (machine account ID)
   - `BW_CLIENTSECRET` (machine account secret)
   - OR `BW_PASSWORD` (your master password - less secure)

### Deploy

1. Go to Actions tab in GitHub
2. Select "Deploy with Bitwarden Secrets"
3. Run workflow
4. Choose profile and environment

## Troubleshooting

### Script says "bw not found"
```bash
npm install -g @bitwarden/cli
```

### Secret not found
Check the name in Bitwarden vault - it should match exactly (e.g., `N8N_ENCRYPTION_KEY`)

### Session expired
```bash
export BW_SESSION=$(bw unlock --raw)
```

### Need to start over
```bash
bw logout
bw login
export BW_SESSION=$(bw unlock --raw)
./setup_bitwarden_secrets.sh
```

## Security Checklist

- [ ] Used strong master password for Bitwarden
- [ ] Enabled 2FA on Bitwarden account
- [ ] Generated all secrets with `openssl rand -hex 32`
- [ ] Never committed .env file to git
- [ ] Used machine account for GitHub Actions (not personal password)
- [ ] Stored backup of .env file securely (offline)

## What's Next?

After setup completes successfully:

1. Services will be accessible at:
   - n8n: http://localhost:5678
   - Open WebUI: http://localhost:3000
   - Supabase: http://localhost:8000
   - Flowise: http://localhost:3001
   - Langfuse: http://localhost:3030

2. Follow the main [README.md](README.md) for:
   - Configuring workflows
   - Setting up credentials
   - Using the AI services

## Need Help?

- **Detailed Guide**: [BITWARDEN_SETUP.md](BITWARDEN_SETUP.md)
- **Main README**: [README.md](README.md)
- **GitHub Issues**: Report problems or ask questions
- **Bitwarden CLI Docs**: https://bitwarden.com/help/cli/
