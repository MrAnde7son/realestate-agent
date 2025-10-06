#!/usr/bin/env bash
set -euo pipefail

cd /app/backend-django

python manage.py migrate --noinput
exec supervisord -n -c /etc/supervisor/conf.d/supervisord.conf
