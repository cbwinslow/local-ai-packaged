#!/usr/bin/env python3
"""
Worker process for handling background tasks.
"""

import os
import sys
import time
import signal
import logging
import argparse
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import SessionLocal
from models import TaskType
from services.worker import Worker, create_worker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)

# Global worker instance
_worker: Optional[Worker] = None

def start_worker(
    worker_id: Optional[str] = None,
    task_types: Optional[List[TaskType]] = None,
    max_tasks: Optional[int] = None,
    poll_interval: float = 1.0,
    task_timeout: int = 300,
    shutdown_timeout: int = 30,
) -> None:
    """Start the worker.
    
    Args:
        worker_id: Unique ID for this worker
        task_types: List of task types to process (None for all)
        max_tasks: Maximum number of tasks to process before shutting down
        poll_interval: Seconds to wait between polling for new tasks
        task_timeout: Maximum time in seconds a task can run before timing out
        shutdown_timeout: Maximum time in seconds to wait for graceful shutdown
    """
    global _worker
    
    db = SessionLocal()
    
    try:
        # Create and configure worker
        _worker = create_worker(
            worker_id=worker_id,
            db=db,
            poll_interval=poll_interval,
            max_tasks=max_tasks,
            task_timeout=task_timeout,
            shutdown_timeout=shutdown_timeout,
        )
        
        # Register signal handlers
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        
        # Start the worker
        logger.info(f"Starting worker {_worker.worker_id}")
        _worker.start()
        
    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if db:
            db.close()

def handle_shutdown(signum, frame) -> None:
    """Handle shutdown signals."""
    global _worker
    
    if _worker:
        logger.info(f"Shutting down worker {_worker.worker_id}...")
        _worker.stop()
    
    sys.exit(0)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Background task worker')
    
    parser.add_argument(
        '--worker-id',
        type=str,
        help='Unique ID for this worker (default: auto-generated)'
    )
    
    parser.add_argument(
        '--task-types',
        type=str,
        nargs='+',
        choices=[t.value for t in TaskType],
        help='Task types to process (default: all)'
    )
    
    parser.add_argument(
        '--max-tasks',
        type=int,
        help='Maximum number of tasks to process before shutting down (default: unlimited)'
    )
    
    parser.add_argument(
        '--poll-interval',
        type=float,
        default=1.0,
        help='Seconds to wait between polling for new tasks (default: 1.0)'
    )
    
    parser.add_argument(
        '--task-timeout',
        type=int,
        default=300,
        help='Maximum time in seconds a task can run before timing out (default: 300)'
    )
    
    parser.add_argument(
        '--shutdown-timeout',
        type=int,
        default=30,
        help='Maximum time in seconds to wait for graceful shutdown (default: 30)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    
    return parser.parse_args()

def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    # Set log level
    logging.basicConfig(level=args.log_level)
    
    # Convert task types to enum values
    task_types = None
    if args.task_types:
        task_types = [TaskType(t) for t in args.task_types]
    
    # Start the worker
    start_worker(
        worker_id=args.worker_id,
        task_types=task_types,
        max_tasks=args.max_tasks,
        poll_interval=args.poll_interval,
        task_timeout=args.task_timeout,
        shutdown_timeout=args.shutdown_timeout,
    )

if __name__ == '__main__':
    main()
