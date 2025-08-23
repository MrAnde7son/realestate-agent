#!/usr/bin/env bash
set -euo pipefail

echo "[boot] Running migrations…"
python manage.py migrate --noinput

# Optional (only if you use Django staticfiles):
# echo "[boot] Collecting static…"
# python manage.py collectstatic --noinput

echo "[boot] Starting supervisor (gunicorn + celery)…"
exec supervisord -n -c /etc/supervisor/conf.d/supervisord.conf
