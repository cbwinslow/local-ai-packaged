# Local AI Packaged Platform

Self-hosted RAG platform for legislative analysis using Neo4j, Supabase, Qdrant, n8n, and Ollama.

## Setup

1. Copy `.env.example` to `.env` and fill vars (e.g., passwords, API keys).
2. `make validate` (checks env).
3. `make ci-local` (lint/test/build).
4. `make deploy` (starts services: frontend:3000, backend:8000, Neo4j:7474, etc.).

## RAG Usage

- Ingest: POST /rag/ingest {"file_path": "sample_bill.txt"} (embeds to Qdrant, entities to Neo4j).
- Query: POST /rag/query {"query": "Analyze Bill X"} (hybrid retrieval + CrewAI analysis).
- UI: http://localhost:3000/rag (sign in, submit queries).

## K8s Migration

1. Install k3s: curl -sfL https://get.k3s.io | sh -
2. kompose convert -f docker-compose.yml (generates k8s/).
3. kubectl apply -f k8s/ (deploys backend/frontend).

## Testing

- `make test` (pytest/Jest/E2E).
- Launch scripts: ./scripts/launch_postgres.sh (individual services).

For issues: Check docker logs; extend with n8n workflows for data ingestion.