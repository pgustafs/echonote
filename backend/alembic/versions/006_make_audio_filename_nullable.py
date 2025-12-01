"""make audio_filename nullable

Revision ID: 006_make_audio_filename_nullable
Revises: 005_add_minio_object_storage
Create Date: 2025-11-30

Migration to make audio_filename column nullable to support
deleting audio files while keeping transcription text.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_make_audio_filename_nullable'
down_revision = '005_add_minio_object_storage'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make audio_filename and duration_seconds nullable"""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('transcriptions', schema=None) as batch_op:
        # Make audio_filename nullable
        batch_op.alter_column('audio_filename',
                   existing_type=sa.String(),
                   nullable=True)

        # Make duration_seconds nullable (it's already nullable but just to be safe)
        batch_op.alter_column('duration_seconds',
                   existing_type=sa.Float(),
                   nullable=True)


def downgrade() -> None:
    """Make audio_filename NOT NULL again"""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('transcriptions', schema=None) as batch_op:
        # Make audio_filename NOT NULL again
        batch_op.alter_column('audio_filename',
                   existing_type=sa.String(),
                   nullable=False)
