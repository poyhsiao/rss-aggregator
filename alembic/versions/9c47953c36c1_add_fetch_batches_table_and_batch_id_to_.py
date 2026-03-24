"""add fetch_batches table and batch_id to feed_items

Revision ID: 9c47953c36c1
Revises: e89818fd8d23
Create Date: 2026-03-23 21:23:12.814624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9c47953c36c1'
down_revision: Union[str, Sequence[str], None] = 'e89818fd8d23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create fetch_batches table
    op.create_table('fetch_batches',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('items_count', sa.Integer(), nullable=False),
    sa.Column('sources', sa.Text(), nullable=False),
    sa.Column('notes', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Add batch_id column to feed_items (nullable for SQLite compatibility)
    op.add_column('feed_items', sa.Column('batch_id', sa.Integer(), nullable=True))
    
    # Note: Foreign key is handled at the model level, not enforced by SQLite
    # SQLite doesn't support adding foreign keys via ALTER TABLE
    # The relationship is defined in SQLAlchemy models


def downgrade() -> None:
    op.drop_column('feed_items', 'batch_id')
    op.drop_table('fetch_batches')