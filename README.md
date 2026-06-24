# RLS demo

RLS を利用したマルチテナント運用のデモ

- super\
  スーパーユーザーとして、全てのテナントにアクセス・操作可能
- operator\
  運用オペレーターとして、全てのテナントにアクセス可能
- admin\
  テナント管理者として、所属するテナントにアクセス・操作可能
- general\
  一般ユーザーとして、所属するテナントにアクセス可能\
  制限された操作のみ可能

## setup

以下がインストール済みを前提とする

- Docker
- Python
- uv

環境変数ファイルの生成

```shell
cp .env.example .env
```

PostgreSQL docker コンテナの起動

```shell
docker compose -f docker/compose.yml up -d
```

DB の初期化

```shell
uv run alembic upgrade head
```

FastAPI サーバの起動

```shell
uv run fastapi dev # dev server
uv run fastapi run # prod server
```

<http://127.0.0.1:8000/docs> で API ドキュメントを確認可能

## test

テナント分離の検証テスト\
マイグレーション適用済みを前提とする

```shell
uv run pytest
```

RLS ポリシーの確認

```shell
uv run psql \
  -h localhost -p 5432 -U postgres -d postgres \
  -f sql/select-policies.sql
```
