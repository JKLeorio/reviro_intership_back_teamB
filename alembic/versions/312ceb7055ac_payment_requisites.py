"""payment_requisites

Revision ID: 312ceb7055ac
Revises: 16b6686a1c17
Create Date: 2025-07-28 14:47:00.789173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '312ceb7055ac'
down_revision: Union[str, None] = '26729c51055a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('payment_requisites',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bank_name', sa.String(), nullable=False),
    sa.Column('account', sa.String(), nullable=False),
    sa.Column('qr', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('payment_checks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('check', sa.String(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.alter_column('lessons', 'passed',
               existing_type=sa.BOOLEAN(),
               server_default=None,
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('lessons', 'passed',
               existing_type=sa.BOOLEAN(),
               server_default=sa.text('false'),
               existing_nullable=False)
    op.drop_table('payment_checks')
    op.drop_table('payment_requisites')
    # ### end Alembic commands ###
