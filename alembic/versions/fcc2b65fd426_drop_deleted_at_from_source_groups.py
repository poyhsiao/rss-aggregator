"""drop_deleted_at_from_source_groups

Revision ID: fcc2b65fd426
Revises: 2532588ec3fb
Create Date: 2026-04-03 11:21:25.617050

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fcc2b65fd426'
down_revision: Union[str, Sequence[str], None] = '2532588ec3fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('source_groups', 'deleted_at')


def downgrade() -> None:
    op.add_column('source_groups', sa.Column('deleted_at', sa.DateTime(), nullable=True, default=None))
