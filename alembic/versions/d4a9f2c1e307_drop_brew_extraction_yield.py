"""drop stored brew.extraction_yield_percent

Extraction yield is a pure function of TDS, beverage yield and dose, so it is no
longer persisted — the domain layer derives it on read alongside ``ratio``. This
drops the column and its non-negative check. The downgrade restores the column and
backfills it from the surviving measurements, matching the old write-time formula.

Revision ID: d4a9f2c1e307
Revises: c3f8a1e6b204
Create Date: 2026-07-15 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd4a9f2c1e307'
down_revision: Union[str, Sequence[str], None] = 'c3f8a1e6b204'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('ck_brew_ey_nonneg', 'brew', type_='check')
    op.drop_column('brew', 'extraction_yield_percent')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('brew', sa.Column('extraction_yield_percent', sa.Numeric(4, 2), nullable=True))
    op.create_check_constraint('ck_brew_ey_nonneg', 'brew', 'extraction_yield_percent >= 0')
    # Recompute the derived value the old code stored: EY = tds * yield / dose.
    op.execute("""
        UPDATE brew
        SET extraction_yield_percent = ROUND(tds_percent * yield_grams / dose_grams, 2)
        WHERE tds_percent IS NOT NULL AND yield_grams IS NOT NULL
    """)
