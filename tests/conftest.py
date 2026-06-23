from contextlib import contextmanager
from typing import Iterator

import pytest

from src.db import Principal, rls_session


@contextmanager
def fetch_all(principal: Principal, sql: str) -> Iterator[list[dict]]:
    """principal の権限で SELECT し、結果行を返す"""
    with rls_session(principal) as cur:
        cur.execute(sql)
        yield cur.fetchall()


@pytest.fixture
def seed() -> dict:
    """
    各テストの前に super 権限でデータを作り直し、生成された seq を返す

    - 2 つのテナントを作成
    - 各テナントに admin と general それぞれのユーザーを作成
    - 各ユーザーが 1 件ずつタスクを保有
    """

    with rls_session(Principal(role="super")) as cur:
        cur.execute("DELETE FROM t_tasks")
        cur.execute("DELETE FROM m_users")
        cur.execute("DELETE FROM m_organizations")

        def add_org(name: str) -> int:
            cur.execute(
                "INSERT INTO m_organizations (company_name) VALUES (%s) RETURNING company_seq",
                (name,),
            )
            return cur.fetchone()["company_seq"]

        def add_user(company_seq: int, name: str) -> int:
            cur.execute(
                "INSERT INTO m_users (company_seq, user_name) VALUES (%s, %s) RETURNING user_seq",
                (company_seq, name),
            )
            return cur.fetchone()["user_seq"]

        def add_task(company_seq: int, owner_seq: int, name: str) -> int:
            cur.execute(
                "INSERT INTO t_tasks (company_seq, owner_seq, task_name) VALUES (%s, %s, %s) RETURNING task_seq",
                (company_seq, owner_seq, name),
            )
            return cur.fetchone()["task_seq"]

        acme = add_org("Acme")
        globex = add_org("Globex")

        alice = add_user(acme, "Alice (Acme admin)")
        bob = add_user(acme, "Bob (Acme general)")
        carol = add_user(globex, "Carol (Globex admin)")
        dave = add_user(globex, "Dave (Globex general)")

        task_alice = add_task(acme, alice, "Acme task by Alice")
        task_bob = add_task(acme, bob, "Acme task by Bob")
        task_carol = add_task(globex, carol, "Globex task by Carol")
        task_dave = add_task(globex, dave, "Globex task by Dave")

    return {
        "acme": acme,
        "globex": globex,
        "alice": alice,
        "bob": bob,
        "carol": carol,
        "dave": dave,
        "task_alice": task_alice,
        "task_bob": task_bob,
        "task_carol": task_carol,
        "task_dave": task_dave,
    }


def super_() -> Principal:
    return Principal(role="super")


def operator() -> Principal:
    return Principal(role="operator")


def admin(company_seq: int, user_seq: int | None = None) -> Principal:
    return Principal(role="admin", company_seq=company_seq, user_seq=user_seq)


def general(company_seq: int, user_seq: int) -> Principal:
    return Principal(role="general", company_seq=company_seq, user_seq=user_seq)
