"""add_partial_unique_indexes

Revision ID: 7afd3e9c530f
Revises: 6b5084543825
Create Date: 2026-03-27 12:36:09.616000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7afd3e9c530f'
down_revision: Union[str, Sequence[str], None] = '6b5084543825'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create partial unique indexes for active sources.
    
    This allows soft-deleted records to have duplicate URLs/names,
    while still enforcing uniqueness for active records.
    """
    # Drop existing unconditional unique constraint on url
    # SQLite names unique constraints as "unique" automatically
    op.execute("DROP INDEX IF EXISTS sqlite_autoindex_sources_1")
    
    # Create partial unique indexes (only for non-deleted records)
    # These enforce uniqueness only where deleted_at IS NULL
    op.execute("""
        CREATE UNIQUE INDEX uq_sources_url_active 
        ON sources(url) 
        WHERE deleted_at IS NULL
    """)
    
    op.execute("""
        CREATE UNIQUE INDEX uq_sources_name_active 
        ON sources(name) 
        WHERE deleted_at IS NULL
    """)


def downgrade() -> None:
    """Revert to unconditional unique constraint."""
    op.execute("DROP INDEX IF EXISTS uq_sources_name_active")
    op.execute("DROP INDEX IF EXISTS uq_sources_url_active")
    
    # Restore the original unique constraint on url
    op.execute("CREATE UNIQUE INDEX sqlite_autoindex_sources_1 ON sources(url)")