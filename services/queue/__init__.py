"""
SQL-based task queue system with Pydantic models.

This module provides a robust queue system for processing tasks asynchronously.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Type, TypeVar, Generic, cast
from enum import Enum
import logging

from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import Session
from pydantic import BaseModel, ValidationError

from ....db import get_db, SessionLocal
from ....models import (
    TaskInDB, TaskCreate, TaskUpdate, QueueStatus, QueuePriority, TaskType,
    BaseModelWithConfig
)
from ....db.models import Task as TaskModel

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModelWithConfig)

class QueueError(Exception):
    """Base exception for queue-related errors."""
    pass

class TaskNotFoundError(QueueError):
    """Raised when a task is not found."""
    pass

class TaskLockError(QueueError):
    """Raised when a task cannot be locked."""
    pass

class TaskValidationError(QueueError):
    """Raised when task validation fails."""
    pass

class TaskQueue:
    """SQL-based task queue with Pydantic models."""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize the task queue.
        
        Args:
            db: SQLAlchemy session. If None, a new session will be created.
        """
        self.db = db or next(get_db())
    
    def _to_pydantic(self, task: TaskModel) -> TaskInDB:
        """Convert a SQLAlchemy model to a Pydantic model."""
        try:
            # Convert task to dict
            task_dict = {
                'id': str(task.id),
                'task_type': task.task_type,
                'payload': task.payload,
                'priority': task.priority,
                'status': task.status,
                'retry_count': task.retry_count,
                'max_retries': task.max_retries,
                'error_message': task.error_message,
                'scheduled_for': task.scheduled_for,
                'parent_task_id': str(task.parent_task_id) if task.parent_task_id else None,
                'depends_on': task.depends_on or [],
                'metadata': task.metadata or {},
                'created_at': task.created_at,
                'updated_at': task.updated_at,
                'started_at': task.started_at,
                'completed_at': task.completed_at,
                'locked_at': task.locked_at,
                'locked_by': str(task.locked_by) if task.locked_by else None,
            }
            
            # Validate with Pydantic
            return TaskInDB(**task_dict)
            
        except ValidationError as e:
            logger.error(f"Failed to validate task {task.id}: {e}")
            raise TaskValidationError(f"Invalid task data: {e}")
    
    def _to_sqlalchemy(self, task: TaskCreate) -> TaskModel:
        """Convert a Pydantic model to a SQLAlchemy model."""
        try:
            # Validate input
            task_data = task.dict(exclude_unset=True)
            
            # Create SQLAlchemy model
            return TaskModel(
                id=uuid.uuid4(),
                task_type=task_data['task_type'],
                payload=task_data.get('payload', {}),
                priority=task_data.get('priority', QueuePriority.NORMAL),
                status=task_data.get('status', QueueStatus.PENDING),
                max_retries=task_data.get('max_retries', 3),
                scheduled_for=task_data.get('scheduled_for'),
                parent_task_id=task_data.get('parent_task_id'),
                depends_on=task_data.get('depends_on', []),
                metadata=task_data.get('metadata', {}),
            )
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise TaskValidationError(f"Invalid task data: {e}")
    
    def create_task(self, task: TaskCreate) -> TaskInDB:
        """Create a new task in the queue.
        
        Args:
            task: Task data
            
        Returns:
            The created task
            
        Raises:
            TaskValidationError: If the task data is invalid
        """
        try:
            # Convert to SQLAlchemy model
            db_task = self._to_sqlalchemy(task)
            
            # Add to database
            self.db.add(db_task)
            self.db.commit()
            self.db.refresh(db_task)
            
            # Convert back to Pydantic
            return self._to_pydantic(db_task)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create task: {e}")
            raise QueueError(f"Failed to create task: {e}")
    
    def get_task(self, task_id: str) -> Optional[TaskInDB]:
        """Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            The task, or None if not found
        """
        try:
            task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task:
                return None
                
            return self._to_pydantic(task)
            
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            raise QueueError(f"Failed to get task: {e}")
    
    def update_task(self, task_id: str, task_update: TaskUpdate) -> Optional[TaskInDB]:
        """Update a task.
        
        Args:
            task_id: Task ID
            task_update: Task update data
            
        Returns:
            The updated task, or None if not found
            
        Raises:
            TaskValidationError: If the update data is invalid
        """
        try:
            # Get existing task
            db_task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not db_task:
                return None
            
            # Update fields
            update_data = task_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_task, field, value)
            
            # Update timestamps
            db_task.updated_at = datetime.utcnow()
            
            # Handle status changes
            if 'status' in update_data:
                new_status = update_data['status']
                if new_status == QueueStatus.PROCESSING and not db_task.started_at:
                    db_task.started_at = datetime.utcnow()
                elif new_status in [QueueStatus.COMPLETED, QueueStatus.FAILED]:
                    db_task.completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(db_task)
            
            return self._to_pydantic(db_task)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update task {task_id}: {e}")
            raise QueueError(f"Failed to update task: {e}")
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if the task was deleted, False if not found
        """
        try:
            task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task:
                return False
                
            self.db.delete(task)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise QueueError(f"Failed to delete task: {e}")
    
    def get_next_task(
        self,
        task_types: Optional[List[TaskType]] = None,
        worker_id: Optional[str] = None,
        lock_timeout: int = 300,
        max_retries: int = 3
    ) -> Optional[TaskInDB]:
        """Get the next available task to process.
        
        Args:
            task_types: List of task types to filter by
            worker_id: ID of the worker requesting the task
            lock_timeout: Time in seconds before a locked task can be retried
            max_retries: Maximum number of retries for failed tasks
            
        Returns:
            The next task to process, or None if no tasks are available
        """
        try:
            # Calculate the cutoff time for locked tasks
            lock_cutoff = datetime.utcnow() - timedelta(seconds=lock_timeout)
            
            # Build the query
            query = self.db.query(TaskModel).filter(
                TaskModel.status.in_([QueueStatus.PENDING, QueueStatus.RETRY]),
                or_(
                    TaskModel.locked_at.is_(None),
                    TaskModel.locked_at < lock_cutoff
                ),
                or_(
                    TaskModel.retry_count < TaskModel.max_retries,
                    TaskModel.max_retries == 0
                ),
                or_(
                    TaskModel.scheduled_for.is_(None),
                    TaskModel.scheduled_for <= datetime.utcnow()
                )
            )
            
            # Filter by task type if specified
            if task_types:
                query = query.filter(TaskModel.task_type.in_(task_types))
            
            # Order by priority and creation time
            query = query.order_by(
                TaskModel.priority.desc(),
                TaskModel.created_at.asc()
            )
            
            # Lock the task for update
            task = query.with_for_update(skip_locked=True).first()
            
            if not task:
                return None
            
            # Update task status
            task.status = QueueStatus.PROCESSING
            task.locked_at = datetime.utcnow()
            task.locked_by = worker_id
            task.retry_count += 1
            task.updated_at = datetime.utcnow()
            
            self.db.commit()
            return self._to_pydantic(task)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to get next task: {e}")
            raise QueueError(f"Failed to get next task: {e}")
    
    def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """Mark a task as completed.
        
        Args:
            task_id: Task ID
            result: Optional result data to store with the task
            
        Returns:
            True if the task was marked as completed, False if not found
        """
        try:
            task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task:
                return False
            
            task.status = QueueStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.locked_at = None
            task.locked_by = None
            
            if result is not None:
                if 'metadata' not in task.metadata:
                    task.metadata = {}
                task.metadata['result'] = result
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to complete task {task_id}: {e}")
            raise QueueError(f"Failed to complete task: {e}")
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """Mark a task as failed.
        
        Args:
            task_id: Task ID
            error_message: Error message
            
        Returns:
            True if the task was marked as failed, False if not found
        """
        try:
            task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task:
                return False
            
            # Check if we should retry
            if task.retry_count < task.max_retries:
                task.status = QueueStatus.RETRY
            else:
                task.status = QueueStatus.FAILED
            
            task.error_message = error_message
            task.completed_at = datetime.utcnow()
            task.locked_at = None
            task.locked_by = None
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to fail task {task_id}: {e}")
            raise QueueError(f"Failed to fail task: {e}")
    
    def retry_task(self, task_id: str, delay_seconds: int = 0) -> bool:
        """Retry a failed task.
        
        Args:
            task_id: Task ID
            delay_seconds: Number of seconds to delay the retry
            
        Returns:
            True if the task was scheduled for retry, False if not found
        """
        try:
            task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task:
                return False
            
            task.status = QueueStatus.PENDING
            task.scheduled_for = datetime.utcnow() + timedelta(seconds=delay_seconds)
            task.locked_at = None
            task.locked_by = None
            task.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to retry task {task_id}: {e}")
            raise QueueError(f"Failed to retry task: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status information, or None if not found
        """
        try:
            task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task:
                return None
            
            return {
                'id': str(task.id),
                'task_type': task.task_type,
                'status': task.status,
                'progress': task.metadata.get('progress') if task.metadata else None,
                'started_at': task.started_at,
                'completed_at': task.completed_at,
                'error_message': task.error_message,
                'created_at': task.created_at,
                'updated_at': task.updated_at,
            }
            
        except Exception as e:
            logger.error(f"Failed to get task status {task_id}: {e}")
            raise QueueError(f"Failed to get task status: {e}")
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a completed task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task result, or None if not found or not completed
        """
        try:
            task = self.db.query(TaskModel).filter(
                TaskModel.id == task_id,
                TaskModel.status == QueueStatus.COMPLETED
            ).first()
            
            if not task or not task.metadata or 'result' not in task.metadata:
                return None
                
            return task.metadata['result']
            
        except Exception as e:
            logger.error(f"Failed to get task result {task_id}: {e}")
            raise QueueError(f"Failed to get task result: {e}")
    
    def cleanup_old_tasks(self, days: int = 7) -> int:
        """Clean up old completed or failed tasks.
        
        Args:
            days: Number of days of history to keep
            
        Returns:
            Number of tasks deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Delete tasks that are completed or failed and older than cutoff
            result = self.db.query(TaskModel).filter(
                TaskModel.status.in_([QueueStatus.COMPLETED, QueueStatus.FAILED]),
                TaskModel.completed_at < cutoff_date
            ).delete(synchronize_session=False)
            
            self.db.commit()
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to clean up old tasks: {e}")
            raise QueueError(f"Failed to clean up old tasks: {e}")


# Create a default task queue instance
task_queue = TaskQueue()
