# AI Tools Integration

This document provides an overview of the AI tools and services that have been integrated into the project.

## Available Services

1. **Graphite** - Metrics and monitoring dashboard
   - Access: http://localhost:8080
   - Data storage: `./graphite/`

2. **libSQL** - mcp-memory-libsql service
   - Access: http://localhost:8081
   - Data storage: `./libsql_data/`

3. **Neo4j** - Graph database for mcp-neo4j-agent-memory
   - Access: http://localhost:7474
   - Data storage: `./neo4j/`

4. **CrewAI** - Agent orchestration framework
   - Access: http://localhost:8000
   - Configuration: `./crewai/`

5. **Letta** - Memory system for agents
   - Access: http://localhost:8001
   - Data storage: `./letta_data/`

6. **Falkor** - High-performance database
   - Access: redis://localhost:6379
   - Data storage: `./falkor_data/`

7. **GraphRAG-SDK** - Graph-based retrieval augmented generation
   - Access: http://localhost:8002
   - Data storage: `./graphrag_data/`

8. **Llama Stack** - LLM application framework
   - Access: http://localhost:8003
   - Data storage: `./llama_data/`

9. **MCP Crawl4AI RAG** - Web crawling and RAG pipeline
   - Access: http://localhost:8004
   - Data storage: `./crawl4ai_data/`

## Management Scripts

### AI Tools Manager (`ai_tools_manager.sh`)

A simple CLI to manage all AI services:

```bash
# Start all services
./ai_tools_manager.sh start

# Start a specific service
./ai_tools_manager.sh start neo4j

# Stop all services
./ai_tools_manager.sh stop

# Show status of all services
./ai_tools_manager.sh status

# Show logs for all services
./ai_tools_manager.sh logs

# Run initial setup
./ai_tools_manager.sh setup
```

### Python Integration Script (`ai_tools_integration.py`)

A Python script for programmatic management of AI tools:

```bash
# Setup all tools
python3 ai_tools_integration.py setup

# Setup a specific tool
python3 ai_tools_integration.py setup neo4j
```

## Environment Variables

Add these to your `.env` file:

```
# API Keys
OPENAI_API_KEY=your_openai_api_key
SERPAPI_API_KEY=your_serpapi_key
LETTA_API_KEY=your_letta_api_key
GRAPHRAG_API_KEY=your_graphrag_api_key
CRAWL4AI_API_KEY=your_crawl4ai_api_key

# Service Ports
GRAPHITE_PORT=8080
LIBSQL_PORT=8081
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
CREWAI_PORT=8000
LETTA_PORT=8001
FALKOR_PORT=6379
GRAPHRAG_PORT=8002
LLAMA_PORT=8003
CRAWL4AI_PORT=8004
```

## Initial Setup

1. Make sure you have Docker and Docker Compose installed
2. Copy `.env.example` to `.env` and update the values
3. Run the setup script:
   ```bash
   ./ai_tools_manager.sh setup
   ```
4. Start the services:
   ```bash
   ./ai_tools_manager.sh start
   ```

## Updating Services

To update all services to their latest versions:

```bash
docker-compose -f docker-compose.yml -f docker-compose.override.ai-tools.yml pull
docker-compose -f docker-compose.yml -f docker-compose.override.ai-tools.yml up -d
```

## Backup and Restore

### Backup Data

```bash
# Create a backup directory
mkdir -p ./backups/$(date +%Y%m%d)

# Backup all volumes
docker run --rm -v $(pwd)/backups/$(date +%Y%m%d):/backup -v graphql_engine_data:/data -v $(pwd):/host alpine tar czf /backup/graphql_engine_data.tar.gz -C /data .
# Repeat for other volumes...
```

### Restore Data

```bash
# Stop services
./ai_tools_manager.sh stop

# Restore volume
docker run --rm -v $(pwd)/backups/20230101:/backup -v graphql_engine_data:/data alpine sh -c "rm -rf /data/* && tar xzf /backup/graphql_engine_data.tar.gz -C /data"
# Repeat for other volumes...

# Start services
./ai_tools_manager.sh start
```
