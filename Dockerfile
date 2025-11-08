# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    CHROME_BIN=/usr/bin/google-chrome-stable

WORKDIR /app

# Install system dependencies required for Django, Celery, Playwright and geo/GIS collectors
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    supervisor \
    curl \
    wget \
    gnupg \
    # Playwright/Chromium runtime deps
    libnss3 \
    libatk-bridge2.0-0 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libdbus-1-3 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libgtk-3-0 \
    libdrm2 \
    libgbm1 \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libatspi2.0-0 \
    libgobject-2.0-0 \
    libglib2.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libfreetype6 \
    fontconfig \
    fonts-noto-core \
    # GIS/geo stack dependencies used by collectors
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    proj-bin \
    libproj-dev \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome for Selenium
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* \
    && google-chrome --version \
    && which google-chrome-stable || which google-chrome || (echo "Chrome binary not found in PATH" && exit 1)

# Install Python dependencies for backend + pipeline + collectors
COPY requirements-production.txt /tmp/requirements-production.txt
# Copy all referenced requirement files so nested -r directives resolve during install
COPY backend-django/requirements.txt /tmp/backend-django/requirements.txt
COPY backend-django/requirements-langchain.txt /tmp/backend-django/requirements-langchain.txt
COPY db/requirements.txt /tmp/db/requirements.txt
COPY orchestration/requirements.txt /tmp/orchestration/requirements.txt
COPY gov/requirements.txt /tmp/gov/requirements.txt
COPY govmap/requirements.txt /tmp/govmap/requirements.txt
COPY gis/requirements.txt /tmp/gis/requirements.txt
COPY yad2/requirements.txt /tmp/yad2/requirements.txt
COPY mavat/requirements.txt /tmp/mavat/requirements.txt
COPY handasa/requirements.txt /tmp/handasa/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements-production.txt

# Preinstall Chromium for Playwright collectors
RUN mkdir -p "$PLAYWRIGHT_BROWSERS_PATH" \
    && python -m playwright install chromium

# Copy the full repository so orchestration/collector modules are available to Django
COPY . /app

# Prepare supervisor configuration and boot script
RUN mkdir -p /etc/supervisor/conf.d \
    && cp backend-django/deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf \
    && chmod +x backend-django/deploy/boot.sh

# Ensure runtime user has access to application files and Playwright browsers
# Also ensure Chrome is accessible (it should be in /usr/bin which is world-readable)
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app "$PLAYWRIGHT_BROWSERS_PATH" \
    && test -x /usr/bin/google-chrome-stable || test -x /usr/bin/google-chrome || (echo "Chrome is not executable" && exit 1)

USER app

# Keep the full repository on the PYTHONPATH for Django, orchestration, and collectors
ENV PYTHONPATH=/app:/app/backend-django
WORKDIR /app

EXPOSE 8000

CMD ["backend-django/deploy/boot.sh"]
