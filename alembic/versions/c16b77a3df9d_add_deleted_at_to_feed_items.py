"""add_deleted_at_to_feed_items

Revision ID: c16b77a3df9d
Revises: 1eee5b09445b
Create Date: 2026-04-03 13:15:30.485093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c16b77a3df9d'
down_revision: Union[str, Sequence[str], None] = '1eee5b09445b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('feed_items', sa.Column('deleted_at', sa.DateTime(), nullable=True, default=None))


def downgrade() -> None:
    op.drop_column('feed_items', 'deleted_at')
