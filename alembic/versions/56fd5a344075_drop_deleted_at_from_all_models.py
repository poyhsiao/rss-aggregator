"""drop_deleted_at_from_all_models

Revision ID: 56fd5a344075
Revises: fcc2b65fd426
Create Date: 2026-04-03 11:42:46.184715

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56fd5a344075'
down_revision: Union[str, Sequence[str], None] = 'fcc2b65fd426'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('api_keys', 'deleted_at')
    op.drop_column('feed_items', 'deleted_at')
    op.drop_column('stats', 'deleted_at')
    op.drop_column('preview_contents', 'deleted_at')
    op.drop_column('fetch_logs', 'deleted_at')
    op.drop_column('fetch_batches', 'deleted_at')
    op.drop_column('source_group_schedules', 'deleted_at')


def downgrade() -> None:
    op.add_column('source_group_schedules', sa.Column('deleted_at', sa.DateTime(), nullable=True, default=None))
    op.add_column('fetch_batches', sa.Column('deleted_at', sa.DateTime(), nullable=True, default=None))
    op.add_column('fetch_logs', sa.Column('deleted_at', sa.DateTime(), nullable=True, default=None))
    op.add_column('preview_contents', sa.Column('deleted_at', sa.DateTime(), nullable=True, default=None))
    op.add_column('stats', sa.Column('deleted_at', sa.DateTime(), nullable=True, default=None))
    op.add_column('feed_items', sa.Column('deleted_at', sa.DateTime(), nullable=True, default=None))
    op.add_column('api_keys', sa.Column('deleted_at', sa.DateTime(), nullable=True, default=None))
