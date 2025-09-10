"""Handlers for bill-related tasks."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from ....models import TaskInDB, TaskType, QueueStatus
from ....db.models import CongressBill, CongressBillAction, CongressBillSubject, CongressBillCosponsor
from ....services.api_clients import congress_gov_client
from .base import TaskHandler

logger = logging.getLogger(__name__)

class BillIngestHandler(TaskHandler):
    """Handler for ingesting bills from the Congress.gov API."""
    
    def handle(self, task: TaskInDB) -> Dict[str, Any]:
        """Handle a bill ingestion task.
        
        Args:
            task: The task to handle
            
        Returns:
            Dict containing the result of the task
            
        Raises:
            Exception: If the task fails
        """
        # Extract parameters from task payload
        congress = task.payload.get('congress')
        bill_type = task.payload.get('bill_type')
        bill_number = task.payload.get('bill_number')
        update_existing = task.payload.get('update_existing', True)
        
        if not all([congress, bill_type, bill_number]):
            raise ValueError("Missing required parameters: congress, bill_type, bill_number")
        
        # Check if bill already exists
        bill_id = f"{congress}{bill_type}{bill_number}"
        existing_bill = self.db.query(CongressBill).filter(
            CongressBill.bill_id == bill_id
        ).first()
        
        if existing_bill and not update_existing:
            self.log(f"Bill {bill_id} already exists and update_existing is False", "info")
            return {
                "status": "skipped",
                "reason": "Bill already exists and update_existing is False",
                "bill_id": bill_id
            }
        
        # Fetch bill data from API
        self.log(f"Fetching bill {congress}/{bill_type}{bill_number} from Congress.gov", "info")
        bill_data = congress_gov_client.get_bill(congress, bill_type, bill_number)
        
        if not bill_data or 'bill' not in bill_data:
            raise ValueError(f"Failed to fetch bill {congress}/{bill_type}{bill_number}")
        
        bill_info = bill_data['bill']
        
        # Create or update bill
        bill_data = {
            'bill_id': bill_id,
            'bill_type': bill_type,
            'number': str(bill_number),
            'congress': congress,
            'title': bill_info.get('title'),
            'short_title': bill_info.get('shortTitle'),
            'popular_title': bill_info.get('popularTitle'),
            'sponsor_name': bill_info.get('sponsor', {}).get('fullName'),
            'sponsor_id': bill_info.get('sponsor', {}).get('bioguideId'),
            'sponsor_state': bill_info.get('sponsor', {}).get('state'),
            'sponsor_party': bill_info.get('sponsor', {}).get('party'),
            'introduced_date': self._parse_date(bill_info.get('introducedDate')),
            'latest_major_action': bill_info.get('latestAction', {}).get('text'),
            'latest_major_action_date': self._parse_date(bill_info.get('latestAction', {}).get('actionDate')),
            'govtrack_url': bill_info.get('govtrackUrl'),
            'congressdotgov_url': bill_info.get('congressdotgovUrl'),
            'gpo_pdf_url': bill_info.get('gpoPdfLink'),
            'congressdotgov_title': bill_info.get('title'),
            'active': bill_info.get('active'),
            'enacted': bill_info.get('enacted'),
            'vetoed': bill_info.get('vetoed'),
            'primary_subject': bill_info.get('primarySubject'),
            'summary': bill_info.get('summary', {}).get('text'),
            'summary_short': bill_info.get('summary', {}).get('text'),
            'latest_summary': bill_info.get('latestSummary', {}).get('text'),
            'latest_summary_date': self._parse_date(bill_info.get('latestSummary', {}).get('updateDate')),
            'raw_data': bill_info,
            'last_fetched_at': datetime.utcnow()
        }
        
        if existing_bill:
            # Update existing bill
            for key, value in bill_data.items():
                setattr(existing_bill, key, value)
            bill = existing_bill
            self.log(f"Updated bill {bill_id}", "info")
        else:
            # Create new bill
            bill = CongressBill(**bill_data)
            self.db.add(bill)
            self.log(f"Created new bill {bill_id}", "info")
        
        self.db.commit()
        
        # Create tasks for related data
        self._create_related_tasks(bill, task)
        
        return {
            "status": "success",
            "bill_id": bill_id,
            "action": "created" if not existing_bill else "updated"
        }
    
    def _create_related_tasks(self, bill: CongressBill, parent_task: TaskInDB) -> None:
        """Create tasks for related bill data.
        
        Args:
            bill: The bill to create tasks for
            parent_task: The parent task
        ""
        from ....services.queue import task_queue
        
        # Create task for bill actions
        task_queue.create_task(
            TaskInDB(
                task_type=TaskType.BILL_ACTION_INGEST,
                payload={
                    'congress': bill.congress,
                    'bill_type': bill.bill_type,
                    'bill_number': bill.number,
                    'bill_id': bill.id
                },
                parent_task_id=parent_task.id,
                priority=parent_task.priority
            )
        )
        
        # Create task for bill subjects
        task_queue.create_task(
            TaskInDB(
                task_type=TaskType.BILL_SUBJECT_INGEST,
                payload={
                    'congress': bill.congress,
                    'bill_type': bill.bill_type,
                    'bill_number': bill.number,
                    'bill_id': bill.id
                },
                parent_task_id=parent_task.id,
                priority=parent_task.priority
            )
        )
        
        # Create task for bill cosponsors
        task_queue.create_task(
            TaskInDB(
                task_type=TaskType.BILL_COSPONSOR_INGEST,
                payload={
                    'congress': bill.congress,
                    'bill_type': bill.bill_type,
                    'bill_number': bill.number,
                    'bill_id': bill.id
                },
                parent_task_id=parent_task.id,
                priority=parent_task.priority
            )
        )
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse a date string from the API.
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Parsed datetime or None if invalid
        """
        if not date_str:
            return None
            
        try:
            # Try parsing ISO 8601 format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None


class BillActionIngestHandler(TaskHandler):
    """Handler for ingesting bill actions."""
    
    def handle(self, task: TaskInDB) -> Dict[str, Any]:
        """Handle a bill action ingestion task."""
        # Implementation similar to BillIngestHandler
        pass


class BillSubjectIngestHandler(TaskHandler):
    """Handler for ingesting bill subjects."""
    
    def handle(self, task: TaskInDB) -> Dict[str, Any]:
        """Handle a bill subject ingestion task."""
        # Implementation similar to BillIngestHandler
        pass


class BillCosponsorIngestHandler(TaskHandler):
    """Handler for ingesting bill cosponsors."""
    
    def handle(self, task: TaskInDB) -> Dict[str, Any]:
        """Handle a bill cosponsor ingestion task."""
        # Implementation similar to BillIngestHandler
        pass
