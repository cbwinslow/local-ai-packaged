"""
Background worker for processing tasks from the task queue.
"""

import os
import time
import signal
import logging
import threading
from typing import Dict, Type, Any, Optional, List, Callable
from datetime import datetime, timedelta
import uuid

from sqlalchemy.orm import Session

from ...db import get_db, SessionLocal
from ...models import TaskType, TaskInDB, QueueStatus, QueuePriority
from ...services.queue import TaskQueue, QueueError, TaskNotFoundError, TaskLockError

logger = logging.getLogger(__name__)

class TaskHandler:
    """Base class for task handlers."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def handle(self, task: TaskInDB) -> Dict[str, Any]:
        """Handle a task.
        
        Args:
            task: The task to handle
            
        Returns:
            Dict containing the result of the task
            
        Raises:
            Exception: If the task fails
        """
        raise NotImplementedError("Subclasses must implement handle()")


class Worker:
    """Background worker that processes tasks from the queue."""
    
    def __init__(
        self,
        worker_id: Optional[str] = None,
        db: Optional[Session] = None,
        queue: Optional[TaskQueue] = None,
        poll_interval: float = 1.0,
        max_tasks: Optional[int] = None,
        task_timeout: int = 300,
        shutdown_timeout: int = 30,
    ):
        """Initialize the worker.
        
        Args:
            worker_id: Unique ID for this worker
            db: Database session
            queue: Task queue
            poll_interval: Seconds to wait between polling for new tasks
            max_tasks: Maximum number of tasks to process before shutting down
            task_timeout: Maximum time in seconds a task can run before timing out
            shutdown_timeout: Maximum time in seconds to wait for graceful shutdown
        """
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.db = db or SessionLocal()
        self.queue = queue or TaskQueue(self.db)
        self.poll_interval = poll_interval
        self.max_tasks = max_tasks
        self.task_timeout = task_timeout
        self.shutdown_timeout = shutdown_timeout
        
        self._running = False
        self._current_task = None
        self._current_task_thread = None
        self._shutdown_event = threading.Event()
        self._task_handlers: Dict[TaskType, Type[TaskHandler]] = {}
        self._tasks_processed = 0
        self._start_time = None
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
    
    def register_handler(self, task_type: TaskType, handler_class: Type[TaskHandler]) -> None:
        """Register a handler for a task type.
        
        Args:
            task_type: The task type to handle
            handler_class: The handler class (must be a subclass of TaskHandler)
        """
        if not issubclass(handler_class, TaskHandler):
            raise ValueError("Handler must be a subclass of TaskHandler")
        self._task_handlers[task_type] = handler_class
    
    def start(self) -> None:
        """Start the worker."""
        if self._running:
            logger.warning("Worker is already running")
            return
        
        logger.info(f"Starting worker {self.worker_id}")
        self._running = True
        self._shutdown_event.clear()
        self._start_time = datetime.utcnow()
        
        try:
            self._run_loop()
        except Exception as e:
            logger.error(f"Worker {self.worker_id} failed: {e}", exc_info=True)
            raise
        finally:
            self._cleanup()
    
    def stop(self, wait: bool = True) -> None:
        """Stop the worker.
        
        Args:
            wait: Whether to wait for the current task to complete
        """
        if not self._running:
            return
            
        logger.info(f"Stopping worker {self.worker_id}")
        self._shutdown_event.set()
        
        if wait and self._current_task_thread and self._current_task_thread.is_alive():
            logger.info(f"Waiting for current task to complete (timeout: {self.shutdown_timeout}s)")
            self._current_task_thread.join(timeout=self.shutdown_timeout)
            
            if self._current_task_thread.is_alive():
                logger.warning("Task did not complete within timeout, forcing shutdown")
        
        self._running = False
    
    def _run_loop(self) -> None:
        """Main worker loop."""
        logger.info(f"Worker {self.worker_id} started")
        
        while self._should_continue():
            try:
                # Get next task
                task = self.queue.get_next_task(
                    task_types=list(self._task_handlers.keys()),
                    worker_id=self.worker_id,
                    lock_timeout=self.task_timeout
                )
                
                if task:
                    self._process_task(task)
                    self._tasks_processed += 1
                    
                    # Check if we've reached the maximum number of tasks
                    if self.max_tasks and self._tasks_processed >= self.max_tasks:
                        logger.info(f"Processed maximum number of tasks ({self.max_tasks}), shutting down")
                        break
                else:
                    # No tasks available, wait before polling again
                    time.sleep(self.poll_interval)
            
            except QueueError as e:
                logger.error(f"Queue error: {e}", exc_info=True)
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {e}", exc_info=True)
                time.sleep(min(self.poll_interval * 2, 60))  # Exponential backoff with max 60s
        
        logger.info(f"Worker {self.worker_id} stopped")
    
    def _process_task(self, task: TaskInDB) -> None:
        """Process a single task.
        
        Args:
            task: The task to process
        """
        logger.info(f"Processing task {task.id} (type: {task.task_type})")
        
        # Create a new database session for this task
        db = SessionLocal()
        
        try:
            # Get the handler for this task type
            handler_class = self._task_handlers.get(task.task_type)
            if not handler_class:
                raise ValueError(f"No handler registered for task type: {task.task_type}")
            
            # Create handler instance
            handler = handler_class(db)
            
            # Process the task in a separate thread with timeout
            result = None
            error = None
            
            def task_worker():
                nonlocal result, error
                try:
                    result = handler.handle(task)
                except Exception as e:
                    error = e
            
            thread = threading.Thread(target=task_worker)
            thread.start()
            
            # Wait for the task to complete or timeout
            thread.join(timeout=self.task_timeout)
            
            if thread.is_alive():
                # Task timed out
                raise TimeoutError(f"Task {task.id} timed out after {self.task_timeout} seconds")
            
            if error:
                raise error
            
            # Task completed successfully
            self.queue.complete_task(str(task.id), result)
            logger.info(f"Completed task {task.id}")
            
        except Exception as e:
            # Task failed
            error_msg = str(e)
            logger.error(f"Task {task.id} failed: {error_msg}", exc_info=True)
            self.queue.fail_task(str(task.id), error_msg)
            
        finally:
            # Close the database session
            db.close()
    
    def _should_continue(self) -> bool:
        """Determine if the worker should continue running."""
        if not self._running:
            return False
            
        if self._shutdown_event.is_set():
            return False
            
        if self.max_tasks and self._tasks_processed >= self.max_tasks:
            return False
            
        return True
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        self._running = False
        
        try:
            if hasattr(self, 'db') and self.db:
                self.db.close()
        except Exception as e:
            logger.error(f"Error closing database connection: {e}", exc_info=True)
    
    def _handle_shutdown_signal(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics.
        
        Returns:
            Dictionary containing worker statistics
        """
        return {
            "worker_id": self.worker_id,
            "running": self._running,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "uptime": (datetime.utcnow() - self._start_time).total_seconds() if self._start_time else 0,
            "tasks_processed": self._tasks_processed,
            "current_task": str(self._current_task.id) if self._current_task else None,
            "poll_interval": self.poll_interval,
            "max_tasks": self.max_tasks,
            "task_timeout": self.task_timeout,
            "shutdown_timeout": self.shutdown_timeout,
            "registered_handlers": list(self._task_handlers.keys()),
        }


def create_worker(
    worker_id: Optional[str] = None,
    db: Optional[Session] = None,
    queue: Optional[TaskQueue] = None,
    poll_interval: float = 1.0,
    max_tasks: Optional[int] = None,
    task_timeout: int = 300,
    shutdown_timeout: int = 30,
) -> Worker:
    """Create and configure a worker.
    
    Args:
        worker_id: Unique ID for this worker
        db: Database session
        queue: Task queue
        poll_interval: Seconds to wait between polling for new tasks
        max_tasks: Maximum number of tasks to process before shutting down
        task_timeout: Maximum time in seconds a task can run before timing out
        shutdown_timeout: Maximum time in seconds to wait for graceful shutdown
        
    Returns:
        Configured worker instance
    """
    worker = Worker(
        worker_id=worker_id,
        db=db,
        queue=queue,
        poll_interval=poll_interval,
        max_tasks=max_tasks,
        task_timeout=task_timeout,
        shutdown_timeout=shutdown_timeout,
    )
    
    # Register default task handlers
    from .handlers import (
        BillIngestHandler,
        MemberIngestHandler,
        BillActionIngestHandler,
        BillSubjectIngestHandler,
        BillCosponsorIngestHandler,
        DocumentDownloadHandler,
        DocumentProcessHandler,
        ReportGenerateHandler,
        DataExportHandler,
    )
    
    worker.register_handler(TaskType.BILL_INGEST, BillIngestHandler)
    worker.register_handler(TaskType.MEMBER_INGEST, MemberIngestHandler)
    worker.register_handler(TaskType.BILL_ACTION_INGEST, BillActionIngestHandler)
    worker.register_handler(TaskType.BILL_SUBJECT_INGEST, BillSubjectIngestHandler)
    worker.register_handler(TaskType.BILL_COSPONSOR_INGEST, BillCosponsorIngestHandler)
    worker.register_handler(TaskType.DOCUMENT_DOWNLOAD, DocumentDownloadHandler)
    worker.register_handler(TaskType.DOCUMENT_PROCESS, DocumentProcessHandler)
    worker.register_handler(TaskType.REPORT_GENERATE, ReportGenerateHandler)
    worker.register_handler(TaskType.DATA_EXPORT, DataExportHandler)
    
    return worker
