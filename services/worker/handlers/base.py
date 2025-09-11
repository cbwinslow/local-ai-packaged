"""Base task handler."""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from models import TaskInDB

class TaskHandler:
    """Base class for task handlers.
    
    Subclasses should implement the handle() method to process tasks.
    """
    
    def __init__(self, db: Session):
        """Initialize the handler.
        
        Args:
            db: Database session
        """
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
    
    def log(self, message: str, level: str = 'info', **kwargs) -> None:
        """Log a message with task context.
        
        Args:
            message: The message to log
            level: Log level (debug, info, warning, error, critical)
            **kwargs: Additional context to include in the log
        """
        # Note: This method requires task context to be available
        # Subclasses should ensure task is passed or available in scope
        task = getattr(self, '_current_task', None)

        log_context = {
            'task_id': str(task.id) if task is not None else None,
            'task_type': task.task_type if task is not None else None,
            'handler': self.__class__.__name__,
            **kwargs
        }
        
        # Use Python logging if logger not set up
        logger = getattr(self, 'logger', logging.getLogger(__name__))
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(message, extra={'context': log_context})
