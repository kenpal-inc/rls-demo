# RLS demo

RLS を利用したマルチテナント運用のデモ

## setup

- docker
- python
- uv

```shell
docker compose -f docker/compose.yml up -d

cp .env.example .env

uv run alembic upgrade head

uv run fastapi dev # dev server
uv run fastapi run # prod server
```

## hist

```shell
uv init

uv add alembic "psycopg[binary]"
uv add --dev ruff

uv run alembic init alembic

uv run alembic revision --rev-id 0001 -m "enable PostGIS"
uv run alembic revision --rev-id 0002 -m "create role"
uv run alembic revision --rev-id 0003 -m "create tables"
uv run alembic revision --rev-id 0004 -m "add privileges"
uv run alembic revision --rev-id 0005 -m "create app user"

uv add "fastapi[standard]"
```
