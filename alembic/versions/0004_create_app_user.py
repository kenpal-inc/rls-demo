"""create app user

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-19 12:25:08.773293

"""

import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    app_user_password = os.environ.get("APP_USER_PASSWORD")
    if not app_user_password:
        raise RuntimeError("APP_USER_PASSWORD environment variable is required")

    op.execute(
        """
        CREATE ROLE app_user
            LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            NOREPLICATION
            NOBYPASSRLS
        """
    )

    bind = op.get_bind()
    password_literal = bind.execute(
        sa.text("SELECT quote_literal(:password)"),
        {"password": app_user_password},
    ).scalar_one()
    op.execute(f"ALTER ROLE app_user WITH PASSWORD {password_literal}")

    op.execute("GRANT super TO app_user")
    op.execute("GRANT operator TO app_user")
    op.execute("GRANT admin TO app_user")
    op.execute("GRANT general TO app_user")


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("REVOKE super FROM app_user")
    op.execute("REVOKE operator FROM app_user")
    op.execute("REVOKE admin FROM app_user")
    op.execute("REVOKE general FROM app_user")

    op.execute("DROP ROLE app_user")
