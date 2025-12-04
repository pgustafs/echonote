"""Fix NULL category values

Revision ID: 009_fix_category_nulls
Revises: 008_populate_category_defaults
Create Date: 2025-12-04 06:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009_fix_category_nulls'
down_revision: Union[str, None] = '008_populate_category_defaults'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Set default category for all existing transcriptions that still have NULL or empty category"""
    conn = op.get_bind()

    # Check how many need fixing
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM transcriptions WHERE category IS NULL OR category = ''")
    )
    count = result.scalar()
    print(f"[009] Found {count} transcriptions with NULL/empty category")

    if count > 0:
        # Update all records
        result = conn.execute(
            sa.text("UPDATE transcriptions SET category = 'voice_memo' WHERE category IS NULL OR category = ''")
        )
        print(f"[009] Updated {result.rowcount} transcriptions")

        # Verify
        result = conn.execute(
            sa.text("SELECT COUNT(*) FROM transcriptions WHERE category IS NULL OR category = ''")
        )
        remaining = result.scalar()
        print(f"[009] Remaining NULL/empty: {remaining}")
    else:
        print("[009] No transcriptions need updating")


def downgrade() -> None:
    """No downgrade needed"""
    pass
