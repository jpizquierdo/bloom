"""split bean into coffee + bean_lot

The physical, per-purchase fields move off ``bean`` (now the coffee concept) into a
new ``bean_lot`` table. Each existing bean is preserved and gets exactly one lot
carrying its current roast/purchase dates, weight, price and finished flag; existing
brews are backfilled to that lot. ``brew.lot_id`` is a new optional reference.

Revision ID: c3f8a1e6b204
Revises: b2e7c9d4a105
Create Date: 2026-07-15 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3f8a1e6b204'
down_revision: Union[str, Sequence[str], None] = 'b2e7c9d4a105'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_MOVED = ("roast_date", "purchase_date", "weight_grams", "price", "is_finished")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'bean_lot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bean_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('roast_date', sa.Date(), nullable=True),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('weight_grams', sa.Integer(), nullable=True),
        sa.Column('price', sa.Numeric(7, 2), nullable=True),
        sa.Column('is_finished', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('weight_grams > 0', name='ck_bean_lot_weight_positive'),
        sa.ForeignKeyConstraint(['bean_id'], ['bean.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_bean_lot_bean_id', 'bean_lot', ['bean_id'])
    op.create_index('idx_bean_lot_user_id', 'bean_lot', ['user_id'])

    # One lot per existing bean, carrying its physical fields (and the bean's owner as buyer).
    op.execute("""
        INSERT INTO bean_lot (bean_id, user_id, roast_date, purchase_date, weight_grams, price, is_finished, created_at)
        SELECT id, user_id, roast_date, purchase_date, weight_grams, price, is_finished, created_at
        FROM bean
    """)

    op.add_column('brew', sa.Column('lot_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_brew_lot_id', 'brew', 'bean_lot', ['lot_id'], ['id'], ondelete='SET NULL')
    op.create_index('idx_brew_lot_id', 'brew', ['lot_id'])
    # Attribute existing brews to the single lot migrated from their bean.
    op.execute("UPDATE brew SET lot_id = bl.id FROM bean_lot bl WHERE bl.bean_id = brew.bean_id")

    op.drop_constraint('ck_bean_weight_positive', 'bean', type_='check')
    for column in _MOVED:
        op.drop_column('bean', column)


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('bean', sa.Column('roast_date', sa.Date(), nullable=True))
    op.add_column('bean', sa.Column('purchase_date', sa.Date(), nullable=True))
    op.add_column('bean', sa.Column('weight_grams', sa.Integer(), nullable=True))
    op.add_column('bean', sa.Column('price', sa.Numeric(7, 2), nullable=True))
    op.add_column('bean', sa.Column('is_finished', sa.Boolean(), server_default=sa.text('false'), nullable=False))

    # Copy back from each bean's earliest lot (the one the upgrade created).
    op.execute("""
        UPDATE bean
        SET roast_date = bl.roast_date,
            purchase_date = bl.purchase_date,
            weight_grams = bl.weight_grams,
            price = bl.price,
            is_finished = bl.is_finished
        FROM (SELECT DISTINCT ON (bean_id) bean_id, roast_date, purchase_date, weight_grams, price, is_finished
              FROM bean_lot ORDER BY bean_id, id) AS bl
        WHERE bl.bean_id = bean.id
    """)
    op.create_check_constraint('ck_bean_weight_positive', 'bean', 'weight_grams > 0')

    op.drop_index('idx_brew_lot_id', table_name='brew')
    op.drop_constraint('fk_brew_lot_id', 'brew', type_='foreignkey')
    op.drop_column('brew', 'lot_id')

    op.drop_index('idx_bean_lot_user_id', table_name='bean_lot')
    op.drop_index('idx_bean_lot_bean_id', table_name='bean_lot')
    op.drop_table('bean_lot')
