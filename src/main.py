from enum import Enum
from typing import Optional

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.db import Principal, rls_session

app = FastAPI(title="RLS demo")


class Role(str, Enum):
    super = "super"
    operator = "operator"
    admin = "admin"
    general = "general"


def get_principal(
    x_role: Role = Header(..., alias="X-Role"),
    x_company_seq: Optional[int] = Header(None, alias="X-Company-Seq"),
    x_user_seq: Optional[int] = Header(None, alias="X-User-Seq"),
) -> Principal:
    return Principal(role=x_role.value, company_seq=x_company_seq, user_seq=x_user_seq)


@app.exception_handler(psycopg.Error)
def handle_psycopg_error(request, exc: psycopg.Error) -> JSONResponse:
    sqlstate = getattr(exc, "sqlstate", None)
    # 42501: 権限不足 / RLS の WITH CHECK 違反
    status = 403 if sqlstate == "42501" else 400
    message = exc.diag.message_primary if exc.diag else str(exc)
    return JSONResponse(
        status_code=status,
        content={"error": message, "sqlstate": sqlstate},
    )


class TaskCreate(BaseModel):
    company_seq: int
    owner_seq: int
    task_name: str
    task_description: Optional[str] = None


class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    task_description: Optional[str] = None


@app.post("/seed", status_code=201, tags=["setup"])
def seed():
    """
    デモ用データ作成

    既存データを削除の後、データを作成
    """

    principal = Principal(role="super")
    with rls_session(principal) as cur:
        cur.execute("DELETE FROM t_tasks")
        cur.execute("DELETE FROM m_users")
        cur.execute("DELETE FROM m_organizations")

        # m_organizations
        cur.execute(
            "INSERT INTO m_organizations (company_name) VALUES (%s) RETURNING company_seq",
            ("Acme",),
        )
        acme = cur.fetchone()["company_seq"]
        cur.execute(
            "INSERT INTO m_organizations (company_name) VALUES (%s) RETURNING company_seq",
            ("Globex",),
        )
        globex = cur.fetchone()["company_seq"]

        # m_users
        def add_user(company_seq: int, name: str) -> int:
            cur.execute(
                "INSERT INTO m_users (company_seq, user_name) VALUES (%s, %s) RETURNING user_seq",
                (company_seq, name),
            )
            return cur.fetchone()["user_seq"]

        alice = add_user(acme, "Alice (Acme admin)")
        bob = add_user(acme, "Bob (Acme general)")
        carol = add_user(globex, "Carol (Globex admin)")
        dave = add_user(globex, "Dave (Globex general)")

        # t_tasks
        def add_task(company_seq: int, owner_seq: int, name: str) -> None:
            cur.execute(
                """
                INSERT INTO t_tasks (company_seq, owner_seq, task_name)
                VALUES (%s, %s, %s)
                """,
                (company_seq, owner_seq, name),
            )

        add_task(acme, alice, "Acme task by Alice")
        add_task(acme, bob, "Acme task by Bob")
        add_task(globex, carol, "Globex task by Carol")
        add_task(globex, dave, "Globex task by Dave")

    return {
        "organizations": {"acme": acme, "globex": globex},
        "users": {"alice": alice, "bob": bob, "carol": carol, "dave": dave},
    }


@app.get("/organizations", tags=["master"])
def list_organizations(principal: Principal = Depends(get_principal)):
    """
    閲覧できる組織一覧

    - super/operator: 全組織閲覧可
    - admin/general: 自組織のみ閲覧可
    """

    with rls_session(principal) as cur:
        cur.execute("SELECT * FROM m_organizations ORDER BY company_seq")
        rows = cur.fetchall()
    return {"count": len(rows), "items": rows}


@app.get("/users", tags=["master"])
def list_users(principal: Principal = Depends(get_principal)):
    """
    閲覧できるユーザー一覧

    - super/operator: 全ユーザー閲覧可
    - admin/general: 自組織のユーザーのみ閲覧可
    """

    with rls_session(principal) as cur:
        cur.execute("SELECT * FROM m_users ORDER BY user_seq")
        rows = cur.fetchall()
    return {"count": len(rows), "items": rows}


@app.get("/tasks")
def list_tasks(principal: Principal = Depends(get_principal)):
    """
    閲覧できるタスク一覧

    - super/operator: 全タスク閲覧可
    - admin/general: 自組織のタスクのみ閲覧可
    """

    with rls_session(principal) as cur:
        cur.execute("SELECT * FROM t_tasks ORDER BY task_seq")
        rows = cur.fetchall()
    return {"count": len(rows), "items": rows}


@app.post("/tasks", status_code=201)
def create_task(body: TaskCreate, principal: Principal = Depends(get_principal)):
    """
    タスク作成

    - super: 任意のテナントへ作成可
    - operator: INSERT 権限なし
    - admin: 自テナントへ作成可
    - general: 自テナント かつ owner_seq=自分 のみ作成可
    """

    with rls_session(principal) as cur:
        cur.execute(
            """
            INSERT INTO t_tasks (company_seq, owner_seq, task_name, task_description)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (body.company_seq, body.owner_seq, body.task_name, body.task_description),
        )
        row = cur.fetchone()
    return row


@app.patch("/tasks/{task_seq}")
def update_task(
    task_seq: int,
    body: TaskUpdate,
    principal: Principal = Depends(get_principal),
):
    """
    タスク更新

    - super: 任意のテナントの行を更新可
    - operator: UPDATE 権限なし
    - general: 自テナント かつ owner_seq=自分 の行のみ更新可
    - admin: 自テナントの行を更新可
    """

    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="no fields to update")

    set_clause = ", ".join(f"{col} = %s" for col in fields)
    params = list(fields.values()) + [task_seq]

    with rls_session(principal) as cur:
        cur.execute(
            f"UPDATE t_tasks SET {set_clause} WHERE task_seq = %s RETURNING *",
            params,
        )
        row = cur.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="task not found or not permitted to update",
        )
    return row


@app.delete("/tasks/{task_seq}", status_code=200)
def delete_task(task_seq: int, principal: Principal = Depends(get_principal)):
    """
    タスク削除

    - super のみレコード削除可能
    """

    with rls_session(principal) as cur:
        cur.execute(
            "DELETE FROM t_tasks WHERE task_seq = %s RETURNING task_seq", (task_seq,)
        )
        row = cur.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="task not found or not permitted to delete",
        )
    return {"deleted_task_seq": row["task_seq"]}
