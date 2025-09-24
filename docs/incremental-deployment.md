### Incremental Deployment Instructions for Local AI Packaged

This guide breaks down the deployment process into measurable iterations for the Local AI Packaged project. Each iteration has:
- **Objective**: Clear goal.
- **Steps**: Actionable commands (run from project root: `/home/foomanchu8008/Documents/local-ai-packaged/local-ai-packaged`).
- **Success Criteria**: How to verify (e.g., output, file check).
- **Error Handling**: If fails, check `docs/errors.md` for similar issues, fix, then retry the iteration. Do not proceed until success. Log new errors there.

Run iterations sequentially. If an iteration fails, stop, fix (e.g., install deps, edit files), rerun from that iteration. Total time: ~10-20 min if no errors.

#### Iteration 1: Environment Setup (Prep .env and Basics)
**Objective**: Ensure .env is populated and basic files are ready (no services yet).

**Steps**:
1. Generate secrets: `./scripts/enhanced-generate-secrets.sh`.
2. Validate env: `./scripts/validate_env.sh` (if exists; else, check .env for placeholders like "$(openssl" – rerun generation if present).
3. Create venv: `uv venv .venv --python=3.10 && source .venv/bin/activate && uv pip install -r requirements.txt`.

**Success Criteria**:
- .env has no "$(openssl" (all values generated, e.g., POSTGRES_PASSWORD len >20).
- `grep -E "POSTGRES_PASSWORD|JWT_SECRET" .env` shows values.
- Venv activates without errors (`which python` points to .venv).

**Error Handling**: If generation fails (e.g., openssl missing), install `sudo apt install openssl`. Retry. Log to errors.md if new.

#### Iteration 2: Dependency Installation (Python/Frontend/Node)
**Objective**: Install all deps for build/test (local and Docker).

**Steps**:
1. Backend: `source .venv/bin/activate && uv pip install -r requirements.txt pytest pytest-cov python-dotenv pyyaml requests pytest-mock`.
2. Frontend: `cd frontend && npm install && npm install lucide-react @testing-library/jest-dom @testing-library/react @testing-library/user-event jest jest-environment-jsdom`.
3. Docker deps: `docker compose build --no-cache frontend` (rebuilds image with deps).

**Success Criteria**:
- No ImportErrors in `pytest tests/ -v` (basic collection passes).
- `npm test` in frontend runs without "module not found".
- Frontend build succeeds (`docker compose build frontend` exit 0).

**Error Handling**: If pip/npm fail (e.g., network), retry with `--no-cache`. If TS errors, edit src/app/dashboard/page.tsx to add `data={[]}` to GraphViewer. Log to errors.md.

#### Iteration 3: Port Clearing and Service Startup (Core Services)
**Objective**: Clear conflicts and start services incrementally (Postgres, Redis first, then full).

**Steps**:
1. Kill ports: `sudo fuser -k 5432/tcp 6379/tcp 3000/tcp 5678/tcp 11434/tcp 6333/tcp 7474/tcp 9000/tcp 8080/tcp || true`.
2. Reset: `docker compose down -v` (clears volumes).
3. Start core: `docker compose up -d postgres redis` (wait 30s).
4. Full start: `./scripts/start-all-services.sh` (or `docker compose up -d --build` if script fails).
5. Wait: `sleep 60` (for health).

**Success Criteria**:
- `docker compose ps` shows postgres/redis Up (status "Up").
- No port warnings in output.
- `docker logs postgres` shows "database system is ready".

**Error Handling**: If bind fails (e.g., "address in use"), rerun kill. If env warnings (e.g., GRAYLOG_PASSWORD_SECRET), add to .env: `echo "GRAYLOG_PASSWORD_SECRET=$(openssl rand -hex 32)" >> .env`. Retry iteration. Log to errors.md.

#### Iteration 4: Test Validation (Unit and Integration)
**Objective**: Run tests to validate setup (env, build, health).

**Steps**:
1. Backend unit: `source .venv/bin/activate && pytest tests/ -v` (expect 20+/22 pass, no errors).
2. Frontend unit: `cd frontend && npm test` (expect 100% pass).
3. Integration: `pytest tests/ -v -m integration` (expect pass if services up).
4. Coverage: `pytest --cov=tests --cov-report=term-missing` (>80% on executed).

**Success Criteria**:
- Pytest: 20+/22 pass, no ImportErrors/skips (or <2 skips for optional).
- Jest: All pass (6/6).
- Coverage: >80% (ignore "no data" if no imports).

**Error Handling**: If pytest fails (e.g., "No module named"), install via uv pip. If Jest fails (e.g., "module not found"), rerun npm install. If integration skips, check Iteration 3. Log to errors.md.

#### Iteration 5: Health Check and Final Validation
**Objective**: Confirm all services healthy and end-to-end.

**Steps**:
1. Health: `./scripts/health-check.sh --check-all` (expect all ✅, e.g., Supabase "OK", n8n healthy).
2. Logs: `docker compose logs -f` (no errors in last 1min).
3. End-to-End: `curl http://localhost:8000/health` (Supabase OK); `curl http://localhost:5678/healthz` (n8n OK).
4. Reports: `./scripts/generate_reports.py` (generates health.json without errors).

**Success Criteria**:
- Health check: All services ✅ (Traefik accessible, no "unhealthy").
- Curl: Return codes 0, expected responses (e.g., "OK" for Supabase).
- No restarts in logs (`docker compose logs | grep "restarting"` empty).

**Error Handling**: If service down (e.g., Traefik 000000), check logs (`docker logs traefik`), fix env (e.g., JWT via `./fix-jwt-problem.sh`), retry Iteration 3. Log to errors.md.

#### Completion and Maintenance
- **Full Success**: All iterations pass → Deployment ready. Run `docker compose up -d` for production.
- **Ongoing**: For updates, rerun Iteration 3+ after changes. Monitor with Grafana (localhost:3003).
- **Rollback**: If fail, `docker compose down -v` and retry from Iteration 1.

Reference `docs/errors.md` for past fixes. If stuck, share output for iteration-specific help.
