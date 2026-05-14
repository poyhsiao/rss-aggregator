"""merge heads

Revision ID: b56ea9244241
Revises: 3c1cf4c7a4b5, 73104d0dab02
Create Date: 2026-05-13 23:24:24.219712

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'b56ea9244241'
down_revision: Union[str, Sequence[str], None] = ('3c1cf4c7a4b5', '73104d0dab02')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
