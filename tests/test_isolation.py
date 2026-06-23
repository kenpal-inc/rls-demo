import psycopg
import pytest

from src.db import Principal, rls_session
from tests.conftest import admin, fetch_all, general, operator, super_


def _count(principal: Principal, table: str) -> int:
    with fetch_all(principal, f"SELECT * FROM {table}") as rows:
        return len(rows)


def _company_seqs(principal: Principal, table: str) -> set[int]:
    with fetch_all(principal, f"SELECT company_seq FROM {table}") as rows:
        return {r["company_seq"] for r in rows}


# ---------------------------------------------------------------------------
# SELECT: 全件閲覧できるロール
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("role_factory", [super_, operator])
def test_super_operator_see_all_tenants(seed, role_factory):
    principal = role_factory()
    assert _count(principal, "m_organizations") == 2
    assert _count(principal, "m_users") == 4
    assert _count(principal, "t_tasks") == 4


# ---------------------------------------------------------------------------
# SELECT: 自テナントのみ閲覧できるロール
# ---------------------------------------------------------------------------


def test_admin_sees_only_own_tenant(seed):
    p = admin(seed["acme"], seed["alice"])
    assert _count(p, "m_organizations") == 1
    assert _count(p, "m_users") == 2
    assert _count(p, "t_tasks") == 2

    # 他テナント(globex)の行は一切見えない
    assert _company_seqs(p, "t_tasks") == {seed["acme"]}
    assert _company_seqs(p, "m_users") == {seed["acme"]}


def test_general_sees_only_own_tenant(seed):
    p = general(seed["acme"], seed["bob"])
    assert _count(p, "t_tasks") == 2
    assert _company_seqs(p, "t_tasks") == {seed["acme"]}

    # general は自テナントの全ユーザーが見える(自分だけではない)
    assert _count(p, "m_users") == 2


def test_admin_cannot_see_other_tenant_rows(seed):
    """Acme admin から Globex のタスクは 0 件に見える"""
    p = admin(seed["acme"], seed["alice"])
    with fetch_all(
        p, f"SELECT * FROM t_tasks WHERE company_seq = {seed['globex']}"
    ) as rows:
        assert rows == []


def test_no_tenant_context_sees_nothing(seed):
    """admin で company_seq を渡さない場合はフェイルクローズで 0 件"""
    p = Principal(role="admin")  # company_seq 未設定
    assert _count(p, "t_tasks") == 0
    assert _count(p, "m_users") == 0


# ---------------------------------------------------------------------------
# INSERT: WITH CHECK による越境書き込みの防止
# ---------------------------------------------------------------------------


def _insert_task(principal: Principal, company_seq: int, owner_seq: int) -> None:
    with rls_session(principal) as cur:
        cur.execute(
            "INSERT INTO t_tasks (company_seq, owner_seq, task_name) VALUES (%s, %s, %s)",
            (company_seq, owner_seq, "x"),
        )


def test_admin_can_insert_into_own_tenant(seed):
    _insert_task(admin(seed["acme"], seed["alice"]), seed["acme"], seed["alice"])
    assert _count(admin(seed["acme"], seed["alice"]), "t_tasks") == 3


def test_admin_cannot_insert_into_other_tenant(seed):
    """WITH CHECK 違反 -> 42501"""
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _insert_task(admin(seed["acme"], seed["alice"]), seed["globex"], seed["carol"])


def test_general_can_insert_own_task(seed):
    _insert_task(general(seed["acme"], seed["bob"]), seed["acme"], seed["bob"])
    assert _count(general(seed["acme"], seed["bob"]), "t_tasks") == 3


def test_general_cannot_insert_task_for_another_owner(seed):
    """general は owner_seq=自分 でないと INSERT できない"""
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _insert_task(general(seed["acme"], seed["bob"]), seed["acme"], seed["alice"])


def test_operator_cannot_insert_task(seed):
    """operator はそもそも t_tasks への INSERT 権限が無い"""
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _insert_task(operator(), seed["acme"], seed["alice"])


# ---------------------------------------------------------------------------
# UPDATE: USING により対象外の行は「存在しない」扱いで更新されない
# ---------------------------------------------------------------------------


def _update_task(principal: Principal, task_seq: int) -> int:
    """更新できた行数を返す"""
    with rls_session(principal) as cur:
        cur.execute(
            "UPDATE t_tasks SET task_name = %s WHERE task_seq = %s RETURNING task_seq",
            ("updated", task_seq),
        )
        return len(cur.fetchall())


def test_admin_can_update_own_tenant_task(seed):
    assert _update_task(admin(seed["acme"], seed["alice"]), seed["task_alice"]) == 1


def test_admin_cannot_update_other_tenant_task(seed):
    """他テナントの行は USING で除外され、エラーにならず 0 行更新"""
    assert _update_task(admin(seed["acme"], seed["alice"]), seed["task_carol"]) == 0


def test_general_can_update_own_task(seed):
    assert _update_task(general(seed["acme"], seed["bob"]), seed["task_bob"]) == 1


def test_general_cannot_update_others_task_same_tenant(seed):
    """同一テナントでも owner が違えば更新できない(0 行)"""
    assert _update_task(general(seed["acme"], seed["bob"]), seed["task_alice"]) == 0


def test_operator_cannot_update_task(seed):
    """operator は t_tasks への UPDATE 権限が無い"""
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _update_task(operator(), seed["task_alice"])


# ---------------------------------------------------------------------------
# DELETE: super のみ
# ---------------------------------------------------------------------------


def _delete_task(principal: Principal, task_seq: int) -> int:
    with rls_session(principal) as cur:
        cur.execute(
            "DELETE FROM t_tasks WHERE task_seq = %s RETURNING task_seq", (task_seq,)
        )
        return len(cur.fetchall())


def test_super_can_delete_task(seed):
    assert _delete_task(super_(), seed["task_alice"]) == 1


def test_admin_cannot_delete_task(seed):
    """admin に DELETE 権限は無い"""
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _delete_task(admin(seed["acme"], seed["alice"]), seed["task_alice"])


def test_general_cannot_delete_task(seed):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _delete_task(general(seed["acme"], seed["bob"]), seed["task_bob"])
