"""drop tasting.tasted_at

A tasting happens at the brew's own moment, so ``tasted_at`` carried no information
beyond ``brew.brewed_at``. The downgrade restores the column and backfills it from
the brew.

Revision ID: a1d9e3f7b562
Revises: c8d4e6f1a209
Create Date: 2026-10-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1d9e3f7b562'
down_revision: Union[str, Sequence[str], None] = 'c8d4e6f1a209'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('tasting', 'tasted_at')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('tasting', sa.Column('tasted_at', sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE tasting SET tasted_at = brew.brewed_at FROM brew WHERE brew.id = tasting.brew_id")
    op.alter_column('tasting', 'tasted_at', nullable=False, server_default=sa.text('now()'))
