# Government Data Ingestion Guide

## Overview

This comprehensive guide covers the complete process of ingesting, analyzing, and reporting on government data from 300+ sources including federal, state, local, and international government websites.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Data Sources](#data-sources)
3. [Ingestion Scripts](#ingestion-scripts)
4. [SQL Analysis](#sql-analysis)
5. [Reporting System](#reporting-system)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install requests beautifulsoup4 selenium pdfplumber aiohttp asyncio
pip install sqlalchemy psycopg2-binary redis neo4j qdrant-client
pip install sentence-transformers transformers torch pandas numpy

# Set up environment variables
export POSTGRES_URL="postgresql://postgres:postgres@localhost:5432/postgres"
export CONGRESS_GOV_API_KEY="your_api_key_here"
export FEC_API_KEY="your_fec_key_here"
export OPENSECRETS_API_KEY="your_opensecrets_key_here"
```

### Basic Usage

```bash
# Start with Congressional data
python scripts/enhanced_government_ingestion.py --source congress --limit 1000

# Ingest from all sources (comprehensive)
python scripts/enhanced_government_ingestion.py --source all --generate-reports

# Generate reports only
python scripts/enhanced_government_ingestion.py --generate-reports
```

## Data Sources

### Source Categories

The system ingests data from 300+ government sources organized into categories:

#### Federal Government (120+ sources)
- **Legislative Branch**: Congress.gov, House.gov, Senate.gov, CRS Reports, GAO Reports
- **Executive Branch**: White House, Federal Register, All 15 Cabinet Departments
- **Judicial Branch**: Supreme Court, Federal Courts, PACER System
- **Independent Agencies**: FEC, FCC, FTC, SEC, EPA, FDA, CDC, NIH, NSA, NASA

#### Intelligence & Defense (25+ sources)
- **Intelligence Community**: CIA FOIA, FBI Vault, NSA FOIA, DARPA
- **Military Branches**: Army, Navy, Air Force, Marines, Space Force, Coast Guard
- **Special Operations**: JSOC, Special Operations Command

#### State Government (50+ sources)
- **All 50 State Legislatures**: Complete coverage of state legislative bodies
- **State Executive Branches**: Governors' offices and state agencies
- **State Judicial Systems**: State supreme courts and appellate courts

#### Local Government (100+ sources)
- **Major Cities**: Top 50 cities' open data portals
- **Counties**: County government data and health rankings
- **Municipal Organizations**: US Conference of Mayors, ICMA, NLC

#### International Sources (50+ sources)
- **European Union**: Parliament, Commission, Council, Member States
- **Other Democracies**: UK, Canada, Australia, Japan, South Korea
- **International Organizations**: UN, World Bank, IMF, OECD, WHO, NATO

#### Specialized Sources (50+ sources)
- **Academic Institutions**: Think tanks, research centers, universities
- **Transparency Organizations**: Sunlight Foundation, ProPublica, OpenSecrets
- **Legal Databases**: Court records, regulatory tracking, treaty databases

### Source Configuration

Sources are configured in `data/government-sources.yaml`:

```yaml
# Federal Sources
CONGRESS_GOV_API: "https://api.congress.gov/v3"
FEC_API: "https://api.open.fec.gov/v1"
WHITE_HOUSE: "https://www.whitehouse.gov/briefing-room"

# State Sources  
CALIFORNIA_LEGISLATURE: "https://leginfo.legislature.ca.gov"
TEXAS_LEGISLATURE: "https://capitol.texas.gov"

# International Sources
UK_PARLIAMENT: "https://www.parliament.uk/business/publications"
EU_PARLIAMENT: "https://www.europarl.europa.eu/portal/en"
```

## Ingestion Scripts

### Enhanced Government Ingestion System

The main ingestion script (`scripts/enhanced_government_ingestion.py`) provides:

#### Core Features
- **Multi-source support**: APIs, web scraping, document processing
- **Async processing**: High-performance concurrent ingestion
- **Rate limiting**: Respectful API usage with configurable limits
- **Error handling**: Robust retry mechanisms and error recovery
- **Data validation**: Content deduplication and quality checks
- **Vector embeddings**: Semantic search capabilities
- **Progress tracking**: Comprehensive logging and statistics

#### Configuration Options

```python
config = IngestionConfig(
    batch_size=1000,                    # Records per batch
    max_concurrent_requests=10,         # Parallel requests
    rate_limit_per_second=5,           # API rate limiting
    retry_attempts=3,                  # Retry on failure
    enable_selenium=False,             # Dynamic content scraping
    enable_pdf_processing=True,        # PDF document parsing
    enable_vector_embeddings=True,     # Semantic search
    deduplicate_content=True,          # Remove duplicates
    validate_data=True                 # Data quality checks
)
```

#### Database Schema

The system creates comprehensive database tables:

- **data_sources**: Source configuration and metadata
- **documents**: Ingested documents with full text and metadata
- **politicians**: Politician profiles with KPIs and metrics
- **bills**: Legislative bills with sponsors, committees, subjects
- **votes**: Voting records with detailed position tracking
- **ingestion_runs**: Performance tracking and statistics

#### Usage Examples

```bash
# Congressional data with custom settings
python scripts/enhanced_government_ingestion.py \
    --source congress \
    --limit 5000 \
    --batch-size 250 \
    --rate-limit 10

# Web scraping with Selenium
python scripts/enhanced_government_ingestion.py \
    --source state \
    --mode scraping \
    --generate-reports

# International sources
python scripts/enhanced_government_ingestion.py \
    --source international \
    --limit 2000
```

### Specialized Ingestion Scripts

#### Simple Congress Ingestion (`scripts/ingest_government_data.py`)
- Lightweight script for basic Congressional data
- Direct PostgreSQL integration
- Simple retry logic and logging
- Good for getting started quickly

#### GovInfo Bulk Data (`scripts/ingest_govinfo_data.py`)
- Specialized for bulk government document processing
- PDF and XML parsing capabilities
- Federal Register and Congressional Record focus

### Document Processing Capabilities

#### Supported Formats
- **HTML**: Web page content extraction
- **PDF**: Full text extraction with pdfplumber
- **XML**: Structured government data parsing
- **JSON**: API response processing
- **CSV**: Tabular data import

#### Text Processing Features
- Content deduplication using SHA-256 hashing
- Language detection and filtering
- Summary generation for long documents
- Metadata extraction (dates, authors, categories)
- Tag and subject classification

## SQL Analysis

### Comprehensive Query Library

The system includes 100+ pre-built SQL queries in `docs/comprehensive_analysis_queries.sql`:

#### Politician Effectiveness Analysis
```sql
-- Top 50 Most Effective Politicians
SELECT 
    p.name,
    p.party,
    p.state,
    COUNT(b.id) AS bills_sponsored,
    COUNT(v.id) AS votes_cast,
    -- Effectiveness score calculation
    CASE 
        WHEN p.chamber = 'senate' THEN COUNT(b.id) * 1.5 + COUNT(v.id) * 0.1
        ELSE COUNT(b.id) * 1.0 + COUNT(v.id) * 0.1
    END AS effectiveness_score
FROM politicians p
LEFT JOIN bills b ON b.sponsor_id = p.id::text
LEFT JOIN votes v ON v.politician_id = p.id::text
WHERE p.current_office = true
GROUP BY p.id, p.name, p.party, p.state, p.chamber
ORDER BY effectiveness_score DESC
LIMIT 50;
```

#### Legislative Trends Analysis
```sql
-- Monthly Bill Introduction Trends
SELECT 
    DATE_TRUNC('month', introduced_date) AS month,
    COUNT(*) AS bills_introduced,
    COUNT(CASE WHEN bill_type = 'hr' THEN 1 END) AS house_bills,
    COUNT(CASE WHEN bill_type = 's' THEN 1 END) AS senate_bills
FROM bills
WHERE introduced_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY DATE_TRUNC('month', introduced_date)
ORDER BY month DESC;
```

#### Voting Pattern Analysis
```sql
-- Bipartisan Cooperation Scores
WITH bipartisan_votes AS (
    SELECT 
        v.politician_id,
        p.party,
        COUNT(*) AS total_votes,
        COUNT(CASE 
            WHEN (p.party = 'Democratic' AND majority_position = 'Republican') OR
                 (p.party = 'Republican' AND majority_position = 'Democratic')
            THEN 1 
        END) AS cross_party_votes
    FROM votes v
    JOIN politicians p ON p.id::text = v.politician_id
    -- Additional logic for majority position calculation
    GROUP BY v.politician_id, p.party
)
SELECT 
    p.name,
    p.party,
    bv.cross_party_votes,
    ROUND((bv.cross_party_votes::numeric / bv.total_votes * 100), 2) AS bipartisan_score
FROM bipartisan_votes bv
JOIN politicians p ON p.id::text = bv.politician_id
ORDER BY bipartisan_score DESC;
```

#### Data Quality Assessment
```sql
-- Comprehensive Data Quality Report
SELECT 
    'Politicians' AS table_name,
    COUNT(*) AS total_records,
    COUNT(CASE WHEN name IS NULL THEN 1 END) AS missing_names,
    COUNT(CASE WHEN party IS NULL THEN 1 END) AS missing_party,
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN name IS NULL THEN 1 END)) * 100.0 / COUNT(*), 
        2
    ) AS data_completeness_pct
FROM politicians
UNION ALL
SELECT 'Bills', COUNT(*), 
       COUNT(CASE WHEN title IS NULL THEN 1 END),
       COUNT(CASE WHEN sponsor_id IS NULL THEN 1 END),
       ROUND((COUNT(*) - COUNT(CASE WHEN title IS NULL THEN 1 END)) * 100.0 / COUNT(*), 2)
FROM bills;
```

### Query Categories

1. **Politician Analytics**
   - Effectiveness scores and rankings
   - Party leadership analysis
   - Bipartisan cooperation metrics
   - Voting attendance and patterns

2. **Legislative Trends**
   - Bill introduction patterns
   - Success rates by party/chamber
   - Subject matter analysis
   - Temporal trend analysis

3. **Committee Analysis**
   - Membership composition
   - Committee influence scores
   - Cross-committee collaboration

4. **Geographic Analysis**
   - State delegation effectiveness
   - Regional policy priorities
   - Cross-state collaboration

5. **Performance Metrics**
   - Data source statistics
   - Ingestion run performance
   - Data quality assessments

## Reporting System

### Automated Report Generation

The system generates comprehensive reports automatically:

#### Executive Summary Report
```json
{
  "ingestion_summary": {
    "total_documents": 25000,
    "documents_added": 5000,
    "politicians_processed": 535,
    "bills_processed": 12000,
    "success_rate": 0.95
  },
  "database_statistics": {
    "total_sources": 286,
    "total_documents": 125000,
    "total_politicians": 1500,
    "total_bills": 45000,
    "total_votes": 250000
  }
}
```

#### Politician Effectiveness Report
- Top 50 most effective legislators
- Party leadership comparison
- Bipartisan cooperation rankings
- Committee influence metrics

#### Legislative Trends Report
- Bill introduction patterns
- Success rates by category
- Subject matter trending
- Seasonal legislative activity

#### Data Quality Assessment
- Source reliability metrics
- Data completeness analysis
- Error rate tracking
- Performance benchmarks

### Report Formats

Reports are generated in multiple formats:
- **JSON**: Machine-readable data for APIs
- **Markdown**: Human-readable summaries
- **CSV**: Tabular data for Excel/analysis
- **HTML**: Web-friendly presentations

### Custom Reports

Create custom reports using the SQL query library:

```python
from enhanced_government_ingestion import EnhancedGovernmentIngestion

# Initialize system
ingestion = EnhancedGovernmentIngestion(config)
await ingestion.initialize()

# Generate specific report
report_dir = await ingestion.generate_comprehensive_reports()
print(f"Reports available at: {report_dir}")
```

## Advanced Features

### Vector Embeddings & Semantic Search

The system creates vector embeddings for semantic search:

```python
# Enable vector embeddings
config.enable_vector_embeddings = True

# Search similar documents
from qdrant_client import QdrantClient
client = QdrantClient("http://localhost:6333")

# Find bills similar to search text
search_results = client.search(
    collection_name="bills",
    query_vector=sentence_transformer.encode("healthcare reform"),
    limit=10
)
```

### Real-time Data Streaming

Set up real-time ingestion for active monitoring:

```python
# Incremental ingestion mode
python scripts/enhanced_government_ingestion.py \
    --mode incremental \
    --source congress \
    --generate-reports
```

### API Integration

The ingested data can be exposed via REST APIs:

```python
# Example FastAPI endpoint
from fastapi import FastAPI
app = FastAPI()

@app.get("/politicians/{politician_id}/effectiveness")
async def get_politician_effectiveness(politician_id: str):
    # Query database for politician metrics
    return effectiveness_data
```

### Data Visualization

Integrate with visualization tools:

```python
import matplotlib.pyplot as plt
import pandas as pd

# Politician effectiveness visualization
df = pd.read_sql(effectiveness_query, db_engine)
plt.figure(figsize=(12, 8))
plt.scatter(df['bills_sponsored'], df['effectiveness_score'], 
           c=df['party'].map({'Democratic': 'blue', 'Republican': 'red'}))
plt.xlabel('Bills Sponsored')
plt.ylabel('Effectiveness Score')
plt.title('Politician Effectiveness Analysis')
plt.show()
```

## Troubleshooting

### Common Issues

#### API Rate Limiting
```bash
# Reduce rate limit
python scripts/enhanced_government_ingestion.py --rate-limit 2

# Check API quotas
curl -H "X-API-Key: $CONGRESS_GOV_API_KEY" https://api.congress.gov/v3/
```

#### Database Connection Issues
```bash
# Check PostgreSQL connection
psql $POSTGRES_URL -c "SELECT version();"

# Reset database schema
python -c "from enhanced_government_ingestion import Base; Base.metadata.drop_all(engine)"
```

#### Memory Issues with Large Datasets
```bash
# Use smaller batch sizes
python scripts/enhanced_government_ingestion.py --batch-size 100

# Disable vector embeddings for faster processing
config.enable_vector_embeddings = False
```

#### Selenium WebDriver Issues
```bash
# Install Chrome WebDriver
sudo apt-get install chromium-chromedriver

# Use headless mode
config.enable_selenium = True
```

### Performance Optimization

#### Database Indices
```sql
-- Add recommended indices for better performance
CREATE INDEX CONCURRENTLY idx_bills_sponsor_date ON bills(sponsor_id, introduced_date);
CREATE INDEX CONCURRENTLY idx_votes_politician_date ON votes(politician_id, vote_date);
CREATE INDEX CONCURRENTLY idx_documents_source_type ON documents(source_id, document_type);
```

#### Parallel Processing
```python
# Increase concurrent requests for faster ingestion
config.max_concurrent_requests = 20
config.rate_limit_per_second = 10
```

#### Disk Space Management
```bash
# Clean up old logs
find logs/ -name "*.log" -mtime +30 -delete

# Compress backup files
gzip data/backups/*.sql
```

### Monitoring & Alerting

#### Health Checks
```bash
# Monitor ingestion performance
python scripts/health-check.py --check-ingestion

# Database health
python scripts/health-check.py --check-database
```

#### Log Analysis
```bash
# Monitor for errors
tail -f logs/ingestion_*.log | grep ERROR

# Check success rates
grep "✅" logs/ingestion_*.log | wc -l
```

## Best Practices

### Data Quality
1. **Validation**: Always enable data validation for production
2. **Deduplication**: Use content hashing to prevent duplicates
3. **Monitoring**: Set up alerts for ingestion failures
4. **Backup**: Regular database backups before major ingestions

### Performance
1. **Rate Limiting**: Respect API rate limits to avoid blocking
2. **Batch Processing**: Use appropriate batch sizes for your hardware
3. **Parallel Processing**: Balance concurrency with system resources
4. **Indexing**: Create database indices for frequent queries

### Security
1. **API Keys**: Store API keys securely in environment variables
2. **Database Access**: Use restricted database users for applications
3. **Network Security**: Implement firewall rules for database access
4. **Data Privacy**: Follow data retention and privacy policies

### Maintenance
1. **Regular Updates**: Keep source configurations updated
2. **Schema Evolution**: Plan for database schema changes
3. **Performance Monitoring**: Track ingestion performance over time
4. **Error Analysis**: Regular review of error logs and patterns

## Support

For additional support:
1. Check the troubleshooting section above
2. Review log files in the `logs/` directory
3. Test individual components before full ingestion runs
4. Use the health check scripts for system validation

The government data ingestion system provides a comprehensive foundation for political analysis, legislative tracking, and government transparency initiatives.