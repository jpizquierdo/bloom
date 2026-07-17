"""add user.password_changed_at

Password-reset tokens carry an ``iat`` claim and are refused once it predates this
column, which is what makes a reset link single-use. Existing rows are stamped with
``now()`` on upgrade — no reset tokens exist yet, so nothing is wrongly invalidated.

Revision ID: e5b1c7d2f409
Revises: d4a9f2c1e307
Create Date: 2026-07-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e5b1c7d2f409'
down_revision: Union[str, Sequence[str], None] = 'd4a9f2c1e307'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'user',
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user', 'password_changed_at')
