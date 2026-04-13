"""Add unique index to users phone

Revision ID: 002_phone_idx
Revises: 001_initial
Create Date: 2026-04-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_phone_idx'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_users_phone', 'users', ['phone'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_phone', table_name='users')
