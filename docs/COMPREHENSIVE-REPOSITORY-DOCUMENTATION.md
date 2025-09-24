# Comprehensive Repository Documentation

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Processes and Procedures](#processes-and-procedures)
  - [Installation and Setup](#installation-and-setup)
  - [Service Deployment](#service-deployment)
  - [RAG AI Agent Workflow](#rag-ai-agent-workflow)
  - [Configuration Management](#configuration-management)
  - [Port Management](#port-management)
- [Services and Components](#services-and-components)
  - [Core Services](#core-services)
  - [Supabase Stack](#supabase-stack)
  - [AI and Workflow Services](#ai-and-workflow-services)
  - [Observability and Utilities](#observability-and-utilities)
- [Docker Configuration](#docker-configuration)
  - [Docker Compose Files](#docker-compose-files)
  - [Volumes and Networks](#volumes-and-networks)
  - [Container Orchestration](#container-orchestration)
- [Diagrams](#diagrams)
  - [High-Level Architecture](#high-level-architecture)
  - [Class Definitions](#class-definitions)
  - [RAG Workflow Sequence](#rag-workflow-sequence)
  - [Docker Network Topology](#docker-network-topology)
  - [Service Dependencies](#service-dependencies)
  - [SQL Tables and ERD](#sql-tables-and-erd)
- [Additional Coverage](#additional-coverage)
  - [Ancillary Files](#ancillary-files)
  - [Security Considerations](#security-considerations)
  - [Potential Improvements](#potential-improvements)
- [Changelog](#changelog)
- [Indexes](#indexes)

## Overview

The "local-ai-packaged" repository is a self-hosted AI development environment for building local Retrieval-Augmented Generation (RAG) AI agents. It provides a complete stack for low-code AI workflow automation using n8n, integrated with Supabase for database and authentication, Ollama for local LLMs, and supporting services like vector databases (Qdrant, PGVector), graph databases (Neo4j), search engines (SearxNG), and observability tools (Langfuse). The setup emphasizes privacy, offline operation, and ease of use for developers building AI agents without cloud dependencies.

Key features:
- **Local RAG AI Agents**: Agentic workflows that handle document ingestion, vector storage, and intelligent querying across text and tabular data.
- **Multi-Service Orchestration**: Docker Compose-managed stack with GPU/CPU profiles and public/private environment support.
- **Extensible Tools**: n8n workflows for Google Drive integration, Postgres querying, and custom AI tools.
- **Configuration Automation**: Python scripts for service, port, and config management.

The repository is curated from the original n8n self-hosted AI starter kit with enhancements including Supabase, Open WebUI, Flowise, Neo4j, Langfuse, and Caddy reverse proxy. It supports development of AI agents for tasks like document analysis, knowledge base querying, and workflow automation.

**Target Users**: Developers, AI researchers, and teams building privacy-focused AI applications.

**License**: Apache License 2.0 (see [`LICENSE`](LICENSE)).

**Third-Party Licenses and Copyrights**:
- **Supabase**: PostgreSQL-based, Apache 2.0. Copyright: Supabase Inc. (2020-present). Services: supabase.com (self-hosted via Docker).
- **n8n**: Workflow automation, Apache 2.0 with Commons Clause. Copyright: n8n GmbH (2019-present). Services: n8n.io.
- **Ollama**: Local LLM runner, MIT License. Copyright: Ollama (2023-present). Services: ollama.ai.
- **Caddy**: Web server/proxy, Apache 2.0. Copyright: Caddy Authors (2015-present). Services: caddyserver.com.
- **Qdrant**: Vector DB, Apache 2.0. Copyright: Qdrant (2021-present). Services: qdrant.tech.
- **Neo4j**: Graph DB, GPL v3 (Community), Commercial license. Copyright: Neo4j Inc. (2007-present). Services: neo4j.com.
- **Langfuse**: LLM observability, MIT. Copyright: Langfuse (2023-present). Services: langfuse.com.
- **SearxNG**: Metasearch, AGPL v3. Copyright: SearxNG contributors (2015-present). Services: searxng.org.
- **Congress.gov API**: U.S. Library of Congress, Public Domain (U.S. Government). Copyright: None (government work). Services: congress.gov.
- **GovInfo API**: U.S. Government Publishing Office, Public Domain. Copyright: None. Services: govinfo.gov.
- **OpenAI API** (optional): Proprietary commercial license. Copyright: OpenAI (2015-present). Services: openai.com.
- **Other Docker images**: Various OSS licenses (Alpine Linux: GPL v2, etc.). All containers use official images with their respective licenses.

**Services Copyright Summary**:
| Service | Copyright Holder | License | Key Files |
|---------|------------------|---------|-----------|
| Supabase | Supabase Inc. | Apache 2.0 | supabase/docker/* |
| n8n | n8n GmbH | Apache 2.0+Commons | n8n/* |
| Ollama | Ollama | MIT | (container only) |
| Congress.gov | U.S. Library of Congress | Public Domain | services/api_clients/congress_gov.py |

Full licenses in respective repositories; this project aggregates under Apache 2.0 compatibility.

## Repository Structure

The project is organized into directories for core configurations, services, and utilities:

- **Root Level**:
  - [`docker-compose.yml`](docker-compose.yml): Main orchestration file including extensions and Supabase.
  - [`start_services.py`](start_services.py): Python script to orchestrate Supabase and AI services startup.
  - [`service-manager.py`](service-manager.py): Manages Docker service status, health, and operations.
  - [`config-manager.py`](config-manager.py): Evaluates and sets up configuration storage.
  - [`port-manager.py`](port-manager.py): Detects and resolves port conflicts.
  - [`.env.example`](.env.example): Template for environment variables (secrets, ports, hostnames).
  - [`README.md`](README.md): Project overview, installation, and troubleshooting.
  - [`Caddyfile`](Caddyfile): Reverse proxy configuration for services.
  - Override files: [`docker-compose.override.private.yml`](docker-compose.override.private.yml), [`docker-compose.override.public.yml`](docker-compose.override.public.yml).

- **supabase/**: Submodule for self-hosted Supabase (Postgres-based backend).
  - [`docker/docker-compose.yml`](supabase/docker/docker-compose.yml): Supabase-specific services (kong, auth, db, etc.).
  - Init scripts: [`volumes/db/*.sql`](supabase/docker/volumes/db/*.sql) for database setup.
  - Functions: [`volumes/functions/*.ts`](supabase/docker/volumes/functions/*.ts).

- **n8n/**: Workflow automation.
  - [`backup/workflows/*.json`](n8n/backup/workflows/*.json): RAG AI agent versions (V1-V3).
  - [`n8n-tool-workflows/*.json`](n8n-tool-workflows/*.json): Utility workflows (Google Doc creation, Postgres table listing).

- **flowise/**: Low-code AI builder.
  - Custom tools: [`*.json`](flowise/*.json) for Slack integration, Postgres queries, Google Docs.

- **reports/**: Python utilities.
  - [`docker_status.py`](reports/docker_status.py): Docker monitoring.
  - [`yaml_validate.py`](reports/yaml_validate.py): YAML validation.

- **searxng/**: Privacy-focused search.
  - [`settings-base.yml`](searxng/settings-base.yml): Search engine configuration.

- **assets/**: Media (e.g., [`n8n-demo.gif`](assets/n8n-demo.gif)).

- **Other**: Shell scripts (e.g., [`fix-supabase-env.sh`](fix-supabase-env.sh) for secret generation), monitoring ([`prometheus.yml`](prometheus.yml)).

Total files: ~100, primarily YAML/JSON configs, Python scripts, and n8n workflows. No CI/CD pipelines or Terraform IaC; Docker Compose serves as primary infrastructure definition.

## Technology Stack

- **Orchestration**: Docker Compose (v2+), Python 3.x (management scripts).
- **Backend/Database**: Supabase (Postgres 15+, pgvector extension), Qdrant (vector DB), Neo4j (graph DB), Valkey/Redis (caching), MinIO (S3-compatible storage), ClickHouse (analytics).
- **AI/ML**: Ollama (local LLMs: Qwen2.5, Nomic-Embed), Langfuse (LLM observability).
- **Workflow/Automation**: n8n (low-code), Flowise (AI agents).
- **Frontend/UI**: Open WebUI (chat interface), Supabase Studio (dashboard), Grafana/Prometheus (monitoring, partial).
- **Networking/Proxy**: Caddy (HTTPS reverse proxy), Kong (API gateway in Supabase).
- **Search**: SearxNG (metasearch engine).
- **Utilities**: Python (psutil, yaml, requests), shell scripts (secret generation).
- **Integrations**: Google Drive API, Slack (via n8n), SMTP (email auth).

Dependencies managed via Docker images; no package managers like npm/pip in root (Supabase uses pnpm).

## Architecture

The system follows a layered architecture:

1. **Presentation Layer**: Web UIs (n8n:5678, Open WebUI:3000, Flowise:3001, Supabase Studio via proxy).
2. **Application Layer**: n8n/Flowise for workflows, Ollama for inference, Langfuse for tracing.
3. **Data Layer**: Supabase (auth/API/DB/storage), Qdrant/Neo4j for vectors/graphs, PGVector for RAG.
4. **Infrastructure Layer**: Docker containers, Caddy proxy, volumes for persistence.

Communication: Internal Docker network (default bridge); HTTP/gRPC between services; Postgres connections for DB ops. External access via Caddy on ports 80/443 (public) or localhost ports (private).

Data Flow: Documents → File Trigger → Ingestion (chunk/embed/store in PGVector) → Agent Query (RAG/SQL tools) → LLM Response.

## Processes and Procedures

### Installation and Setup

**Prerequisites**: Docker/Docker Desktop (v20+), Python 3.8+, Git, Bitwarden CLI (for secrets).

**Step-by-Step**:
1. Clone: `git clone -b stable https://github.com/coleam00/local-ai-packaged.git && cd local-ai-packaged`.
2. Install Bitwarden CLI: `wget -qO- https://downloads.bitwarden.com/cli/Bitwarden_Installer.sh | bash` (or `sudo snap install bw`).
3. Authenticate Bitwarden: `bw login` (use 2FA), then `export BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD)`.
4. Migrate existing secrets (one-time): `./scripts/migrate-secrets-to-bitwarden.sh` (stores .env values in Bitwarden vault).
5. Populate .env: `./scripts/populate-env-from-bitwarden.sh` (pulls from Bitwarden; requires BW_PASSWORD env var).
6. For production: Set hostnames in .env (e.g., `N8N_HOSTNAME=n8n.example.com`), LETSENCRYPT_EMAIL; Use Cloudflare Secrets for env vars.
7. Deploy: `./scripts/deploy-legislative-ai.sh` (handles Supabase init, extensions, DB schema, queue setup).
   - Alternative: `python tools/start_services.py --profile cpu --environment private` (manual start).
8. Verify: `docker compose ps` (all healthy), `curl http://localhost:8000/health` (Supabase), access n8n at http://localhost:9003.

**Database Deployment**:
- Supabase auto-initializes via docker/volumes/db/init/*.sql (JWT roles, pooler, realtime).
- Custom schema: Run `./scripts/deploy-legislative-ai.sh` (creates legislative.bills, votes, ai_agents; RabbitMQ queues).
- ERD: See [SQL Tables/ERD](#sql-tables-and-erd) for full schema.
- Migrations: db/migrations/*.sql (apply via `psql` or Supabase Studio).

**Secrets Management**:
- All secrets in Bitwarden (see [Secrets Setup](docs/secrets-setup.md)): Folders like "Local AI Package/Supabase".
- Repeatable: `./scripts/populate-env-from-bitwarden.sh && source .env` (no regeneration).
- Cloudflare: For prod, use `wrangler secret put SUPABASE_JWT_SECRET` in wrangler.toml.

**Inputs/Outputs**: .env (from Bitwarden); Outputs: Running stack, legislative schema, queues (legislative-ingestion, agent-orchestration).
**Error Handling**: Deploy script validates secrets, handles port conflicts (port-manager.py); Logs: `docker compose logs -f`; Fix JWT: `./fix-jwt-problem.sh`.
**Best Practices**: chmod 600 .env; Backup vault; Rotate annually; Use public env only with TLS; Monitor via Grafana (http://localhost:8010, admin/admin).

### Service Deployment

**Workflow**: Managed by [`start_services.py`](start_services.py).
1. Clone/update Supabase submodule.
2. Copy `.env` to Supabase docker dir.
3. Stop existing containers (project: localai).
4. Start Supabase (`docker compose -f supabase/docker/docker-compose.yml up -d`).
5. Wait 10s for init.
6. Start AI stack (`docker compose -f docker-compose.yml -f override.yml up -d`).
7. Generate SearxNG secret in settings.yml.

**Prerequisites**: Docker running; GPU setup for nvidia/amd profiles.
**Inputs**: Profile (cpu/gpu), environment (private/public); Outputs: Unified localai project containers.
**Error Handling**: Timeout on commands; Fallbacks for platform-specific sed/openssl.
**Best Practices**: Use `--environment public` for cloud (closes non-80/443 ports); Update via `docker compose pull && down/up`.

### RAG AI Agent Workflow

**Description**: [`V3_Local_Agentic_RAG_AI_Agent.json`](n8n/backup/workflows/V3_Local_Agentic_RAG_AI_Agent.json) implements agentic RAG for document querying.

**Ingestion Process**:
1. Local File Trigger watches `/data/shared` for new files (add/change).
2. Loop Over Items → Set File ID (extract path/title/type).
3. Delete old records (docs_pg, document_rows).
4. Switch on type (PDF/Excel/CSV/TXT) → Extract text/data.
5. For tabular: Aggregate → Summarize schema → Insert rows (JSONB in document_rows), Update metadata schema.
6. For text: Chunk (RecursiveCharacterTextSplitter:400) → Embed (Nomic-Embed) → Store in PGVector (documents_pg with metadata).

**Query Process**:
1. Webhook/Chat Trigger (POST /bf4dd093-... with chatInput/sessionId).
2. Edit Fields → RAG AI Agent (Ollama Qwen2.5 via OpenAI-compatible API).
3. Agent uses tools: List Documents (select from document_metadata), Get File Contents (string_agg from documents_pg), Query Document Rows (custom SQL on row_data JSONB).
4. System Prompt: Prioritize RAG, fallback to full doc/SQL for tabular/numeric.
5. Respond to Webhook.

**Prerequisites**: PGVector extension in Supabase; Ollama models pulled (qwen2.5:7b, nomic-embed-text).
**Inputs**: File paths (ingestion), chat queries (JSON: {chatInput, sessionId}); Outputs: Processed embeddings, agent responses.
**Error Handling**: Fallback output in Switch; Postgres error on invalid SQL.
**Best Practices**: Run table creation nodes once (document_metadata, document_rows); Use shared volume for files; Tune chunk size for docs.

### Configuration Management

**Tool**: [`config-manager.py`](config-manager.py) evaluates storage options.

**Process**:
1. Evaluate Supabase DB vs Files (scores: performance/reliability/etc.).
2. Recommend (typically Files for simplicity).
3. Initialize: Create ./config/services.json with defaults (global_settings, services).
4. Update: `update_service_config(service, config)` → Backup → Save JSON.

**Example**: Configures supabase-db (port:5432), n8n (port:5678, deps:['postgres']).

**Prerequisites**: Python (yaml/json); Optional: Supabase for DB mode.
**Inputs**: Service name/config dict; Outputs: services.json, backups.
**Error Handling**: Fallback empty dict on load fail.
**Best Practices**: Git-track configs; Validate schemas; Hot-reload in services.

### Port Management

**Tool**: [`port-manager.py`](port-manager.py) resolves Docker port conflicts.

**Process**:
1. Load ports from docker-compose.yml.
2. Check used ports (lsof/netstat fallback).
3. Detect conflicts (port in used_ports).
4. Find next available (socket bind test, start 8000+).
5. Generate override (docker-compose.override.ports.yml) with new ports.
6. Restart: `docker compose down && up -d`.

**Prerequisites**: lsof/netstat; yaml lib.
**Inputs**: Compose file; Outputs: Override YAML, mappings dict.
**Error Handling**: Warn on no available ports; Skip invalid configs.
**Best Practices**: Run before startup; Use private overrides for localhost binding.

## Services and Components

### Core Services

- **n8n** (image: n8nio/n8n:latest): Low-code workflow engine. Ports: 5678 (internal), 9003 (private). Env: DB=postgres (Supabase), webhook URL. Deps: n8n-import (workflows/credentials). Communication: HTTP to Ollama/Qdrant/Supabase; Scales: Single instance. Monitoring: Langfuse integration.
- **Ollama** (image: ollama/ollama:latest): Local LLM inference. Ports: 11434. Profiles: cpu/gpu-nvidia/gpu-amd (ROCm). Env: Context=8192, max models=2. Volumes: ollama_storage. Deps: None. Communication: HTTP API. Scaling: GPU-accelerated; Pull init models (qwen2.5:7b, nomic-embed).
- **Supabase** (included compose): Full backend stack. See [Supabase Stack](#supabase-stack). Proxy via Caddy:8005.
- **Caddy** (image: caddy:2-alpine): Reverse proxy. Ports: 80/443. Volumes: caddy-data/config. Env: Hostnames (N8N_HOSTNAME etc.), Let's Encrypt email. Deps: All services. Communication: Upstream to service ports. Scaling: Single; Security: Auto-TLS.

**Data Sources Ingested**:
- **Congress.gov API** (Primary): U.S. legislative data (bills, members, actions, subjects, cosponsors). Base: https://api.congress.gov. Endpoints: /bills/{congress}/{type}{number}.json, /actions, /subjects, /cosponsors, /member/{bioguide}. Rate limit: 1000/hr (API key required, public domain data).
- **GovInfo API** (Documents): Federal Register, Code of Federal Regulations, Bills XML/PDF. Base: https://api.govinfo.gov. Collections: BILLS, FR, CFR. Downloads queued via govinfo_download_queue table.
- **USAspending.gov** (Future): Federal spending data (contracts, grants). API key required.
- **Federal Register API** (Integrated via GovInfo): Executive actions, notices.
- **File System** (Local): /data/shared for RAG ingestion (PDF/Excel/CSV/TXT via n8n triggers).

All sources are U.S. Government (public domain); No private data ingested.

### Supabase Stack

Catalog from [`supabase/docker/docker-compose.yml`](supabase/docker/docker-compose.yml):
- **studio** (supabase/studio): Dashboard. Port: 3000 (proxied). Deps: analytics. Env: SUPABASE_URL/KEYS. Health: API profile fetch.
- **kong** (kong:2.8.1): API gateway. Ports: 8000/8443. Volumes: kong.yml. Env: Plugins (auth/cors). Deps: analytics. Communication: Upstream to auth/rest/etc.
- **auth** (supabase/gotrue): Authentication. Port: 9999. Deps: db/analytics. Env: JWT_SECRET, SMTP. Health: /health. Scaling: Session-based.
- **rest** (postgrest): REST API. Port: 3000. Deps: db. Env: PGRST_DB_URI/SCHEMAS. Command: postgrest.
- **realtime** (supabase/realtime): WebSockets. Port: 4000. Deps: db. Env: DB_ENC_KEY, JWT. Health: /api/tenants/health.
- **storage** (supabase/storage-api): File storage. Port: 5000. Volumes: storage. Deps: db/rest/imgproxy. Env: FILE_STORAGE_BACKEND=file. Health: /status.
- **imgproxy** (darthsim/imgproxy): Image processing. Port: 5001. Volumes: storage. Health: imgproxy health.
- **meta** (supabase/postgres-meta): DB management. Port: 8080. Deps: db. Env: PG_META_DB_*.
- **functions** (supabase/edge-runtime): Edge functions. Volumes: functions. Env: SUPABASE_DB_URL. Command: deno start.
- **analytics** (supabase/logflare): Logs/analytics. Port: 4000. Deps: db. Env: POSTGRES_BACKEND_URL. Health: /health.
- **db** (supabase/postgres:15): Postgres DB. Volumes: data, init SQLs (jwt/roles/logs/pooler/realtime/webhooks). Env: POSTGRES_PASSWORD. Health: pg_isready. Command: postgres with custom conf.
- **vector** (timberio/vector): Log shipping. Volumes: vector.yml, docker.sock. Health: /health.
- **supavisor** (supabase/supavisor): Connection pooler. Ports: 5432/6543. Volumes: pooler.exs. Deps: db. Env: DATABASE_URL, POOLER_*. Health: /api/health.

**Inter-Service**: Kong routes to auth/rest/storage; All use shared DB; Realtime subscribes to DB changes.

### AI and Workflow Services

- **flowise** (flowiseai/flowise): AI agent builder. Port: 3001. Env: FLOWISE_USERNAME/PASSWORD. Volumes: ~/.flowise. Entry: sleep then start.
- **open-webui** (ghcr.io/open-webui/open-webui:main): Chat UI. Port: 8080. Volumes: open-webui data. Extra hosts: host.docker.internal.
- **qdrant** (qdrant/qdrant): Vector DB. Ports: 6333/6334. Volumes: qdrant_storage.
- **neo4j** (neo4j:latest): Graph DB. Ports: 7473/7474/7687. Volumes: logs/config/data/plugins. Env: NEO4J_AUTH.
- **n8n-import** (n8n:latest): Imports workflows/credentials. Volumes: ./n8n/backup. Command: import from /backup. One-time.
- **agentic-rag** (Build from ./agentic-knowledge-rag-graph/Dockerfile): RAG API. Port: 8000. Env: NEO4J_URI/AUTH, POSTGRES_URL, QDRANT_URL, OLLAMA_URL. Volumes: agentic_data, ./shared. Deps: postgres, qdrant, neo4j, ollama. Communication: HTTP to Ollama/Qdrant/Supabase; Scales: Single instance. Monitoring: Langfuse integration.

### Observability and Utilities

- **langfuse-web/worker** (langfuse/langfuse:3): LLM tracing. Ports: 3000/3030. Deps: postgres/minio/redis/clickhouse. Env: DATABASE_URL, S3_*, CLICKHOUSE_*.
- **searxng** (searxng/searxng:latest): Search. Port: 8080. Volumes: ./searxng. Env: SEARXNG_BASE_URL, UWSGI_*.
- **Support Services**: postgres (langfuse), redis/valkey, minio, clickhouse (langfuse stack).

**Communication**: HTTP/REST (Caddy proxy), DB connections (Postgres URI), Message queues (none explicit), gRPC (Ollama/Realtime possible).

**Scaling**: Single-container per service; Horizontal via Docker Swarm (not configured); Resource limits in compose (e.g., Ollama GPU res).

**Monitoring/Logging**: Langfuse for AI traces; Docker logs (json-file, 1m max); Partial Prometheus (n8n/localai/rabbitmq).

## Docker Configuration

### Docker Compose Files

- **Main** ([`docker-compose.yml`](docker-compose.yml)): Includes extensions.yml and supabase/docker/docker-compose.yml. Defines volumes (n8n_storage, ollama_storage, etc.), anchors (x-n8n, x-ollama), services (flowise, open-webui, n8n, qdrant, neo4j, caddy, langfuse stack, searxng, ollama profiles). Profiles: cpu/gpu-nvidia/gpu-amd. Healthchecks: wget/pg_isready/redis-cli. Caps: Drop ALL, add NET_BIND_SERVICE.
- **Supabase** ([`supabase/docker/docker-compose.yml`](supabase/docker/docker-compose.yml)): 13 services (studio to supavisor). Multi-stage init via SQL volumes. Healthchecks for all. Volumes: db/data, functions, storage. Env heavy (JWT, SMTP, S3).
- **Overrides**:
  - [`docker-compose.override.private.yml`](docker-compose.override.private.yml): Binds all ports to 127.0.0.1:9001+ (private dev).
  - [`docker-compose.override.public.yml`](docker-compose.override.public.yml): Limits to 80/443 (prod).
  - Public Supabase variant for S3.

**Build Stages**: No multi-stage Dockerfiles in root; Supabase uses pre-built images. Optimizations: Alpine bases (caddy/searxng), expose only needed ports.

**Security Scans**: None automated; Manual via `docker scout` recommended. No vuln scans in scripts.

### Volumes and Networks

**Volumes** (persistent):
- n8n_storage, ollama_storage, qdrant_storage, open-webui, flowise (app data).
- caddy-data/config (TLS/certs).
- langfuse_postgres_data, langfuse_clickhouse_data/logs, langfuse_minio_data (observability).
- Supabase: db/data, storage, functions, logs/vector.yml.
- valkey-data (Redis).
- agentic_data: RAG graph data.

**Networks**: Default Docker bridge (implicit). No custom networks; All services communicate via service names (e.g., n8n → db:5432).

**Persistence Strategies**: Named volumes for state; Bind mounts for configs/scripts (e.g., ./n8n/backup, ./searxng). Backup: Docker volume export or git for configs.

### Container Orchestration

**Build/Run**: `docker compose up -d --profile <profile>`. Init: n8n-import completes before n8n; Ollama-pull before ollama. Depends_on: Langfuse on DBs (healthy); Supabase db on vector.
**Runtime**: Restart: unless-stopped/always. Resource Limits: GPU res for ollama; Cap drops for security (caddy/searxng). Health: Interval 3-5s, retries 3-10.
**Management**: `service-manager.py` for status/start/stop/logs; `docker compose down -v` for cleanup.
**Scaling**: No replicas; Manual via compose scale (e.g., `docker compose up --scale n8n=2`).

## Diagrams

### High-Level Architecture

```mermaid
graph TB
    subgraph "External Access"
        C[Caddy Proxy<br/>80/443]
    end
    subgraph "AI Layer"
        N8N[n8n Workflows]
        OWUI[Open WebUI]
        FL[Flowise]
        OL[Ollama LLM]
    end
    subgraph "Data Layer"
        SB[Supabase<br/>(Auth/API/DB/Storage)]
        QD[Qdrant Vector]
        NJ[Neo4j Graph]
        LG[Langfuse Tracing]
    end
    subgraph "Infrastructure"
        PG[Postgres PGVector]
        R[Redis/Valkey]
        MI[MinIO S3]
        S[SearxNG Search]
        Q[TaskQueue<br/>(SQL-based)]
    end
    C --> N8N
    C --> OWUI
    C --> FL
    C --> SB
    N8N --> OL
    N8N --> PG
    N8N --> QD
    N8N --> NJ
    N8N --> S
    N8N --> Q
    OWUI --> OL
    FL --> OL
    SB --> PG
    LG --> N8N
    LG --> OL
    style C fill:#f9f,stroke:#333
    style PG fill:#bbf,stroke:#333
    style Q fill:#bfb,stroke:#333
```

### Class Definitions

**Database Models** (from [`db/models.py`](db/models.py); SQLAlchemy + Pydantic):
- **APIKey**: Stores API keys (id: UUID, name, api_key, service_name: congress_gov/govinfo, rate_limit, is_active). Relationships: api_calls (APICallLog).
- **APICallLog**: Logs calls (id, api_key_id, service_name, endpoint, method, status_code, response_time_ms, success, error_message, headers/body JSONB, ip_address, created_at). Indexes: service/created_at/api_key.
- **CongressBill**: Bills (id, bill_id: unique, type/number/congress, title/summary, sponsor_id/name/state/party, dates, urls, active/enacted/vetoed, subjects, raw_data JSONB). Relationships: actions/subjects/cosponsors.
- **CongressBillAction**: Actions (id, bill_id, date/text/code/type, committee, acted_by details). Unique: bill_id/date/text.
- **CongressBillSubject**: Subjects (id, bill_id, subject). Unique: bill_id/subject.
- **CongressBillCosponsor**: Cosponsors (id, bill_id, bioguide/thomas/govtrack ids, name/state/district/party, date, original). Unique: bill_id/name/date.
- **CongressMember**: Members (id, member_id unique, names/dob/gender/party/leadership, social ids, urls, in_office, stats: votes/missed/pvi/nominate, raw_data JSONB). Relationships: roles.
- **CongressMemberRole**: Roles (id, member_id, congress/chamber/title/state/party, dates/office/phone, stats). Unique: member_id/congress/chamber.
- **GovInfoCollection**: Collections (id, code unique: BILLS/FR, name/category/description, package_count/last_modified/url).
- **GovInfoPackage**: Packages (id, package_id unique, collection_id, modified/link/class/title/branch/pages/authors/type, raw_metadata/content).
- **GovInfoDownloadQueue**: Queue (id, package_id unique, collection_id, status: pending/downloading/completed/failed, priority/retry/last_error, timestamps).
- **Task**: Queue tasks (id, type: BILL_INGEST/etc., payload JSONB, priority/status/retry, error/scheduled/parent/depends/metadata, timestamps/lock). Relationships: children/parent.

**Queue System** (from [`services/queue/__init__.py`](services/queue/__init__.py)):
- **TaskQueue** class: SQL-based (uses Task model). Methods: create_task(TaskCreate), get_task(id), update_task(TaskUpdate), delete_task, get_next_task(types, worker_id, lock_timeout=300), complete_task(result), fail_task(error), retry_task(delay=0), get_status/result, cleanup_old(days=7).
- Enums: TaskStatus (PENDING/PROCESSING/COMPLETED/FAILED/RETRY), TaskPriority (LOW=1/NORMAL=2/HIGH=3/URGENT=4), TaskType (BILL_INGEST/MEMBER_INGEST/ACTION_INGEST/etc.).
- Features: Locking (locked_at/by, timeout), Dependencies (depends_on list), Retries (max_retries=3), Validation (Pydantic), Pagination/Filtering (status/priority/type).
- Integration: Uses SQLAlchemy Session; Error handling (QueueError/TaskNotFoundError); Logging via logger.

**API Clients** (from [`services/api_clients`](services/api_clients)):
- **CongressGovClient** (congress_gov.py): Inherits BaseAPIClient. Methods: get_bill(congress/type/number), get_actions/subjects/cosponsors/member, search_bills(query). Uses Pydantic: Bill/BillAction/etc. models, PaginatedResponse. Rate limiting, logging (APICallLog).
- Base: _make_request (headers with API key), _parse_response (JSON to model).

**Legend**: Solid arrows = HTTP/DB connections; Dashed = Optional (e.g., search).

### RAG Workflow Sequence

```mermaid
sequenceDiagram
    participant F as File Trigger
    participant I as Ingestion
    participant PG as PGVector
    participant A as Agent
    participant O as Ollama
    participant W as Webhook
    F->>I: New File Detected
    I->>PG: Chunk/Embed/Store
    W->>A: Query (chatInput)
    A->>PG: RAG Retrieve
    PG->>A: Documents
    A->>O: Prompt + Context
    O->>A: Response
    A->>W: Answer
    Note over A,O: Tools: List Docs, Get Contents, SQL Query
```

### Docker Network Topology

```mermaid
graph LR
    subgraph "Docker Network (bridge)"
        C1[Caddy:80/443]
        N1[n8n:5678]
        O1[Ollama:11434]
        S1[Supabase Kong:8000]
        Q1[Qdrant:6333]
        L1[Langfuse:3000]
    end
    C1 -->|Proxy| N1
    C1 -->|Proxy| S1
    N1 -->|HTTP| O1
    N1 -->|Postgres| S1
    N1 -->|Vector| Q1
    L1 -->|DB| S1
    style C1 fill:#ff9
```

### Service Dependencies

```mermaid
graph TD
    N8N[n8n] --> DB[Supabase DB]
    N8N --> OL[Ollama]
    N8N --> QD[Qdrant]
    LANG[Langfuse] --> DB
    LANG --> R[Redis]
    LANG --> CH[ClickHouse]
    LANG --> MI[MinIO]
    Caddy[Caddy] --> N8N
    Caddy --> LANG
    Caddy --> SB[Supabase]
    IMP[n8n-import] --> N8N
    style DB fill:#bbf
    style OL fill:#bfb
```

### SQL Tables and ERD

**Schema** (from [`db/migrations/001_initial_schema.sql`](db/migrations/001_initial_schema.sql); 362 lines):
- Extensions: uuid-ossp, pgcrypto.
- Tables: api_keys (id/name/api_key/service/rate_limit/active/timestamps), api_call_logs (id/api_key_id/service/endpoint/method/status/time/success/error/headers/body/ip/user/timestamp; indexes: service/created/api_key).
- congress_bills (id/bill_id unique/type/number/congress/title/sponsor/dates/actions/urls/active/enacted/subjects/summary/raw/timestamps; indexes: congress/type/sponsor/date/updated).
- congress_bill_actions (id/bill_id/date/text/code/type/committee/acted_by; unique: bill/date/text; indexes: bill/date).
- congress_bill_subjects (id/bill_id/subject; unique: bill/subject; indexes: bill/subject).
- congress_bill_cosponsors (id/bill_id/ids/name/state/district/party/date/original; unique: bill/name/date; indexes: bill/name/state).
- congress_members (id/member_id unique/names/dob/gender/party/leadership/social/ids/urls/office/in_office/stats/raw/timestamps; indexes: state/party).
- congress_member_roles (id/member_id/congress/chamber/titles/state/party/dates/office/stats; unique: member/congress/chamber; indexes: member/congress/chamber/state/party).
- govinfo_collections (id/code unique/name/category/desc/packages/modified/url/timestamps).
- govinfo_packages (id/package_id unique/collection_id/modified/link/class/title/branch/pages/authors/type/raw/content/timestamps; indexes: collection/modified/type).
- govinfo_download_queue (id/package_id unique/collection_id/status/priority/retry/error/timestamps; indexes: status/priority/created).
- Triggers: update_modified_column() for updated_at on updates.
- Function: log_api_call() inserts to api_call_logs (returns UUID).

**ERD** (Mermaid; relationships from models.py):
```mermaid
erDiagram
    APIKey ||--o{ APICallLog : "has"
    CongressBill ||--o{ CongressBillAction : "has"
    CongressBill ||--o{ CongressBillSubject : "has"
    CongressBill ||--o{ CongressBillCosponsor : "has"
    CongressMember ||--o{ CongressMemberRole : "has"
    GovInfoCollection ||--o{ GovInfoPackage : "has"
    GovInfoCollection ||--o{ GovInfoDownloadQueue : "has"
    GovInfoPackage ||--|| GovInfoDownloadQueue : "queued"
    Task ||--o{ Task : "parent_of"
    
    APIKey {
        UUID id PK
        TEXT name
        TEXT api_key UK
        TEXT service_name
        INTEGER rate_limit
        BOOLEAN is_active
    }
    CongressBill {
        UUID id PK
        TEXT bill_id UK
        TEXT bill_type
        INTEGER congress
        TEXT title
        JSONB raw_data
    }
    Task {
        UUID id PK
        ENUM task_type
        JSONB payload
        ENUM status
        INTEGER priority
        JSONB metadata
    }
```

**Version**: v1.2 (2025-09-22; enhanced with new docs links, updated services, changelog).

## Additional Coverage

### Ancillary Files

- **Environment**: [`.env`](.env) (secrets: POSTGRES_PASSWORD, JWT_SECRET, ANON_KEY); Backups (.env.backup.*).
- **Scripts**: [`deploy-legislative-ai.sh`](deploy-legislative-ai.sh) (cloud deploy?), [`fix-jwt-problem.sh`](fix-jwt-problem.sh) (JWT fixes).
- **n8n Tools**: [`Create_Google_Doc.json`](n8n-tool-workflows/Create_Google_Doc.json) (webhook → Google Drive create), [`Get_Postgres_Tables.json`](n8n-tool-workflows/Get_Postgres_Tables.json) (list public tables).
- **Reports**: [`docker_status.py`](reports/docker_status.py) (status checks), [`yaml_validate.py`](reports/yaml_validate.py) (config validation).
- **Other**: [`tasks.md`](tasks.md) (TODOs), [`errors.md`](docs/errors.md) (common issues), [`extensions.yml`](extensions.yml) (Docker extensions), [`prometheus.yml`](prometheus.yml) (basic scraping), LICENSE, .gitignore.

No CI/CD (GitHub Actions in .github/ empty); IaC limited to Docker Compose (declarative services/volumes).

### Security Considerations

- **Secrets**: Use [`fix-supabase-env.sh`](fix-supabase-env.sh) for random generation; Avoid @ in passwords; Store .env securely (gitignore'd).
- **Proxy**: Caddy auto-TLS; Public env limits ports; Cap drops (ALL except NET_BIND_SERVICE).
- **DB**: Supabase roles/JWT; No exposed DB ports in public.
- **Containers**: Non-root users (e.g., clickhouse:101:101); Healthchecks prevent zombie services.
- **Vulns**: Update images (`docker compose pull`); Scan with Trivy/Clair; No secrets in images.
- **Access**: n8n/Flowise/OpenWebUI require local accounts; Supabase DASHBOARD_USERNAME/PASSWORD.

**Improvements**: Add secrets scanning (git-secrets); RBAC in n8n; Vault for dynamic secrets; OWASP scans.

### Potential Improvements

- **CI/CD**: Add GitHub Actions for image builds/tests/deploy (e.g., to Kubernetes).
- **Monitoring**: Full Prometheus/Grafana stack; Alerting on service health.
- **Scaling**: Docker Swarm/K8s manifests; Auto-scaling for n8n workers.
- **Backup**: Automated volume snapshots (e.g., via cron + docker volume backup).
- **Docs**: API refs for custom tools; Video walkthroughs.
- **Performance**: Ollama model quantization; PGVector indexing optimizations.
- **Security**: Add Falco for runtime security; Rotate secrets periodically.

## Changelog

- **v1.0 (2025-09-10)**: Initial comprehensive documentation. Covered all files/services; Added Mermaid diagrams.
- **v1.1 (2025-09-22)**: Enhanced with new docs (services.md, deployment.md, etc.), updated links, standardized structure.
- **Future**: Update post major releases (e.g., Supabase v2, n8n updates).

## Indexes

**Services Index**:
- n8n: [Processes](#service-deployment), Ports 5678
- Supabase: [Stack](#supabase-stack), Proxy 8005
- Ollama: [AI Services](#ai-and-workflow-services), 11434

**Files Index**:
- [`docker-compose.yml`](docker-compose.yml): Line 58 (services start)
- [`V3_Local_Agentic_RAG_AI_Agent.json`](n8n/backup/workflows/V3_Local_Agentic_RAG_AI_Agent.json): Line 278 (agent prompt)

**Cross-References**: See [RAG Workflow](#rag-ai-agent-workflow) for n8n details; [Docker](#docker-configuration) for volumes.

---
*Generated by Roo Code Documentation Writer. Last Updated: 2025-09-22.*