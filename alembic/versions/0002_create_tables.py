"""create tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-19 11:31:17.819722

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "m_organizations",
        sa.Column("company_seq", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
    )
    op.execute("ALTER TABLE m_organizations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE m_organizations FORCE ROW LEVEL SECURITY")

    op.create_table(
        "m_users",
        sa.Column("user_seq", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "company_seq",
            sa.Integer,
            nullable=False,
        ),
        sa.Column("user_name", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
    )
    op.execute("ALTER TABLE m_users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE m_users FORCE ROW LEVEL SECURITY")

    op.create_table(
        "t_tasks",
        sa.Column("task_seq", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "company_seq",
            sa.Integer,
            nullable=False,
        ),
        sa.Column("owner_seq", sa.Integer, nullable=False),
        sa.Column("task_name", sa.String(255), nullable=False),
        sa.Column("task_description", sa.Text, nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
    )
    op.execute("ALTER TABLE t_tasks ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE t_tasks FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("t_tasks")
    op.drop_table("m_users")
    op.drop_table("m_organizations")
