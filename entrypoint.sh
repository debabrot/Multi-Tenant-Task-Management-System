#!/bin/sh
alembic upgrade head
echo "Db migration complete"

exec uvicorn app.backend.main:app --host 0.0.0.0 --port 8000
echo "app is running"