"""add celery task tracking

Revision ID: 002_add_celery_task_tracking
Revises: 001_initial_schema_with_auth
Create Date: 2025-01-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add Celery task tracking fields to transcription table.

    These fields enable background processing of transcriptions:
    - task_id: Celery task ID for tracking
    - status: Processing status (pending, processing, completed, failed)
    - progress: Progress percentage (0-100)
    - error_message: Error message if transcription failed
    """
    # Add task_id column
    op.add_column('transcriptions',
        sa.Column('task_id', sa.String(), nullable=True)
    )
    op.create_index(op.f('ix_transcriptions_task_id'), 'transcriptions', ['task_id'], unique=False)

    # Add status column
    op.add_column('transcriptions',
        sa.Column('status', sa.String(), server_default='completed', nullable=False)
    )

    # Add progress column
    op.add_column('transcriptions',
        sa.Column('progress', sa.Integer(), nullable=True)
    )

    # Add error_message column
    op.add_column('transcriptions',
        sa.Column('error_message', sa.Text(), nullable=True)
    )

    # Set all existing records to status='completed' (they were processed synchronously)
    # This is already handled by server_default='completed'


def downgrade() -> None:
    """
    Remove Celery task tracking fields from transcription table.
    """
    # Remove columns
    op.drop_column('transcriptions', 'error_message')
    op.drop_column('transcriptions', 'progress')
    op.drop_column('transcriptions', 'status')
    op.drop_index(op.f('ix_transcriptions_task_id'), table_name='transcriptions')
    op.drop_column('transcriptions', 'task_id')
