#!/bin/sh
set -e

# Run database migrations before starting the application.
python manage.py makemigrations
python manage.py migrate --noinput

# Execute the main container command (e.g., Gunicorn).
exec "$@"
