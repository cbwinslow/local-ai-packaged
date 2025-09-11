# Political Document Analysis Setup

This document outlines the setup and configuration for the political document analysis system.

## Overview

The system is designed to analyze political documents using a combination of natural language processing, knowledge graphs, and vector databases. It provides tools for document ingestion, processing, analysis, and visualization.

## Prerequisites

1. Docker and Docker Compose installed
2. Required API keys (see Configuration section)
3. Sufficient system resources (recommended: 16GB+ RAM, 4+ CPU cores)

## Configuration

### Required API Keys

1. **Congress.gov API Key**
   - Obtain from: https://api.congress.gov/signup/
   - Set as: `CONGRESS_GOV_API_KEY` in `.env`

2. **OpenAI API Key** (optional, for advanced NLP)
   - Obtain from: https://platform.openai.com/api-keys
   - Set as: `OPENAI_API_KEY` in `.env`

3. **Supabase Configuration**
   - Create a new project at https://supabase.com/
   - Set the following in `.env`:
     - `NEXT_PUBLIC_SUPABASE_URL`
     - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
     - `SUPABASE_SERVICE_ROLE_KEY`

## Services

### Core Services

1. **Neo4j**
   - URL: http://neo4j.opendiscourse.net
   - Default credentials: neo4j / [see .env for password]
   - Used for: Knowledge graph storage and queries

2. **Qdrant**
   - URL: http://qdrant:6333
   - Used for: Vector similarity search

3. **Flowise**
   - URL: http://flowise.opendiscourse.net
   - Used for: Visual workflow design for document processing

4. **n8n**
   - URL: http://n8n.opendiscourse.net
   - Used for: Workflow automation and integration

## Data Flow

### Government Document Ingestion
1. **GovInfo Queue Processing**
   - Scripts query `govinfo_download_queue` table for pending documents
   - Download from package_link URLs with rate limiting (60 requests/minute)
   - Support for PDF, HTML, XML formats
   - Automatic retry logic with exponential backoff

2. **Text Extraction & Normalization**
   - Multi-library extraction: pdfplumber, pypdf2, OCR (Tesseract), BeautifulSoup
   - Quality assessment and fallback mechanisms
   - Text cleaning and normalization

3. **NLP Processing Pipeline**
   - **spaCy NER**: Entity recognition (persons, organizations, locations, dates)
   - **Transformers Integration**: BERT-based enhanced NER for domain-specific entities
   - **sentence-transformers**: Generate 384D embeddings for semantic similarity
   - **Relationship Extraction**: Co-occurrence analysis for entity relationships

4. **Storage & Indexing**
   - PostgreSQL: Extracted text content and entity metadata
   - Neo4j: Entity relationships and knowledge graph nodes/edges
   - Qdrant/Pinecone/FAISS: Vector embeddings for similarity search

### Analysis Methods

#### Entity Analysis & Relationships
- Rule-based relationship extraction between entities
- Fuzzy matching for entity deduplication
- Confidence scoring and validation
- Hierarchical relationship modeling (personal → organizational → policy)

#### Embedding-Based Analysis
- Semantic similarity search across document corpus
- Topic clustering using embedding similarity
- Trend analysis through temporal embedding comparison
- Multi-modal relationship discovery

#### AI Agentic Inference
- **CrewAI**: Multi-agent orchestration for complex analysis
  - Document summarization agents
  - Policy impact assessment agents
  - Entity relationship mapping agents
- **Letta**: Memory persistence for agentic analysis sessions

## Document Ingestion Scripts

### Core Components
1. **supervisor.py**: Orchestrates the ingestion pipeline
   - Continuous monitoring of download queue
   - Batch processing with configurable concurrency
   - Error handling and status tracking

2. **download_processor.py**: Document downloading
   - Rate-limited HTTP downloads with aiohttp
   - Automatic content-type detection
   - Retry logic with exponential backoff
   - Temporary file management

3. **text_extractor.py**: Text extraction from documents
   - Support for PDF, HTML, XML, TXT formats
   - Multiple extraction libraries for robustness
   - OCR fallback for scanned documents
   - Quality estimation and optimization

4. **entity_processor.py**: Named entity recognition
   - spaCy and transformers NER integration
   - Entity deduplication and normalization
   - Relationship extraction heuristics
   - Confidence scoring and metadata

5. **embedding_generator.py**: Vector embeddings
   - sentence-transformers integration
   - Support for Qdrant, FAISS, Pinecone vector DBs
   - Caching and performance optimization
   - Similarity search capabilities

### Usage

```bash
# Run ingestion supervisor
python -m services.ingestion.supervisor

# Test text extraction
python -m services.ingestion.text_extractor sample.pdf

# Generate embeddings
python -m services.ingestion.embedding_generator
```

### Configuration
Scripts support environment variables for:
- `DATABASE_URL`: PostgreSQL connection string
- `NEO4J_URI`: Neo4j connection URI
- `QDRANT_URL`: Qdrant endpoint
- `EMBEDDING_MODEL`: Model name (default: "all-MiniLM-L6-v2")
- `MAX_CONCURRENT_DOWNLOADS`: Download concurrency (default: 5)

## AI Agentic Research & Inference Techniques

### Advanced Text Analysis
- **Government Legal Document Research**: APIs (Congress.gov, GovInfo) + MCP Crawl4AI web scraping
- **Entity Relationships**: spaCy dependency parsing + Neo4j graph traversals
- **BERT Analysis**: Fine-tuning for political domain specific entities
- **NLG/Generation**: transformers GPT integration for report generation
- **SQL Integration**: Complex JOINs for spatio-temporal political analysis

### Agentic Patterns
- **ReAct Agents**: Reasoning traces for entity relationship discovery
- **Chain-of-Thought**: Step-by-step political document analysis
- **Few-Shot Learning**: Political entity recognition with minimal examples
- **Context Distillation**: Token-limit management for long documents
- **Critique Chains**: Self-improvement for analysis accuracy

### Research Methodology
1. **Web Search Integration**: MCP Crawl4AI for supplementary research
2. **Knowledge Graph Construction**: Entity-to-policy relationship mapping
3. **Agentic Workflows**: n8n/Flowise automation with CrewAI agents
4. **Iterative Refinement**: Memory-guided analysis improvement
5. **Cross-Referencing**: Multi-source entity validation

## Security Considerations

1. **Secrets Management**
   - All sensitive credentials are stored in `.env`
   - Never commit `.env` to version control
   - Use environment-specific `.env` files in production

2. **Access Control**
   - All services require authentication
   - API endpoints are rate-limited
   - Sensitive operations require admin privileges

## Development

### Starting the Stack

```bash
docker-compose up -d
docker-compose -f docker-compose.mcp.yml up -d
```

### Stopping the Stack

```bash
docker-compose down
docker-compose -f docker-compose.mcp.yml down
```

## Troubleshooting

### Common Issues

1. **Services not starting**
   - Check logs: `docker-compose logs <service_name>`
   - Verify ports are not in use
   - Check system resource usage

2. **Authentication failures**
   - Verify credentials in `.env`
   - Check service logs for detailed error messages

3. **Performance issues**
   - Monitor resource usage: `docker stats`
   - Consider increasing system resources
   - Optimize database queries

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
