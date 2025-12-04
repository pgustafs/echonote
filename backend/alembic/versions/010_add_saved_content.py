"""Add saved_content table

Revision ID: 010_add_saved_content
Revises: 009_fix_category_nulls
Create Date: 2025-12-04 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010_add_saved_content'
down_revision: Union[str, None] = '009_fix_category_nulls'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create saved_content table"""
    op.create_table(
        'saved_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('ai_action_id', sa.String(), nullable=True),
        sa.Column('transcription_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['transcription_id'], ['transcriptions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add indexes
    op.create_index(op.f('ix_saved_content_content_type'), 'saved_content', ['content_type'], unique=False)
    op.create_index(op.f('ix_saved_content_transcription_id'), 'saved_content', ['transcription_id'], unique=False)
    op.create_index(op.f('ix_saved_content_user_id'), 'saved_content', ['user_id'], unique=False)

    print("[010] Created saved_content table with indexes")


def downgrade() -> None:
    """Drop saved_content table"""
    op.drop_index(op.f('ix_saved_content_user_id'), table_name='saved_content')
    op.drop_index(op.f('ix_saved_content_transcription_id'), table_name='saved_content')
    op.drop_index(op.f('ix_saved_content_content_type'), table_name='saved_content')
    op.drop_table('saved_content')
