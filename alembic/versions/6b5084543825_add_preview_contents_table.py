"""add preview_contents table

Revision ID: 6b5084543825
Revises: 9c47953c36c1
Create Date: 2026-03-26 13:12:41.709134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b5084543825'
down_revision: Union[str, Sequence[str], None] = '9c47953c36c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('preview_contents',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('url', sa.String(length=2048), nullable=False),
    sa.Column('url_hash', sa.String(length=64), nullable=False),
    sa.Column('markdown_content', sa.Text(), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_preview_contents_url'), 'preview_contents', ['url'], unique=True)
    op.create_index(op.f('ix_preview_contents_url_hash'), 'preview_contents', ['url_hash'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_preview_contents_url_hash'), table_name='preview_contents')
    op.drop_index(op.f('ix_preview_contents_url'), table_name='preview_contents')
    op.drop_table('preview_contents')
