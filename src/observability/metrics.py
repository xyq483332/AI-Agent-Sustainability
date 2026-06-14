"""
Metrics Collector (OpenTelemetry SDK)

Collects and exports metrics via OTel SDK → OTLP → OTel Collector → Prometheus.

Public API (backward-compatible):
  - MetricsCollector: wraps OTel MeterProvider, exposes counter/gauge/histogram
  - PluginMetrics: high-level helpers for plugin-specific metrics

Data flow:
  App code → MetricsCollector → OTel SDK (OTLP gRPC) → OTel Collector → Prometheus scrape (:8889)
"""

import logging
import os
from typing import Any, Dict, Optional

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import \
    OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton MeterProvider initialisation
# ---------------------------------------------------------------------------

_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "ai-agent-sustainability")
_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")

_resource = Resource.create({SERVICE_NAME: _SERVICE_NAME})
_exporter = OTLPMetricExporter(endpoint=_OTLP_ENDPOINT, insecure=True)
_reader = PeriodicExportingMetricReader(
    _exporter,
    export_interval_millis=10_000,  # export every 10s
)
_meter_provider = MeterProvider(resource=_resource, metric_readers=[_reader])
_meter = _meter_provider.get_meter(_SERVICE_NAME, "1.0.0")


# ---------------------------------------------------------------------------
# MetricsCollector – wraps OTel instruments with a dict-based query API
# ---------------------------------------------------------------------------


class MetricsCollector:
    """Thin wrapper around OTel Meter that keeps the original dict-based API.

    Internal state (`counters`, `gauges`, `histograms`) is kept for local
    inspection / ``get_metrics()`` calls.  The OTel SDK handles export to
    the OTel Collector automatically.
    """

    def __init__(self, meter: Optional[metrics.Meter] = None):
        self._meter = meter or _meter
        # Local mirrors for get_metrics() inspection
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = {}
        # OTel instruments cache
        self._otel_counters: Dict[str, metrics.Counter] = {}
        self._otel_gauges: Dict[str, metrics.UpDownCounter] = {}
        self._otel_histograms: Dict[str, metrics.Histogram] = {}

    # -- public helpers -----------------------------------------------------

    def increment_counter(
        self, name: str, value: float = 1, labels: Dict[str, str] = None
    ):
        key = self._make_key(name, labels)
        self.counters[key] = self.counters.get(key, 0) + value
        instr = self._get_or_create_counter(name)
        attrs = labels or {}
        instr.add(value, attributes=attrs)

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        key = self._make_key(name, labels)
        old = self.gauges.get(key, 0)
        self.gauges[key] = value
        instr = self._get_or_create_gauge(name)
        attrs = labels or {}
        instr.add(value - old, attributes=attrs)

    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        key = self._make_key(name, labels)
        self.histograms.setdefault(key, []).append(value)
        instr = self._get_or_create_histogram(name)
        attrs = labels or {}
        instr.record(value, attributes=attrs)

    def get_metrics(self) -> Dict[str, Any]:
        """Return a snapshot of all recorded metrics (for /api/v1/metrics)."""
        lines: list[str] = []
        for key, value in self.counters.items():
            lines.append(f"{key} {value}")
        for key, value in self.gauges.items():
            lines.append(f"{key} {value}")
        for key, values in self.histograms.items():
            if values:
                lines.append(f"{key}_avg {sum(values) / len(values)}")
                lines.append(f"{key}_count {len(values)}")
        return {"metrics": "\n".join(lines)}

    def reset(self):
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()

    # -- internal -----------------------------------------------------------

    @staticmethod
    def _make_key(name: str, labels: Dict[str, str] = None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _get_or_create_counter(self, name: str) -> metrics.Counter:
        if name not in self._otel_counters:
            self._otel_counters[name] = self._meter.create_counter(
                name=name, description=f"Counter: {name}", unit="1"
            )
        return self._otel_counters[name]

    def _get_or_create_gauge(self, name: str) -> metrics.UpDownCounter:
        if name not in self._otel_gauges:
            self._otel_gauges[name] = self._meter.create_up_down_counter(
                name=name, description=f"Gauge: {name}", unit="1"
            )
        return self._otel_gauges[name]

    def _get_or_create_histogram(self, name: str) -> metrics.Histogram:
        if name not in self._otel_histograms:
            self._otel_histograms[name] = self._meter.create_histogram(
                name=name, description=f"Histogram: {name}", unit="ms"
            )
        return self._otel_histograms[name]


# ---------------------------------------------------------------------------
# PluginMetrics – domain-specific helpers
# ---------------------------------------------------------------------------


class PluginMetrics:
    """High-level helpers for plugin lifecycle metrics."""

    def __init__(self, collector: MetricsCollector):
        self._c = collector

    def record_plugin_load(self, plugin_name: str, duration_ms: float):
        self._c.observe_histogram(
            "plugin_load_duration_ms",
            duration_ms,
            labels={"plugin": plugin_name},
        )

    def record_plugin_execution(
        self, plugin_name: str, duration_ms: float, success: bool
    ):
        self._c.observe_histogram(
            "plugin_execution_duration_ms",
            duration_ms,
            labels={"plugin": plugin_name, "success": str(success).lower()},
        )
        self._c.increment_counter(
            "plugin_execution_total",
            1,
            labels={"plugin": plugin_name, "success": str(success).lower()},
        )

    def record_security_validation(
        self, plugin_name: str, duration_ms: float, passed: bool
    ):
        self._c.observe_histogram(
            "security_validation_duration_ms",
            duration_ms,
            labels={"plugin": plugin_name, "passed": str(passed).lower()},
        )
        self._c.increment_counter(
            "security_validation_total",
            1,
            labels={"plugin": plugin_name, "passed": str(passed).lower()},
        )

    def set_plugin_memory_usage(self, plugin_name: str, memory_mb: float):
        self._c.set_gauge(
            "plugin_memory_usage_mb",
            memory_mb,
            labels={"plugin": plugin_name},
        )
