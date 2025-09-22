# Workflows Documentation

## Local AI Package Complete Deployment Workflow

### Overview
This workflow covers the complete setup, secret generation, service launch, testing, and monitoring of the Local AI Package.

### Prerequisites
- Docker and Docker Compose installed
- Git repository cloned
- Basic system with 16GB+ RAM, 8+ CPU cores recommended
- GPU (optional) for Ollama

### 1. Environment Setup and Secret Generation

#### Steps
1. **Clone Repository**
```bash
git clone https://github.com/cbwinslow/local-ai-packaged.git
cd local-ai-packaged
```

2. **Generate Secrets**
```bash
bash scripts/generate-secrets.sh
```

3. **Validate Environment**
```bash
bash scripts/validate-env.sh
```

4. **Backup Project**
```bash
./backup-restore.sh backup
```

### 2. Service Initialization

#### Steps
1. **Start Database Services**
```bash
# Postgres
./scripts/launch_postgres.sh

# Optionally start Supabase if needed
./scripts/launch_supabase.sh
```

2. **Start Vector and Graph Databases**
```bash
# Qdrant
./scripts/launch_qdrant.sh

# Neo4j
./scripts/launch_neo4j.sh
```

3. **Start Message Queue and Workflow Engines**
```bash
# RabbitMQ
./scripts/launch_rabbitmq.sh

# N8N
./scripts/launch_n8n.sh

# Flowise (optional)
./scripts/launch_flowise.sh
```

4. **Start AI Inference Services**
```bash
# Ollama with Qwen
./scripts/launch_ollama.sh
```

5. **Start Core API Services**
```bash
# Agentic RAG API
./scripts/launch_agentic-rag.sh

# LocalAI (alternative inference)
./scripts/launch_localai.sh
```

6. **Start Frontend and UI Services**
```bash
# Frontend
./scripts/launch_frontend.sh

# Dashboard
./scripts/launch_dashboard.sh

# Docs Website
./scripts/launch_docs-website.sh
```

7. **Start Search Services**
```bash
# SearxNG
./scripts/launch_searxng.sh
```

8. **Start Monitoring Stack**
```bash
./scripts/launch_monitoring.sh
```

9. **Start Logging and Analytics**
```bash
# Graylog
./scripts/launch_graylog.sh

# Sentry (if configured)
./scripts/launch_sentry.sh
```

### 3. Data Ingestion Workflow

#### Purpose
Load documents into the RAG system for querying.

#### Steps
1. **Document Upload**
   - Use frontend upload interface or API endpoint `/upload`
   - Supported formats: PDF, DOCX, TXT, CSV

2. **Preprocessing Pipeline**
   - **Format Detection**: Determine document type
   - **OCR (if PDF scanned)**: Extract text using Tesseract
   - **Text Extraction**: Parse content using dedicated parsers
   - **Cleaning**: Remove headers, footers, page numbers

3. **Chunking and Embedding**
   - **Semantic Chunking**: Split into 512-token chunks with overlap
   - **Embedding Generation**: Use embedding model (local or API)
   - **Metadata Extraction**: Pull titles, dates, categories

4. **Storage**
   - **Vector Storage**: Store embeddings in Qdrant
   - **Graph Storage**: Build entity-relationship graph in Neo4j
   - **Metadata Storage**: Save metadata in Postgres
   - **Index Update**: Update search indexes in OpenSearch

5. **Indexing**
   - **Full-text Index**: Index text for keyword search
   - **Vector Index**: Create HNSW index for similarity search
   - **Graph Index**: Optimize Neo4j schema indexes

6. **Notification**
   - Send success notification via N8N/Slack
   - Update document status in dashboard

### 4. RAG Query Workflow

#### Purpose
Process user queries using retrieval-augmented generation.

#### Steps
1. **Query Reception**
   - User submits query via frontend form or API
   - Query logged to Loki for analytics

2. **Query Enhancement**
   - **Query Analysis**: Determine intent and keywords
   - **Rewriting**: Expand query for better recall
   - **Multi-modal**: Handle text + image queries if enabled

3. **Retrieval Phase**
   - **Vector Search**: Query Qdrant for top-K similar chunks (K=5)
   - **Graph Traversal**: Find related entities in Neo4j
   - **Metadata Filter**: Apply user permissions, date ranges
   - **Ranking**: Re-rank results using hybrid scoring
   - **Diversity**: Ensure diverse source distribution

4. **Context Building**
   - **Context Assembly**: Combine vector results + graph context
   - **Relevance Scoring**: Weight sources by freshness/recency
   - **Prompt Construction**: Format context for LLM (max 8k tokens)
   - **Safety Check**: Filter out sensitive content

5. **Generation Phase**
   - **Model Selection**: Route to appropriate LLM (Qwen, GPT, etc.)
   - **Prompt Execution**: Send to Ollama/LocalAI with streaming
   - **Response Processing**: Stream tokens to frontend
   - **Citation Generation**: Map response to source documents
   - **Quality Check**: Validate response coherence

6. **Post-processing**
   - **Response Enhancement**: Add citations, suggestions
   - **Fact Verification**: Cross-check with graph knowledge
   - **Logging**: Record query/response latency, token usage
   - **Feedback Loop**: Store interaction for model fine-tuning

7. **Response Delivery**
   - Return formatted response to frontend
   - Include source citations for transparency
   - Update conversation history in user session

### 5. Monitoring and Observability Workflow

#### Purpose
Continuous monitoring of system health and performance.

#### Steps
1. **Metrics Collection**
   - **Prometheus**: Scrape metrics from all services every 15s
   - **Node Exporters**: Monitor host CPU, memory, disk
   - **Custom Metrics**: Service-specific metrics (request latency, error rates)

2. **Log Aggregation**
   - **Promtail**: Tail Docker container logs to Loki
   - **Structured Logging**: All services use JSON format
   - **Pattern Extraction**: Identify common error patterns
   - **Retention Policy**: 14 days rolling retention

3. **Alerting**
   - **Prometheus Rules**: Define alerts for high CPU (>80%), low available memory
   - **Sentry**: Capture exceptions from services
   - **Uptime Kuma**: Monitor service availability (HTTP/TCP)
   - **Slack Integration**: Notify on-call team via N8N workflow

4. **Dashboard Visualization**
   - **Grafana**: Real-time dashboards for:
     - Service response times (P95, P99)
     - Error rates by service
     - Database connection pool usage
     - GPU memory usage for Ollama
     - Queue length for RabbitMQ
   - **Heat Maps**: Identify performance bottlenecks
   - **Correlations**: Link metrics to application performance

5. **Automated Actions**
   - **Auto-scaling**: Restart services exceeding thresholds
   - **Backup Triggers**: Automated backups on error spikes
   - **Anomaly Detection**: ML-based detection of unusual patterns
   - **Health Checks**: Docker healthcheck integration

### 6. Security Audit Workflow

#### Purpose
Regular security validation and vulnerability scanning.

#### Steps
1. **Secret Rotation**
   - Run `bash scripts/generate-secrets.sh` monthly
   - Update all services with new secrets
   - Test service restarts with new credentials

2. **Vulnerability Scanning**
   - **Trivy**: Scan Docker images for vulnerabilities
   - **NPM Audit**: Check frontend dependencies
   - **Bandit**: Static analysis for Python code
   - **ESLint**: Security rules for JavaScript/TypeScript

3. **Access Control**
   - **Supabase Row Level Security**: Verify RLS policies
   - **API Rate Limiting**: Check rate limit configurations
   - **JWT Validation**: Ensure token expiry and signing
   - **CORS Policies**: Validate origin restrictions

4. **Network Security**
   - **Firewall Rules**: Verify exposed ports and services
   - **HTTPS Enforcement**: Check SSL certificate status
   - **Network Segmentation**: Docker network isolation
   - **API Key Rotation**: External service key rotation

5. **Compliance Check**
   - **Data Privacy**: Verify PII handling and encryption
   - **Audit Logs**: Ensure all access logged
   - **Backup Encryption**: Validate backup security
   - **Disaster Recovery**: Test restore procedures

### 7. CI/CD Pipeline Workflow

#### Purpose
Automated testing and deployment workflow.

#### Steps
1. **Code Push Trigger**
   - GitHub webhook triggers CI on push/PR
   - Lint all code with ESLint/Ruff/Black

2. **Test Suite Execution**
   - **Unit Tests**: pytest/np.test (80%+ coverage)
   - **Integration Tests**: Service-to-service API calls
   - **E2E Tests**: Playwright for full user flows
   - **Load Testing**: Artillery for performance

3. **Security Scanning**
   - **Dependency Check**: Safety for Python, npm audit for JS
   - **Static Analysis**: Bandit/SonarQube
   - **Container Scan**: Trivy on Docker images

4. **Build and Package**
   - **Docker Build**: Multi-stage builds for optimization
   - **Image Scanning**: Security vulnerability check
   - **Artifact Publishing**: Publish to GHCR

5. **Staging Deployment**
   - **Staging Environment**: Deploy to staging stack
   - **Smoke Tests**: Basic functionality verification
   - **Performance Tests**: Load testing on staging

6. **Production Deployment**
   - **Blue-Green Deployment**: Zero-downtime rollout
   - **Rollout Monitoring**: Watch metrics during deploy
   - **Rollback Capability**: Automated rollback if issues

7. **Post-Deployment**
   - **Health Checks**: Verify all services healthy
   - **Performance Baseline**: Establish new baselines
   - **Release Notes**: Generate and publish changelog

### 8. Backup and Recovery Workflow

#### Purpose
Ensure data durability and disaster recovery.

#### Steps
1. **Scheduled Backups**
   - Run daily incremental backups to volume storage
   - Weekly full backups with encryption
   - Monthly complete system snapshots

2. **Continuous Data Replication**
   - Postgres: WAL archiving to secondary storage
   - Qdrant: Collection snapshots
   - Neo4j: Graph dump every 6 hours

3. **Recovery Testing**
   - Quarterly disaster recovery drills
   - Test restore from incremental + full backup
   - Verify RTO < 4 hours, RPO < 1 hour

4. **Backup Validation**
   - Verify backup integrity with checksums
   - Test random restore operations
   - Monitor backup success rates

### Success Metrics

#### Performance
- **Response Time**: < 3s for 95% of queries
- **Throughput**: 100+ concurrent users
- **Memory Usage**: < 80% system memory
- **Deployment Time**: < 10 minutes full stack

#### Reliability
- **Uptime**: 99.9% service availability
- **Error Rate**: < 1% failed requests
- **Recovery Time**: < 4 hours from disaster
- **Coverage**: 85%+ code coverage

#### Security
- **Secrets Rotation**: Monthly for all services
- **Vulnerability Age**: < 30 days to fix critical
- **Audit Logs**: 100% access logged
- **Compliance**: GDPR/PII handling verified

### Troubleshooting

#### Common Issues
1. **Service Startup Fails**
   - Check logs with `docker compose logs -f service_name`
   - Verify port availability and conflicts
   - Ensure database connections and credentials

2. **RAG Response Quality**
   - Check embedding model accuracy
   - Verify document chunking and indexing
   - Review prompt templates for correctness
   - Test with diverse query types

3. **Monitoring Alerts**
   - High CPU: Check GPU usage for Ollama
   - Database Connections: Monitor pool exhaustion
   - Vector Search Latency: Check Qdrant cluster health
   - Queue Backlog: Monitor RabbitMQ message rates

4. **Deployment Problems**
   - Network issues: Verify Docker network connectivity
   - Volume mounts: Check permissions and paths
   - Resource limits: Adjust Docker resource constraints
   - Certificate issues: Validate SSL/TLS configuration

#### Emergency Recovery
1. **Immediate Actions**
   - Stop all services with `docker compose down`
   - Identify root cause from logs
   - Restore from latest backup if needed

2. **System Recovery**
   - Restart individual services one by one
   - Run health checks for each
   - Verify data integrity post-recovery
   - Update alerting thresholds if needed

3. **Post-Incident**
   - Root cause analysis
   - Update monitoring rules
   - Adjust resource limits
   - Document recovery procedure
