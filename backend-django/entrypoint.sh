#!/bin/sh
# Don't use set -e here - we want to continue even if some steps fail
# The app should start and listen on the port even if DB connection or migrations fail

# Get PORT from environment (Cloud Run sets this automatically)
PORT=${PORT:-8000}
echo "Starting application on port $PORT"

# Wait for database to be ready (with retries, but don't block startup too long)
echo "Waiting for database connection..."
max_attempts=15  # Reduced from 30 to speed up startup
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
# Don't fail if migrations fail - let the app start and retry on first request
echo "Running migrations..."
python manage.py migrate --noinput || echo "WARNING: Migrations failed, but continuing startup..."

# Execute the main container command (e.g., Gunicorn).
# This MUST succeed - if gunicorn fails to start, the container will fail
echo "Starting application on port $PORT..."
exec "$@"
