"""Populate category defaults for existing transcriptions

Revision ID: 008_populate_category_defaults
Revises: 007_add_category_to_transcription
Create Date: 2025-12-04 06:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008_populate_category_defaults'
down_revision: Union[str, None] = '007_add_category_to_transcription'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Set default category for all existing transcriptions that have NULL or empty category"""
    # Use raw SQL to update all records with NULL or empty category
    conn = op.get_bind()

    # First, let's check how many records need updating
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM transcriptions WHERE category IS NULL OR category = ''")
    )
    count = result.scalar()
    print(f"Found {count} transcriptions without category")

    # Update all records with NULL or empty category
    result = conn.execute(
        sa.text(
            "UPDATE transcriptions SET category = 'voice_memo' WHERE category IS NULL OR category = ''"
        )
    )
    print(f"Updated {result.rowcount} transcriptions to voice_memo")

    # Verify the update
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM transcriptions WHERE category IS NULL OR category = ''")
    )
    remaining = result.scalar()
    print(f"Remaining transcriptions without category: {remaining}")


def downgrade() -> None:
    """No downgrade needed - we're just setting default values"""
    pass
