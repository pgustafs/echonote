"""add category to transcription

Revision ID: 007_add_category_to_transcription
Revises: 006_make_audio_filename_nullable
Create Date: 2025-12-02

Migration to add category field to transcriptions table
for organizing transcriptions by content type (meeting notes,
linkedin posts, email drafts, blog posts, etc.)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_category_to_transcription'
down_revision = '006_make_audio_filename_nullable'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add category column to transcriptions table"""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('transcriptions', schema=None) as batch_op:
        # Add category field with default value 'voice_memo'
        batch_op.add_column(
            sa.Column('category', sa.String(length=50), nullable=False, server_default='voice_memo')
        )


def downgrade() -> None:
    """Remove category column from transcriptions table"""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('transcriptions', schema=None) as batch_op:
        batch_op.drop_column('category')
