"""add source_group_schedules table

Revision ID: 2532588ec3fb
Revises: 440f4ab456c5
Create Date: 2026-04-03 00:08:06.822189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2532588ec3fb'
down_revision: Union[str, Sequence[str], None] = '440f4ab456c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'source_group_schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('cron_expression', sa.String(100), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['source_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_schedules_is_enabled', 'source_group_schedules', ['is_enabled'])


def downgrade() -> None:
    op.drop_index('idx_schedules_is_enabled', table_name='source_group_schedules')
    op.drop_table('source_group_schedules')
