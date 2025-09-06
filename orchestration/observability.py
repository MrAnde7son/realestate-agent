from prometheus_client import Counter, Histogram, start_http_server
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import os

# Tracing setup
resource = Resource(attributes={"service.name": "realestate-pipeline"})
provider = TracerProvider(resource=resource)

# Choose exporter based on environment
_otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
if _otlp_endpoint:
    exporter = OTLPSpanExporter(endpoint=_otlp_endpoint)
else:
    exporter = ConsoleSpanExporter()

provider.add_span_processor(BatchSpanProcessor(exporter))
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

def start_metrics_server(port: int = 8000) -> None:
    global _metrics_started
    if not _metrics_started:
        start_http_server(port)
        _metrics_started = True
