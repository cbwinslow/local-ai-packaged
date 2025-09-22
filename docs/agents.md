# Agents Documentation

## Testing and Monitoring

### Unit Testing with pytest
All Python services use pytest for unit testing. To run tests:

1. Install dev dependencies:
```bash
pip install -e '.[dev]'
```

2. Run unit tests:
```bash
pytest tests/unit -v
```

3. Run with coverage:
```bash
pytest --cov=.
```

### Integration Testing
Integration tests are located in `tests/integration/`. These test API endpoints and database connections.

Run with:
```bash
pytest tests/integration -v
```

### End-to-End Testing
E2E tests use Playwright for frontend flows and async HTTP clients for backend. Run with:
```bash
pytest tests/e2e -v
```

All tests achieve 80%+ coverage requirement.

### Jest Testing for Frontend
Frontend uses Jest for component testing.

1. Install:
```bash
cd frontend && npm install
```

2. Run tests:
```bash
npm test
```

3. Run with coverage:
```bash
npm test -- --coverage
```

### Monitoring Configuration
All services have LOG_LEVEL=DEBUG in .env. Logs are mounted to `./logs` volume.

- **Promtail** in the monitoring stack scrapes logs from services.
- **Loki** stores logs for querying.
- **Grafana** has dashboards for:
  - Service health
  - API response times
  - Database connections
  - Resource usage

- **Sentry** is integrated for error tracking with DSN from .env.
- **Logflare** for Supabase analytics.

### Service Launch and Testing
Use individual scripts in `scripts/` to launch services:

- `./scripts/launch_postgres.sh`
- `./scripts/launch_n8n.sh`
- `./scripts/launch_ollama.sh`
- `./scripts/launch_frontend.sh`
- `./scripts/launch_agentic-rag.sh`
- `./scripts/launch_qdrant.sh`
- `./scripts/launch_neo4j.sh`
- `./scripts/launch_graylog.sh`
- `./scripts/launch_rabbitmq.sh`
- `./scripts/launch_localai.sh`
- `./scripts/launch_supabase.sh`
- `./scripts/launch_monitoring.sh`

Each script handles dependencies and exposes ports appropriately.

### Verification
Run full testing suite after launch:
```bash
pytest
npm test

# Check coverage reports in coverage/html
# View in Grafana at localhost:3000
# Check Sentry for errors
```

### Troubleshooting
- Check logs in `./logs` with `tail -f logs/*`
- Use `docker compose logs -f` for running services
- Frontend logs via browser dev tools
- Database logs via service-specific commands
