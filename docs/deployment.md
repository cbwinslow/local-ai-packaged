# Deployment Procedures

This guide covers deploying the Local AI Package for development, production, and cloud environments. The stack uses Docker Compose for orchestration, with scripts for automated, idempotent setup. Deployment includes core services (n8n, Ollama, Supabase) and extensions for legislative analysis (queues, schemas).

For quick local setup, see [Quick Start](QUICK_START.md). For service details, see [Services](services.md). For secrets, see [Secrets Setup](secrets-setup.md).

## Table of Contents

1. [Local Development](#local-development)
2. [Production Server](#production-server)
3. [Cloud/VPS Deployment](#cloud-vps-deployment)
4. [Scaling and High Availability](#scaling-and-high-availability)
5. [CI/CD Integration](#ci-cd-integration)
6. [Backup and Recovery](#backup-and-recovery)
7. [Troubleshooting](#troubleshooting)

## Local Development

Single-machine setup for development/testing.

### Prerequisites
- Docker 20.10+, Docker Compose 2+.
- Git, Python 3.10+.
- 16GB+ RAM; GPU optional (drivers for NVIDIA/AMD).
- Bitwarden CLI for secrets (recommended).

### Steps

1. **Clone Repository**:
   ```bash
   git clone -b stable https://github.com/coleam00/local-ai-packaged.git
   cd local-ai-packaged
   ```

2. **Secrets Setup**:
   - Install Bitwarden CLI: `wget -qO- https://downloads.bitwarden.com/cli/Bitwarden_Installer.sh | bash`.
   - Authenticate: `bw login` (2FA), `export BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD)`.
   - Populate: `./scripts/populate-env-from-bitwarden.sh` (pulls from vault).
   - Validate: `./scripts/validate_env.sh`.

3. **Launch**:
   ```bash
   ./scripts/start-all-services.sh  # CPU, private (default)
   # GPU: ./scripts/start-all-services.sh -p gpu-nvidia
   ```

   Script handles: requirements check, image pull, port resolution, layered startup (infrastructure → AI → apps), health checks.

4. **Extensions for Analysis**:
   ```bash
   ./scripts/deploy-legislative-ai.sh  # Adds DB tables, queues, sample data
   ```

5. **Verification**:
   - Status: `docker compose ps` (all Up).
   - Health: `./scripts/health-check.sh`.
   - Access: http://localhost:3000 (dashboard), http://localhost:5678 (n8n).
   - Test: Upload file to `./shared` (triggers ingestion); query in dashboard.

Logs: `./logs/launch_*.log`. Private env binds ports to localhost.

## Production Server

Self-hosted on dedicated server (e.g., Ubuntu 22.04).

### Prerequisites
- Server with Docker/Compose, Git, Python.
- Domain/subdomains (for TLS).
- Firewall: Open 80/443 only.

### Steps

1. **Server Preparation**:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose-plugin git python3-pip ufw
   sudo usermod -aG docker $USER
   sudo ufw enable && sudo ufw allow 80,443/tcp && sudo ufw reload
   ```

2. **Clone and Configure**:
   ```bash
   git clone -b stable https://github.com/coleam00/local-ai-packaged.git
   cd local-ai-packaged
   ./scripts/populate-env-from-bitwarden.sh  # Or Cloudflare for prod
   # Edit .env: Set *_HOSTNAME=sub.yourdomain.com, LETSENCRYPT_EMAIL=your@email.com
   source .env
   ```

3. **Launch**:
   ```bash
   ./scripts/start-all-services.sh -e public  # Prod mode, proxy only
   ./scripts/deploy-legislative-ai.sh
   ```

4. **DNS Configuration**:
   - A records: frontend.yourdomain.com → server IP (repeat for n8n, supabase, etc.).
   - Caddy/Traefik handles TLS (auto-certificates).

5. **Verification**:
   - https://yourdomain.com (frontend).
   - https://n8n.yourdomain.com (n8n).
   - Supabase: https://supabase.yourdomain.com (studio at /studio).
   - Logs: `docker compose logs -f`.

Prod env limits exposure; uses reverse proxy for security.

## Cloud/VPS Deployment

Deploy to cloud provider (DigitalOcean, AWS EC2, etc.).

### Prerequisites
- Cloud instance (Ubuntu 22.04+, 4+ cores, 16GB+ RAM; GPU if needed).
- Static IP.
- Domain with A records for subdomains.

### Steps

1. **Instance Launch**: Choose Ubuntu GPU (NVIDIA) or standard; SSH as non-root user.

2. **Install Dependencies**:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose-plugin git python3-pip ufw
   sudo usermod -aG docker ubuntu
   sudo ufw allow 22/tcp  # SSH
   sudo ufw allow 80,443/tcp
   sudo ufw enable
   ```

3. **Clone and Secrets**:
   Same as production; use secure secret manager (Bitwarden/Cloudflare Vault).

4. **Launch**:
   ```bash
   ./scripts/start-all-services.sh -e public
   ./scripts/deploy-legislative-ai.sh
   ```

5. **Domain Setup**:
   - Point domain A record to instance IP.
   - Subdomains: n8n.yourdomain.com, supabase.yourdomain.com (A to IP).
   - Traefik/Caddy: Set N8N_HOSTNAME=n8n.yourdomain.com, etc., in .env.

6. **Security Hardening**:
   - Disable root SSH; use keys.
   - Update .env: Strong passwords, no localhost.
   - Run as non-root: Add to docker-compose.yml if needed.
   - Monitoring: Enable Grafana alerts.

Verification: Access via domain; check logs.

## Scaling and High Availability

- **Horizontal**: Docker Swarm (`docker swarm init`); scale workers: `docker service scale queue-worker=3`.
- **Kubernetes**: Convert compose to K8s manifests (kompose tool); use StatefulSets for DBs.
- **Load Balancing**: Traefik scales n8n/frontend; add replicas for stateless services.
- **HA**: Use external Postgres (RDS), Redis cluster; multiple nodes with shared volumes (NFS).
- **Workers**: Scale ingestion workers: `python scripts/worker.py --scale 4`.
- **Monitoring**: Grafana for queue depth, service uptime.

For large-scale: Use Kubernetes for orchestration; external DBs for HA.

## CI/CD Pipeline

Outline for GitHub Actions (create .github/workflows/deploy.yml):

1. **Lint/Test**: `pytest`, `npm test`.
2. **Build**: `docker compose build`.
3. **Deploy**: SSH to server, `git pull && docker compose up -d`.
4. **Validate**: Health checks, smoke tests.

Example GitHub Action snippet:
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: ssh user@server "cd /path/to/project && ./scripts/deploy-legislative-ai.sh"
```

Integrate with GitHub Secrets for .env vars.

## Backup and Recovery

- **Volumes**: `docker compose down -v` removes; backup: `tar czf backup.tar.gz volumes/`.
- **DB**: `docker exec postgres pg_dump -U postgres postgres > backup.sql`.
- **n8n**: Export workflows via UI or volume backup.
- **Models**: Backup `./volumes/ollama` (Ollama storage).
- **Recovery**: Restore volumes, `docker compose up -d`.

Automated: Cron job for daily backups to S3 (MinIO).

## Troubleshooting

- **Script Fails**: Check .env (validate_env.sh); logs in `./logs/`.
- **Port Conflicts**: `./scripts/port-conflict-resolver.sh`.
- **Supabase/DB**: `./fix-jwt-problem.sh`; see [Troubleshooting](errors.md).
- **Cloud**: Verify ufw (80/443 open), DNS propagation (dig yourdomain.com).
- **Scaling Issues**: Check resource limits in compose; monitor with Grafana.
- **Rollback**: `git checkout HEAD~1 && docker compose down -v && up -d`.

Common: Ensure .env sourced; GPU drivers for cloud instances.

For advanced troubleshooting, see [Troubleshooting](errors.md).

Deployment ensures reliable, secure operation for AI analysis workflows.