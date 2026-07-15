"""user.username handle

Adds a unique ``username`` handle to ``user``. Existing rows are backfilled from
the email's local part (everything before the ``@``); we assume no collisions on
the current, small user base. New usernames are set by an admin today and will
be supplied by the IdP (Keycloak/Authentik) once automated provisioning lands.

Revision ID: b2e7c9d4a105
Revises: 9a4c2b7f1e83
Create Date: 2026-07-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2e7c9d4a105'
down_revision: Union[str, Sequence[str], None] = '9a4c2b7f1e83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('user', sa.Column('username', sa.Text(), nullable=True))
    op.execute("""UPDATE "user" SET username = split_part(email, '@', 1)""")
    op.alter_column('user', 'username', nullable=False)
    op.create_check_constraint('ck_user_username_not_blank', 'user', "btrim(username) <> ''")
    op.create_index('uq_user_username_lower', 'user', [sa.text('lower(username)')], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_user_username_lower', table_name='user')
    op.drop_constraint('ck_user_username_not_blank', 'user', type_='check')
    op.drop_column('user', 'username')
