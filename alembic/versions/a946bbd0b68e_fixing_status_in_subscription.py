"""fixing_status_in_subscription

Revision ID: a946bbd0b68e
Revises: 00dcf66c9e47
Create Date: 2025-07-14 15:05:34.819350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a946bbd0b68e'
down_revision: Union[str, None] = '00dcf66c9e47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
