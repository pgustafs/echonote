"""add user quotas and permissions

Revision ID: 003
Revises: 002
Create Date: 2025-11-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import date


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add user quota and permission fields.

    These fields enable:
    - Role-based access control (user, admin)
    - Daily AI action quotas
    - Premium user support
    - Usage tracking
    """
    # Get database connection to check existing columns
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('users')]

    # Add role column (if not exists)
    if 'role' not in existing_columns:
        op.add_column('users',
            sa.Column('role', sa.String(length=20), server_default='user', nullable=False)
        )

    # Create index for role (check if not exists)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('users')]
    if 'ix_users_role' not in existing_indexes:
        op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # Add premium status column (if not exists)
    if 'is_premium' not in existing_columns:
        op.add_column('users',
            sa.Column('is_premium', sa.Boolean(), server_default='false', nullable=False)
        )

    # Add quota columns (if not exists)
    if 'ai_action_quota_daily' not in existing_columns:
        op.add_column('users',
            sa.Column('ai_action_quota_daily', sa.Integer(), server_default='100', nullable=False)
        )

    if 'ai_action_count_today' not in existing_columns:
        op.add_column('users',
            sa.Column('ai_action_count_today', sa.Integer(), server_default='0', nullable=False)
        )

    if 'quota_reset_date' not in existing_columns:
        # SQLite doesn't support CURRENT_DATE as default in ALTER TABLE
        # Add as nullable first
        op.add_column('users',
            sa.Column('quota_reset_date', sa.Date(), nullable=True)
        )
        # Update existing rows to today's date
        from datetime import date
        today = date.today()
        op.execute(f"UPDATE users SET quota_reset_date = '{today.isoformat()}' WHERE quota_reset_date IS NULL")
        # Can't make column NOT NULL in SQLite after creation, but that's OK
        # New rows will get default from SQLModel

    # Add updated_at timestamp (if not exists)
    if 'updated_at' not in existing_columns:
        op.add_column('users',
            sa.Column('updated_at', sa.DateTime(), nullable=True)
        )


def downgrade() -> None:
    """
    Remove user quota and permission fields.
    """
    # Remove columns in reverse order
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'quota_reset_date')
    op.drop_column('users', 'ai_action_count_today')
    op.drop_column('users', 'ai_action_quota_daily')
    op.drop_column('users', 'is_premium')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_column('users', 'role')
