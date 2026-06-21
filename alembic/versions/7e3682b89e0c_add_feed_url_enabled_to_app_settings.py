"""add feed_url_enabled to app_settings

Revision ID: 7e3682b89e0c
Revises: baffd64ba2d8
Create Date: 2026-05-31 18:42:05.605123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e3682b89e0c'
down_revision: Union[str, Sequence[str], None] = 'baffd64ba2d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add feed_url_enabled column to app_settings table."""
    op.add_column(
        'app_settings',
        sa.Column('feed_url_enabled', sa.Boolean(), nullable=False, server_default='0'),
    )
    op.execute("UPDATE app_settings SET feed_url_enabled = 0 WHERE feed_url_enabled IS NULL")


def downgrade() -> None:
    """Remove feed_url_enabled column from app_settings table."""
    op.drop_column('app_settings', 'feed_url_enabled')