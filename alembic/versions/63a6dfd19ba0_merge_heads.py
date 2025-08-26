"""merge heads

Revision ID: 63a6dfd19ba0
Revises: 54ee37bfcbbd, b475d9331d6b
Create Date: 2025-08-26 07:34:32.900585

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63a6dfd19ba0'
down_revision: Union[str, None] = ('54ee37bfcbbd', 'b475d9331d6b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
