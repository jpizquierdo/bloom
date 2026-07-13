"""roaster as its own table

Replaces the free-text ``bean.roaster`` column with a ``roaster`` table and a
``bean.roaster_id`` FK. Existing values are backfilled: one roaster per distinct
name, compared case-insensitively and with whitespace collapsed, so "Nomad" and
"nomad  coffee" style variants fold into a single row.

Revision ID: 9a4c2b7f1e83
Revises: 1cfe1dd99d74
Create Date: 2026-07-13 11:04:22.118904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9a4c2b7f1e83'
down_revision: Union[str, Sequence[str], None] = '1cfe1dd99d74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Same normalisation as bloom.domain.naming.normalize_name: trim + collapse whitespace.
NORMALIZED = r"regexp_replace(btrim(bean.roaster), '\s+', ' ', 'g')"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('roaster',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('country', sa.Text(), nullable=True),
    sa.Column('city', sa.Text(), nullable=True),
    sa.Column('website', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('uq_roaster_name_lower', 'roaster', [sa.text('lower(name)')], unique=True)

    # One roaster per distinct name; the oldest bean's spelling wins as canonical.
    op.execute(f"""
        INSERT INTO roaster (name)
        SELECT DISTINCT ON (lower({NORMALIZED})) {NORMALIZED}
        FROM bean
        ORDER BY lower({NORMALIZED}), bean.id
    """)

    op.add_column('bean', sa.Column('roaster_id', sa.Integer(), nullable=True))
    op.execute(f"""
        UPDATE bean
        SET roaster_id = r.id
        FROM roaster AS r
        WHERE lower(r.name) = lower({NORMALIZED})
    """)
    op.alter_column('bean', 'roaster_id', nullable=False)
    op.create_foreign_key('fk_bean_roaster_id', 'bean', 'roaster', ['roaster_id'], ['id'], ondelete='RESTRICT')
    op.create_index('idx_bean_roaster_id', 'bean', ['roaster_id'], unique=False)
    op.drop_index('idx_bean_roaster', table_name='bean')
    op.drop_column('bean', 'roaster')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('bean', sa.Column('roaster', sa.Text(), nullable=True))
    op.execute("UPDATE bean SET roaster = r.name FROM roaster AS r WHERE r.id = bean.roaster_id")
    op.alter_column('bean', 'roaster', nullable=False)
    op.create_index('idx_bean_roaster', 'bean', ['roaster'], unique=False)
    op.drop_index('idx_bean_roaster_id', table_name='bean')
    op.drop_constraint('fk_bean_roaster_id', 'bean', type_='foreignkey')
    op.drop_column('bean', 'roaster_id')
    op.drop_index('uq_roaster_name_lower', table_name='roaster')
    op.drop_table('roaster')
