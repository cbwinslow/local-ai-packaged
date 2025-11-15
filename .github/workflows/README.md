# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the Local AI Package.

## Available Workflows

### Deploy with Bitwarden Secrets

**File**: `deploy-with-bitwarden.yml`

Automatically deploys the Local AI Package using secrets stored in Bitwarden vault.

**Features:**
- Fetches secrets from Bitwarden vault
- Supports multiple authentication methods (machine account, user password)
- Validates all required secrets
- Deploys services with specified GPU profile
- Configurable for private or public environments

**Setup Required:**

1. Store all required secrets in your Bitwarden vault (see [BITWARDEN_SETUP.md](../../BITWARDEN_SETUP.md))

2. Add Bitwarden credentials to GitHub repository secrets:
   - Go to: Settings → Secrets and variables → Actions
   - Add either:
     - **Option A (Recommended)**: Machine Account
       - `BW_CLIENTID` - Your Bitwarden machine account client ID
       - `BW_CLIENTSECRET` - Your Bitwarden machine account client secret
     - **Option B**: User Account
       - `BW_PASSWORD` - Your Bitwarden master password (less secure)

3. Run the workflow:
   - Go to Actions tab
   - Select "Deploy with Bitwarden Secrets"
   - Click "Run workflow"
   - Choose your options:
     - **Profile**: cpu, gpu-nvidia, gpu-amd, or none
     - **Environment**: private (default) or public

**Environment Options:**
- **private**: Safe internal network - opens all service ports
- **public**: Public deployment - only ports 80 and 443 are accessible

**When to Use:**
- Automated deployments
- CI/CD pipelines
- Team deployments with shared secrets
- Production deployments

## Secret Naming in Bitwarden

The workflow searches for secrets using these naming patterns (in order):
1. Exact name: `N8N_ENCRYPTION_KEY`
2. User account: `user.account.N8N_ENCRYPTION_KEY`
3. User secret: `user.secret.N8N_ENCRYPTION_KEY`
4. Machine account: `machine.account.N8N_ENCRYPTION_KEY`

## Required GitHub Secrets

| Secret Name | Description | Required For |
|-------------|-------------|--------------|
| `BW_CLIENTID` | Bitwarden machine account client ID | Machine account auth |
| `BW_CLIENTSECRET` | Bitwarden machine account client secret | Machine account auth |
| `BW_PASSWORD` | Bitwarden master password | User account auth |

**Note**: You only need ONE of the authentication methods:
- Machine account (BW_CLIENTID + BW_CLIENTSECRET) - Recommended for CI/CD
- User account (BW_PASSWORD) - Simpler but less secure

## Adding Your Own Workflows

When creating custom workflows:

1. Create a new `.yml` file in this directory
2. Follow GitHub Actions syntax: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions
3. Test thoroughly before deploying to production
4. Document the workflow purpose and setup in this README

## Security Best Practices

1. **Never commit secrets** to workflow files
2. **Use environment-specific secrets** for different deployments
3. **Rotate secrets regularly** in Bitwarden vault
4. **Enable branch protection** to prevent unauthorized workflow changes
5. **Review workflow logs** for any exposed secrets
6. **Use machine accounts** for CI/CD (not personal passwords)
7. **Limit workflow permissions** to minimum required

## Troubleshooting

### Workflow fails with "BW credentials not provided"
- Check that you've added `BW_CLIENTID` + `BW_CLIENTSECRET` OR `BW_PASSWORD` to GitHub secrets

### Workflow fails with "Secret not found"
- Verify the secret exists in your Bitwarden vault
- Check the secret name matches exactly (case-sensitive)
- Try using alternative naming patterns (see Secret Naming above)

### Workflow fails with "Invalid session"
- Machine account credentials may be expired - regenerate in Bitwarden
- For user password auth, verify the password is correct

### Services fail to start
- Check the workflow logs for specific error messages
- Verify all required secrets were fetched successfully
- Ensure Docker is properly configured on the runner

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Bitwarden CLI Documentation](https://bitwarden.com/help/cli/)
- [Local AI Package Setup Guide](../../BITWARDEN_SETUP.md)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
