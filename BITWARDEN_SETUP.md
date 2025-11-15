# Bitwarden Secrets Setup Guide

This guide explains how to use Bitwarden to securely manage and deploy secrets for the Local AI Package.

## Overview

The Local AI Package requires various secrets and credentials to run properly. Instead of manually managing these secrets in a `.env` file, you can store them securely in Bitwarden and automatically fetch them during deployment.

## Benefits

- **Security**: Store all secrets in a secure, encrypted vault
- **Automation**: Automatically populate `.env` file from Bitwarden
- **CI/CD Integration**: Deploy with GitHub Actions using Bitwarden Secrets Manager
- **Team Collaboration**: Share secrets securely with team members
- **Audit Trail**: Track when secrets are accessed

## Prerequisites

1. **Bitwarden Account**: Sign up at [bitwarden.com](https://bitwarden.com)
2. **Bitwarden CLI**: Install the command-line tool
   ```bash
   npm install -g @bitwarden/cli
   ```
   Or download from [GitHub releases](https://github.com/bitwarden/clients/releases)

3. **Python 3**: Required for running the setup scripts

## Required Secrets

The following secrets must be stored in your Bitwarden vault:

### N8N Configuration
- `N8N_ENCRYPTION_KEY` - Generate with: `openssl rand -hex 32`
- `N8N_USER_MANAGEMENT_JWT_SECRET` - Generate with: `openssl rand -hex 32`

### Supabase Secrets
- `POSTGRES_PASSWORD` - Strong password for PostgreSQL database
- `JWT_SECRET` - At least 32 characters long
- `ANON_KEY` - Generate using [Supabase JWT generator](https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys)
- `SERVICE_ROLE_KEY` - Generate using [Supabase JWT generator](https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys)
- `DASHBOARD_USERNAME` - Username for Supabase dashboard
- `DASHBOARD_PASSWORD` - Strong password for Supabase dashboard
- `POOLER_TENANT_ID` - Any numeric value (e.g., 1000)

### Neo4j Secrets
- `NEO4J_AUTH` - Format: `username/password` (e.g., `neo4j/strongpassword`)

### Langfuse Credentials
- `CLICKHOUSE_PASSWORD` - Strong password for ClickHouse
- `MINIO_ROOT_PASSWORD` - Strong password for MinIO
- `LANGFUSE_SALT` - Random string for hashing
- `NEXTAUTH_SECRET` - Generate with: `openssl rand -hex 32`
- `ENCRYPTION_KEY` - Generate with: `openssl rand -hex 32`

### Optional Production Secrets
- `N8N_HOSTNAME` - Domain for n8n (e.g., `n8n.yourdomain.com`)
- `WEBUI_HOSTNAME` - Domain for Open WebUI
- `FLOWISE_HOSTNAME` - Domain for Flowise
- `SUPABASE_HOSTNAME` - Domain for Supabase
- `OLLAMA_HOSTNAME` - Domain for Ollama
- `SEARXNG_HOSTNAME` - Domain for SearXNG
- `NEO4J_HOSTNAME` - Domain for Neo4j
- `LETSENCRYPT_EMAIL` - Email for Let's Encrypt SSL certificates

### Additional Optional Secrets
- `SECRET_KEY_BASE` - Base key for encryption
- `VAULT_ENC_KEY` - 32-character encryption key

## Setting Up Secrets in Bitwarden

### Method 1: Manual Entry via Web Interface

1. Log in to your Bitwarden web vault at [vault.bitwarden.com](https://vault.bitwarden.com)
2. Click **Add Item** (+ button)
3. Select **Login** as the item type
4. Enter the following:
   - **Name**: Use one of these naming patterns:
     - Exact name: `N8N_ENCRYPTION_KEY`
     - User account: `user.account.N8N_ENCRYPTION_KEY`
     - User secret: `user.secret.N8N_ENCRYPTION_KEY`
     - Machine account: `machine.account.N8N_ENCRYPTION_KEY`
   - **Password**: Your secret value
5. Click **Save**
6. Repeat for all required secrets

### Method 2: Using Bitwarden CLI

```bash
# Login to Bitwarden
bw login

# Unlock vault
export BW_SESSION=$(bw unlock --raw)

# Create a secret
bw get template item | jq '.name="N8N_ENCRYPTION_KEY" | .login.password="your-secret-value"' | bw encode | bw create item

# Or use the simpler approach with existing templates
echo "your-secret-value" | bw create item login --name "N8N_ENCRYPTION_KEY" --password
```

### Generating Strong Secrets

Use these commands to generate secure random values:

```bash
# For most secrets (32 bytes hex)
openssl rand -hex 32

# For Python alternative
python -c "import secrets; print(secrets.token_hex(32))"

# For Supabase JWT tokens
# Use the generator at: https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys
```

## Local Setup (Development)

### Option 1: Using the Bash Script

```bash
# Navigate to the repository
cd local-ai-packaged

# Run the setup script
./setup_bitwarden_secrets.sh
```

### Option 2: Using the Python Script

```bash
# Navigate to the repository
cd local-ai-packaged

# Run the setup script
python setup_bitwarden_secrets.py
```

Both scripts will:
1. Check if Bitwarden CLI is installed
2. Verify you're logged in (prompt if not)
3. Unlock your vault (prompt for master password)
4. Search for all required secrets using multiple naming patterns
5. Create a `.env` file with the fetched secrets
6. Display a summary of found/missing secrets

### Script Features

- **Multiple Search Patterns**: Automatically tries different naming conventions
- **Backup Creation**: Backs up existing `.env` file before overwriting
- **Validation**: Checks that all required secrets are present
- **Color-Coded Output**: Visual feedback on success/failure
- **Security Reminders**: Ensures you don't commit secrets to git

## GitHub Actions Deployment

### Setting Up GitHub Secrets

You need to add Bitwarden credentials to your GitHub repository secrets:

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Add the following secrets:

#### Option A: Machine Account (Recommended for CI/CD)

1. Create a machine account in Bitwarden
2. Generate API credentials
3. Add these GitHub secrets:
   - `BW_CLIENTID` - Your Bitwarden client ID
   - `BW_CLIENTSECRET` - Your Bitwarden client secret

#### Option B: User Account

Add this GitHub secret:
- `BW_PASSWORD` - Your Bitwarden master password (less secure, not recommended)

### Running the Workflow

1. Go to **Actions** tab in your GitHub repository
2. Select **Deploy with Bitwarden Secrets** workflow
3. Click **Run workflow**
4. Choose your GPU profile (cpu, gpu-nvidia, gpu-amd, none)
5. Choose your environment (private, public)
6. Click **Run workflow**

The workflow will:
1. Install Bitwarden CLI
2. Login to Bitwarden using your credentials
3. Fetch all secrets from the vault
4. Create the `.env` file
5. Deploy the services using `start_services.py`
6. Verify services are running

## Naming Conventions

The scripts search for secrets using these patterns (in order):

1. **Exact name**: `N8N_ENCRYPTION_KEY`
2. **User account**: `user.account.N8N_ENCRYPTION_KEY`
3. **User secret**: `user.secret.N8N_ENCRYPTION_KEY`
4. **Machine account**: `machine.account.N8N_ENCRYPTION_KEY`

This allows flexibility in how you organize secrets in your vault.

## Troubleshooting

### "Bitwarden CLI not found"

Install the CLI:
```bash
npm install -g @bitwarden/cli
```

Or download from: https://github.com/bitwarden/clients/releases

### "Failed to unlock vault"

Make sure you're using the correct master password. Try:
```bash
bw logout
bw login
export BW_SESSION=$(bw unlock --raw)
```

### "Secret not found"

Ensure the secret exists in your vault with one of the supported naming patterns. You can search manually:
```bash
bw list items --search "N8N_ENCRYPTION_KEY" --session $BW_SESSION
```

### "Invalid session"

Your session may have expired. Re-unlock the vault:
```bash
export BW_SESSION=$(bw unlock --raw)
```

### GitHub Actions fails to fetch secrets

- Verify `BW_CLIENTID` and `BW_CLIENTSECRET` are correctly set in GitHub secrets
- Check that the machine account has access to the vault items
- Ensure secrets are stored in the correct Bitwarden organization/collection

## Security Best Practices

1. **Never commit `.env` files**: Already in `.gitignore`, but be careful
2. **Use strong master password**: Bitwarden is only as secure as your master password
3. **Enable 2FA**: Add two-factor authentication to your Bitwarden account
4. **Use machine accounts for CI/CD**: Don't use personal passwords in GitHub Actions
5. **Rotate secrets regularly**: Update secrets periodically
6. **Audit access**: Review Bitwarden event logs for suspicious activity
7. **Limit permissions**: Only grant access to required secrets

## Alternative: Bitwarden Secrets Manager

For enterprise deployments, consider [Bitwarden Secrets Manager](https://bitwarden.com/products/secrets-manager/):

- Designed specifically for developer secrets
- Machine-to-machine authentication
- Fine-grained access controls
- Integration with CI/CD pipelines
- Usage tracking and audit logs

## Resources

- [Bitwarden CLI Documentation](https://bitwarden.com/help/cli/)
- [Bitwarden API Documentation](https://bitwarden.com/help/api/)
- [Supabase Self-Hosting Guide](https://supabase.com/docs/guides/self-hosting/docker)
- [Generating Strong Passwords](https://bitwarden.com/password-generator/)

## Support

If you encounter issues:

1. Check this documentation
2. Search existing GitHub issues
3. Create a new issue with:
   - Script output (redact any sensitive information)
   - Bitwarden CLI version: `bw --version`
   - Python version: `python --version`
   - Operating system

## Contributing

Improvements to the Bitwarden integration are welcome! Please submit pull requests with:
- Description of changes
- Testing performed
- Any new dependencies
