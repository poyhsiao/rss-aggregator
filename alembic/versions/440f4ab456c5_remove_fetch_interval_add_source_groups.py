"""remove fetch_interval add source_groups

Revision ID: 440f4ab456c5
Revises: 7afd3e9c530f
Create Date: 2026-04-02 00:31:02.000235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '440f4ab456c5'
down_revision: Union[str, Sequence[str], None] = '7afd3e9c530f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("sources") as batch_op:
        batch_op.drop_column("fetch_interval")

    op.create_table(
        "source_groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "source_group_members",
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("sources.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "group_id",
            sa.Integer(),
            sa.ForeignKey("source_groups.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_source_group_members_group_id",
        "source_group_members",
        ["group_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("source_group_members")
    op.drop_table("source_groups")
    with op.batch_alter_table("sources") as batch_op:
        batch_op.add_column(
            sa.Column("fetch_interval", sa.Integer(), server_default="0", nullable=False)
        )
