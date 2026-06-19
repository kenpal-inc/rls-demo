"""add privileges

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-19 11:43:00.518175

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    tenant_expr = "company_seq = current_setting('app.current_company_seq', true)::int"
    user_expr = "user_seq = current_setting('app.current_user_seq', true)::int"

    # m_organizations
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON m_organizations TO super")
    op.execute("GRANT SELECT ON m_organizations TO operator")
    op.execute("GRANT SELECT, UPDATE ON m_organizations TO admin")
    op.execute("GRANT SELECT ON m_organizations TO general")

    op.execute("GRANT USAGE ON SEQUENCE m_organizations_company_seq_seq TO super")

    op.execute(
        """
        CREATE POLICY m_organizations_super_all
        ON m_organizations
        FOR ALL
        TO super
        USING (true)
        WITH CHECK (true)
        """
    )
    op.execute(
        """
        CREATE POLICY m_organizations_operator_select_all
        ON m_organizations
        FOR SELECT
        TO operator
        USING (true)
        """
    )
    op.execute(
        f"""
        CREATE POLICY m_organizations_admin_tenant_select
        ON m_organizations
        FOR SELECT
        TO admin
        USING ({tenant_expr})
        """
    )
    op.execute(
        f"""
        CREATE POLICY m_organizations_admin_tenant_update
        ON m_organizations
        FOR UPDATE
        TO admin
        USING ({tenant_expr})
        WITH CHECK ({tenant_expr})
        """
    )
    op.execute(
        f"""
        CREATE POLICY m_organizations_general_tenant_select
        ON m_organizations
        FOR SELECT
        TO general
        USING ({tenant_expr})
        """
    )

    # m_users
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON m_users TO super")
    op.execute("GRANT SELECT, UPDATE ON m_users TO operator")
    op.execute("GRANT SELECT, INSERT, UPDATE ON m_users TO admin")
    op.execute("GRANT SELECT, UPDATE ON m_users TO general")

    op.execute("GRANT USAGE ON SEQUENCE m_users_user_seq_seq TO super")
    op.execute("GRANT USAGE ON SEQUENCE m_users_user_seq_seq TO admin")

    op.execute(
        """
        CREATE POLICY m_users_super_all
        ON m_users
        FOR ALL
        TO super
        USING (true)
        WITH CHECK (true)
        """
    )
    op.execute(
        """
        CREATE POLICY m_users_operator_select_all
        ON m_users
        FOR SELECT
        TO operator
        USING (true)
        """
    )
    op.execute(
        f"""
        CREATE POLICY m_users_operator_self_update
        ON m_users
        FOR UPDATE
        TO operator
        USING ({user_expr})
        WITH CHECK ({user_expr})
        """
    )
    op.execute(
        f"""
        CREATE POLICY m_users_admin_tenant_select
        ON m_users
        FOR SELECT
        TO admin
        USING ({tenant_expr})
        """
    )
    op.execute(
        f"""
        CREATE POLICY m_users_admin_tenant_update
        ON m_users
        FOR UPDATE
        TO admin
        USING ({tenant_expr})
        WITH CHECK ({tenant_expr})
        """
    )
    op.execute(
        f"""
        CREATE POLICY m_users_admin_tenant_insert
        ON m_users
        FOR INSERT
        TO admin
        WITH CHECK ({tenant_expr})
        """
    )
    op.execute(
        f"""
        CREATE POLICY m_users_general_tenant_select
        ON m_users
        FOR SELECT
        TO general
        USING ({tenant_expr})
        """
    )
    op.execute(
        f"""
        CREATE POLICY m_users_general_self_update
        ON m_users
        FOR UPDATE
        TO general
        USING ({tenant_expr} AND {user_expr})
        WITH CHECK ({tenant_expr} AND {user_expr})
        """
    )

    # t_tasks
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON t_tasks TO super")
    op.execute("GRANT SELECT ON t_tasks TO operator")
    op.execute("GRANT SELECT, INSERT, UPDATE ON t_tasks TO admin")
    op.execute("GRANT SELECT, INSERT, UPDATE ON t_tasks TO general")

    op.execute("GRANT USAGE ON SEQUENCE t_tasks_task_seq_seq TO super")
    op.execute("GRANT USAGE ON SEQUENCE t_tasks_task_seq_seq TO admin")
    op.execute("GRANT USAGE ON SEQUENCE t_tasks_task_seq_seq TO general")

    op.execute(
        """
        CREATE POLICY t_tasks_super_all
        ON t_tasks
        FOR ALL
        TO super
        USING (true)
        WITH CHECK (true)
        """
    )
    op.execute(
        """
        CREATE POLICY t_tasks_operator_select_all
        ON t_tasks
        FOR SELECT
        TO operator
        USING (true)
        """
    )
    op.execute(
        f"""
        CREATE POLICY t_tasks_admin_tenant_select
        ON t_tasks
        FOR SELECT
        TO admin
        USING ({tenant_expr})
        """
    )
    op.execute(
        f"""
        CREATE POLICY t_tasks_admin_tenant_update
        ON t_tasks
        FOR UPDATE
        TO admin
        USING ({tenant_expr})
        WITH CHECK ({tenant_expr})
        """
    )
    op.execute(
        f"""
        CREATE POLICY t_tasks_admin_tenant_insert
        ON t_tasks
        FOR INSERT
        TO admin
        WITH CHECK ({tenant_expr})
        """
    )
    op.execute(
        f"""
        CREATE POLICY t_tasks_general_tenant_select
        ON t_tasks
        FOR SELECT
        TO general
        USING ({tenant_expr})
        """
    )
    op.execute(
        f"""
        CREATE POLICY t_tasks_general_tenant_update
        ON t_tasks
        FOR UPDATE
        TO general
        USING ({tenant_expr} AND owner_seq = current_setting('app.current_user_seq', true)::int)
        WITH CHECK ({tenant_expr} AND owner_seq = current_setting('app.current_user_seq', true)::int)
        """
    )
    op.execute(
        f"""
        CREATE POLICY t_tasks_general_tenant_insert
        ON t_tasks
        FOR INSERT
        TO general
        WITH CHECK ({tenant_expr} AND owner_seq = current_setting('app.current_user_seq', true)::int)
        """
    )


def downgrade() -> None:
    """Downgrade schema."""

    # t_tasks
    op.execute("DROP POLICY t_tasks_general_tenant_insert ON t_tasks")
    op.execute("DROP POLICY t_tasks_general_tenant_update ON t_tasks")
    op.execute("DROP POLICY t_tasks_general_tenant_select ON t_tasks")
    op.execute("DROP POLICY t_tasks_admin_tenant_insert ON t_tasks")
    op.execute("DROP POLICY t_tasks_admin_tenant_update ON t_tasks")
    op.execute("DROP POLICY t_tasks_admin_tenant_select ON t_tasks")
    op.execute("DROP POLICY t_tasks_operator_select_all ON t_tasks")
    op.execute("DROP POLICY t_tasks_super_all ON t_tasks")

    op.execute("REVOKE USAGE ON SEQUENCE t_tasks_task_seq_seq FROM general")
    op.execute("REVOKE USAGE ON SEQUENCE t_tasks_task_seq_seq FROM admin")
    op.execute("REVOKE USAGE ON SEQUENCE t_tasks_task_seq_seq FROM super")

    op.execute("REVOKE SELECT, INSERT, UPDATE, DELETE ON t_tasks FROM super")
    op.execute("REVOKE SELECT ON t_tasks FROM operator")
    op.execute("REVOKE SELECT, INSERT, UPDATE ON t_tasks FROM admin")
    op.execute("REVOKE SELECT, INSERT, UPDATE ON t_tasks FROM general")

    # m_users
    op.execute("DROP POLICY m_users_general_self_update ON m_users")
    op.execute("DROP POLICY m_users_general_tenant_select ON m_users")
    op.execute("DROP POLICY m_users_admin_tenant_insert ON m_users")
    op.execute("DROP POLICY m_users_admin_tenant_update ON m_users")
    op.execute("DROP POLICY m_users_admin_tenant_select ON m_users")
    op.execute("DROP POLICY m_users_operator_self_update ON m_users")
    op.execute("DROP POLICY m_users_operator_select_all ON m_users")
    op.execute("DROP POLICY m_users_super_all ON m_users")

    op.execute("REVOKE USAGE ON SEQUENCE m_users_user_seq_seq FROM admin")
    op.execute("REVOKE USAGE ON SEQUENCE m_users_user_seq_seq FROM super")

    op.execute("REVOKE SELECT, INSERT, UPDATE, DELETE ON m_users FROM super")
    op.execute("REVOKE SELECT, UPDATE ON m_users FROM operator")
    op.execute("REVOKE SELECT, INSERT, UPDATE ON m_users FROM admin")
    op.execute("REVOKE SELECT, UPDATE ON m_users FROM general")

    # m_organizations
    op.execute("DROP POLICY m_organizations_general_tenant_select ON m_organizations")
    op.execute("DROP POLICY m_organizations_admin_tenant_update ON m_organizations")
    op.execute("DROP POLICY m_organizations_admin_tenant_select ON m_organizations")
    op.execute("DROP POLICY m_organizations_operator_select_all ON m_organizations")
    op.execute("DROP POLICY m_organizations_super_all ON m_organizations")

    op.execute("REVOKE USAGE ON SEQUENCE m_organizations_company_seq_seq FROM super")

    op.execute("REVOKE SELECT, INSERT, UPDATE, DELETE ON m_organizations FROM super")
    op.execute("REVOKE SELECT ON m_organizations FROM operator")
    op.execute("REVOKE SELECT, UPDATE ON m_organizations FROM admin")
    op.execute("REVOKE SELECT ON m_organizations FROM general")
