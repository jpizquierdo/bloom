"""rescale tasting scores from 1-10 to 1-5

Every tasting note score moves to a 1-5 "stars" scale (null stays unrated). Existing
values are rescaled by a rule of three, ``ROUND(old * 5.0 / 10)`` (numeric ROUND is
half-away-from-zero, so nothing rated collapses to 0). The 1-10 CHECK constraints are
dropped before the update and recreated as 1-5 afterwards.

Revision ID: a7b8c9d0e1f2
Revises: f6a1c2d3e4b5
Create Date: 2026-07-19 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f6a1c2d3e4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SCORES = ("aroma", "acidity", "sweetness", "body", "bitterness", "aftertaste", "overall")


def upgrade() -> None:
    """Upgrade schema."""
    for column in _SCORES:
        op.drop_constraint(f'ck_tasting_{column}_range', 'tasting', type_='check')

    assignments = ", ".join(f"{column} = ROUND({column} * 5.0 / 10)" for column in _SCORES)
    op.execute(f"UPDATE tasting SET {assignments}")

    for column in _SCORES:
        op.create_check_constraint(f'ck_tasting_{column}_range', 'tasting', f'{column} BETWEEN 1 AND 5')


def downgrade() -> None:
    """Downgrade schema."""
    for column in _SCORES:
        op.drop_constraint(f'ck_tasting_{column}_range', 'tasting', type_='check')

    # Lossy inverse of the rule of three; values stay within 1-10.
    assignments = ", ".join(f"{column} = ROUND({column} * 10.0 / 5)" for column in _SCORES)
    op.execute(f"UPDATE tasting SET {assignments}")

    for column in _SCORES:
        op.create_check_constraint(f'ck_tasting_{column}_range', 'tasting', f'{column} BETWEEN 1 AND 10')
