# Self-hosted AI Package for Legislative Analysis

**Self-hosted AI Package** is an open-source, Docker Compose-based template that bootstraps a comprehensive local AI and low-code development environment. It includes Ollama for local LLMs, n8n for workflow automation, Supabase for database/auth/vector storage, and specialized components for government data ingestion and analysis (e.g., Congress.gov API integration, agentic RAG with Neo4j knowledge graphs).

This enhanced version focuses on legislative AI: ingesting bills/votes from 300+ sources, building knowledge graphs, and enabling agentic workflows for policy analysis, while maintaining privacy and offline capabilities.

## 🚀 Key Features

- **AI Model Management**: Local LLMs via Ollama (Qwen2.5, Nomic-Embed) with GPU/CPU profiles.
- **Workflow Automation**: n8n for agentic RAG pipelines; Flowise for visual AI agents.
- **Data Ingestion**: Automated processing from Congress.gov, GovInfo, FEC; supports PDF/XML/CSV.
- **Knowledge Graph**: Neo4j for entity relationships (politicians, bills, votes).
- **Vector Search**: Qdrant/PGVector for semantic RAG queries.
- **Observability**: Langfuse for LLM tracing; Prometheus/Grafana for monitoring.
- **Security**: Bitwarden-integrated secrets; Caddy/Traefik for HTTPS proxy.
- **Analysis Tools**: SQL queries for trends, effectiveness scores; reports on bipartisan cooperation.

**Important**: If upgrading from pre-June 2024, add `POOLER_DB_POOL_SIZE=5` to `.env` for Supabase compatibility.

## 📖 Documentation

- [Quick Start Guide](docs/QUICK_START.md): One-command setup.
- [Comprehensive Repository Overview](docs/COMPREHENSIVE-REPOSITORY-DOCUMENTATION.md): Full architecture, services, diagrams.
- [Ingestion Guide](docs/INGESTION_GUIDE.md): Government data pipelines.
- [Queue System](docs/QUEUE_SYSTEM.md): Task management for workers.
- [Workflows & Agents](docs/workflows.md): n8n/Flowise integration.
- [Secrets Setup](docs/secrets-setup.md): Bitwarden management.
- [Frontend Architecture](docs/FRONTEND_ARCHITECTURE.md): Next.js dashboard.
- [Troubleshooting](docs/errors.md): Common issues.
- [Environment Rules](ENV_VARIABLES_RULES.md): Required vars.

Community: [Local AI Forum](https://thinktank.ottomator.ai/c/local-ai/18); [Kanban Board](https://github.com/users/coleam00/projects/2).

Original inspiration: [n8n Self-Hosted AI Starter Kit](https://github.com/n8n-io/self-hosted-ai-starter-kit).

![n8n Demo](assets/n8n-demo.gif)

## 🛠️ Prerequisites

- **OS**: Linux/macOS (WSL2 for Windows).
- **Hardware**: 16GB+ RAM; NVIDIA/AMD GPU optional.
- **Software**: Docker 20.10+, Docker Compose 2+, Git, Python 3.10+.
- **API Keys**: Congress.gov (free), optional: OpenAI, SERPAPI.

For GPU: Install NVIDIA/AMD drivers; enable Docker GPU support.

## Installation

1. **Clone Repository**:
   ```bash
   git clone -b stable https://github.com/coleam00/local-ai-packaged.git
   cd local-ai-packaged
   ```

2. **Setup Environment Variables**:
   All environment variables are defined in `.env.example`. You must create a `.env` file with the correct values before launching the services.

   - **Using Bitwarden (Recommended)**:
     1. Install the Bitwarden CLI if you haven't already.
     2. Log in to your Bitwarden account (`bw login`).
     3. Run the population script: `./scripts/populate-env-from-bitwarden.sh`.
        - The script will prompt for your master password to unlock the vault.
        - It reads `.env.example`, fetches corresponding secrets (prefixed with `localai_` in your vault), and creates a `.env` file.
        - For secrets not found in Bitwarden (like API keys), it will insert a placeholder. You must edit the `.env` file to add these manually.

   - **Without Bitwarden**:
     1. Run the script with the `--generate-missing` flag: `./scripts/populate-env-from-bitwarden.sh --generate-missing`.
     2. This will create a `.env` file with newly generated internal secrets.
     3. You must manually edit the `.env` file to add your external API keys (e.g., `OPENAI_API_KEY`).

   - **Validation**: After creating the `.env` file, you can optionally validate it by running `./scripts/validate_env.sh`.

   For production, consider fetching secrets from a secure vault like Bitwarden or Cloudflare Secrets.

3. **Launch Services**:
   - Development: `./scripts/start-all-services.sh` (defaults: CPU, private).
   - GPU: `./scripts/start-all-services.sh -p gpu-nvidia`.
   - Production: `./scripts/start-all-services.sh -e public`.
   - Specific services: `./scripts/start-all-services.sh -s "n8n,frontend"`.

   This handles dependencies, port conflicts, health checks, and monitoring setup.

4. **Deploy Legislative AI Extensions** (for analysis features):
   ```bash
   ./scripts/deploy-legislative-ai.sh
   ```
   Initializes DB schema (bills/votes), queues (RabbitMQ), and sample workflows.

5. **Verify**:
   - Dashboard: http://localhost:3000.
   - n8n: http://localhost:5678 (setup local account).
   - Supabase: http://localhost:8000 (anon key from `.env`).
   - Ollama: `curl http://localhost:11434/api/tags` (models pulled automatically).

   Run tests: `pytest` (backend), `npm test` (frontend).

## Usage

### Quick Start Workflow

1. **Ingest Data**: Upload files to `/shared` or trigger n8n ingestion (e.g., Congress bills via API).
2. **Build Graph**: Agentic RAG chunks/embeds → Qdrant/Neo4j.
3. **Query**: Use dashboard search or n8n agents for analysis (e.g., "bipartisan votes on HR1").
4. **Monitor**: Grafana (http://localhost:3003, admin/admin) for metrics; Langfuse for traces.

### Example: Analyze a Bill

- Trigger: n8n workflow `V3_Local_Agentic_RAG_AI_Agent.json`.
- Query: "Summarize HR1 and its sponsors' effectiveness."
- Output: RAG response with graph viz (Neo4j entities).

See [Ingestion Guide](docs/INGESTION_GUIDE.md) for 300+ sources; [Workflows](docs/workflows.md) for custom agents.

## Deployment

- **Local**: Use `start-all-services.sh` (private env exposes ports).
- **Cloud**: `deploy-legislative-ai.sh` on Ubuntu (opens 80/443 via ufw); set DNS for subdomains (e.g., n8n.yourdomain.com).
- **Scaling**: Docker Swarm/K8s; horizontal workers via queue system.
- **CI/CD**: GitHub Actions (lint/test/deploy); Terraform for IaC (cloud resources).

Public env: Limits exposure to 80/443; auto-TLS via Caddy/Traefik.

## Upgrading

```bash
git pull
docker compose pull
./scripts/start-all-services.sh --force-recreate
```

Migrate DB: `./scripts/setup_database_indexes.py`.

## Troubleshooting

- **Port Conflicts**: `./scripts/port-conflict-resolver.sh`.
- **Supabase Issues**: Check [errors.md](docs/errors.md); regenerate JWT: `./fix-jwt-problem.sh`.
- **GPU**: Verify `nvidia-smi`; fallback to CPU profile.
- **Logs**: `docker compose logs -f`; Grafana for metrics.
- **Health**: `./scripts/health-check.sh`.

Common: No "@" in passwords; expose Docker daemon for WSL.

## Tips

- **Files**: Shared volume `/data/shared` for n8n triggers.
- **Models**: Ollama auto-pulls Qwen2.5; add via `ollama pull <model>`.
- **Security**: Rotate secrets annually; enable 2FA on Bitwarden.
- **Performance**: Index DB (`./scripts/setup_database_indexes.py`); monitor RAM (32GB+ recommended).

## 🎥 Resources

- [Video Guide](https://youtu.be/pOsO40HSbOo).
- [n8n AI Templates](https://n8n.io/workflows/?categories=AI).
- [Supabase Self-Hosting](https://supabase.com/docs/guides/self-hosting).

## 📜 License

Apache 2.0. See [LICENSE](LICENSE). Third-party: Supabase (Apache), n8n (Fair Code), Ollama (MIT).

Curated by coleam00. Contributions welcome!
