#!/bin/sh

# Wait for DB to be ready before running migrations
until python -c "import os; from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL')); engine.connect(); print('Database connected')" 2>/dev/null; do
  echo "Waiting for database to be ready..."
  sleep 5
done

# Run Alembic migrations
echo "Running alembic migrations..."
alembic upgrade head
if [ $? -ne 0 ]; then
  echo "❌ Alembic migration failed"
  exit 1
fi

echo "✅ Database migrations completed"

# Start the FastAPI app
echo "Starting Uvicorn server..."
exec uvicorn app.backend.main:app --host 0.0.0.0 --port 8000