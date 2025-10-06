#!/usr/bin/env bash
set -euo pipefail

# Resolve the Django project directory relative to this script so we can
# reliably locate it even if the container root differs (e.g. /app/backend-django
# or /app/realestate-agent/backend-django).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -d "$REPO_ROOT/backend-django" ]]; then
  DJANGO_DIR="$REPO_ROOT/backend-django"
elif [[ -d "$REPO_ROOT" && -f "$REPO_ROOT/manage.py" ]]; then
  DJANGO_DIR="$REPO_ROOT"
elif [[ -d "/app/backend-django" ]]; then
  DJANGO_DIR="/app/backend-django"
elif [[ -d "/app" && -f "/app/manage.py" ]]; then
  DJANGO_DIR="/app"
else
  echo "Unable to locate Django project directory" >&2
  ls -al "$REPO_ROOT" || true
  exit 1
fi

cd "$DJANGO_DIR"

python manage.py migrate --noinput
exec supervisord -n -c /etc/supervisor/conf.d/supervisord.conf
