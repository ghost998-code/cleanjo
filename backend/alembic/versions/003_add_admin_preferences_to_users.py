"""Add admin preferences to users

Revision ID: 003_admin_prefs
Revises: 002_phone_idx
Create Date: 2026-04-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_admin_prefs'
down_revision: Union[str, None] = '002_phone_idx'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'admin_preferences',
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )
    op.alter_column('users', 'admin_preferences', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'admin_preferences')
