"""Merge multiple heads

Revision ID: fb952d6b2468
Revises: 100b415b1687, 2eca1993fbc3
Create Date: 2025-07-29 11:51:13.971320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb952d6b2468'
down_revision: Union[str, None] = ('100b415b1687', '2eca1993fbc3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
