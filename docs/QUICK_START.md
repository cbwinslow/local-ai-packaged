# 🚀 Quick Start Guide - Local AI Package

Get the Local AI Package running in minutes. This guide covers cloning, secrets setup, launch, and first use for legislative analysis.

## Prerequisites

- **System**: Linux/macOS (WSL2 for Windows); 16GB+ RAM, 50GB+ SSD space.
- **Software**: Docker 20.10+, Docker Compose 2+, Git, Python 3.10+.
- **Optional**: NVIDIA/AMD GPU (for acceleration); Bitwarden CLI (for secrets).
- **API Keys**: Congress.gov (free registration); optional: OpenAI, SERPAPI.

Install Bitwarden CLI (recommended for secrets):
```bash
wget -qO- https://downloads.bitwarden.com/cli/Bitwarden_Installer.sh | bash
```

Verify Docker:
```bash
docker --version && docker compose version
```

## Step 1: Clone Repository

```bash
git clone -b stable https://github.com/coleam00/local-ai-packaged.git
cd local-ai-packaged
```

## Step 2: Secrets Management

Use Bitwarden for secure, repeatable secrets (no regeneration needed).

1. Authenticate Bitwarden:
   ```bash
   bw login  # Enter email/2FA
   export BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD)
   ```

2. Migrate/Store Secrets (one-time if new):
   ```bash
   ./scripts/migrate-secrets-to-bitwarden.sh  # Stores .env values in vault
   ```

3. Populate `.env`:
   ```bash
   ./scripts/populate-env-from-bitwarden.sh
   source .env
   ```

4. Validate:
   ```bash
   ./scripts/validate_env.sh
   ```

For production, use Cloudflare Secrets (Wrangler CLI). See [Secrets Setup](secrets-setup.md).

**Critical Vars**: POSTGRES_PASSWORD, JWT_SECRET, ANON_KEY, NEO4J_AUTH (all 32+ hex chars).

## Step 3: Launch Services

Use the idempotent launch script for safe, multi-run startup.

### Basic Launch (CPU, Local Dev)
```bash
./scripts/start-all-services.sh
```

### GPU Launch
```bash
./scripts/start-all-services.sh -p gpu-nvidia  # Or gpu-amd
```

### Production Launch
```bash
./scripts/start-all-services.sh -e public  # Exposes only 80/443
```

### Specific Services
```bash
./scripts/start-all-services.sh -s "n8n,frontend,postgres"
```

The script:
- Checks requirements/ports.
- Pulls images.
- Starts infrastructure (Postgres, Neo4j, Qdrant).
- Launches Supabase, AI services (Ollama, n8n), apps (frontend).
- Runs health checks.
- Sets up monitoring (Grafana: admin/admin).

Wait ~2-5 min for init (Ollama pulls models). Logs: `./logs/launch_*.log`.

For legislative features:
```bash
./scripts/deploy-legislative-ai.sh  # Adds DB schema, queues, sample workflows
```

## Step 4: Verify Setup

Check status:
```bash
docker compose ps  # All "Up"
./scripts/health-check.sh  # Services healthy
```

Access points (private env; public via domain):
- **Dashboard**: http://localhost:3000 (Next.js frontend).
- **n8n**: http://localhost:5678 (setup local account; import workflows from `./n8n/backup`).
- **Supabase Studio**: http://localhost:8005 (DASHBOARD_PASSWORD from .env).
- **Open WebUI**: http://localhost:3001 (chat with Ollama; add n8n_pipe function).
- **Flowise**: http://localhost:3002 (AI agents).
- **Grafana**: http://localhost:3003 (monitoring; admin/admin).
- **Neo4j Browser**: http://localhost:7474 (NEO4J_AUTH from .env).
- **Qdrant Dashboard**: http://localhost:6333.

Test ingestion:
1. Add file to `./shared` (triggers n8n RAG workflow).
2. Or curl n8n webhook: `curl -X POST http://localhost:5678/webhook/test -d '{"query": "HR1 summary"}'`.

Verify DB: `docker exec -it postgres psql -U postgres -d postgres -c "SELECT * FROM legislative.bills LIMIT 1;"`.

## Step 5: First Use - Analyze Legislation

1. **Ingest Data**: In n8n (5678), activate `V3_Local_Agentic_RAG_AI_Agent.json`; trigger Congress ingestion.
2. **Query**: Dashboard search: "Bipartisan votes on healthcare bills."
3. **Graph Viz**: Neo4j query: `MATCH (p:Politician)-[:SPONSORED]->(b:Bill) RETURN p, b LIMIT 10`.
4. **Monitor**: Grafana for metrics; Langfuse (3004) for traces.

See [Ingestion Guide](INGESTION_GUIDE.md) for sources; [Workflows](workflows.md) for agents.

## Troubleshooting

- **Services Fail**: `docker compose logs -f <service>`; check ports (`lsof -i :5432`).
- **Supabase Errors**: Regenerate JWT: `./fix-jwt-problem.sh`; see [errors.md](errors.md).
- **GPU Issues**: Fallback to CPU; verify drivers.
- **Secrets**: Re-run populate script; validate no placeholders.
- **Ports**: `./scripts/port-conflict-resolver.sh`.

Upgrades: `git pull && docker compose pull && ./scripts/start-all-services.sh --force-recreate`.

## Next Steps

- Customize workflows in n8n.
- Add API keys (Congress.gov) in dashboard.
- Explore [Comprehensive Docs](COMPREHENSIVE-REPOSITORY-DOCUMENTATION.md).
- Scale: Add workers (`python scripts/worker.py`).

Ready for AI-powered legislative analysis! 🚀