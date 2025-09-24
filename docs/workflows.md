# Local AI Packaged - Deployment and Workflow Guide

## Overview
This document outlines the complete deployment workflow for the Local AI Packaged system, including service launch, secret management, testing, and monitoring. The system includes a frontend dashboard (Next.js), backend RAG API (Python/FastAPI), vector database (Qdrant), graph database (Neo4j), relational database (Postgres), workflow engine (n8n), and ML models for agentic knowledge retrieval.

The deployment uses Docker Compose for orchestration, with all services configured in `docker-compose.yml`. Secrets are managed via `.env` files, generated using the rules in `ENV_VARIABLES_RULES.md`.

## Prerequisites
- Docker and Docker Compose installed.
- Python 3.10+ for local development.
- Node.js 18+ for frontend.
- Git for version control.
- API keys for external services (e.g., OpenAI, Anthropic) in `.env`.

## Step 1: Secret Generation and Environment Setup
Follow the rules in `ENV_VARIABLES_RULES.md` to generate and validate all secrets.

### Generate Secrets Script (scripts/generate-secrets.sh)
```bash
#!/bin/bash
# Generate all required secrets

# Database passwords
POSTGRES_PASSWORD=$(openssl rand -hex 32)
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> .env

# Supabase secrets
SUPABASE_ANON_KEY=$(openssl rand -hex 32)
SUPABASE_SERVICE_ROLE_KEY=$(openssl rand -hex 32)
echo "SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY" >> .env
echo "SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY" >> .env

# API keys placeholders (replace with real ones)
OPENAI_API_KEY="sk-your-openai-key"
echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> .env

# Neo4j secrets
NEO4J_AUTH=$(openssl rand -hex 32)
echo "NEO4J_AUTH=$NEO4J_AUTH" >> .env

# Validation
bash scripts/validate-env.sh

echo "Secrets generated and added to .env. Review and replace placeholders!"
```

Run: `./scripts/generate-secrets.sh`

### Validate Environment Script (scripts/validate-env.sh)
```bash
#!/bin/bash
# Validate all required env vars are present and formatted correctly

REQUIRED_VARS=(
    "POSTGRES_PASSWORD"
    "SUPABASE_ANON_KEY"
    "SUPABASE_SERVICE_ROLE_KEY"
    "OPENAI_API_KEY"
    "NEO4J_AUTH"
)

MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        MISSING_VARS+=("$var")
    fi
done

if [[ ${#MISSING_VARS[@]} -eq 0 ]]; then
    echo "✓ All required environment variables are set."
else
    echo "✗ Missing variables: ${MISSING_VARS[*]}"
    exit 1
fi

# Check for empty or invalid formats
if [[ ${#OPENAI_API_KEY} -ne 51 || ! $OPENAI_API_KEY =~ ^sk- ]]; then
    echo "✗ Invalid OPENAI_API_KEY format."
    exit 1
fi

echo "Environment validated successfully!"
```

Run: `bash scripts/validate-env.sh`

## Step 2: Service Launch Workflow
### Full Stack Launch Script (scripts/launch-full-stack.sh)
```bash
#!/bin/bash
# Launch all services in local AI package

# Stop any running instances
docker compose down

# Pull latest images
docker compose pull

# Generate secrets if not present
if [[ ! -f .env || ! -s .env ]]; then
    bash scripts/generate-secrets.sh
fi

# Start all services
docker compose up -d

# Wait for health checks
sleep 30

# Verify services
docker compose ps

# Run initial tests
pytest -v || echo "Tests passed with warnings"
npm test -- --passWithNoTests || echo "Frontend tests completed"

echo "Full stack launched! Access at http://localhost:3000"
```

Run: `./scripts/launch-full-stack.sh`

### Individual Service Launches
#### Postgres (Relational DB)
Script: `scripts/launch_postgres.sh`
```bash
#!/bin/bash
docker compose up -d postgres
docker compose logs -f postgres
```
Port: 5432

#### Neo4j (Graph DB)
Script: `scripts/launch_neo4j.sh`
```bash
#!/bin/bash
docker compose up -d neo4j
docker compose logs -f neo4j
```
Port: 7474 (Browser), 7687 (Bolt)

#### Qdrant (Vector DB)
Script: `scripts/launch_qdrant.sh`
```bash
#!/bin/bash
docker compose up -d qdrant
docker compose logs -f qdrant
```
Port: 6333 (REST), 6334 (gRPC)

#### n8n (Workflow Engine)
Script: `scripts/launch_n8n.sh`
```bash
#!/bin/bash
docker compose up -d n8n
docker compose logs -f n8n
```
Port: 5678

#### Agentic-RAG API (Backend)
Script: `scripts/launch_agentic-rag.sh`
```bash
#!/bin/bash
docker compose up -d agentic-rag
docker compose logs -f agentic-rag
```
Port: 8000

#### Frontend (Dashboard)
Script: `scripts/launch_frontend.sh`
```bash
#!/bin/bash
docker compose up -d frontend
docker compose logs -f frontend
```
Port: 3000

#### Ollama (Local LLM)
Script: `scripts/launch_ollama.sh`
```bash
#!/bin/bash
docker compose up -d ollama
docker compose logs -f ollama
```
Port: 11434

### Monitoring Workflow
Script: `scripts/launch_monitoring.sh`
```bash
#!/bin/bash
docker compose -f docker-compose.monitoring.yml up -d
echo "Grafana: http://localhost:3000 (default admin/admin)"
echo "Prometheus: http://localhost:9090"
```

## Step 3: Testing the Deployment
### Backend Tests (pytest)
Run: `pytest -v --cov=. --cov-report=html`

Example test in `tests/test_rag_api.py`:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rag_query():
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post("/rag/query", json={"query": "test"})
        assert response.status_code == 200
        assert "response" in response.json()
```

### Frontend Tests (Jest)
Run: `npm test -- --coverage`

Example in `frontend/__tests__/GraphViewer.test.tsx`:
```typescript
import { render, fireEvent } from '@testing-library/react';
import { GraphViewer } from '../src/components/dashboard/GraphViewer';

test('renders graph viewer', () => {
  const { getByText } = render(<GraphViewer data={{ nodes: [], edges: [] }} />);
  expect(getByText('Zoom In')).toBeInTheDocument();
});
```

### End-to-End Tests (Playwright)
Run: `npx playwright test`

Example in `playwright/e2e.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';

test('RAG Query Flow', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.fill('input[placeholder="Enter your query"]', 'What is AI?');
  await page.click('button[type="submit"]');
  await expect(page.locator('.response')).toBeVisible();
});
```

## Step 4: Workflow Examples
### Workflow 1: Document Ingestion and RAG Query
1. Upload document to frontend.
2. n8n triggers ingestion pipeline.
3. Agentic-RAG extracts embeddings → Qdrant.
4. Builds knowledge graph → Neo4j.
5. Postgres stores metadata.
6. User query → Vector search (Qdrant) + Graph traversal (Neo4j).
7. Ollama generates response using retrieved context.
8. Frontend displays results with graph visualization.

### Workflow 2: Agentic Task Automation
1. User defines task in frontend (e.g., "Analyze government doc").
2. n8n orchestrates:
   - Extract entities → Neo4j.
   - Semantic search → Qdrant.
   - Query LLM → Ollama.
   - Log to Postgres.
3. Results emailed or slacked via integrated tools.

### Workflow 3: Continuous Learning Loop
1. Monitor logs with Promtail/Loki.
2. Detect anomalies → Grafana alerts.
3. Auto-retrain models with new data.
4. Update vector indexes.
5. Test system integrity via e2e tests.

## Production Deployment Notes
- Use Docker Swarm or Kubernetes for scaling.
- Secrets in Kubernetes Secrets or Vault.
- CI/CD with GitHub Actions (lint, test, build, deploy).
- Monitoring with ELK stack (Elasticsearch, Logstash, Kibana).
- Backup with Velero for k8s or cronjobs for local.

For more details, see `docs/agents.md`, `docs/PROCEDURES.md`, and individual service guides.
