#!/bin/sh
set -e

# Wait for database to be ready (with retries)
echo "Waiting for database connection..."
max_attempts=30
attempt=0
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
    break
  fi
  attempt=$((attempt + 1))
  echo "Database connection attempt $attempt/$max_attempts failed, retrying in 2 seconds..."
  sleep 2
done

if [ $attempt -eq $max_attempts ]; then
  echo "ERROR: Could not connect to database after $max_attempts attempts"
  echo "Database configuration:"
  echo "  POSTGRES_HOST: ${POSTGRES_HOST:-<not set>}"
  echo "  POSTGRES_DB: ${POSTGRES_DB:-<not set>}"
  echo "  POSTGRES_USER: ${POSTGRES_USER:-<not set>}"
  echo "  POSTGRES_PORT: ${POSTGRES_PORT:-<not set>}"
  exit 1
fi

# Run database migrations before starting the application.
echo "Running migrations..."
python manage.py makemigrations || echo "Warning: makemigrations failed or no changes"
python manage.py migrate --noinput

# Execute the main container command (e.g., Gunicorn).
echo "Starting application..."
exec "$@"
