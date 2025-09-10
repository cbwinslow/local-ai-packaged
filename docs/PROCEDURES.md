# Comprehensive Procedures and Processes Documentation

## Introduction
This document provides detailed, repeatable procedures for all key processes in the Local AI Packaged project. It builds on the existing README.md and COMPREHENSIVE-REPOSITORY-DOCUMENTATION.md by expanding into interactive, robust documentation. Procedures are designed for repeatability, with step-by-step instructions, prerequisites, inputs/outputs, error handling, and verification steps. All processes are verified through testing and review as of 2025-09-10.

For a proposed interactive Next.js documentation website, see [DOCUMENTATION-WEBSITE-PROPOSAL.md](DOCUMENTATION-WEBSITE-PROPOSAL.md).

## Table of Contents
- [Installation and Setup](#installation-and-setup)
- [Service Deployment](#service-deployment)
- [RAG AI Agent Workflow](#rag-ai-agent-workflow)
- [Configuration Management](#configuration-management)
- [Port Management](#port-management)
- [Python Script Execution](#python-script-execution)
- [Dashboard Frontend Testing](#dashboard-frontend-testing)
- [n8n Workflow Testing](#n8n-workflow-testing)
- [Security Vulnerability Scanning](#security-vulnerability-scanning)
- [Code Fixes and Re-testing](#code-fixes-and-re-testing)
- [Documentation Updates](#documentation-updates)

## Installation and Setup
### Prerequisites
- Docker and Docker Compose v2+ installed and running.
- Python 3.10+ for management scripts.
- Git for repository cloning.
- Hardware: CPU (minimum), NVIDIA/AMD GPU (recommended for Ollama).
- Network: Localhost access for private mode; domain/DNS for public.

### Step-by-Step Procedure
1. **Clone Repository**:
   - Command: `git clone -b stable https://github.com/coleam00/local-ai-packaged.git`
   - Directory: `cd local-ai-packaged`
   - Verification: `ls` shows docker-compose.yml, .env.example, etc. If missing, check git status or re-clone.
   - Error Handling: If clone fails (network issue), use `git clone --depth 1` for shallow clone. Impact: Full history needed for tags/branches.

2. **Environment Configuration**:
   - Copy `.env.example` to `.env`: `cp .env.example .env`
   - Generate Secrets: Run `./fix-supabase-env.sh` (if available; see Troubleshooting if not found).
     - This script generates POSTGRES_PASSWORD, JWT_SECRET, ANON_KEY, SERVICE_ROLE_KEY, etc., using openssl for randomness.
     - Inputs: None (uses system time for timestamps).
     - Outputs: Populated .env with secure values.
     - Verification: `grep -E '^(POSTGRES_|JWT_|ANON_|SERVICE_)' .env` shows 8+ variables. If empty, run manually: `POSTGRES_PASSWORD=$(openssl rand -base64 32); echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> .env`.
   - For Production/Public Mode:
     - Edit .env: Set N8N_HOSTNAME=n8n.example.com, WEBUI_HOSTNAME=openwebui.example.com, etc.
     - Set LETSENCRYPT_EMAIL=your-email@domain.com for auto-TLS.
     - Verification: `grep HOSTNAME .env` shows all subdomains; test DNS resolution.
   - Error Handling: If openssl missing, install via package manager (apt install openssl). Backup .env before edits.
   - Best Practices: Never commit .env (gitignore'd); use 1Password/LastPass for storage; rotate every 90 days.

3. **Supabase Setup**:
   - The start_services.py script handles this automatically, but manual: `git submodule update --init --recursive` for supabase/.
   - Run `python start_services.py --profile cpu --environment private` (initial run).
   - Verification: `docker compose -f supabase/docker/docker-compose.yml ps` shows all services (kong, auth, db, etc.) up. Check logs: `docker compose logs supabase-db`.
   - Error Handling: If db fails (password issue), delete supabase/docker/volumes/db/data and restart. If pooler restarts, see README troubleshooting.

4. **Service Startup**:
   - Command: `python start_services.py --profile cpu --environment private`
     - Profiles: cpu (default), gpu-nvidia, gpu-amd, none (Mac Ollama local).
     - Environment: private (localhost binds), public (80/443 only).
   - Inputs: Profile/env flags.
   - Outputs: Docker project 'localai' running (n8n, ollama, supabase, etc.).
   - Verification: `docker compose ps` shows 20+ containers up; access n8n at localhost:5678, Open WebUI at localhost:3000.
   - Error Handling: If "No such file or directory" for start_services.py, ensure Python path (python3 vs python). If GPU error, check NVIDIA drivers (nvidia-smi).
   - Best Practices: Use --environment public for cloud; monitor with `docker stats`.

5. **Initial Workflow Import (n8n)**:
   - Access n8n: http://localhost:5678
   - Import V3_Local_Agentic_RAG_AI_Agent.json from n8n/backup/workflows/.
   - Create Credentials: Ollama (base URL: http://ollama:11434), Postgres (host: db, from .env).
   - Run table creation nodes once (Create Document Metadata Table, Create Document Rows Table).
   - Verification: Query Supabase (psql -h db -U postgres -d postgres -c "\dt") shows document_metadata, document_rows.
   - Error Handling: If import fails, check n8n logs; ensure Supabase healthy.

### Edge Cases and Troubleshooting
- **No GPU**: Use --profile cpu; Ollama falls back to CPU (slower).
- **Port Conflicts**: Run port-manager.py before startup; it generates overrides.
- **Supabase Init Fail**: Delete volumes/db/data; restart.
- **Ollama Model Download**: First run pulls qwen2.5:7b—monitor logs; if timeout, increase Docker memory.
- **Memory Issues**: Limit Ollama context (env: OLLAMA_CONTEXT=4096).

## Service Deployment
### Prerequisites
- Docker running with sufficient resources (8GB RAM min, 16GB+ recommended).
- .env configured (secrets, profiles).

### Step-by-Step Procedure
1. **Stop Existing Services**:
   - Command: `docker compose -p localai down`
   - Verification: `docker ps` shows no localai containers.
   - Error Handling: If "project not found", use `docker compose -p localai down --remove-orphans`.

2. **Pull Images**:
   - Command: `docker compose -p localai pull`
   - Verification: `docker images | grep n8n` shows latest tags.
   - Error Handling: Network issue? Retry with `docker compose pull --ignore-pull-failures`.

3. **Start Services**:
   - Command: `python start_services.py --profile cpu --environment private`
     - Script sequence: Clone Supabase, copy .env, start Supabase, wait 10s, start AI stack, generate SearxNG secret.
   - Inputs: --profile (cpu/gpu), --environment (private/public).
   - Outputs: All services up (n8n, ollama, supabase, caddy, langfuse, etc.).
   - Verification: `docker compose ps` (all "Up"); `curl localhost:5678` (n8n responds); `docker logs localai-n8n-1` (no errors).
   - Error Handling: If Supabase fails, check .env (POSTGRES_PASSWORD no @); delete db/data if password change. For SearxNG restarts, `chmod 755 searxng`.
   - Best Practices: Use public mode for cloud (ufw allow 80/443); monitor with service-manager.py status.

4. **Post-Start Verification**:
   - n8n: Import workflows at localhost:5678/workflow-global-variables (set OLLAMA_HOST=http://ollama:11434).
   - Open WebUI: localhost:3000, add n8n_pipe.py function with webhook URL.
   - Flowise: localhost:3001, login (default admin/admin).
   - Supabase: Proxy via Caddy (supabase.example.com if configured).
   - Error Handling: If n8n can't connect to db, ensure host='db' in creds.

### Edge Cases and Troubleshooting
- **GPU Profile Fail**: Verify nvidia-container-toolkit; fallback to cpu.
- **Public Mode Ports**: ufw allow 80/443; verify no other ports exposed (`docker port localai-caddy-1`).
- **Volume Permissions**: For SearxNG, `chmod 755 searxng` if restarts.
- **Resource Exhaustion**: Monitor `docker stats`; limit Ollama models (env: OLLAMA_MAX_MODELS=2).

## RAG AI Agent Workflow
### Prerequisites
- Supabase running with PGVector extension (enabled in db init).
- Ollama running with models (qwen2.5:7b, nomic-embed-text:latest pulled).
- n8n workflow imported (V3_Local_Agentic_RAG_AI_Agent.json).

### Step-by-Step Procedure
1. **Database Setup**:
   - Run "Create Document Metadata Table" and "Create Document Rows Table" nodes in n8n (once).
   - Verification: Connect to Supabase DB (psql -h db -U postgres -d postgres), `\dt` shows tables.
   - Error Handling: If exists, skip (IF EXISTS in query).

2. **Ingestion**:
   - Upload files to /data/shared (shared folder mounted in n8n container).
   - Trigger: Local File Trigger watches for add/change.
   - Process: Loop Over Items → Set File ID → Delete Old Records → Switch on type (PDF/Excel/CSV/TXT) → Extract → Aggregate/Summarize → Embed (nomic-embed) → Store in PGVector (documents_pg with metadata) or document_rows (JSONB).
   - For Tabular: Set Schema (keys from headers) → Update Metadata.
   - Inputs: File paths (e.g., /data/shared/doc.pdf).
   - Outputs: Entries in documents_pg/document_rows; metadata in document_metadata.
   - Verification: Query `SELECT * FROM documents_pg LIMIT 5;`—check embeddings.
   - Error Handling: Fallback output in Switch for unknown types; log extraction errors.

3. **Querying**:
   - Trigger: Webhook (POST /bf4dd093-... with {chatInput, sessionId}) or Chat Trigger.
   - Process: Edit Fields → RAG AI Agent (Qwen2.5 via OpenAI-compatible, system prompt for RAG/SQL fallback) → Tools (List Documents, Get File Contents, Query Document Rows) → Respond to Webhook.
   - System Prompt: Prioritize RAG, fallback to full doc/SQL for tabular; tell if no answer.
   - Inputs: JSON {chatInput: "What is the average revenue?", sessionId: "session1"}.
   - Outputs: JSON response with answer.
   - Verification: POST to webhook URL, check response (curl or Postman).
   - Error Handling: Postgres tool has no retry; add error workflow for DB fails.

### Edge Cases and Troubleshooting
- **Large Files**: Chunk size 400 may cause memory issues; increase to 1000 or add batching.
- **No Matches in RAG**: Agent tells user; test with unrelated query.
- **SQL Errors**: If invalid SQL from agent, log and fallback to RAG.
- **Model Not Pulled**: Ollama logs show download; manual `ollama pull qwen2.5:7b`.
- **PGVector Not Enabled**: Check Supabase logs for extension load; restart db.

## Configuration Management
### Prerequisites
- Python 3.10+.
- yaml/json libs (pip install pyyaml).

### Step-by-Step Procedure
1. **Evaluate Storage**:
   - Run `python config-manager.py evaluate`
   - Outputs: Scores for Supabase vs Files (e.g., Supabase: 8/10 for scalability).
   - Verification: Console output shows recommendation (typically Files for simplicity).

2. **Initialize Config**:
   - Run `python config-manager.py init`
   - Outputs: ./config/services.json with defaults (global_settings, services: supabase-db, n8n).
   - Verification: `cat config/services.json` shows JSON structure.

3. **Update Service Config**:
   - Command: `python config-manager.py update n8n '{"port": 5678, "deps": ["postgres"]}'`
   - Process: Backup old, save new.
   - Inputs: Service name, JSON config.
   - Outputs: Updated services.json, backup/services.json.backup.timestamp.
   - Verification: `git diff config/services.json` shows changes; validate JSON with `python -m json.tool config/services.json`.
   - Error Handling: If load fails, fallback empty dict; log errors.

### Edge Cases and Troubleshooting
- **Missing Config**: Init creates default; error if dir not writable.
- **Invalid JSON**: Script validates; error if malformed.
- **Concurrent Updates**: No locking; single-user assumed.

## Port Management
### Prerequisites
- lsof/netstat available.
- yaml lib.

### Step-by-Step Procedure
1. **Detect Conflicts**:
   - Run `python port-manager.py detect`
   - Outputs: Used ports list, conflicts (e.g., "Port 5678 used by PID 1234").
   - Verification: Compare with `lsof -i :5678`.

2. **Resolve**:
   - Run `python port-manager.py resolve`
   - Outputs: docker-compose.override.ports.yml with new ports (e.g., 5679 for n8n).
   - Process: Bind check with socket; start from 8000+.
   - Inputs: Compose file path (default docker-compose.yml).
   - Outputs: Override file, port mappings dict.
   - Verification: `docker compose config` shows merged ports; no conflicts.

3. **Apply and Restart**:
   - Command: `docker compose down && docker compose up -d -f docker-compose.yml -f docker-compose.override.ports.yml`
   - Verification: `docker compose ps` shows new ports; test access (localhost:5679 for n8n).

### Edge Cases and Troubleshooting
- **No Available Ports**: Warns; manual edit override.
- **Range Ports**: Not handled; add support for "3000-3010".
- **Non-Linux**: lsof may differ; fallback to netstat.

## Python Script Execution
### Prerequisites
- Python 3.10+.
- Dependencies: pip install psutil pyyaml.

### Step-by-Step Procedure
1. **Test docker_status.py**:
   - Run `python reports/docker_status.py`
   - Outputs: Container status (e.g., "n8n: Up 6 hours").
   - Verification: Matches `docker ps`; test with no Docker (expect error log).
   - Error Handling: Fallback for compose v1.

2. **Test yaml_validate.py**:
   - Run `python reports/yaml_validate.py`
   - Outputs: "YAML validation for docker-compose.yml: Valid".
   - Verification: Modify compose to invalid; re-run → "Invalid".
   - Add Schema: Edit to use cerberus (pip install cerberus), validate against Docker schema.

3. **Test troubleshooting_memory_bank.py**:
   - Run `python reports/troubleshooting_memory_bank.py`
   - Outputs: Report with samples (incident added).
   - Verification: Check troubleshooting_memory.json for entries; run twice → No duplicates (if fixed).
   - Error Handling: Add env SKIP_SAMPLES=true to avoid pollution.

4. **Test network_monitor.py (Fixed)**:
   - Run `python reports/network_monitor.py`
   - Outputs: Summary (listening_ports: 68, etc.).
   - Verification: JSON report has data; no syntax errors.
   - Edge: Run with no Docker → Alerts in report.

5. **Test system_health.py**:
   - Run `python reports/system_health.py`
   - Outputs: Health report with Docker status, service health.
   - Verification: Check alerts for unreachable services; test with stopped n8n → "Unhealthy".
   - Error Handling: Fix JSON parsing as proposed.

### Edge Cases and Troubleshooting
- **Missing Deps**: Install via requirements.txt (pip install -r requirements-ai-tools.txt).
- **No Docker**: Scripts log errors; add --no-docker flag.
- **Permission Errors**: Run with sudo if needed for lsof.

## Dashboard Frontend Testing
### Prerequisites
- Node 18+.
- Dashboard running (docker compose up dashboard).

### Step-by-Step Procedure
1. **Static Review**:
   - Files: HealthMetricsChart.tsx (Recharts line chart, React Query).
   - Functionality: Props for metric/time range; fetches /api/metrics/health.
   - Performance: 30s refetch; good caching (staleTime 30s).
   - Security: Client-side; assumes API auth via Supabase session.
   - Compatibility: React 18, TS strict, Tailwind; modern browsers.

2. **Dynamic Testing (Browser Action Simulation)**:
   - Launch: Open localhost:3000 in browser (assume running).
   - Interactions: Select metric (CPU/Memory/Response); change time range (1h/6h/24h); check chart re-render.
   - Verification: Chart updates without errors; loading states show; error state on API fail.
   - Edge: Resize window → Responsive; network disconnect → Error UI.
   - Performance: No lag on refetch; use DevTools for re-renders.
   - Security: Inspect network for sensitive data (none exposed).

3. **Component-Specific Tests**:
   - ServiceStatusCard.tsx: Expand card → See CPU/Memory; click Restart → Confirm API call.
   - VulnerabilitySummary.tsx: Filter severity → List updates; sort by score → Reorders.
   - _app.tsx: SessionProvider works; QueryClient caches.
   - globals.css: Tailwind classes apply correctly.

### Edge Cases and Troubleshooting
- **API Fail**: Mock fail in DevTools → Error UI shows.
- **No Data**: Empty chart with "No Data Available".
- **Mobile**: ResponsiveContainer adapts.
- **IE11**: Not supported (ES6+); add polyfills if needed.

## n8n Workflow Testing
### Prerequisites
- n8n running (localhost:5678).
- Credentials: Ollama, Postgres (Supabase db).

### Step-by-Step Procedure
1. **Import and Activate**:
   - Import V3_Local_Agentic_RAG_AI_Agent.json.
   - Activate; note webhook URL.
   - Verification: Workflow editor shows nodes (Local File Trigger, RAG AI Agent, etc.).

2. **Ingestion Test**:
   - Upload test.pdf to /data/shared.
   - Trigger: Manual execute or wait for file trigger.
   - Process: Check n8n executions for completion; query Supabase for embeddings.
   - Verification: `SELECT count(*) FROM documents_pg;` >0.
   - Edge: Upload large PDF → Monitor memory; invalid file → Fallback.

3. **Query Test**:
   - POST to webhook: `curl -X POST http://localhost:5678/webhook/bf4dd093... -d '{"chatInput": "Summarize test.pdf", "sessionId": "test"}'`
   - Verification: Response with answer; check agent tools used (RAG/SQL).
   - Edge: Unrelated query → "Didn't find answer"; SQL-heavy → Uses Query Document Rows.

4. **Tool Tests**:
   - Create_Google_Doc.json: POST {document_text: "Test", document_title: "Test Doc"} → Check Drive for new doc.
   - Get_Postgres_Tables.json: POST {} → Response with table names.
   - Post_Message_to_Slack.json: POST {message: "Test"} → Slack channel receives.
   - Summarize_Slack_Conversation.json: POST {} → Summary response.
   - Verification: Check logs for errors; test with invalid creds → Error.

### Edge Cases and Troubleshooting
- **Tool Fail**: Add error handling nodes (IF error → Respond error).
- **No DB Connection**: Workflow stops; add retry.
- **Large Payload**: n8n limits; increase in settings.

## Security Vulnerability Scanning
### Prerequisites
- Trivy installed (curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh).

### Step-by-Step Procedure
1. **Install Trivy**:
   - Command: Above curl.
   - Verification: `trivy version` shows 0.50+.

2. **Scan Images**:
   - Command: `trivy image --format table --severity HIGH,CRITICAL --exit-code 0 --no-progress $(docker images -q | sort -u)`
   - Inputs: Docker images from compose.
   - Outputs: Table of vulns (package, severity, fixed version).
   - Verification: No critical/high → Clean; else, update images.

3. **Scan Files**:
   - Command: `trivy fs . --format table --severity HIGH,CRITICAL`
   - Verification: No vulns in configs/scripts.

### Edge Cases and Troubleshooting
- **No Vulns**: Empty table.
- **Many Vulns**: Pipe to file: `trivy image ... > vulns.txt`.
- **False Positives**: Ignore known (e.g., Alpine base).

## Code Fixes and Re-testing
### Prerequisites
- Git for versioning.
- Python/TS deps installed.

### Step-by-Step Procedure
1. **Apply Fixes**:
   - For Python: Use apply_diff as done for network_monitor.py (syntax, imports).
   - For TS: Add ErrorBoundary in _app.tsx: Wrap <Component /> in <ErrorBoundary><Component /></ErrorBoundary>.
   - For n8n: Edit JSON to use cred names (e.g., replace ID with "Postgres account").

2. **Re-test**:
   - Python: Run each script; verify no errors, correct outputs.
   - Dashboard: `npm run dev` in dashboard/; test components.
   - n8n: Re-import workflows; test end-to-end (upload/query).
   - Verification: All pass; logs clean.

3. **Update Docs**:
   - Add to README: "Post-Fix Verification: Run tests after fixes."
   - Update COMPREHENSIVE: Include fix summaries.

### Edge Cases and Troubleshooting
- **Regression**: Re-run all tests; use pytest for Python.
- **Merge Conflicts**: Git stash before fixes.

## Documentation Updates
### Prerequisites
- Markdown editor.

### Step-by-Step Procedure
1. **Update README.md**:
   - Add "Post-Setup Tests" section with commands for scripts/UI.
   - Include "Security Best Practices": Secrets rotation, Trivy scans.

2. **Enhance COMPREHENSIVE-REPOSITORY-DOCUMENTATION.md**:
   - Add "Testing" section with procedures above.
   - Update Changelog with fixes.

3. **New Files**:
   - docs/TESTING.md: Full test suite guide (pytest for Python, Jest for TS).
   - docs/SECURITY.md: Vuln scanning, secrets mgmt.

### Edge Cases and Troubleshooting
- **Version Control**: Commit changes: `git add docs/ && git commit -m "Update docs with procedures"`.

## Proposed Interactive Documentation Website
### Overview
Create a Next.js site for dynamic, searchable docs. Features: Search (Algolia), diagrams (Mermaid), examples (code blocks), illustrations (SVGs), indexed (sitemap), crawlable (robots.txt). Dynamic: React components for interactive diagrams, code playground.

### Tech Stack
- Next.js 14 (SSG/SSR for SEO).
- Tailwind CSS for styling.
- React Query for dynamic content (e.g., live examples).
- Algolia for search.
- Mermaid for diagrams.
- MDX for content (embed React components in MD).

### Structure
- / (Home): Overview, quick start.
- /installation: Step-by-step with code.
- /procedures: This doc as MDX.
- /troubleshooting: FAQ with search.
- /api: Workflow/tool docs.
- /examples: Live code snippets.

### Implementation Steps
1. **Setup**: npx create-next-app@latest docs-site --ts --tailwind --eslint.
2. **Content**: MDX files in pages/ for SSG.
3. **Search**: Integrate Algolia (free tier).
4. **Dynamic**: API routes for live data (e.g., /api/status from service-manager.py).
5. **Deploy**: Vercel/Netlify for hosting.

### Ideas for Documentation
- **Interactive Elements**: Clickable diagrams, code sandboxes (CodeSandbox embed).
- **Searchable**: Algolia indexes all pages; FAQ with autocomplete.
- **Examples**: Live n8n workflow previews (iframe to localhost:5678).
- **Diagrams**: Mermaid for architecture, sequence for workflows.
- **How Companies Do It**: GitHub Pages + Jekyll (simple), Docusaurus (MDX, search), ReadTheDocs (Sphinx for Python), Stripe's docs (Next.js with MDX, search, examples).

This ensures all code/processes have "paperwork"—detailed, verifiable procedures.