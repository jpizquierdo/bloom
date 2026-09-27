"""add reusable recipes per bean

Recipes are optional children of beans. Existing rows need no backfill. A brew may
record nullable recipe provenance, while retaining its own copied parameters.

Revision ID: c8d4e6f1a209
Revises: b7c2d3e4f5a6
Create Date: 2026-09-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c8d4e6f1a209'
down_revision: Union[str, Sequence[str], None] = 'b7c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'recipe',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bean_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('method_id', sa.SmallInteger(), nullable=False),
        sa.Column('grinder_id', sa.Integer(), nullable=True),
        sa.Column('dose_grams', sa.Numeric(6, 2), nullable=False),
        sa.Column('yield_grams', sa.Numeric(6, 2), nullable=True),
        sa.Column('water_grams', sa.Numeric(6, 2), nullable=True),
        sa.Column('grind_setting', sa.Text(), nullable=True),
        sa.Column('water_temp_celsius', sa.Numeric(4, 1), nullable=True),
        sa.Column('brew_time_seconds', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('btrim(name) <> \'\'', name='ck_recipe_name_not_blank'),
        sa.CheckConstraint('dose_grams > 0', name='ck_recipe_dose_positive'),
        sa.CheckConstraint('yield_grams > 0', name='ck_recipe_yield_positive'),
        sa.CheckConstraint('water_grams > 0', name='ck_recipe_water_positive'),
        sa.CheckConstraint('brew_time_seconds > 0', name='ck_recipe_time_positive'),
        sa.ForeignKeyConstraint(['bean_id'], ['bean.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['grinder_id'], ['equipment.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['method_id'], ['brew_method.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_recipe_bean_id', 'recipe', ['bean_id'])
    op.create_index('idx_recipe_method_id', 'recipe', ['method_id'])
    op.create_index('idx_recipe_user_id', 'recipe', ['user_id'])

    op.add_column('brew', sa.Column('recipe_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_brew_recipe_id', 'brew', 'recipe', ['recipe_id'], ['id'], ondelete='SET NULL')
    op.create_index('idx_brew_recipe_id', 'brew', ['recipe_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_brew_recipe_id', table_name='brew')
    op.drop_constraint('fk_brew_recipe_id', 'brew', type_='foreignkey')
    op.drop_column('brew', 'recipe_id')

    op.drop_index('idx_recipe_user_id', table_name='recipe')
    op.drop_index('idx_recipe_method_id', table_name='recipe')
    op.drop_index('idx_recipe_bean_id', table_name='recipe')
    op.drop_table('recipe')
