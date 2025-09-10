"""Add task queue tables

Revision ID: 002
Revises: 001_initial_schema
Create Date: 2025-03-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade():
    # Create enum types
    op.execute("""
    CREATE TYPE task_status AS ENUM (
        'pending',
        'processing',
        'completed',
        'failed',
        'retry'
    )
    """)
    
    op.execute("""
    CREATE TYPE task_priority AS ENUM (
        '1',  -- LOW
        '2',  -- NORMAL
        '3',  -- HIGH
        '4'   -- URGENT
    )
    """)
    
    op.execute("""
    CREATE TYPE task_type AS ENUM (
        'bill_ingest',
        'member_ingest',
        'bill_action_ingest',
        'bill_subject_ingest',
        'bill_cosponsor_ingest',
        'document_download',
        'document_process',
        'report_generate',
        'data_export'
    )
    """)
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('task_type', sa.Enum(
            'bill_ingest', 'member_ingest', 'bill_action_ingest', 'bill_subject_ingest',
            'bill_cosponsor_ingest', 'document_download', 'document_process',
            'report_generate', 'data_export',
            name='task_type'
        ), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('priority', sa.Enum('1', '2', '3', '4', name='task_priority'), server_default='2', nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'retry', name='task_status'), server_default='pending', nullable=False),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('max_retries', sa.Integer(), server_default='3', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('parent_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('depends_on', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['parent_task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)
    op.create_index(op.f('ix_tasks_priority'), 'tasks', ['priority'], unique=False)
    op.create_index(op.f('ix_tasks_created_at'), 'tasks', ['created_at'], unique=False)
    op.create_index(op.f('ix_tasks_scheduled_for'), 'tasks', ['scheduled_for'], unique=False)
    op.create_index(op.f('ix_tasks_locked_at'), 'tasks', ['locked_at'], unique=False)
    op.create_index(op.f('ix_tasks_task_type'), 'tasks', ['task_type'], unique=False)
    
    # Add indexes for common query patterns
    op.execute("""
    CREATE INDEX idx_tasks_pending_priority 
    ON tasks (priority DESC, created_at ASC) 
    WHERE status = 'pending' AND (scheduled_for IS NULL OR scheduled_for <= NOW())
    """)
    
    op.execute("""
    CREATE INDEX idx_tasks_retry_priority 
    ON tasks (priority DESC, created_at ASC) 
    WHERE status = 'retry' AND (scheduled_for IS NULL OR scheduled_for <= NOW())
    """)
    
    # Add function to update updated_at timestamp
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for tasks table
    op.execute("""
    CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade():
    # Drop trigger and function
    op.execute('DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop indexes
    op.drop_index('idx_tasks_retry_priority', table_name='tasks')
    op.drop_index('idx_tasks_pending_priority', table_name='tasks')
    op.drop_index(op.f('ix_tasks_task_type'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_locked_at'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_scheduled_for'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_created_at'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_priority'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_status'), table_name='tasks')
    
    # Drop tables
    op.drop_table('tasks')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS task_status')
    op.execute('DROP TYPE IF EXISTS task_priority')
    op.execute('DROP TYPE IF EXISTS task_type')
