"""add_partial_unique_indexes

Revision ID: 7afd3e9c530f
Revises: 6b5084543825
Create Date: 2026-03-27 12:36:09.616000

"""
from typing import Sequence, Union

from alembic import op


revision: str = '7afd3e9c530f'
down_revision: Union[str, Sequence[str], None] = '6b5084543825'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.drop_index('sqlite_autoindex_sources_1')
    
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
    op.execute("DROP INDEX IF EXISTS uq_sources_name_active")
    op.execute("DROP INDEX IF EXISTS uq_sources_url_active")
    
    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.create_index('sqlite_autoindex_sources_1', ['url'], unique=True)