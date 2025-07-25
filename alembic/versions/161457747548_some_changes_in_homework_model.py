"""some changes in homework model

Revision ID: 161457747548
Revises: a03b4c3d85b3
Create Date: 2025-07-16 13:50:57.709138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '161457747548'
down_revision: Union[str, None] = 'a03b4c3d85b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('homeworks', sa.Column('file_path', sa.String(), nullable=True))
    op.alter_column('homeworks', 'description',
               existing_type=sa.TEXT(),
               nullable=True)
    op.alter_column('homeworks', 'deadline',
               existing_type=sa.DATE(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('homeworks', 'deadline',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DATE(),
               existing_nullable=False)
    op.alter_column('homeworks', 'description',
               existing_type=sa.TEXT(),
               nullable=False)
    op.drop_column('homeworks', 'file_path')
    # ### end Alembic commands ###
