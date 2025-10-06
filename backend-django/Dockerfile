FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev supervisor \
    libnss3 libatk-bridge2.0-0 libxcb1 libxcomposite1 libxdamage1 libxfixes3 \
    libxrender1 libxtst6 libxi6 libdbus-1-3 libxrandr2 libasound2 \
    libatk1.0-0 libgtk-3-0 libdrm2 libgbm1 \
    libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libatspi2.0-0 libgobject-2.0-0 libglib2.0-0 libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev libfreetype6 fontconfig libjpeg62-turbo fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

# Copy the repository contents (frontend directories excluded via .dockerignore)
COPY . .

# Install Python dependencies for each internal service
RUN set -eux; \
    pip install --no-cache-dir -r ./backend-django/requirements.txt; \
    for req in orchestration gov govmap yad2 mavat gis db; do \
        req_file="./${req}/requirements.txt"; \
        if [ -f "${req_file}" ]; then \
            pip install --no-cache-dir -r "${req_file}"; \
        fi; \
    done

# Supervisor config + boot script
RUN cp ./backend-django/deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN chmod +x ./backend-django/deploy/boot.sh

# Set the working directory to the Django project so manage.py commands run correctly
WORKDIR ./backend-django

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000


# Run: migrate -> supervisor (gunicorn + celery)
CMD ["/app/backend-django/deploy/boot.sh"]
