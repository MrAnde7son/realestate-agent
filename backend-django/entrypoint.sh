#!/bin/sh
# Get PORT from environment (Cloud Run sets this automatically)
PORT=${PORT:-8000}
echo "Starting application on port $PORT"

echo "Waiting for database connection..."
max_attempts=3
attempt=0
db_connected=0

while [ $attempt -lt $max_attempts ]; do
  if python -c "
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')
django.setup()
from django.db import connection
connection.ensure_connection()
" 2>/dev/null; then
    echo "Database connection successful!"
    db_connected=1
    break
  fi
  attempt=$((attempt + 1))
  echo "Database connection attempt $attempt/$max_attempts failed, retrying in 1 second..."
  sleep 1
done

if [ $db_connected -eq 0 ]; then
  echo "WARNING: Could not connect to database after $max_attempts attempts"
  echo "Database configuration:"
  echo "  POSTGRES_HOST: ${POSTGRES_HOST:-<not set>}"
  echo "  POSTGRES_DB: ${POSTGRES_DB:-<not set>}"
  echo "  POSTGRES_USER: ${POSTGRES_USER:-<not set>}"
  echo "  POSTGRES_PORT: ${POSTGRES_PORT:-<not set>}"
  echo "Continuing anyway - application will retry database connection on first request..."
fi

# Run database migrations before starting the application.
echo "Applying migrations..."
if ! python manage.py migrate --noinput 2>&1; then
    echo "ERROR: Migrations failed! Exiting..."
    exit 1
fi

echo "Starting application on port $PORT..."
exec "$@"
