# Secure Secrets Management Setup Plan

## Overview
To securely manage API keys for project tools (Jira, Bitbucket, Linear, GitHub, Supabase, n8n, etc.), we recommend using chezmoi for local, encrypted secrets management. This avoids direct exposure of sensitive data in version control. Alternatives like browser access to Bitwarden or Cloudflare Secrets are considered but require manual intervention.

## Why Chezmoi?
- Encrypts secrets using age or GPG.
- Templates for environment-specific values (e.g., .env files).
- Integrates with dotfiles for bash_secrets.
- No need to share keys with AI tools; manage locally.

## Prerequisites
- Git installed (already present).
- Age keypair or GPG for encryption (generate if needed).

## Step-by-Step Setup Plan

### 1. Install Chezmoi
Use package manager (Ubuntu/Debian assumed from Linux OS):
```
sudo apt update && sudo apt install chezmoi
```
Or via curl:
```
sh -c "curl -sfL https://git.io/chezmoi | sh"
```

### 2. Initialize Chezmoi Repository
```
chezmoi init --apply
mkdir -p ~/.local/share/chezmoi
```

### 3. Generate Encryption Key (if not using GPG)
```
age-keygen -o ~/.config/age/key.txt
```
Secure the public key for sharing encrypted files if needed.

### 4. Create bash_secrets Template
Create `~/.local/share/chezmoi/bash_secrets.tmpl` with placeholders:
```
#!/bin/bash
# Encrypted secrets loader

# Project Tracking Tools
export JIRA_API_URL="https://your-org.atlassian.net"
export JIRA_API_TOKEN="{{ .jira_token }}"
export BITBUCKET_USERNAME="{{ .bitbucket_user }}"
export BITBUCKET_APP_PASSWORD="{{ .bitbucket_password }}"
export LINEAR_API_KEY="{{ .linear_key }}"
export GITHUB_TOKEN="{{ .github_pat }}"

# Infrastructure
export SUPABASE_URL="{{ .supabase_url }}"
export SUPABASE_ANON_KEY="{{ .supabase_anon }}"
export N8N_API_URL="{{ .n8n_url }}"
export N8N_BASIC_AUTH="{{ .n8n_auth }}"

# Load into environment
source <(chezmoi cat bash_secrets.tmpl | chezmoi decrypt --template-to bash_secrets.sh)
```

### 5. Add Secrets to Chezmoi
Edit the template with actual values (encrypted):
```
chezmoi add bash_secrets.tmpl
chezmoi edit bash_secrets.tmpl
```
Fill placeholders, then:
```
chezmoi apply
```

### 6. Integrate with Existing Scripts
Update scripts like `deploy-legislative-ai.sh` to source `bash_secrets.sh`:
```bash
# At top of script
[ -f ~/bash_secrets.sh ] && source ~/bash_secrets.sh
```

### 7. Version Control (Securely)
- Add chezmoi repo to .gitignore for encrypted files.
- Commit templates (without secrets) to Git.
- For team: Share public age key to encrypt shared secrets.

## Alternative: Browser Access to Secrets Stores
If chezmoi setup is deferred:
1. Use browser_action to navigate to Bitwarden/Cloudflare login (user provides credentials manually).
2. Screenshot/export keys (manual copy-paste recommended for security).
3. Store temporarily in .env (gitignore'd) for immediate use.

## Security Notes
- Never commit unencrypted keys.
- Use 2FA for all services.
- Rotate keys periodically.
- For AI-assisted updates, use keys only in local scripts, not direct tool calls.

## Next Steps
- Confirm OS/package manager for install command.
- Provide placeholders or initial values for template.
- Switch to code mode for script updates after setup.