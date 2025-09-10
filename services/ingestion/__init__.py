"""
Data ingestion service for government data.

This module provides functions to ingest data from various government APIs
and store it in the database.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ...models import (
    BillInDB, MemberInDB, BillActionInDB, BillSubjectInDB, BillCosponsorInDB,
    TaskInDB, TaskType, QueuePriority, QueueStatus
)
from ...db.models import (
    CongressBill, CongressMember, CongressBillAction, 
    CongressBillSubject, CongressBillCosponsor, Task
)
from ...services.queue import task_queue
from ...services.api_clients import congress_gov_client

logger = logging.getLogger(__name__)

class IngestionService:
    """Service for ingesting government data."""
    
    def __init__(self, db: Session):
        """Initialize the ingestion service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def queue_bill_ingestion(
        self,
        congress: int,
        bill_type: str,
        bill_number: str,
        update_existing: bool = True,
        priority: QueuePriority = QueuePriority.NORMAL,
        parent_task_id: Optional[str] = None,
    ) -> str:
        """Queue a bill for ingestion.
        
        Args:
            congress: Congress number
            bill_type: Bill type (hr, s, etc.)
            bill_number: Bill number
            update_existing: Whether to update existing bills
            priority: Task priority
            parent_task_id: ID of parent task (if any)
            
        Returns:
            ID of the created task
        """
        task = TaskInDB(
            task_type=TaskType.BILL_INGEST,
            payload={
                'congress': congress,
                'bill_type': bill_type,
                'bill_number': bill_number,
                'update_existing': update_existing,
            },
            priority=priority,
            parent_task_id=parent_task_id,
        )
        
        return task_queue.create_task(task)
    
    def queue_member_ingestion(
        self,
        bioguide_id: str,
        update_existing: bool = True,
        priority: QueuePriority = QueuePriority.NORMAL,
        parent_task_id: Optional[str] = None,
    ) -> str:
        """Queue a member for ingestion.
        
        Args:
            bioguide_id: Bioguide ID of the member
            update_existing: Whether to update existing members
            priority: Task priority
            parent_task_id: ID of parent task (if any)
            
        Returns:
            ID of the created task
        """
        task = TaskInDB(
            task_type=TaskType.MEMBER_INGEST,
            payload={
                'bioguide_id': bioguide_id,
                'update_existing': update_existing,
            },
            priority=priority,
            parent_task_id=parent_task_id,
        )
        
        return task_queue.create_task(task)
    
    def queue_bill_action_ingestion(
        self,
        bill_id: str,
        congress: int,
        bill_type: str,
        bill_number: str,
        priority: QueuePriority = QueuePriority.NORMAL,
        parent_task_id: Optional[str] = None,
    ) -> str:
        """Queue bill actions for ingestion.
        
        Args:
            bill_id: ID of the bill
            congress: Congress number
            bill_type: Bill type (hr, s, etc.)
            bill_number: Bill number
            priority: Task priority
            parent_task_id: ID of parent task (if any)
            
        Returns:
            ID of the created task
        """
        task = TaskInDB(
            task_type=TaskType.BILL_ACTION_INGEST,
            payload={
                'bill_id': bill_id,
                'congress': congress,
                'bill_type': bill_type,
                'bill_number': bill_number,
            },
            priority=priority,
            parent_task_id=parent_task_id,
        )
        
        return task_queue.create_task(task)
    
    def queue_bill_subject_ingestion(
        self,
        bill_id: str,
        congress: int,
        bill_type: str,
        bill_number: str,
        priority: QueuePriority = QueuePriority.NORMAL,
        parent_task_id: Optional[str] = None,
    ) -> str:
        """Queue bill subjects for ingestion.
        
        Args:
            bill_id: ID of the bill
            congress: Congress number
            bill_type: Bill type (hr, s, etc.)
            bill_number: Bill number
            priority: Task priority
            parent_task_id: ID of parent task (if any)
            
        Returns:
            ID of the created task
        """
        task = TaskInDB(
            task_type=TaskType.BILL_SUBJECT_INGEST,
            payload={
                'bill_id': bill_id,
                'congress': congress,
                'bill_type': bill_type,
                'bill_number': bill_number,
            },
            priority=priority,
            parent_task_id=parent_task_id,
        )
        
        return task_queue.create_task(task)
    
    def queue_bill_cosponsor_ingestion(
        self,
        bill_id: str,
        congress: int,
        bill_type: str,
        bill_number: str,
        priority: QueuePriority = QueuePriority.NORMAL,
        parent_task_id: Optional[str] = None,
    ) -> str:
        """Queue bill cosponsors for ingestion.
        
        Args:
            bill_id: ID of the bill
            congress: Congress number
            bill_type: Bill type (hr, s, etc.)
            bill_number: Bill number
            priority: Task priority
            parent_task_id: ID of parent task (if any)
            
        Returns:
            ID of the created task
        """
        task = TaskInDB(
            task_type=TaskType.BILL_COSPONSOR_INGEST,
            payload={
                'bill_id': bill_id,
                'congress': congress,
                'bill_type': bill_type,
                'bill_number': bill_number,
            },
            priority=priority,
            parent_task_id=parent_task_id,
        )
        
        return task_queue.create_task(task)
    
    def queue_batch_ingestion(
        self,
        task_type: TaskType,
        items: List[Dict[str, Any]],
        batch_size: int = 10,
        priority: QueuePriority = QueuePriority.NORMAL,
    ) -> List[str]:
        """Queue a batch of items for ingestion.
        
        Args:
            task_type: Type of tasks to create
            items: List of item data dictionaries
            batch_size: Number of items per batch
            priority: Task priority
            
        Returns:
            List of task IDs
        """
        task_ids = []
        
        # Create batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Create a parent task for the batch
            parent_task = TaskInDB(
                task_type=task_type,
                payload={
                    'batch_size': len(batch),
                    'total_batches': (len(items) + batch_size - 1) // batch_size,
                    'current_batch': i // batch_size + 1,
                },
                priority=priority,
            )
            
            parent_task_id = task_queue.create_task(parent_task)
            
            # Create child tasks for each item in the batch
            for item in batch:
                task = TaskInDB(
                    task_type=task_type,
                    payload=item,
                    priority=priority,
                    parent_task_id=parent_task_id,
                )
                task_ids.append(task_queue.create_task(task))
            
            task_ids.append(parent_task_id)
        
        return task_ids

# Singleton instance
ingestion_service = IngestionService(None)

def get_ingestion_service(db: Optional[Session] = None) -> IngestionService:
    """Get an instance of the ingestion service.
    
    Args:
        db: Optional database session. If None, a new session will be created.
    """
    if db is None:
        from ...db import SessionLocal
        db = SessionLocal()
    
    if ingestion_service.db is None:
        ingestion_service.db = db
    
    return ingestion_service
