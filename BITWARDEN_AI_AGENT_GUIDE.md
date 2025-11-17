# Using Bitwarden as an AI Agent for Secrets Management

This document explains how to leverage Bitwarden programmatically for AI agent development and secrets management.

## Bitwarden CLI for AI Agent Workflows

### Installation
```bash
npm install -g @bitwarden/cli
# OR download from https://github.com/bitwarden/clients/releases
```

### Authentication Methods

#### 1. Session-Based Authentication (Recommended for Scripts)
```bash
bw login
export BW_SESSION=$(bw unlock --raw)
```

#### 2. API Key Authentication (Recommended for Production)
```bash
export BW_CLIENTID="your-client-id"
export BW_CLIENTSECRET="your-client-secret"
```

#### 3. Direct Login (For Interactive Use)
```bash
bw login --email="your@email.com"
```

### Common AI Agent Use Cases

#### 1. Retrieving Secrets for Applications
```bash
# Get item by name
bw get item "SecretName" --session $BW_SESSION

# Get specific field
bw get item "SecretName" --session $BW_SESSION | jq -r '.login.password'

# Search for items by name pattern
bw list items --search "n8n" --session $BW_SESSION
```

#### 2. Batch Secret Retrieval
```bash
#!/bin/bash
# Example script to pull multiple secrets

SECRET_NAMES=(
    "N8N_ENCRYPTION_KEY"
    "N8N_USER_MANAGEMENT_JWT_SECRET" 
    "POSTGRES_PASSWORD"
    "JWT_SECRET"
    "ANON_KEY"
    "SERVICE_ROLE_KEY"
)

for secret_name in "${SECRET_NAMES[@]}"; do
    value=$(bw get item "$secret_name" --session $BW_SESSION | jq -r '.login.password')
    echo "$secret_name=$value"
done
```

#### 3. Conditional Logic Based on Secret Availability
```bash
# Check if secret exists before proceeding
if bw get item "MY_SECRET" --session $BW_SESSION &> /dev/null; then
    echo "Secret found, continuing..."
    # Proceed with workflow
else
    echo "Secret not found, exiting..."
    exit 1
fi
```

### Integration Patterns for AI Agents

#### Pattern 1: Environment Variable Injection
```bash
# Create .env file dynamically
cat > .env << EOF
$(bw get item "N8N_ENCRYPTION_KEY" --session $BW_SESSION | jq -r '.login.password' | sed 's/^/N8N_ENCRYPTION_KEY=/')
$(bw get item "JWT_SECRET" --session $BW_SESSION | jq -r '.login.password' | sed 's/^/JWT_SECRET=/')
EOF
```

#### Pattern 2: Runtime Secret Injection
```python
import subprocess
import json

def get_secret(secret_name):
    """Retrieve secret from Bitwarden"""
    result = subprocess.run(
        ['bw', 'get', 'item', secret_name, '--session', os.environ['BW_SESSION']],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        item = json.loads(result.stdout)
        return item['login']['password']
    return None

# Use in application
db_password = get_secret("POSTGRES_PASSWORD")
```

#### Pattern 3: Multi-Account Secret Resolution
```bash
# Try multiple naming patterns for secrets
get_secret_with_fallback() {
    local secret_name=$1
    local patterns=(
        "$secret_name"                    # Exact name
        "user.account.$secret_name"       # User account
        "user.secret.$secret_name"        # User secret
        "machine.account.$secret_name"    # Machine account
    )
    
    for pattern in "${patterns[@]}"; do
        if value=$(bw get item "$pattern" --session $BW_SESSION 2>/dev/null | jq -r '.login.password' 2>/dev/null); then
            if [ "$value" != "null" ] && [ -n "$value" ]; then
                echo "$value"
                return 0
            fi
        fi
    done
    
    return 1  # Not found
}

# Usage
db_pass=$(get_secret_with_fallback "POSTGRES_PASSWORD")
```

### Security Considerations

#### 1. Session Management
```bash
# Always clear session when done
trap 'unset BW_SESSION' EXIT

# Or time-limit sessions
export BW_SESSION=$(bw unlock --raw)
sleep 300  # 5 minutes
unset BW_SESSION
```

#### 2. Output Redirection Security
```bash
# Secure output handling
secret_value=$(bw get item "SECRET" --session $BW_SESSION | jq -r '.login.password')
export SECRET_VAR="$secret_value"  # Use environment instead of file
unset secret_value  # Clear from memory
```

#### 3. Audit Trail
```bash
# Log access attempts (without sensitive data)
echo "$(date): Access request for $(whoami) at $(pwd)" >> access.log
```

### Advanced Use Cases

#### 1. Dynamic Environment Setup
```bash
#!/bin/bash
# AI Agent Environment Setup Script

# Define required secrets mapping
declare -A SECRET_MAP
SECRET_MAP["N8N_ENCRYPTION_KEY"]="N8N_ENCRYPTION_KEY"
SECRET_MAP["N8N_JWT_SECRET"]="N8N_USER_MANAGEMENT_JWT_SECRET" 
SECRET_MAP["POSTGRES_PASSWORD"]="POSTGRES_PASSWORD"
SECRET_MAP["JWT_SECRET"]="JWT_SECRET"
# ... add more mappings

# Generate environment file from Bitwarden
echo "# Auto-generated from Bitwarden $(date)" > .env.temp
for env_var in "${!SECRET_MAP[@]}"; do
    secret_value=$(bw get item "${SECRET_MAP[$env_var]}" --session $BW_SESSION | jq -r '.login.password')
    if [ -n "$secret_value" ] && [ "$secret_value" != "null" ]; then
        echo "$env_var=$secret_value" >> .env.temp
    else
        echo "# WARNING: $env_var not found in Bitwarden" >> .env.temp
        echo "$env_var=" >> .env.temp  # Placeholder
    fi
done

mv .env.temp .env
```

#### 2. Secrets Validation and Health Checks
```bash
validate_secrets() {
    local required_secrets=(
        "N8N_ENCRYPTION_KEY"
        "N8N_USER_MANAGEMENT_JWT_SECRET"
        "POSTGRES_PASSWORD"
    )
    
    local missing=()
    for secret in "${required_secrets[@]}"; do
        if ! bw get item "$secret" --session $BW_SESSION &>/dev/null; then
            missing+=("$secret")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo "Missing secrets: ${missing[*]}"
        return 1
    fi
    
    echo "All required secrets are available"
    return 0
}
```

### API-Based Operations (Alternative)

For production environments, you can also use Bitwarden Secrets Manager API:

```bash
# Example API call (requires Secrets Manager subscription)
BW_ACCESS_TOKEN=$(bw sm access-token --quiet)
BW_ORGANIZATION_ID="your-org-id"

curl -X POST \
  -H "Authorization: Bearer $BW_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  https://secrets.bitwarden.com/api/organizations/$BW_ORGANIZATION_ID/secrets/import \
  -d '{"secrets": [{"key": "EXAMPLE_KEY", "value": "example-value", "note": "Example secret"}]}'
```

## Best Practices

1. **Never hardcode credentials** in scripts
2. **Use session-based authentication** for temporary access
3. **Implement fallback patterns** for secret retrieval
4. **Log access attempts** for audit trails
5. **Clear sensitive data** from memory after use
6. **Use specific permission levels** for different use cases
7. **Regularly rotate secrets** that are accessed programmatically