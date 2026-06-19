import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional
from urllib.parse import urlsplit

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row


ALLOWED_ROLES = {"super", "operator", "admin", "general"}


load_dotenv()


def app_user_conninfo() -> dict:
    base = os.environ.get("DATABASE_URL")
    password = os.environ.get("APP_USER_PASSWORD")
    if not base:
        raise RuntimeError("DATABASE_URL environment variable is required")
    if not password:
        raise RuntimeError("APP_USER_PASSWORD environment variable is required")

    parts = urlsplit(base)
    return {
        "host": parts.hostname or "localhost",
        "port": parts.port or 5432,
        "dbname": parts.path.lstrip("/") or "postgres",
        "user": "app_user",
        "password": password,
    }


@dataclass
class Principal:
    role: str
    company_seq: Optional[int] = None
    user_seq: Optional[int] = None


@contextmanager
def rls_session(principal: Principal) -> Iterator[psycopg.Cursor]:
    if principal.role not in ALLOWED_ROLES:
        raise ValueError(f"unknown role: {principal.role}")

    conn = psycopg.connect(**app_user_conninfo(), row_factory=dict_row)
    try:
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL ROLE {principal.role}")

            if principal.company_seq is not None:
                cur.execute(
                    "SELECT set_config('app.current_company_seq', %s, true)",
                    (str(principal.company_seq),),
                )
            if principal.user_seq is not None:
                cur.execute(
                    "SELECT set_config('app.current_user_seq', %s, true)",
                    (str(principal.user_seq),),
                )

            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
