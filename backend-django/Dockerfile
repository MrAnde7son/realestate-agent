FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev supervisor \
    libnss3 libatk-bridge2.0-0 libxcb1 libxcomposite1 libxdamage1 libxfixes3 \
    libxrender1 libxtst6 libxi6 libdbus-1-3 libxrandr2 libasound2t64 \
    libatk1.0-0 libgtk-3-0 libdrm2 libgbm1 \
    libcairo2 libcairo2-dev libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libpango1.0-dev libatspi2.0-0 libgobject-2.0-0 libglib2.0-0 \
    libgdk-pixbuf-2.0-0 libxml2-dev libxslt-dev libffi-dev \
    libfreetype6 fontconfig libjpeg-turbo8 fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project
COPY . .

# Supervisor config + boot script
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN chmod +x /app/deploy/boot.sh

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000


# Run: migrate -> supervisor (gunicorn + celery)
CMD ["/app/deploy/boot.sh"]
