#!/usr/bin/env bash
set -euo pipefail
python manage.py migrate --noinput
exec supervisord -n -c /etc/supervisor/conf.d/supervisord.conf
