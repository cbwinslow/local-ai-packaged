"""
Database models for the government data pipeline.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional, Dict, Any, Union
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Text, 
    Float, JSON, UniqueConstraint, Index, text, BigInteger, ARRAY, Enum
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB, ARRAY as PGARRAY
from sqlalchemy.orm import relationship, validates
import uuid

from . import Base  # Import the Base from db/__init__.py

# Enums for Task model
class TaskStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

class TaskPriority(int, PyEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class TaskType(str, PyEnum):
    BILL_INGEST = "bill_ingest"
    MEMBER_INGEST = "member_ingest"
    BILL_ACTION_INGEST = "bill_action_ingest"
    BILL_SUBJECT_INGEST = "bill_subject_ingest"
    BILL_COSPONSOR_INGEST = "bill_cosponsor_ingest"
    DOCUMENT_DOWNLOAD = "document_download"
    DOCUMENT_PROCESS = "document_process"
    REPORT_GENERATE = "report_generate"
    DATA_EXPORT = "data_export"

class APIKey(Base):
    """Model for storing API keys and their metadata."""
    __tablename__ = 'api_keys'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False)
    service_name = Column(String(50), nullable=False)  # e.g., 'congress_gov', 'govinfo'
    rate_limit_per_hour = Column(Integer, default=1000)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    created_by = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    api_calls = relationship("APICallLog", back_populates="api_key_rel")
    
    def __repr__(self):
        return f"<APIKey(name='{self.name}', service='{self.service_name}')>"
    
    @validates('service_name')
    def validate_service_name(self, key, service_name):
        valid_services = ['congress_gov', 'govinfo', 'usaspending', 'federal_register']
        if service_name not in valid_services:
            raise ValueError(f"Invalid service name. Must be one of: {', '.join(valid_services)}")
        return service_name


class APICallLog(Base):
    """Model for logging API calls for monitoring and rate limiting."""
    __tablename__ = 'api_call_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey('api_keys.id', ondelete='SET NULL'))
    service_name = Column(String(50), nullable=False)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    success = Column(Boolean)
    error_message = Column(Text)
    request_headers = Column(JSONB)
    response_headers = Column(JSONB)
    request_body = Column(Text)
    response_body = Column(Text)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    api_key_rel = relationship("APIKey", back_populates="api_calls")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_call_logs_service', 'service_name'),
        Index('idx_api_call_logs_created_at', 'created_at'),
        Index('idx_api_call_logs_api_key_id', 'api_key_id'),
    )
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'service_name': self.service_name,
            'endpoint': self.endpoint,
            'method': self.method,
            'status_code': self.status_code,
            'response_time_ms': self.response_time_ms,
            'success': self.success,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CongressBill(Base):
    """Model for storing bills from Congress.gov."""
    __tablename__ = 'congress_bills'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(String(100), unique=True, nullable=False)
    bill_type = Column(String(10), nullable=False)
    number = Column(String(10), nullable=False)
    congress = Column(Integer, nullable=False)
    title = Column(Text)
    short_title = Column(Text)
    popular_title = Column(Text)
    sponsor_id = Column(String(50))
    sponsor_name = Column(String(255))
    sponsor_state = Column(String(2))
    sponsor_party = Column(String(1))
    introduced_date = Column(DateTime(timezone=True))
    latest_major_action = Column(Text)
    latest_major_action_date = Column(DateTime(timezone=True))
    govtrack_url = Column(Text)
    congressdotgov_url = Column(Text)
    gpo_pdf_url = Column(Text)
    congressdotgov_title = Column(Text)
    active = Column(Boolean)
    enacted = Column(Boolean)
    vetoed = Column(Boolean)
    primary_subject = Column(Text)
    summary = Column(Text)
    summary_short = Column(Text)
    latest_summary = Column(Text)
    latest_summary_date = Column(DateTime(timezone=True))
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    last_fetched_at = Column(DateTime(timezone=True))
    
    # Relationships
    actions = relationship("CongressBillAction", back_populates="bill", cascade="all, delete-orphan")
    subjects = relationship("CongressBillSubject", back_populates="bill", cascade="all, delete-orphan")
    cosponsors = relationship("CongressBillCosponsor", back_populates="bill", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_congress_bills_congress', 'congress'),
        Index('idx_congress_bills_bill_type', 'bill_type'),
        Index('idx_congress_bills_sponsor_id', 'sponsor_id'),
        Index('idx_congress_bills_introduced_date', 'introduced_date'),
        Index('idx_congress_bills_updated_at', 'updated_at'),
    )
    
    def __repr__(self):
        return f"<CongressBill({self.bill_id}: {self.title})>"


class CongressBillAction(Base):
    """Model for storing bill actions from Congress.gov."""
    __tablename__ = 'congress_bill_actions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('congress_bills.id', ondelete='CASCADE'), nullable=False)
    action_date = Column(DateTime(timezone=True), nullable=False)
    action_text = Column(Text, nullable=False)
    action_code = Column(String(50))
    action_type = Column(String(100))
    action_committee = Column(String(255))
    acted_by = Column(String(255))
    acted_by_chamber = Column(String(20))
    acted_by_party = Column(String(1))
    acted_by_state = Column(String(2))
    acted_by_district = Column(String(10))
    acted_by_title = Column(String(100))
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    bill = relationship("CongressBill", back_populates="actions")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('bill_id', 'action_date', 'action_text', name='uq_bill_action_unique'),
        Index('idx_congress_bill_actions_bill_id', 'bill_id'),
        Index('idx_congress_bill_actions_action_date', 'action_date'),
    )
    
    def __repr__(self):
        return f"<CongressBillAction({self.bill_id}: {self.action_date} - {self.action_text[:50]}...)>"


class CongressBillSubject(Base):
    """Model for storing bill subjects from Congress.gov."""
    __tablename__ = 'congress_bill_subjects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('congress_bills.id', ondelete='CASCADE'), nullable=False)
    subject = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    bill = relationship("CongressBill", back_populates="subjects")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('bill_id', 'subject', name='uq_bill_subject_unique'),
        Index('idx_congress_bill_subjects_bill_id', 'bill_id'),
        Index('idx_congress_bill_subjects_subject', 'subject'),
    )
    
    def __repr__(self):
        return f"<CongressBillSubject({self.bill_id}: {self.subject[:50]}...)>"


class CongressBillCosponsor(Base):
    """Model for storing bill cosponsors from Congress.gov."""
    __tablename__ = 'congress_bill_cosponsors'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('congress_bills.id', ondelete='CASCADE'), nullable=False)
    bioguide_id = Column(String(20))
    thomas_id = Column(String(20))
    govtrack_id = Column(String(20))
    name = Column(String(255), nullable=False)
    state = Column(String(2))
    district = Column(String(10))
    party = Column(String(1))
    date_cosponsored = Column(DateTime(timezone=True))
    is_original_cosponsor = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    bill = relationship("CongressBill", back_populates="cosponsors")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('bill_id', 'name', 'date_cosponsored', name='uq_bill_cosponsor_unique'),
        Index('idx_congress_bill_cosponsors_bill_id', 'bill_id'),
        Index('idx_congress_bill_cosponsors_name', 'name'),
        Index('idx_congress_bill_cosponsors_state', 'state'),
    )
    
    def __repr__(self):
        return f"<CongressBillCosponsor({self.bill_id}: {self.name})>"


class CongressMember(Base):
    """Model for storing members of Congress."""
    __tablename__ = 'congress_members'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    suffix = Column(String(20))
    date_of_birth = Column(DateTime(timezone=True))
    gender = Column(String(1))
    party = Column(String(1))
    leadership_role = Column(String(100))
    twitter_account = Column(String(100))
    facebook_account = Column(String(100))
    youtube_account = Column(String(100))
    govtrack_id = Column(String(20))
    cspan_id = Column(String(20))
    votesmart_id = Column(String(20))
    icpsr_id = Column(String(20))
    crp_id = Column(String(20))
    google_entity_id = Column(String(100))
    fec_candidate_id = Column(String(20))
    url = Column(Text)
    rss_url = Column(Text)
    contact_form = Column(Text)
    in_office = Column(Boolean)
    cook_pvi = Column(String(10))
    dw_nominate = Column(Float)
    ideal_point = Column(Float)
    seniority = Column(Integer)
    next_election = Column(String(10))
    total_votes = Column(Integer)
    missed_votes = Column(Integer)
    total_present = Column(Integer)
    last_updated = Column(DateTime(timezone=True))
    ocd_id = Column(String(100))
    office = Column(Text)
    phone = Column(String(50))
    fax = Column(String(50))
    state_rank = Column(String(50))
    senate_class = Column(String(20))
    state_name = Column(String(100))
    lis_id = Column(String(10))
    missed_votes_pct = Column(Float)
    votes_with_party_pct = Column(Float)
    votes_against_party_pct = Column(Float)
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    
    # Relationships
    roles = relationship("CongressMemberRole", back_populates="member", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CongressMember({self.first_name} {self.last_name})>"


class CongressMemberRole(Base):
    """Model for storing roles of members of Congress."""
    __tablename__ = 'congress_member_roles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey('congress_members.id', ondelete='CASCADE'), nullable=False)
    congress = Column(Integer, nullable=False)
    chamber = Column(String(20), nullable=False)  # 'house', 'senate', 'joint'
    title = Column(Text)
    short_title = Column(Text)
    state = Column(String(2))
    party = Column(String(1))
    leadership_role = Column(String(100))
    fec_candidate_id = Column(String(20))
    seniority = Column(Integer)
    district = Column(String(10))
    at_large = Column(Boolean)
    ocd_id = Column(String(100))
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    office = Column(Text)
    phone = Column(String(50))
    fax = Column(String(50))
    contact_form = Column(Text)
    cook_pvi = Column(String(10))
    dw_nominate = Column(Float)
    ideal_point = Column(Float)
    next_election = Column(String(10))
    total_votes = Column(Integer)
    missed_votes = Column(Integer)
    total_present = Column(Integer)
    senate_class = Column(String(20))
    state_rank = Column(String(50))
    lis_id = Column(String(10))
    bills_sponsored = Column(Integer)
    bills_cosponsored = Column(Integer)
    missed_votes_pct = Column(Float)
    votes_with_party_pct = Column(Float)
    votes_against_party_pct = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    
    # Relationships
    member = relationship("CongressMember", back_populates="roles")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('member_id', 'congress', 'chamber', name='uq_member_role_unique'),
        Index('idx_congress_member_roles_member_id', 'member_id'),
        Index('idx_congress_member_roles_congress', 'congress'),
        Index('idx_congress_member_roles_chamber', 'chamber'),
        Index('idx_congress_member_roles_state', 'state'),
        Index('idx_congress_member_roles_party', 'party'),
    )
    
    def __repr__(self):
        return f"<CongressMemberRole({self.member_id}: {self.chamber} {self.congress}th)>"


class GovInfoCollection(Base):
    """Model for storing GovInfo collection metadata."""
    __tablename__ = 'govinfo_collections'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_code = Column(String(50), unique=True, nullable=False)  # e.g., 'BILLS', 'FR', 'CFR'
    collection_name = Column(String(255), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    package_count = Column(Integer)
    package_last_modified = Column(DateTime(timezone=True))
    download_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    last_checked_at = Column(DateTime(timezone=True))
    
    # Relationships
    packages = relationship("GovInfoPackage", back_populates="collection", cascade="all, delete-orphan")
    download_queue = relationship("GovInfoDownloadQueue", back_populates="collection", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<GovInfoCollection({self.collection_code}: {self.collection_name})>"


class GovInfoPackage(Base):
    """Model for storing GovInfo package metadata."""
    __tablename__ = 'govinfo_packages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(String(255), unique=True, nullable=False)  # e.g., 'BILLS-118hr1234ih'
    collection_id = Column(UUID(as_uuid=True), ForeignKey('govinfo_collections.id', ondelete='CASCADE'), nullable=False)
    last_modified = Column(DateTime(timezone=True), nullable=False)
    package_link = Column(Text)
    doc_class = Column(String(100))
    title = Column(Text)
    branch = Column(String(50))
    pages = Column(Integer)
    government_author1 = Column(Text)
    government_author2 = Column(Text)
    document_type = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    last_checked_at = Column(DateTime(timezone=True))
    raw_metadata = Column(JSONB)
    content = Column(Text)
    
    # Relationships
    collection = relationship("GovInfoCollection", back_populates="packages")
    download_queue = relationship("GovInfoDownloadQueue", back_populates="package", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_govinfo_packages_collection_id', 'collection_id'),
        Index('idx_govinfo_packages_last_modified', 'last_modified'),
        Index('idx_govinfo_packages_document_type', 'document_type'),
    )
    
    def __repr__(self):
        return f"<GovInfoPackage({self.package_id}: {self.title[:50]}...)>"


class GovInfoDownloadQueue(Base):
    """Model for tracking GovInfo package downloads."""
    __tablename__ = 'govinfo_download_queue'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(String(255), unique=True, nullable=False)  # Reference to package_id in govinfo_packages
    collection_id = Column(UUID(as_uuid=True), ForeignKey('govinfo_collections.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(20), nullable=False, default='pending')  # pending, downloading, completed, failed
    priority = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    last_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    collection = relationship("GovInfoCollection", back_populates="download_queue")
    package = relationship("GovInfoPackage", back_populates="download_queue", 
                          primaryjoin="foreign(GovInfoDownloadQueue.package_id) == GovInfoPackage.package_id",
                          uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_govinfo_download_queue_status', 'status'),
        Index('idx_govinfo_download_queue_priority', 'priority'),
        Index('idx_govinfo_download_queue_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<GovInfoDownloadQueue({self.package_id}: {self.status})>"


class GovInfoDocument(Base):
    """Model for storing government documents from GovInfo."""
    __tablename__ = 'govinfo_documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(String(255), unique=True, nullable=False)
    collection_code = Column(String(50))
    title = Column(Text)
    category = Column(String(100))
    document_type = Column(String(100))
    branch = Column(String(50))
    publisher = Column(String(255))
    publication_date = Column(DateTime(timezone=True))
    last_modified = Column(DateTime(timezone=True))
    raw_metadata = Column(JSONB)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    last_checked_at = Column(DateTime(timezone=True))
    
    # Indexes
    __table_args__ = (
        Index('idx_govinfo_documents_collection_code', 'collection_code'),
        Index('idx_govinfo_documents_branch', 'branch'),
        Index('idx_govinfo_documents_document_type', 'document_type'),
        Index('idx_govinfo_documents_publication_date', 'publication_date'),
        Index('idx_govinfo_documents_last_modified', 'last_modified'),
    )
    
    def __repr__(self):
        return f"<GovInfoDocument({self.package_id}: {self.title[:50]}...)>"

class Task(Base):
    """Model for tasks in the task queue."""
    __tablename__ = 'tasks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type = Column(Enum(TaskType), nullable=False)
    payload = Column(JSONB, nullable=False, default={})
    priority = Column(Enum(TaskPriority), default=TaskPriority.NORMAL, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    error_message = Column(Text)
    scheduled_for = Column(DateTime(timezone=True))
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='SET NULL'))
    depends_on = Column(ARRAY(String), default=[])  # List of task IDs this task depends on
    metadata = Column(JSONB, default={})  # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    locked_at = Column(DateTime(timezone=True))
    locked_by = Column(String(100))  # Worker ID or process ID
    
    # Relationships
    children = relationship("Task", backref='parent', remote_side=[id])
    
    __table_args__ = (
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_priority', 'priority'),
        Index('idx_tasks_created_at', 'created_at'),
        Index('idx_tasks_scheduled_for', 'scheduled_for'),
        Index('idx_tasks_locked_at', 'locked_at'),
        Index('idx_tasks_task_type', 'task_type'),
    )
    
    def __repr__(self):
        return f"<Task(id={self.id}, type={self.task_type}, status={self.status})>"

# Create a dictionary of all models for easy access
MODELS = {
    'tasks': Task,
    'api_keys': APIKey,
    'api_call_logs': APICallLog,
    'congress_bills': CongressBill,
    'congress_bill_actions': CongressBillAction,
    'congress_bill_subjects': CongressBillSubject,
    'congress_bill_cosponsors': CongressBillCosponsor,
    'congress_members': CongressMember,
    'congress_member_roles': CongressMemberRole,
    'govinfo_collections': GovInfoCollection,
    'govinfo_packages': GovInfoPackage,
    'govinfo_download_queue': GovInfoDownloadQueue,
    'govinfo_documents': GovInfoDocument,
    'task_queue': Task
}