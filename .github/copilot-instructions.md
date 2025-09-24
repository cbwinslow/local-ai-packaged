# Local AI Packaged - AI Agent Instructions

## Project Overview
This repo is a Docker Compose-orchestrated self-hosted AI platform for legislative data analysis. Core goal: Privacy-focused, offline RAG agents ingesting government data (bills, votes from Congress.gov/FEC) into Neo4j graphs and Qdrant vectors, processed via n8n workflows and Ollama LLMs. Avoid cloud deps; prioritize local persistence in `./volumes/`. Example data flow: Ingest PDF bills to `/shared/` → n8n chunks/embeds → Supabase auth → Neo4j entities → Langfuse-traced query response.

## Architecture
- **Services**: n8n (workflows, e.g., `./n8n/backup/V3_Local_Agentic_RAG_AI_Agent.json` for RAG), Supabase (Postgres DB/auth/vectors at `http://localhost:8000`), Ollama (LLMs on port 11434, auto-pull Qwen2.5), Qdrant (vectors on 6333), Neo4j (graphs on 7474), Traefik (proxy on 80/443, routes via labels in docker-compose.yml).
- **Boundaries**: Backend Python scripts (`./scripts/`) handle ingestion (e.g., `government-data-ingestion.py` uses Postgres/Qdrant); Frontend Next.js (`./frontend/`) queries via Supabase SDK. Communication: HTTP via Traefik; queues via RabbitMQ (`./docker-compose.yml`); shared files in `/data/shared`.
- **Why**: Modular for easy scaling (e.g., GPU profiles in docker-compose); Bitwarden secrets (`./scripts/populate-env-from-bitwarden.sh`) ensure secure, non-committed configs. No Kubernetes—Compose for simplicity.

## Developer Workflows
- **Setup**: `uv venv .venv --python=3.10; source .venv/bin/activate; uv pip install -r requirements.txt` (uv over pip for speed). Secrets: `./scripts/enhanced-generate-secrets.sh` evaluates openssl in .env.template to .env (never commit .env).
- **Build/Run**: `./scripts/start-all-services.sh` (or `docker compose up -d --profile gpu-nvidia` for GPU). Debug: Use `.vscode/launch.json` (Python: debugpy for scripts; Node attach for n8n on 9229). Non-obvious: `docker compose logs -f supabase` for DB issues; `./scripts/health-check.sh --check-all` validates services.
- **Tests**: Backend: `uv run pytest tests/` (e.g., `test_deployment.py` checks docker up/Supabase health). Frontend: `cd frontend && npm test` (Jest for rendering, e.g., mocks Supabase client). Coverage: `pytest --cov=tests --cov-report=term-missing`. Run full: `./scripts/generate_reports.py` for health/network reports.
- **Deploy**: Local: `start-all-services.sh -e public` (exposes 80/443). Cloud: `./scripts/deploy-legislative-ai.sh` (Ubuntu, ufw for ports). CI: GitHub Actions lint/test/deploy (Conventional Commits).

## Conventions & Patterns
- **Python**: PEP 8 via Black (`uv run black scripts/`); type hints everywhere (e.g., `government-data-ingestion.py` uses `from pathlib import Path`). Patterns: Async ingestion with asyncio (e.g., `ingest_govinfo_data.py` batches API calls); env vars via `os.getenv` (e.g., `POSTGRES_PASSWORD` from .env).
- **JS/TS**: Airbnb style; Next.js App Router (`./frontend/src/app/`). Patterns: Supabase auth helpers (`@supabase/auth-helpers-nextjs` in `pages/index.tsx`); TanStack Query for data fetching (e.g., bills list with optimistic updates).
- **Docker**: Profiles (cpu/gpu-nvidia in docker-compose.yml); volumes bind to `./volumes/` for persistence (e.g., postgres_data_persistent). Labels for Traefik routing (e.g., `traefik.http.routers.frontend.rule=Host(\`${FRONTEND_HOSTNAME}\`)`).
- **Git**: Feature branches (`feature/ai-ingestion`); pre-commit hooks (`.pre-commit-config.yaml` for linting). No secrets in commits—use .env.example.
- **Integrations**: n8n nodes call Ollama (`http://ollama:11434`); Supabase for auth (anon key in .env); RabbitMQ queues for workers (`worker.py` processes tasks from `tasks` table).

## Key Files/Dirs
- `./docker-compose.yml`: Core services; extend with overrides (e.g., docker-compose.override.ai-tools.yml).
- `./scripts/start-all-services.sh`: Orchestrates compose up, health checks, model pulls.
- `./n8n/backup/*.json`: Workflows (import via n8n-import service).
- `./frontend/src/app/docs/page.tsx`: Example of lucide-react icons and markdown rendering.
- `./agentic-knowledge-rag-graph/main.py`: RAG entrypoint (Neo4j/Qdrant integration).
- `./docs/errors.md`: Troubleshooting (e.g., Supabase pooler restarts due to JWT chars).

Follow agents.md for AI-specific rules (uv venvs, small changes). Reference README.md for quick starts.
