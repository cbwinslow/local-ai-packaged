# Services, Docker Compose, and Launch Scripts

This document details the Local AI Package's services, Docker Compose configuration, and launch procedures. The stack supports AI workflows, government data ingestion, RAG queries, knowledge graphs, and monitoring for legislative analysis.

For architecture diagrams, ERD, and full file listings, see [Comprehensive Repository Documentation](COMPREHENSIVE-REPOSITORY-DOCUMENTATION.md).

## Docker Compose Overview

Configuration is managed in [`docker-compose.yml`](docker-compose.yml), with includes for extensions and Supabase. Use `docker compose config` to validate.

### Networks
Services communicate via service names (e.g., `n8n` → `postgres:5432`).

- **localai** (bridge): Custom internal network for AI services.
- **supabase** (bridge): Supabase stack (DB, auth, API).
- **default** (localai_default, bridge): Primary network for all other services.

### Volumes (Persistent Storage)
Volumes use bind mounts to host directories (`${PWD}/volumes/<service>`) for data survival across container removals. Create the structure:
```bash
mkdir -p volumes/{postgres,qdrant,ollama,n8n,flowise,open-webui,neo4j,langfuse/{postgres,clickhouse/{data,logs},minio},valkey,agentic,rabbitmq,graylog,localai,opensearch,mongo}
```

Key volumes:
- **postgres_data_persistent**: Supabase/Postgres data/migrations.
- **qdrant_data_persistent**: Vector collections/embeddings.
- **ollama_storage**: Downloaded models (e.g., Qwen2.5.gguf).
- **n8n_storage**: Workflows, credentials, executions.
- **flowise**: Agent configs, flows.
- **open-webui**: User data, chat history.
- **neo4j_data**: Graph nodes/relationships (data/logs/config/plugins).
- **langfuse_postgres_data**: Tracing DB.
- **langfuse_clickhouse_data/logs**: Analytics storage.
- **langfuse_minio_data**: S3-compatible traces/media.
- **valkey-data**: Redis cache/keys.
- **agentic_data**: RAG graph files/shared data.
- **rabbitmq_data**: Message queues (legislative-ingestion, agent-orchestration).
- **graylog_data**: Log storage.
- **localai_data**: Inference models.
- **opensearch_data**: Search indices.
- **mongo_data**: Graylog metadata.

Backup: `tar czf volumes-backup.tar.gz volumes/`; restore with `tar xzf`.

### Profiles
Profiles control hardware usage (set via `--profile` in launch scripts):
- **cpu** (default): CPU-only; suitable for dev/testing.
- **gpu-nvidia**: Reserves 1 NVIDIA GPU; requires drivers/CUDA.
- **gpu-amd**: Exposes AMD ROCm devices (/dev/kfd, /dev/dri); Linux-only.

Example: `docker compose --profile gpu-nvidia up -d ollama`.

### Overrides and Includes
- **docker-compose.override.private.yml**: Dev mode; binds ports to 127.0.0.1 (e.g., n8n:5678, frontend:3000).
- **docker-compose.override.public.yml**: Prod mode; exposes only 80/443 via Traefik/Caddy.
- **Generated Overrides**: Port resolver creates `.override.private.generated.yml` for conflicts.
- **Includes**:
  - `./extensions.yml`: Volumes for monitoring/queues.
  - `./docker-compose.traefik.yml`: Traefik proxy (optional).
  - `./supabase/docker/docker-compose.yml`: Supabase (13 services: db, auth, kong, etc.).

Load full config: `docker compose -f docker-compose.yml -f docker-compose.override.private.yml up -d`.

Security: Cap drops (ALL except NET_BIND_SERVICE); non-root users where possible.

## Services

The stack has ~25 services. Below is a table of key ones (grouped by layer). Full details in docker-compose.yml.

### Infrastructure Layer

| Service | Image | Ports (Private Env) | Key Env Vars | Dependencies | Volumes | Description | Healthcheck |
|---------|-------|---------------------|--------------|--------------|---------|-------------|-------------|
| **postgres** | postgres:16-alpine | 5432 | POSTGRES_PASSWORD, POSTGRES_DB | None | postgres_data_persistent | Relational DB (Supabase core, PGVector extension). | pg_isready |
| **redis** (valkey) | valkey/valkey:8-alpine | 6379 | None | None | valkey-data | Caching/pub-sub for n8n/Langfuse. | redis-cli ping |
| **neo4j** | neo4j:5.23.0 | 7474 (HTTP), 7687 (Bolt) | NEO4J_AUTH | None | neo4j_data | Knowledge graph for entities (bills, politicians). Browser: http://localhost:7474. | wget /browser/ |
| **qdrant** | qdrant/qdrant:v1.10.1 | 6333 (REST), 6334 (gRPC) | None | None | qdrant_data_persistent | Vector DB for RAG embeddings. Dashboard: http://localhost:6333/dashboard. | wget /collections |
| **minio** | minio/minio:latest | 9000 (API), 9001 (Console) | MINIO_ROOT_PASSWORD | None | langfuse_minio_data | S3-compatible storage for traces/media. Console: http://localhost:9001. | mc ready local |
| **clickhouse** | clickhouse/clickhouse-server:24.8 | 8123 (HTTP), 9000 (Native) | CLICKHOUSE_PASSWORD | None | langfuse_clickhouse_data/logs | Analytics for Langfuse. | wget /ping |
| **rabbitmq** | rabbitmq:3-management | 5672 (AMQP), 15672 (UI) | RABBITMQ_DEFAULT_USER/PASS | None | rabbitmq_data | Message queues (ingestion, orchestration). UI: http://localhost:15672. | rabbitmq-diagnostics status |
| **opensearch** | opensearchproject/opensearch:latest | 9200 (HTTP), 9600 (Perf) | DISABLE_SECURITY_PLUGIN=true | None | opensearch_data | Search engine for Graylog. | curl /_cluster/health |
| **mongo** | mongo:7.0 | 27017 | None | None | mongo_data | Metadata for Graylog. | N/A |

### AI & Workflow Layer

| Service | Image | Ports (Private Env) | Key Env Vars | Dependencies | Volumes | Description | Healthcheck |
|---------|-------|---------------------|--------------|--------------|---------|-------------|-------------|
| **ollama-cpu/gpu-nvidia/gpu-amd** | ollama/ollama:0.3.12 (rocm for AMD) | 11434 | OLLAMA_HOST, OLLAMA_CONTEXT_LENGTH=8192 | None | ollama_storage | Local LLM inference (Qwen2.5, Nomic-Embed). Auto-pulls models. | N/A |
| **n8n-import** | n8nio/n8n:latest | None | DB_* (Postgres) | None | ./n8n/backup | Imports workflows/credentials (one-time). | N/A |
| **n8n** | n8nio/n8n:latest | 5678 | N8N_ENCRYPTION_KEY, WEBHOOK_URL, DB_TYPE=postgresdb | n8n-import, postgres | n8n_storage, ./shared | Low-code workflows (RAG agents, ingestion). Access: http://localhost:5678. | wget /healthz |
| **flowise** | flowiseai/flowise:latest | 3001 | FLOWISE_USERNAME/PASSWORD | None | flowise | Visual AI agent builder. Access: http://localhost:3001. | N/A |
| **open-webui** | ghcr.io/open-webui/open-webui:main | 8080 | None | ollama | open-webui | Chat interface for LLMs/agents. Access: http://localhost:8080. | N/A |
| **agentic-rag** | Build from ./agentic-knowledge-rag-graph/Dockerfile | 8000 | NEO4J_URI/AUTH, POSTGRES_URL, QDRANT_URL, OLLAMA_URL | postgres, qdrant, neo4j, ollama | agentic_data, ./shared | RAG API with graph integration. Access: http://localhost:8000. | N/A |
| **localai** | quay.io/go-skynet/local-ai:latest | 8080 | LOCALAI_API_KEY | rabbitmq | localai_data | Alternative local inference (OpenAI-compatible). | curl /health |

### Frontend & Proxy Layer

| Service | Image | Ports (Private Env) | Key Env Vars | Dependencies | Volumes | Description | Healthcheck |
|---------|-------|---------------------|--------------|--------------|---------|-------------|-------------|
| **frontend** | Build from ./frontend/Dockerfile (Next.js) | 3000 | NEXT_PUBLIC_SUPABASE_URL/ANON_KEY, NEXTAUTH_SECRET, DATABASE_URL | postgres | None | Dashboard for search, workflows, metrics. Access: http://localhost:3000. | N/A |
| **searxng** | searxng/searxng:latest | 8080 | SEARXNG_BASE_URL, UWSGI_* | None | ./searxng | Privacy-focused metasearch. Access: http://localhost:8080. | N/A |

### Observability Layer

| Service | Image | Ports (Private Env) | Key Env Vars | Dependencies | Volumes | Description | Healthcheck |
|---------|-------|---------------------|--------------|--------------|---------|-------------|-------------|
| **langfuse-worker** | langfuse/langfuse-worker:3.0.0 | 3030 | DATABASE_URL, CLICKHOUSE_*, S3_* (MinIO) | postgres, minio, redis, clickhouse | None | LLM tracing processor. | N/A |
| **langfuse-web** | langfuse/langfuse:3.0.0 | 3000 | NEXTAUTH_*, LANGFUSE_INIT_* | langfuse-worker deps | None | Tracing UI. Access: http://localhost:3000. | N/A |
| **graylog** | graylog/graylog:5.2 | 9000, 12201/udp | GRAYLOG_PASSWORD_SECRET, ROOT_PASSWORD_SHA2 | mongo, opensearch | graylog_data | Centralized logging. UI: http://localhost:9000. | curl /api/system |
| **prometheus** (extensions.yml) | prom/prometheus:latest | 9090 | None | None | prometheus_data | Metrics collection. Config: prometheus.yml. | wget /-/healthy |
| **grafana** (extensions.yml) | grafana/grafana:latest | 3000 | GF_SECURITY_ADMIN_USER/PASSWORD=admin | prometheus | grafana_data | Dashboards. Access: http://localhost:3000. | wget /api/health |

### Supabase Stack (Included via docker-compose.yml)
13 services (db, auth, kong, rest, realtime, storage, etc.). Ports: 5432 (pooler), 8000 (kong). Env: JWT_SECRET, ANON_KEY, POSTGRES_PASSWORD. Volumes: db/data, storage, functions. Deps: Internal (db first). See Supabase docs for details.

### Traefik/Caddy (Optional Proxy)
- **traefik** (docker-compose.traefik.yml): Dynamic routing, Let's Encrypt. Ports: 80/443, 8080 (dashboard).
- **caddy** (built-in): Static HTTPS proxy. Caddyfile routes subdomains (n8n.yourdomain.com).

Public env uses these for secure exposure.

## Launch Scripts

Scripts in `./scripts/` provide idempotent, automated startup. All source `.env` and handle deps/health.

### Full Stack Launch: start-all-services.sh
Idempotent script for complete setup (infrastructure → AI → apps → monitoring).

Usage:
```bash
./scripts/start-all-services.sh  # CPU, private (default)
./scripts/start-all-services.sh -p gpu-nvidia -e public  # GPU, prod
./scripts/start-all-services.sh -s "n8n,frontend" --skip-health-checks  # Specific, no checks
./scripts/start-all-services.sh --dry-run --verbose  # Preview
```

Steps:
1. Checks requirements (Docker, ports, disk, GPU).
2. Sets up .env/secrets (calls populate-env-from-bitwarden.sh).
3. Resolves ports (port-conflict-resolver.sh).
4. Prepares compose files (base + overrides + extensions).
5. Pulls images.
6. Stops existing (project: localai).
7. Starts layers: Infrastructure (postgres, neo4j), Supabase, AI (ollama, n8n), apps (frontend), monitoring.
8. Health checks (curl/wget on key endpoints).
9. Displays status/access URLs, logs to `./logs/launch_*.log`.

Options: -p (profile), -e (env), -s (services), --force-recreate (down -v), --verbose.

### Individual Launch Scripts (launch_*.sh)
Modular scripts for specific services (up -d + logs tail).

Examples:
- **launch_postgres.sh**: Starts postgres; waits for pg_isready.
  ```bash
  ./scripts/launch_postgres.sh  # Exposes 5432
  ```
- **launch_n8n.sh**: Starts n8n (deps: postgres); imports workflows.
- **launch_ollama.sh**: Starts ollama (profile-specific); pulls models.
- **launch_frontend.sh**: Builds/starts Next.js (deps: postgres).
- **launch_agentic-rag.sh**: Starts RAG API (deps: postgres, qdrant, neo4j).
- **launch_qdrant.sh**: Starts vector DB.
- **launch_neo4j.sh**: Starts graph DB; sets auth.

Usage: `./scripts/launch_<service>.sh [logs]`. Each handles deps, exposes ports, tails logs.

### Deployment Script: deploy-legislative-ai.sh
Extends base stack for analysis (DB schema, queues, monitoring).

Usage:
```bash
./scripts/deploy-legislative-ai.sh  # Adds legislative schema, RabbitMQ queues, sample ingestion
```

Steps:
1. Clones/pulls repo.
2. Populates .env from Bitwarden.
3. Creates extensions.yml (Prometheus, Grafana, Loki, OpenSearch, Graylog, RabbitMQ, LocalAI).
4. Updates Caddyfile/prometheus.yml/overrides for new services.
5. Starts base (start_services.py).
6. Inits DB: Creates `legislative.bills/votes/ai_agents` tables.
7. Sets up queues: legislative-ingestion, agent-orchestration, monitoring-events.
8. Tests: Sample curl to n8n, DB query, RabbitMQ publish, LocalAI model load.
9. Outputs access (Grafana:8010, Graylog:8013, etc.).

For cloud: Run on Ubuntu; opens ufw 80/443; set DNS.

### Other Utilities
- **validate_env.sh**: Checks required vars (e.g., POSTGRES_PASSWORD length).
- **port-conflict-resolver.sh**: Scans/rebinds ports (generates override).
- **health-check.sh**: Runs curl/psql/redis-cli checks.
- **worker.py**: Starts queue worker (processes tasks from RabbitMQ/Postgres).

## Best Practices

- **Launch Order**: Use start-all-services.sh for deps (e.g., n8n after postgres).
- **Scaling**: `docker compose up --scale n8n=3`; add workers for queues.
- **Updates**: `git pull && docker compose pull && ./scripts/start-all-services.sh --force-recreate`.
- **Monitoring**: Grafana dashboards for CPU/RAM; Langfuse for AI traces.
- **Security**: Private env for dev; public with TLS. Rotate secrets via Bitwarden.
- **Troubleshooting**: `docker compose logs -f`; see [errors.md](errors.md).

This setup ensures reliable, observable services for AI legislative tools.