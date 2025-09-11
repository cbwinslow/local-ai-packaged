# MCP Server Integration

This document outlines the MCP (Model Control Protocol) servers integrated into the Local AI Platform and how to use them.

## Overview

We've integrated several MCP servers to enhance the platform's capabilities:

1. **Congress.gov MCP** - Access to legislative data
2. **Neo4j Agent Memory** - Knowledge graph for agent memory
3. **Vectorize MCP** - Document vectorization and search
4. **StackHawk MCP** - Security testing
5. **PluggedIn MCP** - Central management of MCP services

## Setup

### Prerequisites

1. Docker and Docker Compose
2. Required API keys (see `.env` file)

### Environment Variables

Create or update your `.env` file with the following variables:

```bash
# Neo4j
NEO4J_PASSWORD=your_secure_password

# Congress.gov
CONGRESS_GOV_API_KEY=your_congress_gov_api_key

# Pinecone (for Vectorize MCP)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX=your_pinecone_index

# StackHawk
STACKHAWK_API_KEY=your_stackhawk_api_key

# Vectorize MCP
VECTORIZE_API_KEY=$(openssl rand -hex 32)
```

### Starting the Services

Run the setup script to generate necessary configurations:

```bash
chmod +x scripts/setup-mcp-env.sh
./scripts/setup-mcp-env.sh
```

Then start the services:

```bash
docker-compose up -d
```

## MCP Server Details

### 1. Congress.gov MCP

- **Port**: 3001
- **Health Check**: `GET http://localhost:3001/health`
- **Purpose**: Access to legislative data from Congress.gov

### 2. Neo4j Agent Memory MCP

- **Port**: 3002
- **Health Check**: `GET http://localhost:3002/health`
- **Neo4j Browser**: http://localhost:7474
- **Purpose**: Persistent memory and knowledge graph for AI agents

### 3. Vectorize MCP

- **Port**: 3003
- **Health Check**: `GET http://localhost:3003/health`
- **Purpose**: Document vectorization and semantic search

### 4. StackHawk MCP

- **Port**: 3005
- **Health Check**: `GET http://localhost:3005/health`
- **Purpose**: Automated security testing

### 5. PluggedIn MCP (Manager)

- **Port**: 3004
- **Health Check**: `GET http://localhost:3004/health`
- **Purpose**: Central management of all MCP services

## Integration Examples

### Using Congress.gov MCP

```python
import requests

# Get bill details
response = requests.get(
    "http://localhost:3001/api/bills/117/hr3076",
    headers={"Authorization": f"Bearer {os.getenv('CONGRESS_GOV_API_KEY')}"}
)
print(response.json())
```

### Using Neo4j Agent Memory

```python
import requests

# Store a memory
response = requests.post(
    "http://localhost:3002/api/memory",
    json={
        "agent_id": "agent1",
        "content": "User prefers dark mode",
        "metadata": {"source": "ui_preferences"}
    },
    headers={"X-API-Key": os.getenv("NEO4J_PASSWORD")}
)
```

### Using Vectorize MCP

```python
import requests

# Vectorize text
response = requests.post(
    "http://localhost:3003/api/vectorize",
    json={"text": "Sample document text"},
    headers={"X-API-Key": os.getenv("VECTORIZE_API_KEY")}
)
```

## Security Considerations

1. Always use HTTPS in production
2. Rotate API keys regularly
3. Restrict access to MCP endpoints using network policies
4. Monitor logs for unusual activity

## Troubleshooting

1. Check container logs: `docker-compose logs <service_name>`
2. Verify environment variables are set correctly
3. Ensure ports are not in use by other services
4. Check health endpoints for service status

## Next Steps

1. Set up monitoring for MCP services
2. Implement rate limiting
3. Add authentication between services
4. Set up backup and recovery procedures
