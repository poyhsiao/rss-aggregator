"""add feature_flags table

Revision ID: 73104d0dab02
Revises: c16b77a3df9d
Create Date: 2026-05-13 17:21:04.834032

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '73104d0dab02'
down_revision: Union[str, Sequence[str], None] = 'c16b77a3df9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Insert default feature flags (table already created by 3c1cf4c7a4b5)
    # Use dialect-specific SQL for idempotent inserts
    dialect = op.get_bind().dialect.name
    if dialect == 'postgresql':
        op.execute("""
            INSERT INTO feature_flags (key, value, updated_at)
            VALUES ('groups_enabled', 'true', CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO NOTHING
        """)
        op.execute("""
            INSERT INTO feature_flags (key, value, updated_at)
            VALUES ('group_schedules_enabled', 'true', CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO NOTHING
        """)
        op.execute("""
            INSERT INTO feature_flags (key, value, updated_at)
            VALUES ('source_group_schedules_enabled', 'true', CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO NOTHING
        """)
    else:
        # SQLite compatible
        op.execute("""
            INSERT OR IGNORE INTO feature_flags (key, value, updated_at)
            VALUES ('groups_enabled', 'true', CURRENT_TIMESTAMP)
        """)
        op.execute("""
            INSERT OR IGNORE INTO feature_flags (key, value, updated_at)
            VALUES ('group_schedules_enabled', 'true', CURRENT_TIMESTAMP)
        """)
        op.execute("""
            INSERT OR IGNORE INTO feature_flags (key, value, updated_at)
            VALUES ('source_group_schedules_enabled', 'true', CURRENT_TIMESTAMP)
        """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM feature_flags WHERE key IN ('groups_enabled', 'group_schedules_enabled', 'source_group_schedules_enabled')")