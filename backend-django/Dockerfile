FROM python:3.11-slim
WORKDIR /app

# OS deps...
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev supervisor \
    libnss3 libatk-bridge2.0-0 libxcb1 libxcomposite1 libxdamage1 libxfixes3 \
    libxrender1 libxtst6 libxi6 libdbus-1-3 libxrandr2 libasound2 \
    libatk1.0-0 libgtk-3-0 libdrm2 libgbm1 \
    libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libatspi2.0-0 libgobject-2.0-0 libglib2.0-0 libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev libfreetype6 fontconfig libjpeg62-turbo fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

# --- Install backend requirements FIRST, explicitly ---
# Works whether context is repo root or not; fails fast if the file is actually missing
COPY backend-django/requirements.txt /tmp/backend-reqs.txt
RUN pip install --no-cache-dir -r /tmp/backend-reqs.txt

# If you truly need per-module reqs, do them explicitly (optional):
# COPY orchestration/requirements.txt /tmp/orchestration-reqs.txt
# RUN pip install --no-cache-dir -r /tmp/orchestration-reqs.txt
# ...repeat for others only if those files exist in the repo...

# --- Now copy the whole repo (UI excluded via .dockerignore if you want) ---
COPY . .

# Supervisor + boot
RUN cp ./backend-django/deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf \
 && chmod +x ./backend-django/deploy/boot.sh

# Work in Django folder
WORKDIR /app/backend-django

# Non-root (if supervisord/gunicorn paths permit)
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["/app/backend-django/deploy/boot.sh"]
