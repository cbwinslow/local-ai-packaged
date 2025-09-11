# Local AI Package - Project Context

## Project Overview

This repository provides a self-hosted AI and low-code development environment using Docker Compose. It combines several open-source tools to create a comprehensive platform for building and running AI workflows locally:

- **AI Model Management**: Ollama for running local LLMs
- **Workflow Automation**: n8n for visual workflow building
- **Monitoring & Observability**: Prometheus, Grafana, and OpenSearch
- **Knowledge Graph**: Neo4j for advanced data relationships
- **Vector Search**: Qdrant vector database
- **Database & Auth**: Supabase (PostgreSQL-based)
- **Agent Memory**: Neo4j Agent Memory for graph-based memory
- **RAG Tools**: GraphRAG-SDK, LightRAG, MCP Crawl4AI RAG

The project is designed to be a starter kit for developers to experiment with self-hosted AI agents and workflows, combining robust components that work well together for proof-of-concept projects.

## Key Technologies & Services

### Core Services
1. **n8n**: Low-code workflow automation platform
2. **Supabase**: Open-source Firebase alternative (PostgreSQL, auth, vector storage)
3. **Ollama**: Cross-platform LLM runtime
4. **Open WebUI**: ChatGPT-like interface for local models
5. **Flowise**: Visual AI agent builder
6. **Qdrant**: High-performance vector database
7. **Neo4j**: Graph database for knowledge graphs
8. **SearXNG**: Privacy-focused metasearch engine
9. **Caddy**: Web server with automatic HTTPS
10. **Langfuse**: LLM engineering platform for observability

### MCP (Model Context Protocol) Services
1. **Congress.gov MCP Server**: Access to U.S. legislative data
2. **Neo4j Agent Memory MCP**: Graph-based memory system
3. **Memgraph**: Alternative high-performance graph database
4. **FalkorDB**: Redis-based graph database
5. **Vectorize MCP Server**: Vectorization service
6. **PluggedIn MCP**: MCP manager
7. **StackHawk MCP**: Security scanning service

### Monitoring Stack
1. **Prometheus**: Metrics collection
2. **Grafana**: Visualization dashboard
3. **OpenSearch**: Log aggregation
4. **Loki**: Log aggregation system
5. **Tempo**: Distributed tracing

## Development Environment

### Prerequisites
- Python 3.10
- UV package manager
- Docker and Docker Compose
- Node.js 18+ (for frontend development)

### Setup Process
1. Clone the repository
2. Create a Python virtual environment with UV:
   ```bash
   uv venv .venv --python=3.10
   source .venv/bin/activate
   uv pip install -r requirements-dev.txt
   ```
3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Running the Application

### Environment Setup
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Generate secure secrets using `./fix-supabase-env.sh` or manually with `openssl`
3. For production deployments, set Caddy configuration variables in `.env`

### Starting Services
To start the services, you need to run the `start_services.py` function. However, as there is already data in the database, we should not run it now to avoid conflicts.

The project includes a Python script (`service-manager.py`) to manage core services:
```bash
# Start all services
python3 service-manager.py start

# Stop all services
python3 service-manager.py stop

# Check service status
python3 service-manager.py status
```

For GPU users, use the appropriate profile:
```bash
python3 service-manager.py start --profile gpu-nvidia
```

### AI Tools Management
Use the `ai_tools_manager.sh` script to manage AI services:
```bash
# Start all AI services
./ai_tools_manager.sh start

# Start a specific service (e.g., neo4j)
./ai_tools_manager.sh start neo4j

# Show status of all services
./ai_tools_manager.sh status

# View logs
./ai_tools_manager.sh logs

# Run initial setup
./ai_tools_manager.sh setup
```

## Data Ingestion

### Government Data Ingestion
The project includes a script (`scripts/ingest_government_data.py`) for ingesting government data from various sources:

1. **Congress.gov API**: Ingests bills, members, and votes
2. **Govinfo.gov Bulk Data**: Access to legislative data, government documents, and declassified materials

#### Govinfo.gov Data Sources
The following data collections are available from govinfo.gov:

1. **Legislative Data**:
   - Bills and resolutions
   - Members of Congress
   - Voting records
   - Congressional committee materials

2. **Government Documents**:
   - Executive agency publications
   - Budget and presidential materials
   - Compilation of presidential documents
   - Public papers of the president

3. **Declassified Materials**:
   - President John F. Kennedy Assassination Records Collection
   - Records of the Watergate Special Prosecution Force
   - Independent Counsel Investigations
   - Featured Commission Publications

#### Access Methods
1. **API Access**: Programmatic access through govinfo API
2. **Bulk Data Repository**: Large collections of data available for download
3. **RSS Feeds**: Available for most collections
4. **Link Service**: For constructing predictable links to documents

To ingest approximately 30 years of data from these sources, you would need to:
1. Register for API keys where required
2. Configure the ingestion script with appropriate parameters
3. Run the ingestion process with proper rate limiting
4. Store the data in the Supabase SQL database
5. Vectorize the documents and store them in the Qdrant vector database

## Development Workflow

### Git Workflow
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature branches
- `bugfix/*`: Bug fix branches
- `release/*`: Release preparation branches

### Coding Standards
- **Python**: PEP 8, type hints, Google-style docstrings
- **JavaScript/TypeScript**: Airbnb style guide, TypeScript preferred
- **Git Commits**: Conventional Commits specification

### Testing
- Use pytest for Python testing
- Write unit tests for new functionality
- Run tests with coverage:
  ```bash
  uv run pytest --cov=src tests/
  ```

## Project Structure

The project is organized around Docker Compose services with the following key directories:

- `supabase/`: Supabase configuration and data
- `n8n/`: n8n workflows and credentials
- `neo4j/`: Neo4j configuration and data
- `models/`: Local AI models
- `mcp-servers/`: Model Context Protocol server implementations
- `dashboard/`: Monitoring dashboard application
- `frontend/`: Main frontend application
- `monitoring/`: Monitoring stack configurations
- `docs/`: Project documentation
- `scripts/`: Utility scripts

## Building and Running

### Docker Compose Profiles
The project uses Docker Compose profiles for different hardware configurations:
- `cpu`: CPU-only mode
- `gpu-nvidia`: NVIDIA GPU support
- `gpu-amd`: AMD GPU support
- `none`: No built-in Ollama (for external Ollama)

### Accessing Services
After starting the services, you can access:
- n8n: http://localhost:5678/
- Open WebUI: http://localhost:3000/
- Supabase Studio: http://localhost:54323/
- Neo4j Browser: http://localhost:7474/
- Grafana: http://localhost:3001/
- Prometheus: http://localhost:9090/

### Upgrading Services
To update all containers to their latest versions:
```bash
# Stop all services
docker compose -p localai -f docker-compose.yml --profile <your-profile> down

# Pull latest versions of all containers
docker compose -p localai -f docker-compose.yml --profile <your-profile> pull

# Start services again with your desired profile
python3 service-manager.py start --profile <your-profile>
```

## Security and Configuration

### Secret Management
All secrets should be generated using secure random values:
- Use `./fix-supabase-env.sh` for automated generation
- Or manually generate with `openssl` commands
- Never commit secrets to version control

### Production Deployment
When deploying to production:
1. Set all Caddy configuration variables in `.env`
2. Use the `--environment public` flag with the service manager
3. Configure DNS A records for your subdomains
4. Ensure proper firewall configuration (ufw)

## Troubleshooting

Common issues and solutions are documented in the main README.md:
- Supabase pooler restarting
- Supabase analytics startup failure
- GPU support issues
- SearXNG permissions
- Missing Supabase files

For dependency conflicts:
```bash
# Clean up environment
uv pip freeze | xargs uv pip uninstall -y
uv pip install -r requirements.txt
```

## License

This project is licensed under the Apache License 2.0.