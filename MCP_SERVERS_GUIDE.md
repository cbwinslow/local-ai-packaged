# Comprehensive MCP Servers List for Local AI Package

## Overview

This document provides a comprehensive list of MCP (Model Context Protocol) servers implemented in the Local AI Package, designed to create a robust AI development environment with permanent data storage and industry-standard practices.

## 🏗️ Architecture Overview

The Local AI Package implements a production-ready, microservices architecture with:

- **Permanent Data Storage**: All data persists through Docker volume recreation
- **Cloud Integration**: Support for Cloudflare, Oracle OCI, and Azure free tiers
- **Robust Networking**: Traefik reverse proxy with automatic HTTPS
- **Comprehensive Monitoring**: Grafana, Prometheus, and Langfuse integration
- **Security Best Practices**: Secrets management, encrypted communications
- **Backup & Recovery**: Automated backup system with cloud storage options

## 📋 MCP Servers List

### Government Data MCP Servers

#### 1. Congress.gov MCP Server
- **Port**: 3001
- **Purpose**: Access U.S. Congressional data, bills, votes, and member information
- **API Requirements**: Congress.gov API key
- **Data Sources**: congress.gov, govinfo.gov
- **Features**:
  - Real-time bill tracking
  - Voting record analysis
  - Member profile data
  - Committee information

#### 2. Federal Register MCP Server
- **Port**: 3011
- **Purpose**: Federal regulations, executive orders, and agency rules
- **API Requirements**: Federal Register API key
- **Features**:
  - Regulation tracking
  - Public comment analysis
  - Agency rule monitoring
  - Executive order tracking

#### 3. FEC (Federal Election Commission) MCP Server
- **Port**: 3012
- **Purpose**: Campaign finance data, candidate information, election results
- **API Requirements**: FEC API key
- **Features**:
  - Campaign contribution tracking
  - Candidate financial data
  - PAC and Super PAC analysis
  - Election expenditure monitoring

### Database and Memory MCP Servers

#### 4. Neo4j Agent Memory MCP
- **Port**: 3013
- **Purpose**: Graph-based agent memory and knowledge representation
- **Dependencies**: Neo4j database
- **Features**:
  - Agent conversation history
  - Knowledge graph construction
  - Relationship mapping
  - Context preservation

#### 5. PostgreSQL MCP Server
- **Port**: 3014
- **Purpose**: Relational database operations and analytics
- **Dependencies**: PostgreSQL database
- **Features**:
  - SQL query execution
  - Data analysis
  - Report generation
  - Schema management

#### 6. Redis MCP Server
- **Port**: 3015
- **Purpose**: Caching, session management, and real-time data
- **Dependencies**: Redis/Valkey
- **Features**:
  - Cache management
  - Session storage
  - Real-time analytics
  - Pub/sub messaging

### AI and Vector Database MCP Servers

#### 7. Vectorize MCP Server
- **Port**: 3016
- **Purpose**: Vector embeddings and similarity search
- **Dependencies**: Qdrant vector database
- **Features**:
  - Document embeddings
  - Semantic search
  - Similarity analysis
  - Vector operations

#### 8. Embeddings MCP Server
- **Port**: 3017
- **Purpose**: Text and document embedding generation
- **Dependencies**: Ollama, OpenAI API
- **Features**:
  - Multiple embedding models
  - Batch processing
  - Cache optimization
  - Model comparison

### Cloud Integration MCP Servers

#### 9. Azure MCP Server
- **Port**: 3018
- **Purpose**: Microsoft Azure cloud services integration
- **Requirements**: Azure credentials
- **Features**:
  - Resource management
  - Storage operations
  - AI services access
  - Cost monitoring

#### 10. Cloudflare MCP Server
- **Port**: 3019
- **Purpose**: Cloudflare services integration
- **Requirements**: Cloudflare API token
- **Features**:
  - DNS management
  - R2 storage operations
  - Workers deployment
  - Analytics access

#### 11. Oracle Cloud Infrastructure (OCI) MCP Server
- **Port**: 3020
- **Purpose**: Oracle Cloud services integration
- **Requirements**: OCI credentials
- **Features**:
  - Always Free tier management
  - Object storage operations
  - Database services
  - Resource monitoring

### Development and Management MCP Servers

#### 12. PluggedIn MCP (MCP Manager)
- **Port**: 3021
- **Purpose**: MCP server discovery and management
- **Features**:
  - Server registration
  - Health monitoring
  - Configuration management
  - Service discovery

#### 13. GitHub MCP Server
- **Port**: 3022
- **Purpose**: GitHub repository and project management
- **Requirements**: GitHub token
- **Features**:
  - Repository operations
  - Issue tracking
  - Pull request management
  - Code analysis

### Security and Monitoring MCP Servers

#### 14. StackHawk Security MCP
- **Port**: 3023
- **Purpose**: Security scanning and vulnerability assessment
- **Requirements**: StackHawk API key
- **Features**:
  - DAST scanning
  - Vulnerability reporting
  - Security monitoring
  - Compliance checking

#### 15. Log Analysis MCP Server
- **Port**: 3024
- **Purpose**: System and application log analysis
- **Features**:
  - Log aggregation
  - Pattern recognition
  - Anomaly detection
  - Alert generation

## 🗄️ Database Servers

### Graph Databases

#### Neo4j Community Edition
- **Ports**: 7474 (HTTP), 7687 (Bolt)
- **Purpose**: Primary graph database for relationships and knowledge graphs
- **Features**:
  - APOC plugins
  - Graph Data Science library
  - Persistent storage
  - Cypher query language

#### Memgraph
- **Ports**: 7688 (Bolt), 3000 (Lab), 7444 (Monitoring)
- **Purpose**: High-performance graph analytics
- **Features**:
  - AI-enabled operations
  - Real-time analytics
  - Machine learning integration
  - Stream processing

#### FalkorDB
- **Port**: 6379
- **Purpose**: Redis-compatible graph database
- **Features**:
  - High-performance queries
  - Redis protocol compatibility
  - Memory optimization
  - GraphBLAS algorithms

## 🔧 Configuration and Setup

### Environment Variables

All MCP servers are configured through environment variables defined in `.env` file:

```bash
# Generate all secrets and configuration
./scripts/enhanced-generate-secrets.sh

# Update with your API keys
# Edit .env file and add:
OPENAI_API_KEY=your-openai-key
CONGRESS_GOV_API_KEY=your-congress-key
GITHUB_TOKEN=your-github-token
# ... etc
```

### Docker Compose Commands

```bash
# Start all services
docker compose up -d

# Start specific profiles
docker compose --profile cpu up -d        # CPU-only profile
docker compose --profile gpu-nvidia up -d # NVIDIA GPU profile
docker compose --profile gpu-amd up -d    # AMD GPU profile

# View logs
docker compose logs -f [service-name]

# Stop all services
docker compose down
```

## 💾 Data Persistence Strategy

### Industry-Standard Approach

The Local AI Package implements industry-standard data persistence:

1. **Named Docker Volumes**: All critical data uses persistent volumes
2. **Bind Mounts**: Host directory mapping for easy backup
3. **Automated Backups**: Scheduled backup system with cloud storage
4. **Configuration Management**: Version-controlled configurations
5. **Disaster Recovery**: Comprehensive restore procedures

### Volume Structure

```
volumes/
├── postgres/data/          # PostgreSQL data
├── qdrant/data/           # Vector database
├── neo4j/                 # Graph database
│   ├── data/
│   ├── logs/
│   ├── import/
│   └── plugins/
├── supabase/              # Supabase components
│   ├── db/data/
│   └── storage/
├── mcp/                   # MCP server data
│   ├── congress/
│   ├── azure/
│   ├── cloudflare/
│   └── ...
└── backups/               # Automated backups
    ├── daily/
    ├── weekly/
    └── monthly/
```

### Backup and Recovery

```bash
# Create full backup
./scripts/backup-restore-enhanced.sh backup full

# Create incremental backup
./scripts/backup-restore-enhanced.sh backup incremental

# List available backups
./scripts/backup-restore-enhanced.sh list

# Restore from backup
./scripts/backup-restore-enhanced.sh restore backup_file.tar.gz --confirm

# Cloud backup to Cloudflare R2
./scripts/backup-restore-enhanced.sh cloud-backup cloudflare

# Clean old backups
./scripts/backup-restore-enhanced.sh clean --older-than-days=30
```

## ☁️ Cloud Integration for Permanent Storage

### Cloudflare (Free Tier Benefits)
- **R2 Storage**: 10GB free storage
- **Workers**: 100,000 requests/day
- **D1 Database**: SQLite database
- **Analytics**: Real-time metrics

### Oracle Cloud Infrastructure (Always Free)
- **Block Storage**: 200GB
- **Autonomous Database**: 20GB
- **Compute**: 2 OCPU hours
- **Object Storage**: 10GB

### Azure (12 Months Free)
- **Storage**: 5GB LRS
- **Database**: 250GB SQL Database
- **Functions**: 1M requests/month
- **AI Services**: Various quotas

## 🚀 Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd local-ai-packaged
   ./scripts/enhanced-generate-secrets.sh
   ```

2. **Start core services**:
   ```bash
   docker compose up -d postgres redis qdrant
   ```

3. **Start MCP servers**:
   ```bash
   docker compose up -d mcp-congress-gov mcp-neo4j-agent-memory
   ```

4. **Start full stack**:
   ```bash
   docker compose up -d
   ```

5. **Access services**:
   - Supabase Dashboard: http://localhost:8000
   - Neo4j Browser: http://localhost:7474
   - Grafana: http://localhost:3001 (when monitoring is enabled)

## 🔒 Security Considerations

1. **Secrets Management**: All secrets are generated automatically
2. **Network Security**: Services communicate through internal networks
3. **Access Control**: Role-based access with JWT tokens
4. **Encryption**: TLS encryption for external communications
5. **Regular Updates**: Keep Docker images updated

## 📊 Monitoring and Observability

- **Langfuse**: LLM observability and analytics
- **Grafana**: Metrics visualization
- **Prometheus**: Metrics collection
- **Health Checks**: Automated service monitoring
- **Log Aggregation**: Centralized logging

## 🤝 Contributing

To add a new MCP server:

1. Create server directory: `mcp-servers/your-server/`
2. Add Dockerfile and configuration
3. Update `docker-compose.mcp.yml`
4. Add volume definitions
5. Update this documentation

## 📞 Support

For issues and questions:
1. Check the logs: `docker compose logs -f [service]`
2. Run health checks: `./scripts/health-check.sh`
3. Review configuration: `docker compose config`
4. Backup and restore if needed

---

*This Local AI Package provides a production-ready, scalable foundation for AI development with permanent data storage and industry-standard practices.*