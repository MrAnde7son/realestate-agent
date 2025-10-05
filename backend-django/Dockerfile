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

# Copy requirements and install Python dependencies
COPY backend-django/requirements.txt .
COPY orchestration/requirements.txt ./orchestration-requirements.txt
COPY gov/requirements.txt ./gov-requirements.txt
COPY govmap/requirements.txt ./govmap-requirements.txt
COPY yad2/requirements.txt ./yad2-requirements.txt
COPY mavat/requirements.txt ./mavat-requirements.txt
COPY gis/requirements.txt ./gis-requirements.txt
COPY db/requirements.txt ./db-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r orchestration-requirements.txt && \
    pip install --no-cache-dir -r gov-requirements.txt && \
    pip install --no-cache-dir -r govmap-requirements.txt && \
    pip install --no-cache-dir -r yad2-requirements.txt && \
    pip install --no-cache-dir -r mavat-requirements.txt && \
    pip install --no-cache-dir -r gis-requirements.txt && \
    pip install --no-cache-dir -r db-requirements.txt

# Copy all required modules from root directory
# Note: Data pipeline imports from orchestration, utils, db, yad2, gov, gis, govmap, mavat
COPY orchestration /app/orchestration
COPY utils /app/utils
COPY db /app/db
COPY yad2 /app/yad2
COPY gov /app/gov
COPY gis /app/gis
COPY govmap /app/govmap
COPY mavat /app/mavat

# Copy the Django project
COPY backend-django /app/backend-django

# Supervisor config + boot script
RUN cp /app/backend-django/deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN chmod +x /app/backend-django/deploy/boot.sh

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000


# Run: migrate -> supervisor (gunicorn + celery)
CMD ["/app/backend-django/deploy/boot.sh"]
