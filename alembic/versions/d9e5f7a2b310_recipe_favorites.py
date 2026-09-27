"""add personal recipe favorites

Favorites are user-specific bookmarks of shared recipes. Existing users and recipes
need no backfill; the absence of an association means the recipe is not favorited.

Revision ID: d9e5f7a2b310
Revises: c8d4e6f1a209
Create Date: 2026-09-27 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd9e5f7a2b310'
down_revision: Union[str, Sequence[str], None] = 'c8d4e6f1a209'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'recipe_favorite',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipe.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'recipe_id'),
    )
    op.create_index('idx_recipe_favorite_recipe_id', 'recipe_favorite', ['recipe_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_recipe_favorite_recipe_id', table_name='recipe_favorite')
    op.drop_table('recipe_favorite')
