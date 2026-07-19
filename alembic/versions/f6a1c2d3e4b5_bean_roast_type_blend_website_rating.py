"""add bean.roast_type, blend, website, rating

Adds four columns describing the coffee itself. Existing rows are backfilled with
``roast_type='unknown'`` and ``blend='unknown'`` (we cannot know their real values);
new beans created through the API default ``blend`` to ``single_origin`` instead, so the
column default is switched to that after the backfill. ``rating`` (1-5) and ``website``
are nullable and start NULL — a bean is rated later, and NULL means unrated.

Revision ID: f6a1c2d3e4b5
Revises: e5b1c7d2f409
Create Date: 2026-07-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f6a1c2d3e4b5'
down_revision: Union[str, Sequence[str], None] = 'e5b1c7d2f409'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('bean', sa.Column('roast_type', sa.Text(), nullable=False, server_default=sa.text("'unknown'")))
    # Backfill existing rows to 'unknown', then make 'single_origin' the default for new rows.
    op.add_column('bean', sa.Column('blend', sa.Text(), nullable=False, server_default=sa.text("'unknown'")))
    op.alter_column('bean', 'blend', server_default=sa.text("'single_origin'"))
    op.add_column('bean', sa.Column('rating', sa.SmallInteger(), nullable=True))
    op.add_column('bean', sa.Column('website', sa.Text(), nullable=True))

    op.create_check_constraint('ck_bean_roast_type', 'bean', "roast_type IN ('filter', 'espresso', 'omni', 'unknown')")
    op.create_check_constraint('ck_bean_blend', 'bean', "blend IN ('single_origin', 'blend', 'unknown')")
    op.create_check_constraint('ck_bean_rating_range', 'bean', 'rating BETWEEN 1 AND 5')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_bean_rating_range', 'bean', type_='check')
    op.drop_constraint('ck_bean_blend', 'bean', type_='check')
    op.drop_constraint('ck_bean_roast_type', 'bean', type_='check')

    op.drop_column('bean', 'website')
    op.drop_column('bean', 'rating')
    op.drop_column('bean', 'blend')
    op.drop_column('bean', 'roast_type')
