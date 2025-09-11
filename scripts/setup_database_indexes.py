#!/usr/bin/env python3
"""
Database Indexing Script
Sets up indexes for improved query performance on government data tables.
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Config
POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')

def create_indexes():
    """Create indexes for improved query performance."""
    engine = create_engine(POSTGRES_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create indexes for CongressMember table
        logger.info("Creating indexes for CongressMember table")
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_members_party ON congress_members(party)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_members_state ON congress_members(state_name)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_members_last_name ON congress_members(last_name)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_members_first_name ON congress_members(first_name)"))
        
        # Create indexes for CongressMemberRole table
        logger.info("Creating indexes for CongressMemberRole table")
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_member_roles_party ON congress_member_roles(party)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_member_roles_state ON congress_member_roles(state)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_member_roles_congress ON congress_member_roles(congress)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_member_roles_chamber ON congress_member_roles(chamber)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_member_roles_dates ON congress_member_roles(start_date, end_date)"))
        
        # Create indexes for CongressBill table
        logger.info("Creating indexes for CongressBill table")
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_bills_sponsor_party ON congress_bills(sponsor_party)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_bills_sponsor_state ON congress_bills(sponsor_state)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_bills_congress ON congress_bills(congress)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_bills_bill_type ON congress_bills(bill_type)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_bills_introduced_date ON congress_bills(introduced_date)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_bills_enacted ON congress_bills(enacted)"))
        
        # Create indexes for CongressBillCosponsor table
        logger.info("Creating indexes for CongressBillCosponsor table")
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_bill_cosponsors_party ON congress_bill_cosponsors(party)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_bill_cosponsors_state ON congress_bill_cosponsors(state)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_congress_bill_cosponsors_date ON congress_bill_cosponsors(date_cosponsored)"))
        
        # Create indexes for GovInfoDocument table
        logger.info("Creating indexes for GovInfoDocument table")
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_govinfo_documents_collection ON govinfo_documents(collection_code)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_govinfo_documents_branch ON govinfo_documents(branch)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_govinfo_documents_document_type ON govinfo_documents(document_type)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_govinfo_documents_publication_date ON govinfo_documents(publication_date)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_govinfo_documents_last_modified ON govinfo_documents(last_modified)"))
        
        # Create composite indexes for common queries
        logger.info("Creating composite indexes for common queries")
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_member_role_composite ON congress_member_roles(member_id, congress, chamber)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_bill_sponsor_composite ON congress_bills(sponsor_id, introduced_date)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_cosponsor_bill_composite ON congress_bill_cosponsors(bill_id, date_cosponsored)"))
        
        session.commit()
        logger.info("All indexes created successfully")
        
    except Exception as e:
        session.rollback()
        logger.error("Error creating indexes: %s", str(e))
        raise
    finally:
        session.close()

def drop_indexes():
    """Drop all custom indexes (for cleanup purposes)."""
    engine = create_engine(POSTGRES_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Drop indexes for CongressMember table
        session.execute(text("DROP INDEX IF EXISTS idx_congress_members_party"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_members_state"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_members_last_name"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_members_first_name"))
        
        # Drop indexes for CongressMemberRole table
        session.execute(text("DROP INDEX IF EXISTS idx_congress_member_roles_party"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_member_roles_state"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_member_roles_congress"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_member_roles_chamber"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_member_roles_dates"))
        
        # Drop indexes for CongressBill table
        session.execute(text("DROP INDEX IF EXISTS idx_congress_bills_sponsor_party"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_bills_sponsor_state"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_bills_congress"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_bills_bill_type"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_bills_introduced_date"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_bills_enacted"))
        
        # Drop indexes for CongressBillCosponsor table
        session.execute(text("DROP INDEX IF EXISTS idx_congress_bill_cosponsors_party"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_bill_cosponsors_state"))
        session.execute(text("DROP INDEX IF EXISTS idx_congress_bill_cosponsors_date"))
        
        # Drop indexes for GovInfoDocument table
        session.execute(text("DROP INDEX IF EXISTS idx_govinfo_documents_collection"))
        session.execute(text("DROP INDEX IF EXISTS idx_govinfo_documents_branch"))
        session.execute(text("DROP INDEX IF EXISTS idx_govinfo_documents_document_type"))
        session.execute(text("DROP INDEX IF EXISTS idx_govinfo_documents_publication_date"))
        session.execute(text("DROP INDEX IF EXISTS idx_govinfo_documents_last_modified"))
        
        # Drop composite indexes
        session.execute(text("DROP INDEX IF EXISTS idx_member_role_composite"))
        session.execute(text("DROP INDEX IF EXISTS idx_bill_sponsor_composite"))
        session.execute(text("DROP INDEX IF EXISTS idx_cosponsor_bill_composite"))
        
        session.commit()
        logger.info("All indexes dropped successfully")
        
    except Exception as e:
        session.rollback()
        logger.error("Error dropping indexes: %s", str(e))
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_indexes()