"""add_groups_column_to_fetch_batches

Revision ID: 1eee5b09445b
Revises: 56fd5a344075
Create Date: 2026-04-03 12:48:16.625768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1eee5b09445b'
down_revision: Union[str, Sequence[str], None] = '56fd5a344075'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('fetch_batches', sa.Column('groups', sa.Text(), nullable=True, server_default=""))


def downgrade() -> None:
    op.drop_column('fetch_batches', 'groups')
