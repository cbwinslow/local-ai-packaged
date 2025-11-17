# Local AI Package - Complete Services Inventory

## All Available Services

### Core AI Services
1. **n8n** - Workflow automation platform
   - Internal: http://n8n:5678
   - External: https://n8n.cloudcurio.cc
   - Purpose: Visual workflow automation

2. **Ollama** - Local LLM serving
   - Internal: http://ollama:11434
   - External: https://ollama.cloudcurio.cc
   - Purpose: Run local Large Language Models

3. **Open WebUI** - Chat interface
   - Internal: http://open-webui:8080
   - External: https://openwebui.cloudcurio.cc
   - Purpose: Chat interface for LLMs

4. **Flowise** - AI agent builder
   - Internal: http://flowise:3001
   - External: https://flowise.cloudcurio.cc
   - Purpose: Visual AI agent builder

### Database & Storage Services
5. **Supabase** - Backend-as-a-Service
   - Components: auth, db, storage, real-time, functions, analytics
   - Internal: http://kong:8000 (gateway)
   - External: https://supabase.cloudcurio.cc
   - Purpose: Database, authentication, storage

6. **Qdrant** - Vector database
   - Internal: http://qdrant:6333
   - External: https://qdrant.cloudcurio.cc
   - Purpose: Vector similarity search

7. **Neo4j** - Graph database
   - Internal: http://localai-neo4j-1:7474
   - External: https://neo4j.cloudcurio.cc
   - Purpose: Graph-based data storage

8. **PostgreSQL** - Relational database
   - Internal: http://localai-postgres-1:5432
   - Purpose: Primary relational database

### Specialized Services
9. **SearXNG** - Privacy-respecting meta search engine
   - Internal: http://searxng:8080
   - External: https://searxng.cloudcurio.cc
   - Purpose: Privacy-focused search aggregation

10. **Langfuse** - LLM engineering platform
    - Internal: http://langfuse-web:3000
    - External: https://langfuse.cloudcurio.cc
    - Purpose: Observability for LLM operations

11. **MinIO** - Object storage
    - Internal: http://localai-minio-1:9000
    - Purpose: S3-compatible object storage

12. **ClickHouse** - Analytics database
    - Internal: http://localai-clickhouse-1:8123
    - Purpose: Analytics and observability backend

### Supporting Services
13. **Redis/Valkey** - In-memory data store
    - Internal: http://redis:6379
    - Purpose: Caching and session storage

14. **Kong** - API Gateway
    - Internal: http://kong:8000
    - Purpose: API management for Supabase

### Current Status
- **Running**: n8n, Ollama, Open WebUI, Flowise, Qdrant, Neo4j, SearXNG, Supabase components
- **Configured**: Langfuse, MinIO, ClickHouse, PostgreSQL, Redis
- **Accessible**: All services configured in Cloudflare Tunnel DNS routes

### Port Mappings (Internal)
- n8n: 5678
- open-webui: 8080
- ollama: 11434
- flowise: 3001
- qdrant: 6333/6334
- localai-neo4j-1: 7474/7473/7687
- searxng: 8080
- langfuse-web: 3000
- kong: 8000 (part of Supabase)
- postgres: 5432
- minio: 9000/9001
- clickhouse: 8123/9000
- redis: 6379

## Cloudflare Tunnel Access Points
All services are now accessible via HTTPS through the Cloudflare Tunnel:
- All cloudcurio.cc subdomains route through the tunnel
- SSL termination handled by Cloudflare
- Direct access bypasses the port conflicts on 80/443