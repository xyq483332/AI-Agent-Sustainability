"""
Unit Tests for Observability Stack (OpenTelemetry-based)

Tests use an in-memory OTel MetricReader so no running Collector is needed.
"""

import os
import sys

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from observability.metrics import MetricsCollector, PluginMetrics

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_collector():
    """Create a MetricsCollector backed by an in-memory OTel reader."""
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    meter = provider.get_meter("test-meter", "0.0.0")
    return MetricsCollector(meter=meter), reader, provider


# ---------------------------------------------------------------------------
# MetricsCollector tests
# ---------------------------------------------------------------------------


def test_metrics_collector_initialization():
    """Test metrics collector initialization"""
    collector, reader, provider = _make_collector()

    assert len(collector.counters) == 0
    assert len(collector.gauges) == 0
    assert len(collector.histograms) == 0
    provider.shutdown()


def test_metrics_collector_increment_counter():
    """Test counter increment"""
    collector, reader, provider = _make_collector()

    collector.increment_counter("test_counter", 1)
    collector.increment_counter("test_counter", 2)

    # Local mirror
    assert collector.counters["test_counter"] == 3

    # OTel metric exported
    data = reader.get_metrics_data()
    names = [
        m.name
        for rm in data.resource_metrics
        for sm in rm.scope_metrics
        for m in sm.metrics
    ]
    assert "test_counter" in names

    provider.shutdown()


def test_metrics_collector_set_gauge():
    """Test gauge setting"""
    collector, reader, provider = _make_collector()

    collector.set_gauge("test_gauge", 42.0)
    collector.set_gauge("test_gauge", 50.0)

    assert collector.gauges["test_gauge"] == 50.0

    data = reader.get_metrics_data()
    names = [
        m.name
        for rm in data.resource_metrics
        for sm in rm.scope_metrics
        for m in sm.metrics
    ]
    assert "test_gauge" in names

    provider.shutdown()


def test_metrics_collector_observe_histogram():
    """Test histogram observation"""
    collector, reader, provider = _make_collector()

    collector.observe_histogram("test_histogram", 10.0)
    collector.observe_histogram("test_histogram", 20.0)
    collector.observe_histogram("test_histogram", 30.0)

    # Local mirror
    assert len(collector.histograms["test_histogram"]) == 3

    # OTel metric exported
    data = reader.get_metrics_data()
    names = [
        m.name
        for rm in data.resource_metrics
        for sm in rm.scope_metrics
        for m in sm.metrics
    ]
    assert "test_histogram" in names

    provider.shutdown()


def test_metrics_collector_reset():
    """Test metrics reset"""
    collector, reader, provider = _make_collector()

    collector.increment_counter("test_counter", 1)
    collector.set_gauge("test_gauge", 42.0)
    collector.observe_histogram("test_histogram", 10.0)

    collector.reset()

    metrics = collector.get_metrics()
    assert metrics["metrics"] == ""

    provider.shutdown()


def test_get_metrics_format():
    """Test get_metrics returns Prometheus-like text"""
    collector, reader, provider = _make_collector()

    collector.increment_counter("req_total", 5)
    collector.set_gauge("temp_c", 36.5)
    collector.observe_histogram("latency_ms", 100.0)
    collector.observe_histogram("latency_ms", 200.0)

    result = collector.get_metrics()
    text = result["metrics"]

    assert "req_total 5" in text
    assert "temp_c 36.5" in text
    assert "latency_ms_avg 150.0" in text
    assert "latency_ms_count 2" in text

    provider.shutdown()


def test_labels():
    """Test that labels are correctly attached"""
    collector, reader, provider = _make_collector()

    collector.increment_counter("hits", 1, labels={"method": "GET"})
    collector.increment_counter("hits", 1, labels={"method": "POST"})

    assert collector.counters["hits{method=GET}"] == 1
    assert collector.counters["hits{method=POST}"] == 1

    data = reader.get_metrics_data()
    found_attrs = set()
    for rm in data.resource_metrics:
        for sm in rm.scope_metrics:
            for m in sm.metrics:
                for dp in m.data.data_points:
                    found_attrs.update(dp.attributes.keys())
    assert "method" in found_attrs

    provider.shutdown()


# ---------------------------------------------------------------------------
# PluginMetrics tests
# ---------------------------------------------------------------------------


def test_plugin_metrics():
    """Test plugin-specific metrics via OTel"""
    collector, reader, provider = _make_collector()
    plugin_metrics = PluginMetrics(collector)

    plugin_metrics.record_plugin_load("test_plugin", 150.0)
    plugin_metrics.record_plugin_execution("test_plugin", 250.0, True)
    plugin_metrics.record_security_validation("test_plugin", 50.0, True)
    plugin_metrics.set_plugin_memory_usage("test_plugin", 128.0)

    # Verify OTel metrics were exported
    data = reader.get_metrics_data()
    names = set()
    for rm in data.resource_metrics:
        for sm in rm.scope_metrics:
            for m in sm.metrics:
                names.add(m.name)

    assert "plugin_load_duration_ms" in names
    assert "plugin_execution_duration_ms" in names
    assert "security_validation_duration_ms" in names
    assert "plugin_memory_usage_mb" in names

    provider.shutdown()


def test_plugin_execution_counter():
    """Test that plugin execution increments a counter"""
    collector, reader, provider = _make_collector()
    pm = PluginMetrics(collector)

    pm.record_plugin_execution("my_plugin", 100.0, True)
    pm.record_plugin_execution("my_plugin", 200.0, True)
    pm.record_plugin_execution("my_plugin", 150.0, False)

    data = reader.get_metrics_data()
    for rm in data.resource_metrics:
        for sm in rm.scope_metrics:
            for m in sm.metrics:
                if m.name == "plugin_execution_total":
                    # Should have data points for success=true and success=false
                    attrs = [dp.attributes for dp in m.data.data_points]
                    assert any(a.get("success") == "true" for a in attrs)
                    assert any(a.get("success") == "false" for a in attrs)

    provider.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
