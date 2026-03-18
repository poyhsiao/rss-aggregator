"""add_status_to_error_logs

Revision ID: e89818fd8d23
Revises: 4fba2de389ca
Create Date: 2026-03-18 23:13:08.750242

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e89818fd8d23'
down_revision: Union[str, Sequence[str], None] = '4fba2de389ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'error_logs',
        sa.Column('status', sa.String(length=20), nullable=False, server_default='error')
    )
    op.add_column(
        'error_logs',
        sa.Column('items_count', sa.Integer(), nullable=True)
    )
    op.alter_column('error_logs', 'error_type', new_column_name='log_type')
    op.alter_column('error_logs', 'error_message', new_column_name='message')
    op.rename_table('error_logs', 'fetch_logs')


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table('fetch_logs', 'error_logs')
    op.alter_column('error_logs', 'message', new_column_name='error_message')
    op.alter_column('error_logs', 'log_type', new_column_name='error_type')
    op.drop_column('error_logs', 'items_count')
    op.drop_column('error_logs', 'status')
