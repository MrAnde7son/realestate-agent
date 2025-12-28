from __future__ import annotations

import sys
from contextlib import nullcontext
from types import ModuleType, SimpleNamespace


class _DummyTransformer:
    @staticmethod
    def from_crs(*args, **kwargs):
        return _DummyTransformer()

    def transform(self, x, y, *args, **kwargs):
        return x, y


sys.modules.setdefault("pyproj", SimpleNamespace(Transformer=_DummyTransformer))

if "selenium" not in sys.modules:
    selenium_module = ModuleType("selenium")
    webdriver_module = ModuleType("selenium.webdriver")
    webdriver_module.__path__ = []  # mark as package
    common_module = ModuleType("selenium.webdriver.common")
    common_module.__path__ = []
    action_chains_module = ModuleType("selenium.webdriver.common.action_chains")
    by_module = ModuleType("selenium.webdriver.common.by")
    keys_module = ModuleType("selenium.webdriver.common.keys")
    selenium_common_module = ModuleType("selenium.common")
    selenium_common_module.__path__ = []
    selenium_common_exceptions_module = ModuleType("selenium.common.exceptions")
    chrome_module = ModuleType("selenium.webdriver.chrome")
    chrome_module.__path__ = []
    chrome_service_module = ModuleType("selenium.webdriver.chrome.service")
    support_module = ModuleType("selenium.webdriver.support")
    support_module.__path__ = []
    support_ui_module = ModuleType("selenium.webdriver.support.ui")
    expected_conditions_module = ModuleType(
        "selenium.webdriver.support.expected_conditions"
    )

    class _DummyBy:
        ID = "id"
        XPATH = "xpath"
        CSS_SELECTOR = "css"

    class _DummyKeys:
        ENTER = "enter"

    class _DummyChromeOptions:
        def add_argument(self, *args, **kwargs):
            return None

        def add_experimental_option(self, *args, **kwargs):
            return None

    class _DummyChrome:
        def __init__(self, *args, **kwargs):
            pass

        def execute_cdp_cmd(self, *args, **kwargs):
            return None

        def execute_script(self, *args, **kwargs):
            return ""

    class _DummyService:
        def __init__(self, *args, **kwargs):
            pass

    class _DummySeleniumException(Exception):
        pass

    webdriver_module.ChromeOptions = _DummyChromeOptions
    webdriver_module.Chrome = _DummyChrome

    by_module.By = _DummyBy
    keys_module.Keys = _DummyKeys
    chrome_service_module.Service = _DummyService
    support_ui_module.WebDriverWait = object
    support_module.ui = support_ui_module
    support_module.expected_conditions = expected_conditions_module
    for name in (
        "WebDriverException",
        "TimeoutException",
        "NoSuchElementException",
        "ElementClickInterceptedException",
        "StaleElementReferenceException",
        "ElementNotInteractableException",
    ):
        setattr(selenium_common_exceptions_module, name, _DummySeleniumException)

    selenium_module.webdriver = webdriver_module

    sys.modules["selenium"] = selenium_module
    sys.modules["selenium.webdriver"] = webdriver_module

    class _DummyActionChains:
        def __init__(self, *args, **kwargs):
            pass

        def move_to_element(self, *args, **kwargs):
            return self

        def click(self, *args, **kwargs):
            return self

        def perform(self, *args, **kwargs):
            return None

    action_chains_module.ActionChains = _DummyActionChains

    sys.modules["selenium.webdriver.common"] = common_module
    sys.modules["selenium.webdriver.common.action_chains"] = action_chains_module
    sys.modules["selenium.webdriver.common.by"] = by_module
    sys.modules["selenium.webdriver.common.keys"] = keys_module
    sys.modules["selenium.webdriver.chrome"] = chrome_module
    sys.modules["selenium.webdriver.chrome.service"] = chrome_service_module
    sys.modules["selenium.webdriver.support"] = support_module
    sys.modules["selenium.webdriver.support.ui"] = support_ui_module
    sys.modules["selenium.webdriver.support.expected_conditions"] = (
        expected_conditions_module
    )
    sys.modules["selenium.common"] = selenium_common_module
    sys.modules["selenium.common.exceptions"] = selenium_common_exceptions_module


if "pandas" not in sys.modules:
    pandas_module = ModuleType("pandas")

    class _DummyDataFrame(dict):
        pass

    def _identity(*args, **kwargs):  # pragma: no cover - testing stub
        return args[0] if args else None

    pandas_module.DataFrame = _DummyDataFrame
    pandas_module.Series = _DummyDataFrame
    pandas_module.json_normalize = _identity
    pandas_module.Timestamp = lambda *args, **kwargs: None

    sys.modules["pandas"] = pandas_module

if "prometheus_client" not in sys.modules:
    prometheus_module = ModuleType("prometheus_client")

    class _DummyMetric:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def observe(self, *args, **kwargs):
            return None

        def inc(self, *args, **kwargs):
            return None

    prometheus_module.Counter = _DummyMetric
    prometheus_module.Histogram = _DummyMetric
    prometheus_module.start_http_server = lambda *args, **kwargs: None

    sys.modules["prometheus_client"] = prometheus_module

if "opentelemetry" not in sys.modules:
    otel_module = ModuleType("opentelemetry")
    trace_module = ModuleType("opentelemetry.trace")
    context_module = ModuleType("opentelemetry.context")

    class _DummyTracer:
        def start_as_current_span(self, *args, **kwargs):
            return nullcontext()

        def start_span(self, *args, **kwargs):
            return nullcontext()

    def _get_tracer(*args, **kwargs):
        return _DummyTracer()

    def _set_tracer_provider(*args, **kwargs):
        return None

    def _context_identity(*args, **kwargs):
        return None

    context_module.attach = _context_identity
    context_module.detach = _context_identity
    context_module.get_current = _context_identity
    context_module.set_value = _context_identity

    trace_module.get_tracer = _get_tracer
    trace_module.set_tracer_provider = _set_tracer_provider

    sdk_module = ModuleType("opentelemetry.sdk")
    resources_module = ModuleType("opentelemetry.sdk.resources")

    class _DummyResource:
        def __init__(self, *args, **kwargs):
            pass

    resources_module.Resource = _DummyResource

    sdk_trace_module = ModuleType("opentelemetry.sdk.trace")

    class _DummyTracerProvider:
        def __init__(self, *args, **kwargs):
            pass

        def add_span_processor(self, *args, **kwargs):
            return None

    sdk_trace_module.TracerProvider = _DummyTracerProvider

    sdk_trace_export_module = ModuleType("opentelemetry.sdk.trace.export")

    class _DummyBatchSpanProcessor:
        def __init__(self, *args, **kwargs):
            pass

    class _DummyConsoleSpanExporter:
        def __init__(self, *args, **kwargs):
            pass

    sdk_trace_export_module.BatchSpanProcessor = _DummyBatchSpanProcessor
    sdk_trace_export_module.ConsoleSpanExporter = _DummyConsoleSpanExporter

    exporter_module = ModuleType("opentelemetry.exporter")
    exporter_otlp_module = ModuleType("opentelemetry.exporter.otlp")
    exporter_otlp_proto_module = ModuleType("opentelemetry.exporter.otlp.proto")
    exporter_otlp_proto_http_module = ModuleType(
        "opentelemetry.exporter.otlp.proto.http"
    )
    exporter_otlp_proto_http_trace_module = ModuleType(
        "opentelemetry.exporter.otlp.proto.http.trace_exporter"
    )

    class _DummyOTLPSpanExporter:
        def __init__(self, *args, **kwargs):
            pass

    exporter_otlp_proto_http_trace_module.OTLPSpanExporter = _DummyOTLPSpanExporter

    otel_module.trace = trace_module
    otel_module.sdk = sdk_module
    otel_module.context = context_module

    sys.modules["opentelemetry"] = otel_module
    sys.modules["opentelemetry.trace"] = trace_module
    sys.modules["opentelemetry.context"] = context_module
    sys.modules["opentelemetry.sdk"] = sdk_module
    sys.modules["opentelemetry.sdk.resources"] = resources_module
    sys.modules["opentelemetry.sdk.trace"] = sdk_trace_module
    sys.modules["opentelemetry.sdk.trace.export"] = sdk_trace_export_module
    sys.modules["opentelemetry.exporter"] = exporter_module
    sys.modules["opentelemetry.exporter.otlp"] = exporter_otlp_module
    sys.modules["opentelemetry.exporter.otlp.proto"] = exporter_otlp_proto_module
    sys.modules["opentelemetry.exporter.otlp.proto.http"] = (
        exporter_otlp_proto_http_module
    )
    sys.modules["opentelemetry.exporter.otlp.proto.http.trace_exporter"] = (
        exporter_otlp_proto_http_trace_module
    )
