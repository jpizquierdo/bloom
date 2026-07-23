"""one tasting per user per brew

Each user may taste a given brew at most once. Existing duplicate
``(brew_id, user_id)`` rows are collapsed to the most recent one (greatest
``tasted_at``, tiebreak greatest ``id``) before the unique constraint is added,
since creating it on dirty data would fail.

Revision ID: b7c2d3e4f5a6
Revises: a7b8c9d0e1f2
Create Date: 2026-07-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b7c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        DELETE FROM tasting
        WHERE id NOT IN (
            SELECT DISTINCT ON (brew_id, user_id) id
            FROM tasting
            ORDER BY brew_id, user_id, tasted_at DESC, id DESC
        )
        """
    )
    op.create_unique_constraint('uq_tasting_brew_user', 'tasting', ['brew_id', 'user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_tasting_brew_user', 'tasting', type_='unique')
