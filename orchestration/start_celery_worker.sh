#!/bin/bash
# Start Celery worker with minimal HTTP health check for Cloud Run

set -e

PORT=${PORT:-8080}

# Start minimal HTTP health check server in background
python3 <<EOF &
import http.server
import socketserver
import threading
import os

PORT = int(os.environ.get('PORT', '8080'))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/healthz', '/health'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *args):
        pass

with socketserver.TCPServer(('0.0.0.0', PORT), Handler) as httpd:
    httpd.serve_forever()
EOF

# Wait a moment for health server to start
sleep 0.5

# Configure Celery worker defaults for Cloud Run memory constraints
CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-1}
MAX_TASKS_PER_CHILD=${CELERY_MAX_TASKS_PER_CHILD:-10}
PREFETCH_MULTIPLIER=${CELERY_WORKER_PREFETCH_MULTIPLIER:-1}

echo "Starting Celery worker with concurrency=${CONCURRENCY}, max_tasks_per_child=${MAX_TASKS_PER_CHILD}, prefetch_multiplier=${PREFETCH_MULTIPLIER}"

# Run Celery worker in foreground
exec celery -A broker_backend worker -l info \
    -c "$CONCURRENCY" \
    --max-tasks-per-child "$MAX_TASKS_PER_CHILD" \
    --prefetch-multiplier "$PREFETCH_MULTIPLIER"

