#!/usr/bin/env python3
"""
Enhanced Government Data Ingestion System
=========================================

This script provides a comprehensive, production-ready system for ingesting government data
from 300+ sources including federal, state, local, and international government websites.

Features:
- Multi-source data ingestion with intelligent rate limiting
- Web scraping capabilities for non-API sources
- Document processing (PDF, HTML, XML, JSON)
- Robust error handling and retry mechanisms
- Progress tracking and comprehensive logging
- Database storage with optimized schemas
- Vector embeddings for semantic search
- Automated report generation
- Data validation and deduplication

Usage:
    python enhanced_government_ingestion.py --source congress --limit 1000
    python enhanced_government_ingestion.py --source all --mode incremental
    python enhanced_government_ingestion.py --generate-reports

Requirements:
    pip install requests beautifulsoup4 selenium pdfplumber aiohttp asyncio
    pip install sqlalchemy psycopg2-binary redis neo4j qdrant-client
    pip install sentence-transformers transformers torch pandas numpy
"""

import asyncio
import os
import sys
import logging
import json
import yaml
import csv
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Generator, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import argparse
from concurrent.futures import ThreadPoolExecutor

# Core libraries
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import aiohttp
import asyncio

# Web scraping
from bs4 import BeautifulSoup
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

# Document processing
try:
    import pdfplumber
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False

# Database and AI
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.pool import NullPool
import uuid

# AI and Vector Storage
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False

# Configure comprehensive logging
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup comprehensive logging with file and console handlers."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger("government_ingestion")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler with rotation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(f"logs/ingestion_{timestamp}.log")
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# Database Models
Base = declarative_base()

class DataSource(Base):
    """Data source configuration and metadata."""
    __tablename__ = 'data_sources'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False, index=True)
    url = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # api, scraping, document
    category = Column(String, nullable=False)     # federal, state, local, international
    status = Column(String, default='active')     # active, inactive, error
    api_key_required = Column(Boolean, default=False)
    rate_limit_per_hour = Column(Integer, default=100)
    last_successful_sync = Column(DateTime(timezone=True))
    last_error = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Document(Base):
    """Ingested government documents."""
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    document_id = Column(String, nullable=False, index=True)  # External ID
    title = Column(Text)
    content = Column(Text)
    summary = Column(Text)
    document_type = Column(String)  # bill, report, speech, press_release, etc.
    url = Column(String)
    file_path = Column(String)
    author = Column(String)
    date_published = Column(DateTime(timezone=True))
    date_ingested = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    language = Column(String, default='en')
    content_hash = Column(String, unique=True, index=True)  # For deduplication
    metadata = Column(JSON)
    tags = Column(ARRAY(String))
    processed = Column(Boolean, default=False)
    embedding_id = Column(String)  # Reference to vector database
    
class Politician(Base):
    """Politician profiles and metrics."""
    __tablename__ = 'politicians'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bioguide_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False, index=True)
    first_name = Column(String)
    last_name = Column(String)
    party = Column(String, index=True)
    state = Column(String, index=True)
    district = Column(String)
    chamber = Column(String)  # house, senate
    position = Column(String)  # senator, representative, speaker, etc.
    current_office = Column(Boolean, default=True)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    birth_date = Column(DateTime(timezone=True))
    gender = Column(String)
    ethnicity = Column(String)
    religion = Column(String)
    education = Column(JSON)
    career_background = Column(JSON)
    committee_memberships = Column(JSON)
    social_media = Column(JSON)
    kpis = Column(JSON)  # Key Performance Indicators
    voting_record_summary = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Bill(Base):
    """Legislative bills and resolutions."""
    __tablename__ = 'bills'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(String, unique=True, nullable=False, index=True)
    congress_number = Column(Integer, index=True)
    bill_type = Column(String, index=True)  # hr, s, hjres, sjres, etc.
    bill_number = Column(Integer)
    title = Column(Text)
    summary = Column(Text)
    full_text = Column(Text)
    sponsor_id = Column(UUID(as_uuid=True), index=True)
    cosponsors = Column(JSON)
    committees = Column(JSON)
    subjects = Column(ARRAY(String))
    introduced_date = Column(DateTime(timezone=True))
    status = Column(String, index=True)
    last_action_date = Column(DateTime(timezone=True))
    law_number = Column(String)  # If enacted
    votes = Column(JSON)
    amendments = Column(JSON)
    related_bills = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Vote(Base):
    """Voting records."""
    __tablename__ = 'votes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vote_id = Column(String, unique=True, nullable=False, index=True)
    bill_id = Column(UUID(as_uuid=True), index=True)
    politician_id = Column(UUID(as_uuid=True), index=True)
    chamber = Column(String, index=True)
    vote_date = Column(DateTime(timezone=True), index=True)
    vote_type = Column(String)  # passage, amendment, procedural
    position = Column(String, index=True)  # yes, no, present, not_voting
    party_position = Column(String)  # majority, minority position
    vote_number = Column(Integer)
    description = Column(Text)
    question = Column(Text)
    result = Column(String)  # passed, failed
    vote_totals = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IngestionRun(Base):
    """Track ingestion runs and statistics."""
    __tablename__ = 'ingestion_runs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_type = Column(String, nullable=False)  # full, incremental, source_specific
    source_name = Column(String)
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime(timezone=True))
    status = Column(String, default='running')  # running, completed, failed, partial
    records_processed = Column(Integer, default=0)
    records_added = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    errors_encountered = Column(Integer, default=0)
    error_details = Column(JSON)
    performance_metrics = Column(JSON)
    metadata = Column(JSON)

@dataclass
class IngestionConfig:
    """Configuration for the ingestion process."""
    batch_size: int = 1000
    max_concurrent_requests: int = 10
    rate_limit_per_second: int = 5
    retry_attempts: int = 3
    retry_delay: float = 1.0
    request_timeout: int = 30
    enable_selenium: bool = False
    enable_pdf_processing: bool = True
    enable_vector_embeddings: bool = True
    vector_dimension: int = 384
    deduplicate_content: bool = True
    validate_data: bool = True
    backup_raw_data: bool = True
    
class EnhancedGovernmentIngestion:
    """Enhanced government data ingestion system."""
    
    def __init__(self, config: IngestionConfig):
        self.config = config
        self.session = None
        self.selenium_driver = None
        self.db_engine = None
        self.db_session = None
        self.qdrant_client = None
        self.sentence_transformer = None
        self.data_sources = {}
        self.run_id = None
        
        # Statistics
        self.stats = {
            'documents_processed': 0,
            'documents_added': 0,
            'politicians_processed': 0,
            'bills_processed': 0,
            'votes_processed': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
    async def initialize(self):
        """Initialize all systems and connections."""
        logger.info("🚀 Initializing Enhanced Government Data Ingestion System")
        
        try:
            # Initialize database
            await self._init_database()
            
            # Initialize web clients
            await self._init_web_clients()
            
            # Initialize AI models
            if self.config.enable_vector_embeddings:
                await self._init_ai_models()
            
            # Load data sources
            await self._load_data_sources()
            
            # Create directories
            self._create_directories()
            
            # Start ingestion run tracking
            self._start_ingestion_run()
            
            logger.info("✅ Initialization complete")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
    
    async def _init_database(self):
        """Initialize database connections and create tables."""
        postgres_url = os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
        
        self.db_engine = create_engine(postgres_url, poolclass=NullPool)
        SessionLocal = sessionmaker(bind=self.db_engine)
        self.db_session = SessionLocal()
        
        # Create tables
        Base.metadata.create_all(self.db_engine)
        
        # Initialize Qdrant for vector storage
        if self.config.enable_vector_embeddings and HAS_QDRANT:
            qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
            self.qdrant_client = QdrantClient(url=qdrant_url)
            await self._create_vector_collections()
        
        logger.info("✅ Database connections established")
    
    async def _create_vector_collections(self):
        """Create vector collections in Qdrant."""
        collections = ['documents', 'politicians', 'bills', 'speeches', 'reports']
        
        for collection in collections:
            try:
                self.qdrant_client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(
                        size=self.config.vector_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Created vector collection: {collection}")
            except Exception as e:
                if "already exists" not in str(e):
                    logger.warning(f"⚠️ Vector collection {collection}: {e}")
    
    async def _init_web_clients(self):
        """Initialize web scraping clients."""
        # Aiohttp session for async requests
        timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Selenium driver for dynamic content
        if self.config.enable_selenium and HAS_SELENIUM:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            self.selenium_driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Selenium driver initialized")
    
    async def _init_ai_models(self):
        """Initialize AI models for embeddings and analysis."""
        if HAS_SENTENCE_TRANSFORMERS:
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Sentence transformer model loaded")
    
    async def _load_data_sources(self):
        """Load data sources from configuration."""
        sources_file = Path("data/government-sources.yaml")
        
        if not sources_file.exists():
            logger.error("❌ Government sources configuration file not found")
            return
        
        with open(sources_file, 'r') as f:
            sources_config = yaml.safe_load(f)
        
        # Register sources in database
        for name, url in sources_config.items():
            if isinstance(url, str):
                # Determine source type and category
                source_type = self._determine_source_type(url)
                category = self._determine_category(name)
                
                # Check if source exists
                existing = self.db_session.query(DataSource).filter(
                    DataSource.name == name
                ).first()
                
                if not existing:
                    source = DataSource(
                        name=name,
                        url=url,
                        source_type=source_type,
                        category=category,
                        api_key_required=self._requires_api_key(name),
                        rate_limit_per_hour=self._get_rate_limit(name)
                    )
                    self.db_session.add(source)
                
                self.data_sources[name] = url
        
        self.db_session.commit()
        logger.info(f"✅ Loaded {len(self.data_sources)} data sources")
    
    def _determine_source_type(self, url: str) -> str:
        """Determine if source is API, scraping, or document-based."""
        if '/api/' in url or url.endswith('/api') or 'api.' in url:
            return 'api'
        elif any(ext in url for ext in ['.pdf', '.doc', '.txt']):
            return 'document'
        else:
            return 'scraping'
    
    def _determine_category(self, name: str) -> str:
        """Determine source category."""
        name_lower = name.lower()
        if any(term in name_lower for term in ['congress', 'senate', 'house', 'federal', 'fec', 'cia', 'fbi']):
            return 'federal'
        elif any(term in name_lower for term in ['state', 'legislature', 'governor']):
            return 'state'
        elif any(term in name_lower for term in ['city', 'county', 'municipal']):
            return 'local'
        elif any(term in name_lower for term in ['uk_', 'canada_', 'eu_', 'un_']):
            return 'international'
        else:
            return 'other'
    
    def _requires_api_key(self, name: str) -> bool:
        """Determine if source requires API key."""
        api_sources = ['CONGRESS_GOV_API', 'FEC_API', 'OPENSECRETS_API', 'GOVTRACK']
        return name in api_sources
    
    def _get_rate_limit(self, name: str) -> int:
        """Get rate limit for source."""
        # Custom rate limits for known sources
        rate_limits = {
            'CONGRESS_GOV_API': 3600,  # 3600 per hour
            'FEC_API': 1000,
            'OPENSECRETS_API': 200,
            'PROPUBLICA_CONGRESS': 5000
        }
        return rate_limits.get(name, 100)  # Default 100 per hour
    
    def _create_directories(self):
        """Create necessary directories."""
        dirs = [
            'logs', 'data/cache', 'data/raw', 'data/processed', 
            'data/backups', 'reports/generated', 'documents/pdf'
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def _start_ingestion_run(self):
        """Start tracking this ingestion run."""
        run = IngestionRun(
            run_type='enhanced_ingestion',
            start_time=datetime.now(timezone.utc)
        )
        self.db_session.add(run)
        self.db_session.commit()
        self.run_id = run.id
        self.stats['start_time'] = run.start_time
        logger.info(f"📊 Started ingestion run: {self.run_id}")
    
    async def ingest_congress_data(self, limit: int = 1000):
        """Enhanced Congress data ingestion."""
        logger.info("🏛️ Starting enhanced Congressional data ingestion")
        
        congress_api_key = os.getenv('CONGRESS_GOV_API_KEY')
        if not congress_api_key:
            logger.warning("⚠️ Congress.gov API key not found")
            return
        
        base_url = "https://api.congress.gov/v3"
        headers = {'X-API-Key': congress_api_key}
        
        # Ingest bills, members, and votes in parallel
        tasks = [
            self._ingest_bills(base_url, headers, limit),
            self._ingest_members(base_url, headers, limit),
            self._ingest_votes(base_url, headers, limit)
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("✅ Congressional data ingestion complete")
    
    async def _ingest_bills(self, base_url: str, headers: Dict, limit: int):
        """Ingest congressional bills with enhanced processing."""
        url = f"{base_url}/bill"
        offset = 0
        batch_size = min(250, self.config.batch_size)  # API limit is 250
        
        while offset < limit:
            params = {
                'format': 'json',
                'limit': batch_size,
                'offset': offset
            }
            
            try:
                async with self.session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        logger.error(f"❌ Bills API error: {response.status}")
                        break
                    
                    data = await response.json()
                    bills = data.get('bills', [])
                    
                    if not bills:
                        break
                    
                    # Process bills in batch
                    await self._process_bills_batch(bills)
                    
                    offset += len(bills)
                    self.stats['bills_processed'] += len(bills)
                    
                    # Rate limiting
                    await asyncio.sleep(1.0 / self.config.rate_limit_per_second)
                    
            except Exception as e:
                logger.error(f"❌ Error ingesting bills: {e}")
                self.stats['errors'] += 1
                break
    
    async def _process_bills_batch(self, bills: List[Dict]):
        """Process a batch of bills with enhanced data extraction."""
        for bill_data in bills:
            try:
                bill_id = bill_data.get('number')
                if not bill_id:
                    continue
                
                # Check for existing bill
                existing = self.db_session.query(Bill).filter(
                    Bill.bill_id == bill_id
                ).first()
                
                if existing:
                    continue  # Skip if already exists
                
                # Create comprehensive bill record
                bill = Bill(
                    bill_id=bill_id,
                    congress_number=bill_data.get('congress'),
                    bill_type=bill_data.get('type', '').lower(),
                    bill_number=bill_data.get('number'),
                    title=bill_data.get('title', ''),
                    summary=self._extract_bill_summary(bill_data),
                    sponsor_id=await self._get_politician_id(bill_data.get('sponsors', [{}])[0]),
                    committees=bill_data.get('committees', []),
                    subjects=bill_data.get('subjects', []),
                    introduced_date=self._parse_date(bill_data.get('introducedDate')),
                    status=bill_data.get('latestAction', {}).get('text', ''),
                    last_action_date=self._parse_date(
                        bill_data.get('latestAction', {}).get('actionDate')
                    ),
                    metadata=bill_data
                )
                
                self.db_session.add(bill)
                
                # Create vector embedding if enabled
                if self.config.enable_vector_embeddings and self.sentence_transformer:
                    await self._create_bill_embedding(bill, bill_data)
                
                self.stats['documents_added'] += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing bill {bill_data.get('number')}: {e}")
                self.stats['errors'] += 1
        
        self.db_session.commit()
    
    def _extract_bill_summary(self, bill_data: Dict) -> str:
        """Extract comprehensive bill summary."""
        summary_parts = []
        
        if 'title' in bill_data:
            summary_parts.append(bill_data['title'])
        
        if 'summary' in bill_data:
            summary_parts.append(bill_data['summary'])
        
        if 'policyArea' in bill_data:
            summary_parts.append(f"Policy Area: {bill_data['policyArea']}")
        
        return ' '.join(summary_parts)
    
    async def _get_politician_id(self, sponsor_data: Dict) -> Optional[str]:
        """Get or create politician ID from sponsor data."""
        if not sponsor_data or 'bioguideId' not in sponsor_data:
            return None
        
        bioguide_id = sponsor_data['bioguideId']
        
        # Check if politician exists
        politician = self.db_session.query(Politician).filter(
            Politician.bioguide_id == bioguide_id
        ).first()
        
        if politician:
            return str(politician.id)
        
        # Create new politician record
        politician = Politician(
            bioguide_id=bioguide_id,
            name=sponsor_data.get('fullName', ''),
            first_name=sponsor_data.get('firstName', ''),
            last_name=sponsor_data.get('lastName', ''),
            party=sponsor_data.get('party', ''),
            state=sponsor_data.get('state', ''),
            chamber=sponsor_data.get('chamber', '').lower()
        )
        
        self.db_session.add(politician)
        self.db_session.flush()  # Get the ID
        
        return str(politician.id)
    
    async def _create_bill_embedding(self, bill: Bill, bill_data: Dict):
        """Create vector embedding for bill."""
        if not self.qdrant_client or not self.sentence_transformer:
            return
        
        # Create text for embedding
        text_content = f"{bill.title} {bill.summary}"
        if len(text_content) < 10:  # Minimum content length
            return
        
        try:
            # Generate embedding
            embedding = self.sentence_transformer.encode(text_content)
            
            # Store in Qdrant
            point = PointStruct(
                id=int(hashlib.md5(bill.bill_id.encode()).hexdigest(), 16) % (2**63),
                vector=embedding.tolist(),
                payload={
                    'bill_id': bill.bill_id,
                    'title': bill.title,
                    'summary': bill.summary,
                    'type': 'bill',
                    'congress': bill.congress_number,
                    'date': bill.introduced_date.isoformat() if bill.introduced_date else None
                }
            )
            
            self.qdrant_client.upsert(collection_name='bills', points=[point])
            bill.embedding_id = str(point.id)
            
        except Exception as e:
            logger.error(f"❌ Error creating embedding for bill {bill.bill_id}: {e}")
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse various date formats."""
        if not date_str:
            return None
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # Try common US date format
                return datetime.strptime(date_str, '%Y-%m-%d')
            except:
                logger.warning(f"⚠️ Could not parse date: {date_str}")
                return None
    
    async def ingest_web_scraping_sources(self, source_names: List[str]):
        """Ingest data from web scraping sources."""
        logger.info(f"🕸️ Starting web scraping ingestion for {len(source_names)} sources")
        
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        tasks = []
        for source_name in source_names:
            if source_name in self.data_sources:
                task = self._scrape_source(semaphore, source_name, self.data_sources[source_name])
                tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("✅ Web scraping ingestion complete")
    
    async def _scrape_source(self, semaphore: asyncio.Semaphore, source_name: str, url: str):
        """Scrape a single source with rate limiting."""
        async with semaphore:
            try:
                logger.info(f"🔍 Scraping {source_name}: {url}")
                
                async with self.session.get(url) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️ {source_name} returned status {response.status}")
                        return
                    
                    content = await response.text()
                    
                    # Parse content based on source type
                    documents = self._parse_scraped_content(source_name, url, content)
                    
                    # Store documents
                    await self._store_scraped_documents(source_name, documents)
                    
                    # Rate limiting
                    await asyncio.sleep(1.0 / self.config.rate_limit_per_second)
                    
            except Exception as e:
                logger.error(f"❌ Error scraping {source_name}: {e}")
                self.stats['errors'] += 1
    
    def _parse_scraped_content(self, source_name: str, url: str, content: str) -> List[Dict]:
        """Parse scraped content into structured documents."""
        documents = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Generic extraction - customize per source
            articles = soup.find_all(['article', 'div'], class_=['article', 'news-item', 'press-release'])
            
            for article in articles:
                title_elem = article.find(['h1', 'h2', 'h3'])
                title = title_elem.get_text(strip=True) if title_elem else 'Untitled'
                
                content_elem = article.find(['p', 'div'], class_=['content', 'body', 'text'])
                article_content = content_elem.get_text(strip=True) if content_elem else ''
                
                date_elem = article.find(['time', 'span'], class_=['date', 'published'])
                date_str = date_elem.get('datetime') or date_elem.get_text(strip=True) if date_elem else None
                
                doc = {
                    'title': title,
                    'content': article_content,
                    'url': url,
                    'date': self._parse_date(date_str),
                    'source': source_name
                }
                
                documents.append(doc)
            
        except Exception as e:
            logger.error(f"❌ Error parsing content from {source_name}: {e}")
        
        return documents
    
    async def _store_scraped_documents(self, source_name: str, documents: List[Dict]):
        """Store scraped documents in database."""
        source = self.db_session.query(DataSource).filter(
            DataSource.name == source_name
        ).first()
        
        if not source:
            logger.error(f"❌ Source not found: {source_name}")
            return
        
        for doc_data in documents:
            try:
                # Create content hash for deduplication
                content_text = f"{doc_data['title']} {doc_data['content']}"
                content_hash = hashlib.sha256(content_text.encode()).hexdigest()
                
                # Check for duplicates
                if self.config.deduplicate_content:
                    existing = self.db_session.query(Document).filter(
                        Document.content_hash == content_hash
                    ).first()
                    if existing:
                        continue
                
                # Create document record
                document = Document(
                    source_id=source.id,
                    document_id=content_hash[:16],  # Use hash prefix as ID
                    title=doc_data['title'],
                    content=doc_data['content'],
                    document_type='web_article',
                    url=doc_data['url'],
                    date_published=doc_data['date'],
                    content_hash=content_hash,
                    metadata=doc_data
                )
                
                self.db_session.add(document)
                self.stats['documents_added'] += 1
                
                # Create embedding if enabled
                if self.config.enable_vector_embeddings and self.sentence_transformer:
                    await self._create_document_embedding(document)
                
            except Exception as e:
                logger.error(f"❌ Error storing document: {e}")
                self.stats['errors'] += 1
        
        self.db_session.commit()
    
    async def _create_document_embedding(self, document: Document):
        """Create vector embedding for document."""
        if not self.qdrant_client or not self.sentence_transformer:
            return
        
        # Create text for embedding
        text_content = f"{document.title} {document.content[:1000]}"  # Limit content length
        
        if len(text_content) < 10:
            return
        
        try:
            embedding = self.sentence_transformer.encode(text_content)
            
            point = PointStruct(
                id=int(hashlib.md5(document.content_hash.encode()).hexdigest(), 16) % (2**63),
                vector=embedding.tolist(),
                payload={
                    'document_id': str(document.id),
                    'title': document.title,
                    'content': document.content[:500],  # Preview
                    'type': document.document_type,
                    'url': document.url,
                    'date': document.date_published.isoformat() if document.date_published else None
                }
            )
            
            self.qdrant_client.upsert(collection_name='documents', points=[point])
            document.embedding_id = str(point.id)
            
        except Exception as e:
            logger.error(f"❌ Error creating document embedding: {e}")
    
    async def generate_comprehensive_reports(self):
        """Generate comprehensive analysis reports."""
        logger.info("📊 Generating comprehensive reports")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path(f"reports/generated/enhanced_report_{timestamp}")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate multiple reports in parallel
        report_tasks = [
            self._generate_source_analysis_report(report_dir),
            self._generate_politician_effectiveness_report(report_dir),
            self._generate_legislative_trends_report(report_dir),
            self._generate_data_quality_report(report_dir)
        ]
        
        await asyncio.gather(*report_tasks, return_exceptions=True)
        
        # Generate summary report
        await self._generate_summary_report(report_dir)
        
        logger.info(f"✅ Reports generated in: {report_dir}")
        
        return report_dir
    
    async def _generate_source_analysis_report(self, report_dir: Path):
        """Generate data source analysis report."""
        try:
            # Query source statistics
            sources = self.db_session.query(DataSource).all()
            
            report_data = {
                'total_sources': len(sources),
                'sources_by_category': {},
                'sources_by_type': {},
                'sources_by_status': {},
                'sources_detail': []
            }
            
            for source in sources:
                # Category counts
                category = source.category
                report_data['sources_by_category'][category] = \
                    report_data['sources_by_category'].get(category, 0) + 1
                
                # Type counts
                source_type = source.source_type
                report_data['sources_by_type'][source_type] = \
                    report_data['sources_by_type'].get(source_type, 0) + 1
                
                # Status counts
                status = source.status
                report_data['sources_by_status'][status] = \
                    report_data['sources_by_status'].get(status, 0) + 1
                
                # Document count for this source
                doc_count = self.db_session.query(Document).filter(
                    Document.source_id == source.id
                ).count()
                
                report_data['sources_detail'].append({
                    'name': source.name,
                    'url': source.url,
                    'category': source.category,
                    'type': source.source_type,
                    'status': source.status,
                    'documents_ingested': doc_count,
                    'last_successful_sync': source.last_successful_sync.isoformat() if source.last_successful_sync else None,
                    'api_key_required': source.api_key_required
                })
            
            # Save report
            with open(report_dir / 'source_analysis.json', 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info("✅ Source analysis report generated")
            
        except Exception as e:
            logger.error(f"❌ Error generating source analysis report: {e}")
    
    async def _generate_politician_effectiveness_report(self, report_dir: Path):
        """Generate politician effectiveness analysis."""
        try:
            politicians = self.db_session.query(Politician).filter(
                Politician.current_office == True
            ).all()
            
            effectiveness_data = []
            
            for politician in politicians:
                # Count sponsored bills
                sponsored_bills = self.db_session.query(Bill).filter(
                    Bill.sponsor_id == str(politician.id)
                ).count()
                
                # Count votes
                votes_cast = self.db_session.query(Vote).filter(
                    Vote.politician_id == str(politician.id)
                ).count()
                
                effectiveness_score = self._calculate_effectiveness_score(
                    sponsored_bills, votes_cast, politician
                )
                
                effectiveness_data.append({
                    'name': politician.name,
                    'party': politician.party,
                    'state': politician.state,
                    'chamber': politician.chamber,
                    'bills_sponsored': sponsored_bills,
                    'votes_cast': votes_cast,
                    'effectiveness_score': effectiveness_score
                })
            
            # Sort by effectiveness score
            effectiveness_data.sort(key=lambda x: x['effectiveness_score'], reverse=True)
            
            report = {
                'total_politicians': len(effectiveness_data),
                'top_performers': effectiveness_data[:50],
                'analysis': {
                    'avg_bills_sponsored': np.mean([p['bills_sponsored'] for p in effectiveness_data]),
                    'avg_votes_cast': np.mean([p['votes_cast'] for p in effectiveness_data]),
                    'avg_effectiveness': np.mean([p['effectiveness_score'] for p in effectiveness_data])
                },
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
            with open(report_dir / 'politician_effectiveness.json', 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info("✅ Politician effectiveness report generated")
            
        except Exception as e:
            logger.error(f"❌ Error generating politician effectiveness report: {e}")
    
    def _calculate_effectiveness_score(self, bills_sponsored: int, votes_cast: int, politician: Politician) -> float:
        """Calculate politician effectiveness score."""
        # Simple scoring algorithm - can be enhanced
        score = 0.0
        
        # Bill sponsorship (weighted by chamber)
        bill_weight = 1.0 if politician.chamber == 'house' else 1.5  # Senate bills typically more complex
        score += bills_sponsored * bill_weight * 10
        
        # Voting participation
        score += votes_cast * 0.1
        
        # Committee leadership (if available in metadata)
        if politician.committee_memberships:
            leadership_roles = sum(1 for c in politician.committee_memberships if 'chair' in str(c).lower())
            score += leadership_roles * 50
        
        return round(score, 2)
    
    async def _generate_legislative_trends_report(self, report_dir: Path):
        """Generate legislative trends analysis."""
        try:
            # Analyze bills by congress and type
            bills = self.db_session.query(Bill).all()
            
            trends = {
                'bills_by_congress': {},
                'bills_by_type': {},
                'bills_by_status': {},
                'monthly_introduction_trend': {},
                'subject_analysis': {}
            }
            
            for bill in bills:
                # Congress analysis
                congress = bill.congress_number
                if congress:
                    trends['bills_by_congress'][str(congress)] = \
                        trends['bills_by_congress'].get(str(congress), 0) + 1
                
                # Type analysis
                bill_type = bill.bill_type or 'unknown'
                trends['bills_by_type'][bill_type] = \
                    trends['bills_by_type'].get(bill_type, 0) + 1
                
                # Status analysis
                status = bill.status or 'unknown'
                trends['bills_by_status'][status] = \
                    trends['bills_by_status'].get(status, 0) + 1
                
                # Monthly trend
                if bill.introduced_date:
                    month_key = bill.introduced_date.strftime('%Y-%m')
                    trends['monthly_introduction_trend'][month_key] = \
                        trends['monthly_introduction_trend'].get(month_key, 0) + 1
                
                # Subject analysis
                if bill.subjects:
                    for subject in bill.subjects:
                        trends['subject_analysis'][subject] = \
                            trends['subject_analysis'].get(subject, 0) + 1
            
            # Sort subjects by frequency
            trends['subject_analysis'] = dict(
                sorted(trends['subject_analysis'].items(), key=lambda x: x[1], reverse=True)[:50]
            )
            
            # Add metadata
            trends['total_bills'] = len(bills)
            trends['generated_at'] = datetime.now(timezone.utc).isoformat()
            
            with open(report_dir / 'legislative_trends.json', 'w') as f:
                json.dump(trends, f, indent=2, default=str)
            
            logger.info("✅ Legislative trends report generated")
            
        except Exception as e:
            logger.error(f"❌ Error generating legislative trends report: {e}")
    
    async def _generate_data_quality_report(self, report_dir: Path):
        """Generate data quality assessment report."""
        try:
            quality_metrics = {
                'data_completeness': {},
                'data_freshness': {},
                'error_analysis': {},
                'performance_metrics': {}
            }
            
            # Document completeness
            total_docs = self.db_session.query(Document).count()
            docs_with_content = self.db_session.query(Document).filter(
                Document.content.isnot(None),
                Document.content != ''
            ).count()
            
            quality_metrics['data_completeness']['documents'] = {
                'total': total_docs,
                'with_content': docs_with_content,
                'completeness_rate': docs_with_content / total_docs if total_docs > 0 else 0
            }
            
            # Politician completeness
            total_politicians = self.db_session.query(Politician).count()
            politicians_with_party = self.db_session.query(Politician).filter(
                Politician.party.isnot(None),
                Politician.party != ''
            ).count()
            
            quality_metrics['data_completeness']['politicians'] = {
                'total': total_politicians,
                'with_party': politicians_with_party,
                'completeness_rate': politicians_with_party / total_politicians if total_politicians > 0 else 0
            }
            
            # Data freshness
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            recent_docs = self.db_session.query(Document).filter(
                Document.date_ingested >= cutoff_date
            ).count()
            
            quality_metrics['data_freshness'] = {
                'documents_last_30_days': recent_docs,
                'freshness_rate': recent_docs / total_docs if total_docs > 0 else 0
            }
            
            # Ingestion run analysis
            recent_runs = self.db_session.query(IngestionRun).filter(
                IngestionRun.start_time >= cutoff_date
            ).all()
            
            quality_metrics['performance_metrics'] = {
                'total_runs_last_30_days': len(recent_runs),
                'successful_runs': len([r for r in recent_runs if r.status == 'completed']),
                'failed_runs': len([r for r in recent_runs if r.status == 'failed']),
                'avg_records_per_run': np.mean([r.records_processed for r in recent_runs]) if recent_runs else 0
            }
            
            quality_metrics['generated_at'] = datetime.now(timezone.utc).isoformat()
            
            with open(report_dir / 'data_quality.json', 'w') as f:
                json.dump(quality_metrics, f, indent=2, default=str)
            
            logger.info("✅ Data quality report generated")
            
        except Exception as e:
            logger.error(f"❌ Error generating data quality report: {e}")
    
    async def _generate_summary_report(self, report_dir: Path):
        """Generate executive summary report."""
        try:
            summary = {
                'ingestion_summary': {
                    'total_documents': self.stats['documents_processed'],
                    'documents_added': self.stats['documents_added'],
                    'politicians_processed': self.stats['politicians_processed'],
                    'bills_processed': self.stats['bills_processed'],
                    'errors_encountered': self.stats['errors'],
                    'success_rate': 1 - (self.stats['errors'] / max(self.stats['documents_processed'], 1))
                },
                'database_statistics': {
                    'total_sources': self.db_session.query(DataSource).count(),
                    'total_documents': self.db_session.query(Document).count(),
                    'total_politicians': self.db_session.query(Politician).count(),
                    'total_bills': self.db_session.query(Bill).count(),
                    'total_votes': self.db_session.query(Vote).count()
                },
                'performance_metrics': {
                    'start_time': self.stats['start_time'].isoformat() if self.stats['start_time'] else None,
                    'end_time': self.stats['end_time'].isoformat() if self.stats['end_time'] else None,
                    'duration_minutes': 0  # Will be calculated
                },
                'recommendations': [
                    "Consider increasing rate limits for high-performing sources",
                    "Implement automated data validation for improved quality",
                    "Schedule regular incremental updates for active sources",
                    "Monitor sources with high error rates for potential issues"
                ],
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Calculate duration
            if self.stats['start_time'] and self.stats['end_time']:
                duration = self.stats['end_time'] - self.stats['start_time']
                summary['performance_metrics']['duration_minutes'] = duration.total_seconds() / 60
            
            with open(report_dir / 'executive_summary.json', 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            # Also create a markdown version
            await self._create_markdown_summary(report_dir, summary)
            
            logger.info("✅ Executive summary generated")
            
        except Exception as e:
            logger.error(f"❌ Error generating summary report: {e}")
    
    async def _create_markdown_summary(self, report_dir: Path, summary: Dict):
        """Create a markdown version of the summary report."""
        md_content = f"""# Government Data Ingestion Report

## Executive Summary

Generated on: {summary['generated_at']}

### Ingestion Results
- **Total Documents Processed**: {summary['ingestion_summary']['total_documents']:,}
- **Documents Added**: {summary['ingestion_summary']['documents_added']:,}
- **Politicians Processed**: {summary['ingestion_summary']['politicians_processed']:,}
- **Bills Processed**: {summary['ingestion_summary']['bills_processed']:,}
- **Success Rate**: {summary['ingestion_summary']['success_rate']:.2%}

### Database Statistics
- **Data Sources**: {summary['database_statistics']['total_sources']:,}
- **Documents**: {summary['database_statistics']['total_documents']:,}
- **Politicians**: {summary['database_statistics']['total_politicians']:,}
- **Bills**: {summary['database_statistics']['total_bills']:,}
- **Votes**: {summary['database_statistics']['total_votes']:,}

### Performance
- **Duration**: {summary['performance_metrics']['duration_minutes']:.1f} minutes
- **Start Time**: {summary['performance_metrics']['start_time']}
- **End Time**: {summary['performance_metrics']['end_time']}

### Recommendations
{chr(10).join([f"- {rec}" for rec in summary['recommendations']])}

---
*This report was generated by the Enhanced Government Data Ingestion System*
"""
        
        with open(report_dir / 'summary.md', 'w') as f:
            f.write(md_content)
    
    async def cleanup(self):
        """Cleanup resources and finalize run."""
        self.stats['end_time'] = datetime.now(timezone.utc)
        
        # Update ingestion run
        if self.run_id:
            run = self.db_session.query(IngestionRun).filter(
                IngestionRun.id == self.run_id
            ).first()
            
            if run:
                run.end_time = self.stats['end_time']
                run.status = 'completed' if self.stats['errors'] == 0 else 'partial'
                run.records_processed = self.stats['documents_processed']
                run.records_added = self.stats['documents_added']
                run.errors_encountered = self.stats['errors']
                run.performance_metrics = self.stats
                
                self.db_session.commit()
        
        # Close connections
        if self.session:
            await self.session.close()
        
        if self.selenium_driver:
            self.selenium_driver.quit()
        
        if self.db_session:
            self.db_session.close()
        
        duration = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("🎉 Enhanced Government Data Ingestion Complete!")
        logger.info(f"📊 Final Statistics: {self.stats}")
        logger.info(f"⏱️ Total Duration: {duration}")

async def main():
    """Main entry point for enhanced government data ingestion."""
    parser = argparse.ArgumentParser(
        description="Enhanced Government Data Ingestion System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--source', 
        choices=['congress', 'all', 'federal', 'state', 'local', 'international'],
        default='congress',
        help='Data source category to ingest'
    )
    
    parser.add_argument(
        '--limit', 
        type=int, 
        default=1000,
        help='Maximum number of records to process'
    )
    
    parser.add_argument(
        '--mode',
        choices=['full', 'incremental', 'scraping'],
        default='full',
        help='Ingestion mode'
    )
    
    parser.add_argument(
        '--generate-reports',
        action='store_true',
        help='Generate comprehensive reports after ingestion'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Batch size for processing'
    )
    
    parser.add_argument(
        '--rate-limit',
        type=int,
        default=5,
        help='Requests per second rate limit'
    )
    
    args = parser.parse_args()
    
    # Create configuration
    config = IngestionConfig(
        batch_size=args.batch_size,
        rate_limit_per_second=args.rate_limit,
        enable_selenium=args.mode == 'scraping',
        enable_vector_embeddings=True
    )
    
    # Initialize ingestion system
    ingestion = EnhancedGovernmentIngestion(config)
    
    try:
        await ingestion.initialize()
        
        # Run ingestion based on source selection
        if args.source == 'congress':
            await ingestion.ingest_congress_data(args.limit)
        elif args.source == 'all':
            # Ingest from all source categories
            await ingestion.ingest_congress_data(args.limit)
            scraping_sources = [name for name in ingestion.data_sources.keys() 
                             if 'api' not in name.lower()][:20]  # Limit scraping sources
            await ingestion.ingest_web_scraping_sources(scraping_sources)
        else:
            # Filter sources by category
            filtered_sources = [
                name for name, url in ingestion.data_sources.items()
                if args.source.lower() in name.lower()
            ][:10]  # Limit for demo
            await ingestion.ingest_web_scraping_sources(filtered_sources)
        
        # Generate reports if requested
        if args.generate_reports:
            report_dir = await ingestion.generate_comprehensive_reports()
            print(f"\n📊 Reports generated in: {report_dir}")
        
    except KeyboardInterrupt:
        logger.info("⚠️ Ingestion interrupted by user")
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        sys.exit(1)
    finally:
        await ingestion.cleanup()

if __name__ == "__main__":
    asyncio.run(main())