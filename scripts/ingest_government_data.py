#!/usr/bin/env python3.10

"""
Government Data Ingestion Script
Ingests bills, members, and votes from congress.gov API into Supabase SQL queue.
Uses requests for API, SQLAlchemy for DB, and logs progress.

Prerequisites:
- pip install requests sqlalchemy psycopg2-binary tweepy transformers torch
- Supabase running with .env vars (POSTGRES_URL, etc.).
- API key for congress.gov (free, register at https://api.congress.gov).
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
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import time

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ingestion.log')
    ]
)
logger = logging.getLogger(__name__)

# Config
CONGRESS_API_KEY = os.getenv('CONGRESS_API_KEY', 'your_api_key_here')
POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
BILLS_ENDPOINT = 'https://api.congress.gov/v3/bill'
MEMBERS_ENDPOINT = 'https://api.congress.gov/v3/member'
VOTES_ENDPOINT = 'https://api.congress.gov/v3/vote'
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

class Bill(Base):
    __tablename__ = 'bills'
    id = Column(Integer, primary_key=True)
    bill_id = Column(String, unique=True, index=True)
    title = Column(String)
    sponsor = Column(String)
    summary = Column(String)
    status = Column(String)
    introduced_date = Column(DateTime)
    bill_metadata = Column(JSON, name='metadata')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Member(Base):
    __tablename__ = 'members'
    id = Column(Integer, primary_key=True)
    member_id = Column(String, unique=True, index=True)
    name = Column(String)
    party = Column(String)
    state = Column(String)
    twitter_handle = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True)
    vote_id = Column(String, unique=True, index=True)
    bill_id = Column(String, index=True)
    member_id = Column(String, index=True)
    position = Column(String)
    date = Column(DateTime)
    vote_metadata = Column(JSON, name='metadata')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class IngestionLog(Base):
    __tablename__ = 'ingestion_logs'
    id = Column(Integer, primary_key=True)
    entity_type = Column(String)  # 'bill', 'member', 'vote'
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
    for table_class in [Bill, Member, Vote, IngestionLog]:
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

def ingest_bills(limit: int = 100, offset: int = 0) -> int:
    """Ingest bills from congress.gov with pagination."""
    try:
        params: Dict[str, Any] = {
            'api_key': CONGRESS_API_KEY,
            'format': 'json',
            'limit': min(limit, 250),  # API max is 250
            'offset': offset
        }
        
        data = make_api_request(BILLS_ENDPOINT, params)
        if not data or 'bills' not in data:
            logger.error("No bill data received from API")
            log_ingestion('bill', 0, 'failed', 'No data received')
            return 0
            
        bills = data.get('bills', [])
        if not bills:
            logger.info("No more bills to process")
            return 0
            
        db = next(get_db())
        processed = 0
        
        for bill in bills:
            try:
                bill_id = bill.get('bill_id')
                if not bill_id:
                    logger.warning("Skipping bill with no ID")
                    continue
                    
                existing = db.query(Bill).filter(Bill.bill_id == bill_id).first()
                if not existing:
                    new_bill = Bill(
                        bill_id=bill_id,
                        title=bill.get('title', ''),
                        sponsor=bill.get('sponsor', {}).get('name', ''),
                        summary=bill.get('summary', ''),
                        status=bill.get('status', ''),
                        introduced_date=datetime.fromisoformat(
                            bill.get('introduced_date', datetime.now(timezone.utc).isoformat())
                        ),
                        bill_metadata=bill
                    )
                    db.add(new_bill)
                    processed += 1
            except Exception as e:
                logger.error("Error processing bill %s: %s", bill.get('bill_id', 'unknown'), str(e))
                db.rollback()
                continue
                
        db.commit()
        logger.info("Processed %d bills", processed)
        log_ingestion('bill', processed, 'success' if processed > 0 else 'partial')
        return len(bills)
        
    except Exception as e:
        logger.error("Error in ingest_bills: %s", str(e), exc_info=True)
        log_ingestion('bill', 0, 'failed', str(e))
        return 0

def ingest_members(limit: int = 100, offset: int = 0) -> int:
    """Ingest members from congress.gov with pagination."""
    try:
        params: Dict[str, Any] = {
            'api_key': CONGRESS_API_KEY,
            'format': 'json',
            'limit': min(limit, 250),
            'offset': offset
        }
        
        data = make_api_request(MEMBERS_ENDPOINT, params)
        if not data or 'members' not in data:
            logger.error("No member data received from API")
            log_ingestion('member', 0, 'failed', 'No data received')
            return 0
            
        members = data.get('members', [])
        if not members:
            logger.info("No more members to process")
            return 0
            
        db = next(get_db())
        processed = 0
        
        for member in members:
            try:
                member_id = member.get('bioguide_id')
                if not member_id:
                    logger.warning("Skipping member with no ID")
                    continue
                    
                existing = db.query(Member).filter(Member.member_id == member_id).first()
                if not existing:
                    new_member = Member(
                        member_id=member_id,
                        name=member.get('name', ''),
                        party=member.get('party', ''),
                        state=member.get('state', ''),
                        twitter_handle=member.get('twitter', '')
                    )
                    db.add(new_member)
                    processed += 1
            except Exception as e:
                logger.error(
                    "Error processing member %s: %s",
                    member.get('bioguide_id', 'unknown'),
                    str(e)
                )
                db.rollback()
                continue
                
        db.commit()
        logger.info("Processed %d members", processed)
        log_ingestion('member', processed, 'success' if processed > 0 else 'partial')
        return len(members)
        
    except Exception as e:
        logger.error("Error in ingest_members: %s", str(e), exc_info=True)
        log_ingestion('member', 0, 'failed', str(e))
        return 0

def ingest_votes(limit: int = 100, offset: int = 0) -> int:
    """Ingest votes from congress.gov with pagination."""
    try:
        params: Dict[str, Any] = {
            'api_key': CONGRESS_API_KEY,
            'format': 'json',
            'limit': min(limit, 250),
            'offset': offset
        }
        
        data = make_api_request(VOTES_ENDPOINT, params)
        if not data or 'votes' not in data:
            logger.error("No vote data received from API")
            log_ingestion('vote', 0, 'failed', 'No data received')
            return 0
            
        votes = data.get('votes', [])
        if not votes:
            logger.info("No more votes to process")
            return 0
            
        db = next(get_db())
        processed = 0
        
        for vote in votes:
            try:
                vote_id = vote.get('vote_id')
                if not vote_id:
                    logger.warning("Skipping vote with no ID")
                    continue
                    
                existing = db.query(Vote).filter(Vote.vote_id == vote_id).first()
                if not existing:
                    new_vote = Vote(
                        vote_id=vote_id,
                        bill_id=vote.get('bill_id', ''),
                        member_id=vote.get('member_id', ''),
                        position=vote.get('position', ''),
                        date=datetime.fromisoformat(
                            vote.get('date', datetime.now(timezone.utc).isoformat())
                        ),
                        vote_metadata=vote
                    )
                    db.add(new_vote)
                    processed += 1
            except Exception as e:
                logger.error("Error processing vote %s: %s", vote.get('vote_id', 'unknown'), str(e))
                db.rollback()
                continue
                
        db.commit()
        logger.info("Processed %d votes", processed)
        log_ingestion('vote', processed, 'success' if processed > 0 else 'partial')
        return len(votes)
        
    except Exception as e:
        logger.error("Error in ingest_votes: %s", str(e), exc_info=True)
        log_ingestion('vote', 0, 'failed', str(e))
        return 0

def main() -> int:
    """Main function to run the ingestion process."""
    logger.info("Starting government data ingestion")
    
    try:
        # Create tables if they don't exist
        create_tables()
        
        # Ingest data with pagination
        batch_size = 100
        
        # Ingest bills
        logger.info("Starting bill ingestion")
        offset = 0
        while True:
            count = ingest_bills(batch_size, offset)
            if count < batch_size:
                break
            offset += count
            time.sleep(1)  # Be nice to the API
        
        # Ingest members
        logger.info("Starting member ingestion")
        offset = 0
        while True:
            count = ingest_members(batch_size, offset)
            if count < batch_size:
                break
            offset += count
            time.sleep(1)
        
        # Ingest votes
        logger.info("Starting vote ingestion")
        offset = 0
        while True:
            count = ingest_votes(batch_size, offset)
            if count < batch_size:
                break
            offset += count
            time.sleep(1)
        
        logger.info("Government data ingestion complete")
        return 0
        
    except Exception as e:
        logger.error("Fatal error in main: %s", str(e), exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())