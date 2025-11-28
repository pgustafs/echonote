"""make transcription_id nullable for chat actions

Revision ID: d304647e9bc3
Revises: 004
Create Date: 2025-11-28 11:16:25.312010

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd304647e9bc3'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make transcription_id nullable to support chat and improve actions without transcription context
    op.alter_column(
        'ai_actions',
        'transcription_id',
        existing_type=sa.INTEGER(),
        nullable=True
    )


def downgrade() -> None:
    # Revert: make transcription_id not nullable
    # Note: This will fail if there are NULL values in the column
    op.alter_column(
        'ai_actions',
        'transcription_id',
        existing_type=sa.INTEGER(),
        nullable=False
    )
