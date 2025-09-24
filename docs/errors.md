# Monitoring, Reports, and Troubleshooting

This guide addresses common errors, monitoring setup, and report generation for the Local AI Package. It expands on Supabase-specific issues to cover the full stack (n8n, Ollama, queues, etc.) and includes monitoring with Grafana/Prometheus/Langfuse.

For service details, see [Services](services.md). For deployment issues, see [Deployment](deployment.md).

## Table of Contents

1. [Common Errors and Solutions](#common-errors-and-solutions)
2. [Monitoring Setup](#monitoring-setup)
3. [Report Generation](#report-generation)
4. [Troubleshooting Tools](#troubleshooting-tools)

## Common Errors and Solutions

### Supabase Errors

- **Pooler Restarting**: Connection pooler crashes.
  - **Cause**: Invalid JWT, env mismatch, or special chars in passwords (e.g., "@").
  - **Solution**: Run `./fix-jwt-problem.sh`; regenerate secrets: `./scripts/generate-secrets.sh`. Clear volumes if needed: `docker compose down -v`.
  - **Verification**: `docker logs supabase-pooler` stable; `curl http://localhost:8000/health` returns OK.

- **Analytics Startup Failure**: Analytics container fails after password change.
  - **Cause**: Cached credentials in DB.
  - **Solution**: `docker compose down -v` to reset volumes, then restart services.
  - **Prevention**: Use Bitwarden for consistent secrets; avoid special chars.

- **Service Unavailable (Kong/Auth)**: API gateway or auth errors.
  - **Cause**: DB not ready or JWT expiration.
  - **Solution**: Restart: `docker compose restart kong auth`; ensure POSTGRES_PASSWORD consistent across .env files.
  - **Verification**: `docker logs supabase-kong` shows requests; `curl -H "apikey: ${ANON_KEY}" http://localhost:8000/rest/v1/ -H "apikey: ${SERVICE_ROLE_KEY}" http://localhost:8000/rest/v1/rpc/admin/`.

- **Realtime Unhealthy**: WebSocket service issues.
  - **Cause**: DB encryption key mismatch.
  - **Solution**: Verify DB_ENC_KEY in .env; restart realtime: `docker compose restart realtime`.

### n8n Errors

- **Workflow Import Fails**: Credentials or workflows not loading.
  - **Cause**: Invalid DB connection or missing files in ./n8n/backup.
  - **Solution**: Restart n8n-import: `docker compose restart n8n-import`; check logs: `docker logs n8n-import`.
  - **Verification**: In n8n UI (http://localhost:5678), workflows are listed.

- **Webhook Not Triggering**: File triggers or webhooks fail.
  - **Cause**: Shared volume not mounted or webhook URL wrong.
  - **Solution**: Ensure `./shared` exists; set WEBHOOK_URL=http://localhost:5678 in .env; restart n8n.
  - **Verification**: `curl -X POST http://localhost:5678/webhook/test -d '{}'`.

### Ollama Errors

- **Model Pull Fails**: Models not downloading.
  - **Cause**: Network or storage issues.
  - **Solution**: Manual pull: `docker exec ollama ollama pull qwen2.5:7b-instruct-q4_K_M`.
  - **Verification**: `docker exec ollama ollama list` shows models.

- **GPU Not Used**: Inference on CPU despite GPU profile.
  - **Cause**: Docker GPU not enabled or drivers missing.
  - **Solution**: Verify `nvidia-smi`; restart with `--profile gpu-nvidia`; fallback to cpu.
  - **Verification**: `docker exec ollama nvidia-smi` (GPU profile).

### Queue and Worker Errors

- **Tasks Stuck in Pending**: Workers not processing.
  - **Cause**: Worker not running or DB lock timeout.
  - **Solution**: Start worker: `python scripts/worker.py --task-types bill_ingest`; check RabbitMQ UI (http://localhost:15672) for queue depth.
  - **Verification**: `docker exec postgres psql -U postgres -c "SELECT COUNT(*) FROM tasks WHERE status = 'pending';"`.

- **Dead Letter Queue**: Persistent failures.
  - **Cause**: Max retries exceeded.
  - **Solution**: Query failed tasks: `SELECT * FROM tasks WHERE status = 'failed' ORDER BY updated_at DESC;`; manual retry or cleanup.
  - **Verification**: Worker logs: `python scripts/worker.py --log-level DEBUG`.

### General Errors

- **Port Conflicts**: Service fails to bind.
  - **Solution**: `./scripts/port-conflict-resolver.sh resolve`; or manual `lsof -i :5432` and kill conflicting processes.
  - **Verification**: `docker compose ps` shows no conflicts.

- **Volume Permissions**: Data not persisting.
  - **Cause**: Docker user lacks write access.
  - **Solution**: `sudo chown -R $USER:$USER volumes/`; restart.
  - **Verification**: Create test file in `./shared`, restart, check if persists.

- **Memory Issues**: Ollama or workers OOM.
  - **Solution**: Increase limits in docker-compose.yml (e.g., memory: 4G for ollama); use smaller models.
  - **Verification**: `docker stats` shows RAM < limits.

## Monitoring Setup

The stack includes built-in monitoring for performance and debugging.

### Grafana/Prometheus

1. **Start**: Included in start-all-services.sh (ports 3003/9090 private).
   - Config: prometheus.yml scrapes n8n, ollama, rabbitmq metrics.

2. **Access**: http://localhost:3003 (admin/admin).
3. **Dashboards**:
   - **Service Health**: Up/down status, response times.
   - **Resource Usage**: CPU/RAM per container (docker stats exporter).
   - **Queue Depth**: RabbitMQ queue lengths (prometheus-rabbitmq-exporter if added).
   - **DB Metrics**: Postgres connections, query times (postgres_exporter).
   - **AI Metrics**: Ollama inference latency, model loads.

4. **Setup Custom Dashboards**:
   - Import JSON from community (e.g., n8n dashboard).
   - Add panels: Add data source (Prometheus:9090), query `up{job="n8n"}` for uptime.

### Langfuse

- **Purpose**: LLM observability (traces, spans for n8n agents).
- **Access**: http://localhost:3004 (init user from .env or default).
- **Integration**: n8n nodes send traces automatically; view traces for RAG queries.
- **Metrics**: Request latency, token usage, error rates for Ollama calls.

### Reports

Generated by scripts in `./reports/`; run via cron for scheduled.

- **docker_status.py**: Container health/status.
  ```bash
  python reports/docker_status.py  # JSON output
  ```

- **system_health.py**: System resources (CPU, RAM, disk).
  ```bash
  python reports/system_health.py --output json > health.json
  ```

- **network_monitor.py**: Network connectivity between services.
  ```bash
  python reports/network_monitor.py
  ```

- **generate_reports.py**: Full suite (health, network, queue stats).
  ```bash
  python scripts/generate_reports.py  # Outputs to reports/generated/
  ```

- **trivy-scan.md**: Security scan results (run `trivy image --exit-code 0 --no-progress --format markdown . > reports/trivy-scan.md`).
- **yaml_validate.py**: Config validation.

View reports in `./reports/generated/` (JSON, Markdown, TXT). Integrate with Grafana for dashboards.

### Log Aggregation

- **Docker Logs**: `docker compose logs -f <service>` for real-time.
- **Graylog**: http://localhost:9000 (admin/admin); GELF input for services.
- **Loki** (extensions): Scrapes logs; query in Grafana.

## Troubleshooting Tools

- **health-check.sh**: Overall system health (curl/psql/redis-cli).
  ```bash
  ./scripts/health-check.sh --check-all
  ```

- **validate_env.sh**: Env var validation.
- **reports/docker_status.py**: Container status.
- **docker compose ps/logs**: Service-specific.

Common workflow:
1. Run `./scripts/health-check.sh`.
2. Check Grafana (3003) for metrics.
3. View Langfuse traces for AI issues.
4. Query DB: `docker exec postgres psql -U postgres -c "SELECT * FROM tasks WHERE status = 'failed';"`.

For persistent issues, see individual service logs or [Services](services.md).

This ensures reliable monitoring and quick error resolution for production use.