#!/usr/bin/env bash
set -e
echo "[entrypoint] Applying database migrations..."
alembic upgrade head
echo "[entrypoint] Starting API on :8080"
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
