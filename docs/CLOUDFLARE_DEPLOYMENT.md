# Cloudflare Deployment Guide

This guide walks you through deploying the Local AI Package to Cloudflare using Terraform and the opendiscourse.net domain.

## Prerequisites

1. **Cloudflare Account**: Ensure you have a Cloudflare account with the opendiscourse.net domain added
2. **Terraform**: Install Terraform >= 1.5
3. **API Tokens**: Generate a Cloudflare API token with appropriate permissions

## Quick Start

1. **Configure Terraform Variables**:
   ```bash
   cd terraform/cloudflare
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your actual values
   ```

2. **Deploy Infrastructure**:
   ```bash
   ./deploy.sh deploy
   ```

3. **Update DNS Records**: Point your server IP to the created DNS records

## Detailed Setup

### 1. Cloudflare API Token

Create an API token at [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens) with:

- **Permissions**:
  - Zone:Read, Zone:Edit
  - Account:Read
  - Cloudflare Workers:Edit (if using Workers)
  - DNS:Edit

- **Zone Resources**:
  - Include: `opendiscourse.net`

### 2. Configure Variables

Edit `terraform/cloudflare/terraform.tfvars`:

```hcl
# Required
cloudflare_api_token = "your-actual-api-token"
cloudflare_account_id = "your-account-id"

# Optional (defaults provided)
domain_name = "opendiscourse.net"
environment = "prod"
enable_analytics = true
enable_bot_protection = true
```

### 3. Deploy Infrastructure

```bash
cd terraform/cloudflare
./deploy.sh deploy
```

This will:
- Create DNS records for all services
- Set up R2 buckets for storage
- Configure security rules
- Enable analytics (if enabled)

### 4. Update Server Configuration

After deployment, update your server's IP address in the DNS records:

```bash
# Get the deployment outputs
terraform output
```

Then update the placeholder IP (192.0.2.1) with your actual server IP.

## Services Deployed

The Terraform configuration creates DNS records for:

- `opendiscourse.net` - Main domain
- `n8n.opendiscourse.net` - N8N Workflow Automation
- `webui.opendiscourse.net` - Open WebUI Chat Interface
- `flowise.opendiscourse.net` - Flowise AI Agent Builder
- `supabase.opendiscourse.net` - Supabase Database & Auth
- `langfuse.opendiscourse.net` - Langfuse LLM Observability
- `ollama.opendiscourse.net` - Ollama LLM API
- `searxng.opendiscourse.net` - SearXNG Search Engine
- `neo4j.opendiscourse.net` - Neo4j Knowledge Graph
- `agentic.opendiscourse.net` - Agentic Knowledge RAG
- `traefik.opendiscourse.net` - Traefik Load Balancer
- `grafana.opendiscourse.net` - Grafana Monitoring
- `prometheus.opendiscourse.net` - Prometheus Metrics

## R2 Storage Buckets

Three R2 buckets are created:

1. **Storage Bucket**: `local-ai-{environment}-storage` - General file storage
2. **Model Cache**: `local-ai-{environment}-models` - LLM model caching
3. **Backup Bucket**: `local-ai-{environment}-backup` - System backups

## Security Features

- SSL/TLS certificates (automatic via Cloudflare)
- Bot protection and rate limiting
- Firewall rules for API endpoints
- DDoS protection
- Geographic blocking (configurable)

## Monitoring

- Web Analytics (if enabled)
- Performance insights
- Security event logging
- Custom dashboards

## Troubleshooting

### Common Issues

1. **API Token Errors**: Ensure your token has all required permissions
2. **Zone Not Found**: Verify the domain is added to your Cloudflare account
3. **Deployment Failures**: Check Terraform logs for specific errors

### Validation Commands

```bash
# Validate Terraform configuration
terraform validate

# Check DNS propagation
dig opendiscourse.net
dig n8n.opendiscourse.net

# Test SSL certificates
curl -I https://opendiscourse.net
```

### Cleanup

To destroy all infrastructure:

```bash
./deploy.sh destroy
```

**⚠️ Warning**: This will permanently delete all Cloudflare resources!

## Next Steps

After successful deployment:

1. Configure your server to use the new domain names
2. Update SSL certificates to use Cloudflare origin certificates
3. Configure your applications to use the R2 buckets
4. Set up monitoring and alerting
5. Test all service endpoints

## Advanced Configuration

### Custom Domains

To use a different domain, update the `domain_name` variable in `terraform.tfvars`.

### Environment Separation

Deploy multiple environments by changing the `environment` variable:

```hcl
environment = "staging"  # Creates staging.opendiscourse.net
```

### Security Hardening

Enable additional security features:

```hcl
enable_bot_protection = true
enable_waf = true
security_level = "high"
```

## Support

For issues related to:
- Cloudflare configuration: Check Cloudflare documentation
- Terraform errors: Review Terraform logs
- DNS issues: Use DNS propagation tools
- Application connectivity: Verify firewall and security group settings