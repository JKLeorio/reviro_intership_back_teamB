"""Add Stripe fields to Payment model

Revision ID: 230de5a0782f
Revises: 6a03deec8dbd
Create Date: 2025-08-16 16:24:24.293634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '230de5a0782f'
down_revision: Union[str, None] = '6a03deec8dbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Добавляем новое значение в enum
    op.execute("ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'stripe'")


def downgrade():
    # Ничего не удаляем, так как customer_email и stripe_payment_intent_id уже существуют
    pass