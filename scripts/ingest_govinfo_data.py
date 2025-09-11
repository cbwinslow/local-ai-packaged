#!/usr/bin/env python3
"""
GovInfo Data Ingestion Script
Ingests government documents from govinfo.gov API into the database.
Uses requests for API, SQLAlchemy for DB, and logs progress.

Prerequisites:
- pip install requests sqlalchemy psycopg2-binary
- Database running with .env vars (POSTGRES_URL, etc.).
- API key for govinfo.gov (register at https://api.data.gov).
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Generator
from urllib.parse import urlencode
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import time

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('govinfo_ingestion.log')
    ]
)
logger = logging.getLogger(__name__)

# Config
GOVINFO_API_KEY = os.getenv('GOVINFO_API_KEY', 'your_api_key_here')
POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
GOVINFO_API_BASE = 'https://api.govinfo.gov'
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Configure requests session with retry
session = requests.Session()
retries = Retry(
    total=MAX_RETRIES,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
session.mount('https://', HTTPAdapter(max_retries=retries))

# SQLAlchemy setup
Base = declarative_base()

class GovInfoDocument(Base):
    __tablename__ = 'govinfo_documents'
    id = Column(Integer, primary_key=True)
    package_id = Column(String, unique=True, index=True)
    collection_code = Column(String)
    title = Column(Text)
    category = Column(String)
    document_type = Column(String)
    branch = Column(String)
    publisher = Column(String)
    publication_date = Column(DateTime)
    last_modified = Column(DateTime)
    raw_metadata = Column(JSON, name='metadata')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class IngestionLog(Base):
    __tablename__ = 'ingestion_logs'
    id = Column(Integer, primary_key=True)
    entity_type = Column(String)  # 'govinfo_document'
    records_processed = Column(Integer)
    status = Column(String)  # 'success', 'partial', 'failed'
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

def get_db() -> Generator[Session, None, None]:
    """Get a database session."""
    engine = create_engine(POSTGRES_URL, poolclass=NullPool)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables() -> None:
    """Create database tables if they don't exist."""
    engine = create_engine(POSTGRES_URL)
    inspector = inspect(engine)
    
    # Only create tables that don't exist
    for table_class in [GovInfoDocument, IngestionLog]:
        if not inspector.has_table(table_class.__tablename__):
            table_class.__table__.create(engine)
    
    logger.info("Database tables verified/created")

def make_api_request(url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Make an API request with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                logger.warning(
                    "Request failed (attempt %d/%d). Retrying in %ds...",
                    attempt + 1, MAX_RETRIES, wait_time
                )
                time.sleep(wait_time)
                continue
            logger.error("API request failed after %d attempts: %s", MAX_RETRIES, str(e))
            return None
    return None

def log_ingestion(entity_type: str, records_processed: int, status: str, error: Optional[str] = None) -> None:
    """Log the ingestion result to the database."""
    db = next(get_db())
    try:
        log = IngestionLog(
            entity_type=entity_type,
            records_processed=records_processed,
            status=status,
            error_message=error
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to log ingestion: %s", str(e))
    finally:
        db.close()

def get_collection_list() -> List[Dict[str, Any]]:
    """Get list of available collections from govinfo API."""
    try:
        params = {
            'api_key': GOVINFO_API_KEY
        }
        
        # Try to get collections - this might need adjustment based on actual API
        url = f"{GOVINFO_API_BASE}/collections"
        data = make_api_request(url, params)
        
        if not data:
            logger.warning("Could not retrieve collections list from API")
            # Return a default list of known collections
            return [
                {"collectionCode": "CPD", "name": "Compilation of Presidential Documents"},
                {"collectionCode": "FR", "name": "Federal Register"},
                {"collectionCode": "CFR", "name": "Code of Federal Regulations"},
                {"collectionCode": "BILLS", "name": "Congressional Bills"},
                {"collectionCode": "CRPT", "name": "Congressional Reports"},
                {"collectionCode": "CDOC", "name": "Congressional Documents"},
                {"collectionCode": "CHRG", "name": "Congressional Hearings"},
                {"collectionCode": "CPRT", "name": "Congressional Committee Prints"},
                {"collectionCode": "CREC", "name": "Congressional Record"},
                {"collectionCode": "PLAW", "name": "Public and Private Laws"},
                {"collectionCode": "STATUTE", "name": "Statutes at Large"},
                {"collectionCode": "USCODE", "name": "United States Code"}
            ]
            
        return data.get('collections', [])
    except Exception as e:
        logger.error("Error getting collection list: %s", str(e))
        return []

def ingest_collection_documents(collection_code: str, limit: int = 100, offset: int = 0) -> int:
    """Ingest documents from a specific govinfo collection."""
    try:
        params = {
            'api_key': GOVINFO_API_KEY,
            'offset': offset,
            'pageSize': min(limit, 1000)  # API limit
        }
        
        url = f"{GOVINFO_API_BASE}/collections/{collection_code}"
        data = make_api_request(url, params)
        
        if not data:
            logger.error("No data received from API for collection %s", collection_code)
            log_ingestion('govinfo_document', 0, 'failed', f'No data for {collection_code}')
            return 0
            
        packages = data.get('packages', [])
        if not packages:
            logger.info("No more documents to process for collection %s", collection_code)
            return 0
            
        db = next(get_db())
        processed = 0
        
        for package in packages:
            try:
                package_id = package.get('packageId')
                if not package_id:
                    logger.warning("Skipping package with no ID in collection %s", collection_code)
                    continue
                    
                existing = db.query(GovInfoDocument).filter(GovInfoDocument.package_id == package_id).first()
                if not existing:
                    # Get detailed package information
                    detail_params = {'api_key': GOVINFO_API_KEY}
                    detail_url = f"{GOVINFO_API_BASE}/packages/{package_id}"
                    detail_data = make_api_request(detail_url, detail_params)
                    
                    if not detail_data:
                        detail_data = package  # Use summary data if detail request fails
                    
                    publication_date = None
                    if detail_data.get('dateIssued'):
                        try:
                            publication_date = datetime.fromisoformat(detail_data['dateIssued'].replace('Z', '+00:00'))
                        except:
                            pass
                    
                    last_modified = None
                    if detail_data.get('lastModified'):
                        try:
                            last_modified = datetime.fromisoformat(detail_data['lastModified'].replace('Z', '+00:00'))
                        except:
                            pass
                    
                    new_document = GovInfoDocument(
                        package_id=package_id,
                        collection_code=collection_code,
                        title=detail_data.get('title', ''),
                        category=detail_data.get('category', ''),
                        document_type=detail_data.get('documentType', ''),
                        branch=detail_data.get('branch', ''),
                        publisher=detail_data.get('publisher', ''),
                        publication_date=publication_date,
                        last_modified=last_modified,
                        raw_metadata=detail_data
                    )
                    db.add(new_document)
                    processed += 1
            except Exception as e:
                logger.error("Error processing package %s: %s", package.get('packageId', 'unknown'), str(e))
                db.rollback()
                continue
                
        db.commit()
        logger.info("Processed %d documents from collection %s", processed, collection_code)
        log_ingestion('govinfo_document', processed, 'success' if processed > 0 else 'partial')
        return len(packages)
        
    except Exception as e:
        logger.error("Error in ingest_collection_documents for %s: %s", collection_code, str(e), exc_info=True)
        log_ingestion('govinfo_document', 0, 'failed', str(e))
        return 0

def ingest_presidential_documents(limit: int = 100, offset: int = 0) -> int:
    """Ingest presidential documents (Compilation of Presidential Documents)."""
    return ingest_collection_documents('CPD', limit, offset)

def ingest_federal_register_documents(limit: int = 100, offset: int = 0) -> int:
    """Ingest Federal Register documents."""
    return ingest_collection_documents('FR', limit, offset)

def ingest_congressional_reports(limit: int = 100, offset: int = 0) -> int:
    """Ingest Congressional Reports."""
    return ingest_collection_documents('CRPT', limit, offset)

def ingest_government_documents(limit: int = 100, offset: int = 0) -> int:
    """Ingest various government documents from multiple collections."""
    collections = ['CPD', 'FR', 'CFR', 'CRPT', 'CDOC', 'CHRG', 'CPRT']
    total_processed = 0
    
    for collection in collections:
        logger.info("Starting ingestion for collection: %s", collection)
        offset = 0
        while True:
            count = ingest_collection_documents(collection, limit, offset)
            if count < limit:
                break
            offset += count
            time.sleep(1)  # Be nice to the API
        total_processed += offset + count
    
    return total_processed

def main() -> int:
    """Main function to run the govinfo data ingestion process."""
    logger.info("Starting govinfo data ingestion")
    
    try:
        # Create tables if they don't exist
        create_tables()
        
        # Ingest data with pagination
        batch_size = 100
        
        # Ingest presidential documents
        logger.info("Starting presidential documents ingestion")
        offset = 0
        while True:
            count = ingest_presidential_documents(batch_size, offset)
            if count < batch_size:
                break
            offset += count
            time.sleep(1)
        
        # Ingest federal register documents
        logger.info("Starting federal register documents ingestion")
        offset = 0
        while True:
            count = ingest_federal_register_documents(batch_size, offset)
            if count < batch_size:
                break
            offset += count
            time.sleep(1)
        
        # Ingest congressional reports
        logger.info("Starting congressional reports ingestion")
        offset = 0
        while True:
            count = ingest_congressional_reports(batch_size, offset)
            if count < batch_size:
                break
            offset += count
            time.sleep(1)
        
        # Ingest other government documents
        logger.info("Starting other government documents ingestion")
        ingest_government_documents(batch_size, 0)
        
        logger.info("GovInfo data ingestion complete")
        return 0
        
    except Exception as e:
        logger.error("Fatal error in main: %s", str(e), exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())