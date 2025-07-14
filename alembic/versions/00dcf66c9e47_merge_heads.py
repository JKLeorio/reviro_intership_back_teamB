"""Merge heads

Revision ID: 00dcf66c9e47
Revises: bea0662e686e, c1cc6e61d740
Create Date: 2025-07-14 14:07:22.476238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00dcf66c9e47'
down_revision: Union[str, None] = ('bea0662e686e', 'c1cc6e61d740')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
