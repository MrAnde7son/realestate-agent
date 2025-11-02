FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev \
    libnss3 libatk-bridge2.0-0 libxcb1 libxcomposite1 libxdamage1 libxfixes3 \
    libxrender1 libxtst6 libxi6 libdbus-1-3 libxrandr2 libasound2 \
    libatk1.0-0 libgtk-3-0 libdrm2 libgbm1 \
    libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libatspi2.0-0 libgobject-2.0-0 libglib2.0-0 libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev libfreetype6 fontconfig libjpeg62-turbo fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend-django/requirements.txt /tmp/backend-requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend-requirements.txt

# Copy the full repository so Django can import shared modules
COPY . /app

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Ensure Django and shared modules are importable regardless of working directory
ENV PYTHONPATH=/app/backend-django:/app
WORKDIR /app/backend-django

# Expose port
EXPOSE 8000

# Launch gunicorn directly for the backend-only image
CMD ["gunicorn", "broker_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
