"""add minio object storage

Revision ID: 005_add_minio_object_storage
Revises: d304647e9bc3
Create Date: 2025-11-29

Migration to add MinIO object storage support for audio files.
This adds minio_object_path column and makes audio_data nullable
to transition from storing BLOBs in PostgreSQL to object storage.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '005_add_minio_object_storage'
down_revision = 'd304647e9bc3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add MinIO object storage support"""
    # Get connection and inspector to check existing columns
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('transcriptions')]
    indexes = [idx['name'] for idx in inspector.get_indexes('transcriptions')]

    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('transcriptions', schema=None) as batch_op:
        # Add minio_object_path column only if it doesn't exist
        if 'minio_object_path' not in columns:
            batch_op.add_column(sa.Column('minio_object_path', sa.String(), nullable=True))

        # Make audio_data nullable (transition from BLOB to object storage)
        # SQLite requires table recreation for this, handled automatically by batch mode
        batch_op.alter_column('audio_data',
                   existing_type=sa.LargeBinary(),
                   nullable=True)

        # Add index on minio_object_path for faster lookups only if it doesn't exist
        if 'ix_transcriptions_minio_object_path' not in indexes:
            batch_op.create_index('ix_transcriptions_minio_object_path', ['minio_object_path'], unique=False)


def downgrade() -> None:
    """Remove MinIO object storage support"""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('transcriptions', schema=None) as batch_op:
        # Drop index
        batch_op.drop_index('ix_transcriptions_minio_object_path')

        # Make audio_data NOT NULL again
        batch_op.alter_column('audio_data',
                   existing_type=sa.LargeBinary(),
                   nullable=False)

        # Drop minio_object_path column
        batch_op.drop_column('minio_object_path')
