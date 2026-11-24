"""add user.oidc_subject

Links an account to its OpenID Connect ``sub`` claim on the first SSO login. Nullable:
local-only accounts never get one.

Revision ID: a7c3e9d1b582
Revises: d9e2b4a6c801
Create Date: 2026-11-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a7c3e9d1b582'
down_revision: Union[str, Sequence[str], None] = 'd9e2b4a6c801'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('user', sa.Column('oidc_subject', sa.Text(), nullable=True))
    op.create_unique_constraint('user_oidc_subject_key', 'user', ['oidc_subject'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('user_oidc_subject_key', 'user', type_='unique')
    op.drop_column('user', 'oidc_subject')
