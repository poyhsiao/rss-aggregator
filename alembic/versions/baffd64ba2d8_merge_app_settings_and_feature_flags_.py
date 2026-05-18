"""merge app_settings and feature_flags heads

Revision ID: baffd64ba2d8
Revises: 8f15de7f6e78, d7d3380aca40
Create Date: 2026-05-14 19:18:48.864433

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = 'baffd64ba2d8'
down_revision: Union[str, Sequence[str], None] = ('8f15de7f6e78', 'd7d3380aca40')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
