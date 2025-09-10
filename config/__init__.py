"""
Configuration module for the government data pipeline.

This module handles loading and managing configuration settings from environment variables
and configuration files.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f"Loaded environment variables from {env_path}")

class Config:
    """Base configuration class."""
    
    # Application settings
    APP_NAME = os.getenv('APP_NAME', 'government-data-pipeline')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    ENV = os.getenv('ENV', 'development')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    
    # Database settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'govdata')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    DB_SSLMODE = os.getenv('DB_SSLMODE', 'prefer')
    
    # Construct database URL
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSLMODE}"
    
    # API Keys
    CONGRESS_GOV_API_KEY = os.getenv('CONGRESS_GOV_API_KEY', '')
    GOVINFO_API_KEY = os.getenv('GOVINFO_API_KEY', '')
    FEDREG_API_KEY = os.getenv('FEDREG_API_KEY', '')
    USA_SPENDING_API_KEY = os.getenv('USA_SPENDING_API_KEY', '')
    
    # API Rate Limits (requests per minute)
    CONGRESS_GOV_RATE_LIMIT = int(os.getenv('CONGRESS_GOV_RATE_LIMIT', '1000'))
    GOVINFO_RATE_LIMIT = int(os.getenv('GOVINFO_RATE_LIMIT', '1000'))
    FEDREG_RATE_LIMIT = int(os.getenv('FEDREG_RATE_LIMIT', '1000'))
    USA_SPENDING_RATE_LIMIT = int(os.getenv('USA_SPENDING_RATE_LIMIT', '1000'))
    
    # API Base URLs
    CONGRESS_GOV_API_BASE = os.getenv('CONGRESS_GOV_API_BASE', 'https://api.congress.gov/v3')
    GOVINFO_API_BASE = os.getenv('GOVINFO_API_BASE', 'https://api.govinfo.gov')
    FEDREG_API_BASE = os.getenv('FEDREG_API_BASE', 'https://www.federalregister.gov/api/v1')
    USA_SPENDING_API_BASE = os.getenv('USA_SPENDING_API_BASE', 'https://api.usaspending.gov')
    
    # Data directories
    DATA_DIR = Path(os.getenv('DATA_DIR', str(Path(__file__).parent.parent / 'data')))
    CACHE_DIR = DATA_DIR / 'cache'
    DOWNLOADS_DIR = DATA_DIR / 'downloads'
    LOGS_DIR = DATA_DIR / 'logs'
    
    # Create directories if they don't exist
    for directory in [DATA_DIR, CACHE_DIR, DOWNLOADS_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = LOGS_DIR / f'{APP_NAME}.log'
    
    # Neo4j configuration
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')
    NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')
    
    # Cache settings (in seconds)
    CACHE_TTL = int(os.getenv('CACHE_TTL', '86400'))  # 24 hours
    
    # Worker settings
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert config to dictionary, excluding sensitive information."""
        config_dict = {}
        for key, value in cls.__dict__.items():
            if key.startswith('_') or callable(value) or key.isupper() is False:
                continue
            
            # Skip sensitive data
            if any(sensitive in key.lower() for sensitive in ['key', 'password', 'secret']):
                config_dict[key] = '***REDACTED***' if value else None
            else:
                config_dict[key] = value
        
        return config_dict
    
    @classmethod
    def print_config(cls):
        """Print the current configuration (excluding sensitive data)."""
        import pprint
        print(f"\n{'='*50}\n{cls.APP_NAME} Configuration\n{'='*50}")
        pprint.pprint(cls.to_dict(), width=120)
        print("="*50 + "\n")


# Create config instance
config = Config()

# Print config in debug mode
if config.DEBUG:
    config.print_config()
