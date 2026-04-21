"""merge_feature_flags_and_app_settings

Revision ID: 27aa41c9338d
Revises: 2a3a8993c9c2, 8f15de7f6e78
Create Date: 2026-04-22 07:18:03.242754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27aa41c9338d'
down_revision: Union[str, Sequence[str], None] = ('2a3a8993c9c2', '8f15de7f6e78')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
