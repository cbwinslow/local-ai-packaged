"""
Task handlers for the worker.

This module contains the task handlers that process different types of tasks
in the background worker.
"""

from typing import Dict, Any, Type
from ...models import TaskType
from .base import TaskHandler
from .bills import BillIngestHandler, BillActionIngestHandler, BillSubjectIngestHandler, BillCosponsorIngestHandler
from .members import MemberIngestHandler
from .documents import DocumentDownloadHandler, DocumentProcessHandler
from .reports import ReportGenerateHandler
from .exports import DataExportHandler

# Map of task types to their handler classes
HANDLERS: Dict[TaskType, Type[TaskHandler]] = {
    TaskType.BILL_INGEST: BillIngestHandler,
    TaskType.MEMBER_INGEST: MemberIngestHandler,
    TaskType.BILL_ACTION_INGEST: BillActionIngestHandler,
    TaskType.BILL_SUBJECT_INGEST: BillSubjectIngestHandler,
    TaskType.BILL_COSPONSOR_INGEST: BillCosponsorIngestHandler,
    TaskType.DOCUMENT_DOWNLOAD: DocumentDownloadHandler,
    TaskType.DOCUMENT_PROCESS: DocumentProcessHandler,
    TaskType.REPORT_GENERATE: ReportGenerateHandler,
    TaskType.DATA_EXPORT: DataExportHandler,
}

def get_handler_class(task_type: TaskType) -> Type[TaskHandler]:
    """Get the handler class for a task type.
    
    Args:
        task_type: The task type
        
    Returns:
        The handler class
        
    Raises:
        ValueError: If no handler is registered for the task type
    """
    handler_class = HANDLERS.get(task_type)
    if not handler_class:
        raise ValueError(f"No handler registered for task type: {task_type}")
    return handler_class

__all__ = [
    'TaskHandler',
    'BillIngestHandler',
    'MemberIngestHandler',
    'BillActionIngestHandler',
    'BillSubjectIngestHandler',
    'BillCosponsorIngestHandler',
    'DocumentDownloadHandler',
    'DocumentProcessHandler',
    'ReportGenerateHandler',
    'DataExportHandler',
    'get_handler_class',
]
