"""add app_settings table

Revision ID: 8f15de7f6e78
Revises: c16b77a3df9d
Create Date: 2026-04-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f15de7f6e78'
down_revision: Union[str, Sequence[str], None] = 'c16b77a3df9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'app_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('group_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('schedule_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('share_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.execute("INSERT INTO app_settings (id, group_enabled, schedule_enabled, share_enabled) VALUES (1, 0, 0, 0)")


def downgrade() -> None:
    op.drop_table('app_settings')
