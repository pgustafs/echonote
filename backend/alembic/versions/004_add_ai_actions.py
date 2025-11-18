"""add ai_actions table

Revision ID: 004
Revises: 003
Create Date: 2025-11-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create ai_actions table for tracking AI-powered operations on transcriptions.

    This table stores:
    - User-requested AI actions (summarize, translate, generate content, etc.)
    - Request parameters and results
    - Quota cost tracking
    - Performance metrics
    """
    # Create ai_actions table
    op.create_table(
        'ai_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('transcription_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='work_in_progress', nullable=False),
        sa.Column('request_params', sa.Text(), server_default='{}', nullable=False),
        sa.Column('result_data', sa.Text(), nullable=True),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('quota_cost', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_duration_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['transcription_id'], ['transcriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for performance
    op.create_index(op.f('ix_ai_actions_action_id'), 'ai_actions', ['action_id'], unique=True)
    op.create_index(op.f('ix_ai_actions_action_type'), 'ai_actions', ['action_type'], unique=False)
    op.create_index(op.f('ix_ai_actions_created_at'), 'ai_actions', ['created_at'], unique=False)
    op.create_index(op.f('ix_ai_actions_status'), 'ai_actions', ['status'], unique=False)
    op.create_index(op.f('ix_ai_actions_transcription_id'), 'ai_actions', ['transcription_id'], unique=False)
    op.create_index(op.f('ix_ai_actions_user_id'), 'ai_actions', ['user_id'], unique=False)


def downgrade() -> None:
    """
    Drop ai_actions table and all associated indexes.
    """
    # Drop indexes first
    op.drop_index(op.f('ix_ai_actions_user_id'), table_name='ai_actions')
    op.drop_index(op.f('ix_ai_actions_transcription_id'), table_name='ai_actions')
    op.drop_index(op.f('ix_ai_actions_status'), table_name='ai_actions')
    op.drop_index(op.f('ix_ai_actions_created_at'), table_name='ai_actions')
    op.drop_index(op.f('ix_ai_actions_action_type'), table_name='ai_actions')
    op.drop_index(op.f('ix_ai_actions_action_id'), table_name='ai_actions')

    # Drop table
    op.drop_table('ai_actions')
