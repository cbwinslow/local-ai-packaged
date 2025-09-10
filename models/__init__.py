"""
Pydantic models for the government data pipeline.

This module contains all the Pydantic models used for data validation and serialization.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, HttpUrl, validator, root_validator
from enum import Enum

# Common Enums
class Chamber(str, Enum):
    HOUSE = "house"
    SENATE = "senate"
    JOINT = "joint"

class Party(str, Enum):
    DEMOCRAT = "D"
    REPUBLICAN = "R"
    INDEPENDENT = "I"
    OTHER = "O"

class BillStatus(str, Enum):
    INTRODUCED = "introduced"
    COMMITTEE = "committee"
    CALENDAR = "calendar"
    FLOOR = "floor"
    PASSED_ONE_CHAMBER = "passed_one_chamber"
    PASSED_BOTH_CHAMBERS = "passed_both_chambers"
    RESOLVING_DIFFERENCES = "resolving_differences"
    TO_PRESIDENT = "to_president"
    SIGNED = "signed"
    VETOED = "vetoed"
    LAW = "law"

# Base Models
class BaseModelWithConfig(BaseModel):
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }
        orm_mode = True
        validate_assignment = True
        arbitrary_types_allowed = True

# Member Models
class MemberBase(BaseModelWithConfig):
    """Base model for a member of Congress."""
    member_id: str = Field(..., description="Unique identifier for the member")
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    suffix: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=1)
    party: Optional[Party] = None
    leadership_role: Optional[str] = None
    twitter_account: Optional[str] = None
    facebook_account: Optional[str] = None
    youtube_account: Optional[str] = None
    govtrack_id: Optional[str] = None
    cspan_id: Optional[str] = None
    votesmart_id: Optional[str] = None
    icpsr_id: Optional[str] = None
    crp_id: Optional[str] = None
    google_entity_id: Optional[str] = None
    fec_candidate_id: Optional[str] = None
    url: Optional[HttpUrl] = None
    rss_url: Optional[HttpUrl] = None
    contact_form: Optional[str] = None
    in_office: Optional[bool] = None
    cook_pvi: Optional[str] = None
    dw_nominate: Optional[float] = None
    ideal_point: Optional[float] = None
    seniority: Optional[int] = None
    next_election: Optional[str] = None
    total_votes: Optional[int] = None
    missed_votes: Optional[int] = None
    total_present: Optional[int] = None
    last_updated: Optional[datetime] = None
    ocd_id: Optional[str] = None
    office: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    state_rank: Optional[str] = None
    senate_class: Optional[str] = None
    state_name: Optional[str] = None
    lis_id: Optional[str] = None
    missed_votes_pct: Optional[float] = None
    votes_with_party_pct: Optional[float] = None
    votes_against_party_pct: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None

class MemberCreate(MemberBase):
    """Model for creating a new member."""
    pass

class MemberUpdate(MemberBase):
    """Model for updating an existing member."""
    pass

class MemberInDB(MemberBase):
    """Model for a member in the database."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config(MemberBase.Config):
        orm_mode = True

# Bill Models
class BillBase(BaseModelWithConfig):
    """Base model for a bill."""
    bill_id: str = Field(..., description="Unique identifier for the bill")
    bill_type: str = Field(..., description="Type of bill (hr, s, etc.)")
    number: str = Field(..., description="Bill number")
    congress: int = Field(..., description="Congress number")
    title: Optional[str] = None
    short_title: Optional[str] = None
    popular_title: Optional[str] = None
    sponsor_id: Optional[str] = None
    sponsor_name: Optional[str] = None
    sponsor_state: Optional[str] = None
    sponsor_party: Optional[Party] = None
    introduced_date: Optional[date] = None
    latest_major_action: Optional[str] = None
    latest_major_action_date: Optional[datetime] = None
    govtrack_url: Optional[HttpUrl] = None
    congressdotgov_url: Optional[HttpUrl] = None
    gpo_pdf_url: Optional[HttpUrl] = None
    congressdotgov_title: Optional[str] = None
    active: Optional[bool] = None
    enacted: Optional[bool] = None
    vetoed: Optional[bool] = None
    primary_subject: Optional[str] = None
    summary: Optional[str] = None
    summary_short: Optional[str] = None
    latest_summary: Optional[str] = None
    latest_summary_date: Optional[datetime] = None
    status: Optional[BillStatus] = None
    raw_data: Optional[Dict[str, Any]] = None

class BillCreate(BillBase):
    """Model for creating a new bill."""
    pass

class BillUpdate(BillBase):
    """Model for updating an existing bill."""
    pass

class BillInDB(BillBase):
    """Model for a bill in the database."""
    id: str
    created_at: datetime
    updated_at: datetime
    last_fetched_at: Optional[datetime] = None

    class Config(BillBase.Config):
        orm_mode = True

# Bill Action Models
class BillActionBase(BaseModelWithConfig):
    """Base model for a bill action."""
    bill_id: str
    action_date: datetime
    action_text: str
    action_code: Optional[str] = None
    action_type: Optional[str] = None
    action_committee: Optional[str] = None
    acted_by: Optional[str] = None
    acted_by_chamber: Optional[Chamber] = None
    acted_by_party: Optional[Party] = None
    acted_by_state: Optional[str] = None
    acted_by_district: Optional[str] = None
    acted_by_title: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

class BillActionCreate(BillActionBase):
    """Model for creating a new bill action."""
    pass

class BillActionUpdate(BillActionBase):
    """Model for updating an existing bill action."""
    pass

class BillActionInDB(BillActionBase):
    """Model for a bill action in the database."""
    id: str
    created_at: datetime

    class Config(BillActionBase.Config):
        orm_mode = True

# Queue System Models
class QueueStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

class QueuePriority(int, Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class TaskType(str, Enum):
    BILL_INGEST = "bill_ingest"
    MEMBER_INGEST = "member_ingest"
    BILL_ACTION_INGEST = "bill_action_ingest"
    BILL_SUBJECT_INGEST = "bill_subject_ingest"
    BILL_COSPONSOR_INGEST = "bill_cosponsor_ingest"
    DOCUMENT_DOWNLOAD = "document_download"
    DOCUMENT_PROCESS = "document_process"
    REPORT_GENERATE = "report_generate"
    DATA_EXPORT = "data_export"

class TaskBase(BaseModelWithConfig):
    """Base model for a task in the queue."""
    task_type: TaskType
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: QueuePriority = QueuePriority.NORMAL
    status: QueueStatus = QueueStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    parent_task_id: Optional[str] = None
    depends_on: Optional[List[str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskCreate(TaskBase):
    """Model for creating a new task."""
    pass

class TaskUpdate(TaskBase):
    """Model for updating an existing task."""
    pass

class TaskInDB(TaskBase):
    """Model for a task in the database."""
    id: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    locked_at: Optional[datetime] = None
    locked_by: Optional[str] = None

    class Config(TaskBase.Config):
        orm_mode = True

# API Models
class Pagination(BaseModel):
    """Pagination model for API responses."""
    page: int = 1
    page_size: int = 20
    total_items: int = 0
    total_pages: int = 1

class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    pagination: Optional[Pagination] = None

# Report Models
class ReportType(str, Enum):
    BILL_ACTIVITY = "bill_activity"
    MEMBER_ACTIVITY = "member_activity"
    VOTE_ANALYSIS = "vote_analysis"
    COMMITTEE_ACTIVITY = "committee_activity"
    DOCUMENT_ANALYSIS = "document_analysis"
    CUSTOM = "custom"

class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ReportBase(BaseModelWithConfig):
    """Base model for a report."""
    report_type: ReportType
    title: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: ReportStatus = ReportStatus.PENDING
    generated_by: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReportCreate(ReportBase):
    """Model for creating a new report."""
    pass

class ReportUpdate(ReportBase):
    """Model for updating an existing report."""
    pass

class ReportInDB(ReportBase):
    """Model for a report in the database."""
    id: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[HttpUrl] = None

    class Config(ReportBase.Config):
        orm_mode = True

# Export all models
__all__ = [
    # Enums
    'Chamber', 'Party', 'BillStatus', 'QueueStatus', 'QueuePriority', 'TaskType',
    'ReportType', 'ReportStatus',
    
    # Base Models
    'BaseModelWithConfig',
    
    # Member Models
    'MemberBase', 'MemberCreate', 'MemberUpdate', 'MemberInDB',
    
    # Bill Models
    'BillBase', 'BillCreate', 'BillUpdate', 'BillInDB',
    
    # Bill Action Models
    'BillActionBase', 'BillActionCreate', 'BillActionUpdate', 'BillActionInDB',
    
    # Queue System Models
    'TaskBase', 'TaskCreate', 'TaskUpdate', 'TaskInDB',
    
    # API Models
    'Pagination', 'APIResponse',
    
    # Report Models
    'ReportBase', 'ReportCreate', 'ReportUpdate', 'ReportInDB',
]
