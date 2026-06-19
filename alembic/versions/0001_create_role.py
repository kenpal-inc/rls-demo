"""create role

Revision ID: 0001
Revises:
Create Date: 2026-06-19 11:26:48.584443

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("CREATE ROLE super")
    op.execute("CREATE ROLE operator")

    op.execute("CREATE ROLE admin")
    op.execute("CREATE ROLE general")


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("DROP ROLE super")
    op.execute("DROP ROLE operator")

    op.execute("DROP ROLE admin")
    op.execute("DROP ROLE general")
