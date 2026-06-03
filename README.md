# Backend Setup

## Prerequisites

- Python 3.11+
- `uv`
- Docker

## Local Setup

```bash
cp .env.example .env
uv sync
```

## Start Database (Docker)

```bash
docker run --name springstreet-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=springstreet \
  -p 5432:5432 \
  -d postgres:16
```

## Run Migrations

```bash
uv run alembic upgrade head
```

## Start Backend

```bash
uv run python main.py
```
