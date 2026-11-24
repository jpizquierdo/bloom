"""user.email unique case-insensitively

Emails were unique only byte-for-byte, so ``Bob@x.com`` and ``bob@x.com`` could be two
accounts, and login and password recovery matched on the exact spelling. Lookups now fold
case, and this index makes the database refuse a case-variant duplicate, the same way
``uq_user_username_lower`` does for handles.

Existing rows are left as typed. If two accounts already differ only by case the upgrade
stops and names them: which one to keep is a decision for the owner, not for a migration.

Revision ID: d9e2b4a6c801
Revises: a1d9e3f7b562
Create Date: 2026-11-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd9e2b4a6c801'
down_revision: Union[str, Sequence[str], None] = 'a1d9e3f7b562'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    clashes = op.get_bind().execute(
        sa.text(
            'SELECT lower(email), array_agg(email ORDER BY id) FROM "user" '
            'GROUP BY lower(email) HAVING count(*) > 1'
        )
    ).all()
    if clashes:
        listed = "; ".join(", ".join(emails) for _, emails in clashes)
        raise RuntimeError(
            f"Cannot make user emails case-insensitively unique; these accounts differ only by case: {listed}. "
            "Merge or rename them, then run the upgrade again."
        )
    op.create_index('uq_user_email_lower', 'user', [sa.text('lower(email)')], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_user_email_lower', table_name='user')
