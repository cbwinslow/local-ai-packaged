# Task Queue System

## Overview

The task queue system provides a robust, persistent way to manage background jobs for the government data ingestion pipeline. It's built on top of PostgreSQL and SQLAlchemy, with Pydantic models for type safety and validation.

## Key Components

### 1. Database Models

- **Task**: Represents a unit of work in the queue
  - Status: pending, processing, completed, failed, retry
  - Priority: 1 (low) to 4 (urgent)
  - Task types: bill_ingest, member_ingest, etc.
  - Supports parent-child relationships and dependencies

### 2. Queue Service (`services/queue/__init__.py`)

Core queue operations:
- Create, retrieve, update, and delete tasks
- Lock tasks for processing
- Handle task completion/failure
- Retry failed tasks with exponential backoff
- Clean up old tasks

### 3. Worker System (`services/worker/`)

- **Worker**: Processes tasks from the queue
  - Polls for available tasks
  - Executes task handlers
  - Handles timeouts and retries
  - Graceful shutdown support

- **Task Handlers**: Implement business logic for specific task types
  - Bill ingestion
  - Member data updates
  - Document processing
  - Report generation
  - Data exports

## Usage

### Starting a Worker

```bash
# Start a worker with default settings
python -m scripts.worker

# Custom worker configuration
python -m scripts.worker \
  --worker-id worker-1 \
  --task-types bill_ingest member_ingest \
  --max-tasks 100 \
  --poll-interval 2.0 \
  --task-timeout 600 \
  --log-level INFO
```

### Creating Tasks

```python
from models import TaskInDB, TaskType, QueuePriority
from services.queue import task_queue

# Create a new task
task = TaskInDB(
    task_type=TaskType.BILL_INGEST,
    payload={
        'congress': 118,
        'bill_type': 'hr',
        'bill_number': '1',
        'update_existing': True
    },
    priority=QueuePriority.NORMAL
)

# Add to queue
task_id = task_queue.create_task(task)
```

### Task Dependencies

```python
# Create a parent task
parent_task = TaskInDB(
    task_type=TaskType.BILL_INGEST,
    payload={
        'congress': 118,
        'bill_type': 'hr',
        'bill_number': '1'
    }
)
parent_id = task_queue.create_task(parent_task)

# Create a dependent task
child_task = TaskInDB(
    task_type=TaskType.BILL_ACTION_INGEST,
    payload={
        'bill_id': '118hr1',
        'congress': 118,
        'bill_type': 'hr',
        'bill_number': '1'
    },
    parent_task_id=parent_id
)
child_id = task_queue.create_task(child_task)
```

## Monitoring

The queue system provides several ways to monitor tasks:

1. **Database Queries**:
   ```sql
   -- Pending tasks by priority
   SELECT priority, COUNT(*) 
   FROM tasks 
   WHERE status = 'pending' 
   GROUP BY priority 
   ORDER BY priority DESC;
   
   -- Failed tasks
   SELECT task_type, error_message 
   FROM tasks 
   WHERE status = 'failed' 
   ORDER BY updated_at DESC 
   LIMIT 10;
   ```

2. **Worker Logs**:
   - Each worker logs its activities with structured context
   - Includes task IDs, timing, and error details

3. **Metrics** (TODO):
   - Tasks processed per minute
   - Average processing time
   - Error rates by task type
   - Queue depth

## Error Handling

- Failed tasks are automatically retried with exponential backoff
- After max retries, tasks are marked as failed
- Error details are stored in the task record
- Dead letter queue for manual inspection of problematic tasks

## Scaling

- Multiple workers can run in parallel
- Workers can be specialized by task type
- Horizontal scaling by adding more worker instances
- Database connection pooling for high throughput

## Best Practices

1. **Idempotency**: Design task handlers to be idempotent
2. **Small Tasks**: Keep tasks small and focused
3. **Error Handling**: Handle expected errors gracefully
4. **Logging**: Include detailed context in logs
5. **Monitoring**: Set up alerts for failed tasks
6. **Backpressure**: Monitor queue depth and scale workers accordingly

## Deployment

### Requirements

- Python 3.8+
- PostgreSQL 12+
- Required Python packages (see `requirements-queue.txt`)

### Database Setup

1. Create database and user
2. Run migrations:
   ```bash
   alembic upgrade head
   ```

### Running in Production

Use a process manager like systemd or supervisor to run worker processes:

```ini
# /etc/supervisor/conf.d/worker.conf
[program:worker]
command=/path/to/venv/bin/python -m scripts.worker --worker-id worker-1 --max-tasks 1000
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/worker/err.log
stdout_logfile=/var/log/worker/out.log
```

## Future Enhancements

1. **Priority Queues**: Separate queues for different priority levels
2. **Scheduled Tasks**: Built-in support for delayed execution
3. **Batch Processing**: Process multiple tasks in a single transaction
4. **Dead Letter Queue**: Automatic handling of failed tasks
5. **Admin Interface**: Web UI for monitoring and managing tasks
6. **Distributed Tracing**: End-to-end tracing of task execution
7. **Rate Limiting**: Control task execution rate
8. **Task DAGs**: Complex workflows with dependencies
