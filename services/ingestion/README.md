# Government Document Ingestion Service

This module provides a comprehensive pipeline for ingesting, processing, and analyzing government documents from the GovInfo system.

## Architecture

The ingestion service follows a multi-stage pipeline:

```
GovInfo Queue → Download → Text Extraction → Entity Processing → Embedding → Storage
     ↓            ↓           ↓                  ↓             ↓            ↓
 govinfo_packages  Rate-     pdfplumber +       spaCy +        sentence-     PostgreSQL +
 govinfo_download  limiting  pypdf2 + OCR      transformers    transformers   Neo4j + Qdrant
 _queue            retry     BeautifulSoup                     FAISS
```

## Prerequisites

Install required dependencies:

```bash
pip install spacy sentence-transformers transformers psycopg2-binary aiohttp aiofiles beautifulsoup4 pypdf2 pdfplumber pytesseract pillow qdrant-client faiss-cpu neo4j-driver
python -m spacy download en_core_web_md
```

## Environment Variables

```bash
# Database connections
DATABASE_URL=postgresql://user:password@localhost:5432/db
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Vector database (choose one)
QDRANT_URL=http://localhost:6333
PINECONE_API_KEY=your_pinecone_key

# Processing configuration
MAX_CONCURRENT_DOWNLOADS=5
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DB_TYPE=faiss  # Options: qdrant, faiss, pinecone, none
TEMP_DIR=/tmp/govinfo_downloads

# Logging
LOG_LEVEL=INFO
```

## Usage Examples

### 1. Run Complete Ingestion Pipeline

```python
# Run the full ingestion supervisor
python -m services.ingestion.supervisor

# Or programmatically
from services.ingestion.supervisor import IngestionSupervisor

supervisor = IngestionSupervisor(
    max_concurrent_downloads=5,
    batch_size=25,
    max_workers=8
)

async def run():
    await supervisor.run_ingestion_loop()

asyncio.run(run())
```

### 2. Process Individual Components

```python
# Download a document
from services.ingestion.download_processor import DocumentDownloader

async with DocumentDownloader() as downloader:
    result = await downloader.download_document({
        'package_id': 'USCODE-2020-title26',
        'package_link': 'https://example.gov/document.pdf'
    })
    print("Downloaded to:", result['file_path'])

# Extract text
from services.ingestion.text_extractor import TextExtractor

extractor = TextExtractor()
text = extractor.extract_text('/path/to/document.pdf')
print(f"Extracted {len(text)} characters")

# Process entities
from services.ingestion.entity_processor import EntityProcessor

processor = EntityProcessor()
entities = processor.extract_entities(text)
print(f"Found {len(entities)} entities")

# Generate embeddings
from services.ingestion.embedding_generator import EmbeddingGenerator

generator = EmbeddingGenerator(vector_db="faiss")
embeddings = generator.generate_embeddings(text)
stored = generator.store_embeddings('document-123', embeddings)
print(f"Embeddings stored: {stored}")
```

### 3. Search Similar Documents

```python
# Search for similar documents
similar = generator.search_similar("tax policy reform", top_k=5)
for doc in similar:
    print(f"Document: {doc['id']}, Score: {doc['score']:.2f}")
```

### 4. Entity Relationship Analysis

```python
# Find relationships between entities
relationships = processor.find_entity_relationships(entities, text)
for rel in relationships:
    print(f"{rel['entity1']} {rel['relationship_type']} {rel['entity2']}")

# Get entity statistics
stats = processor.get_entity_stats(entities)
print(f"Entity types: {stats['entity_type_counts']}")
```

## Configuration Options

### DocumentDownloader
- `max_concurrent`: Maximum parallel downloads (default: 5)
- `timeout`: HTTP timeout in seconds (default: 30)
- `max_retries`: Retry attempts (default: 3)
- `rate_limit_rpm`: Rate limit (default: 60)
- `user_agent`: Custom user agent string

### TextExtractor
- Automatically tries multiple extractors:
  - pdfplumber (PDFs)
  - pypdf2 (PDFs)
  - OCR (scanned PDFs)
  - BeautifulSoup (HTML/XML)
  - Plain text (TXT/MD)

### EntityProcessor
- `model_name`: spaCy model (default: "en_core_web_md")
- `use_transformers`: Enable BERT NER (default: False)
- `confidence_threshold`: Entity confidence threshold (default: 0.7)

### EmbeddingGenerator
- `model_name`: SentenceTransformer model
- `vector_db`: Database type ("qdrant", "faiss", "pinecone", "none")
- `dimension`: Embedding dimension (auto-detected)
- `cache_dir`: Cache directory

## Database Schema Integration

The scripts integrate with the existing database schema:

```sql
-- Queue processing
SELECT * FROM govinfo_download_queue WHERE status = 'pending'

-- Text storage
UPDATE govinfo_packages SET content = ? WHERE package_id = ?

-- Entity storage (extend as needed)
INSERT INTO entity_mentions (package_id, entity_text, entity_type, confidence)
VALUES (?, ?, ?, ?)

-- Relationship storage (Neo4j)
MERGE (e1:Entity {name: ?})-[r:RELATED {type: ?}]->(e2:Entity {name: ?})
```

## Monitoring and Metrics

The supervisor provides processing statistics:

```python
stats = await supervisor.process_batch()
print(f"Processed: {stats.total_processed}")
print(f"Successful downloads: {stats.successful_downloads}")
print(f"Current processing time: {stats.total_time_seconds:.1f}s")
```

## Error Handling

- **Network errors**: Automatic retry with exponential backoff
- **Corrupted files**: Fallback to OCR or skip processing
- **Model failures**: Graceful degradation to basic processing
- **Database errors**: Transaction rollback and logging

## Performance Optimization

1. **Batch Processing**: Process documents in configurable batches
2. **Concurrency**: Parallel downloads and thread-based CPU processing
3. **Caching**: Embedding cache and file deduplication
4. **Resource Limits**: Memory and CPU monitoring
5. **Async Operations**: Non-blocking I/O for network operations

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   - Install required packages: `pip install -r requirements.txt`
   - Download spaCy models: `python -m spacy download en_core_web_md`

2. **Database Connection**
   - Verify DATABASE_URL environment variable
   - Check PostgreSQL service status

3. **Vector Database**
   - For Qdrant: Ensure service is running on port 6333
   - For Pinecone: Set API key and index name

4. **Memory Issues**
   - Reduce batch_size for large documents
   - Use OCR=False for faster processing
   - Monitor with `docker stats`

5. **PDF Processing Errors**
   - Check file permissions
   - Verify PDF is not password-protected
   - Try alternative extraction libraries

### Debug Mode

Enable detailed logging:

```bash
LOG_LEVEL=DEBUG python -m services.ingestion.supervisor
```

## Testing

Run unit tests:

```bash
python -m pytest services/ingestion/tests/
```

Test individual components:

```bash
# Test download
python services/ingestion/download_processor.py

# Test extraction
python services/ingestion/text_extractor.py test.pdf

# Test entity processing
python services/ingestion/entity_processor.py

# Test embeddings
python services/ingestion/embedding_generator.py
```

## Integration with AI Tools

### CrewAI Integration
```python
from crewai import Agent, Task, Crew
from services.ingestion import supervisor

# Create agents for document analysis
analysis_agent = Agent(
    name="Document Analyzer",
    role="Political Document Analysis",
    goal="Extract and analyze key insights from government documents"
)

# Use ingestion supervisor in crew workflow
crew = Crew(agents=[analysis_agent], tasks=[...])
```

### Neo4j Queries
```cypher
// Find connections between politicians and policies
MATCH (p:Person)-[r:SPONSORED]->(b:Bill)-[r2:MENTIONS]->(org:Organization)
RETURN p.name, b.title, org.name, r2.confidence
ORDER BY r2.confidence DESC
```

### Flowise/n8n Automation
Configure webhooks to trigger ingestion on new document availability and create automated reporting dashboards.
