"""Tracing and metrics utilities for the orchestration layer.

This module wires up OpenTelemetry tracing and uses ``prometheus-client`` to
emit Prometheus metrics.  The dependency is required for the counters and
histograms defined below as well as the HTTP metrics endpoint exposed via
``start_metrics_server``.
"""

import os

from prometheus_client import Counter, Histogram, start_http_server
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Tracing setup
resource = Resource(attributes={"service.name": "realestate-pipeline"})
provider = TracerProvider(resource=resource)

# Choose exporter based on environment
_otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
_enable_tracing = os.getenv("ENABLE_TRACING", "false").lower() == "true"

if _otlp_endpoint:
    exporter = OTLPSpanExporter(endpoint=_otlp_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
elif _log_level == "DEBUG" and _enable_tracing:
    # Only use console exporter in debug mode when explicitly enabled
    exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
else:
    # In production, don't add any span processor to avoid verbose output
    pass
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# Prometheus metrics
COLLECTOR_LATENCY = Histogram(
    "collector_latency_seconds",
    "Time spent collecting data from each source",
    ["source"],
)
COLLECTOR_SUCCESS = Counter(
    "collector_success_total",
    "Successful collector calls",
    ["source"],
)
COLLECTOR_FAILURE = Counter(
    "collector_failure_total",
    "Failed collector calls",
    ["source"],
)

_metrics_started = False
_metrics_server = None

def start_metrics_server(port: int = 8000) -> None:
    global _metrics_started, _metrics_server
    if not _metrics_started:
        try:
            _metrics_server = start_http_server(port)
            _metrics_started = True
        except OSError as e:
            if e.errno == 48:  # Address already in use
                # In test environment, this is expected - just mark as started
                _metrics_started = True
            else:
                raise
