"""
Database module for the government data pipeline.

This module provides database connection and models for the application.
"""

from typing import Optional
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/govdata"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Create session factory
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

# Create base class for models
Base = declarative_base()
metadata = MetaData()

@contextmanager
def get_db():
    """
    Provide a transactional database session to callers.
    
    Yields a SQLAlchemy session bound to the module's engine. The session's transaction is committed when the caller completes normally; if an exception occurs, the transaction is rolled back and the exception is re-raised. The session is closed on exit in all cases.
    
    Returns:
        session (Session): A SQLAlchemy Session configured from SessionLocal.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

def init_db():
    """
    Initialize the database schema by importing model modules and creating any missing tables.
    
    Imports the application's model modules to ensure models are registered with SQLAlchemy, then invokes Base.metadata.create_all(bound to the configured engine) to create tables that do not yet exist. Logs completion when finished. Intended to be called during application startup.
    """
    Initialize the database by creating all tables.
    This should be called during application startup.
    ""
    from . import models  # Import models to register them with SQLAlchemy
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
