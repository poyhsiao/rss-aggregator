"""merge dual feature_flags heads

Revision ID: d7d3380aca40
Revises: 3c1cf4c7a4b5, 73104d0dab02
Create Date: 2026-05-14 19:18:36.394438

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd7d3380aca40'
down_revision: Union[str, Sequence[str], None] = ('3c1cf4c7a4b5', '73104d0dab02')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 3c1cf4c7a4b5 creates the table; 73104d0dab02 just inserts.
    # Use IF NOT EXISTS to handle case where 3c1cf4 already ran.
    dialect = op.get_bind().dialect.name
    if dialect == 'postgresql':
        op.execute("""
            CREATE TABLE IF NOT EXISTS feature_flags (
                key VARCHAR(100) PRIMARY KEY,
                value VARCHAR(50) NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
    else:
        # SQLite
        op.execute("""
            CREATE TABLE IF NOT EXISTS feature_flags (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
