"""add source_group_schedules_enabled

Revision ID: ac0b10d09cdf
Revises: 7e3682b89e0c
Create Date: 2026-05-31 22:35:07.743291

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac0b10d09cdf'
down_revision: Union[str, Sequence[str], None] = '7e3682b89e0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('app_settings', sa.Column('source_group_schedules_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('app_settings', 'source_group_schedules_enabled')