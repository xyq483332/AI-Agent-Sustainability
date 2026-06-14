"""
Unit Tests for Observability Stack
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from observability.metrics import MetricsCollector, PluginMetrics


def test_metrics_collector_initialization():
    """Test metrics collector initialization"""
    collector = MetricsCollector()
    
    assert len(collector.metrics) == 0
    assert len(collector.counters) == 0
    assert len(collector.gauges) == 0
    assert len(collector.histograms) == 0


def test_metrics_collector_increment_counter():
    """Test counter increment"""
    collector = MetricsCollector()
    
    collector.increment_counter("test_counter", 1)
    collector.increment_counter("test_counter", 2)
    
    metrics = collector.get_metrics()
    assert "test_counter 3" in metrics['metrics']


def test_metrics_collector_set_gauge():
    """Test gauge setting"""
    collector = MetricsCollector()
    
    collector.set_gauge("test_gauge", 42.0)
    collector.set_gauge("test_gauge", 50.0)
    
    metrics = collector.get_metrics()
    assert "test_gauge 50.0" in metrics['metrics']


def test_metrics_collector_observe_histogram():
    """Test histogram observation"""
    collector = MetricsCollector()
    
    collector.observe_histogram("test_histogram", 10.0)
    collector.observe_histogram("test_histogram", 20.0)
    collector.observe_histogram("test_histogram", 30.0)
    
    metrics = collector.get_metrics()
    assert "test_histogram_avg 20.0" in metrics['metrics']
    assert "test_histogram_count 3" in metrics['metrics']


def test_metrics_collector_reset():
    """Test metrics reset"""
    collector = MetricsCollector()
    
    collector.increment_counter("test_counter", 1)
    collector.set_gauge("test_gauge", 42.0)
    collector.observe_histogram("test_histogram", 10.0)
    
    collector.reset()
    
    metrics = collector.get_metrics()
    assert metrics['metrics'] == ""


def test_plugin_metrics():
    """Test plugin-specific metrics"""
    collector = MetricsCollector()
    plugin_metrics = PluginMetrics(collector)
    
    # Record plugin load
    plugin_metrics.record_plugin_load("test_plugin", 150.0)
    
    # Record plugin execution
    plugin_metrics.record_plugin_execution("test_plugin", 250.0, True)
    
    # Record security validation
    plugin_metrics.record_security_validation("test_plugin", 50.0, True)
    
    # Set memory usage
    plugin_metrics.set_plugin_memory_usage("test_plugin", 128.0)
    
    metrics = collector.get_metrics()
    assert "plugin_load_duration_ms" in metrics['metrics']
    assert "plugin_execution_duration_ms" in metrics['metrics']
    assert "security_validation_duration_ms" in metrics['metrics']
    assert "plugin_memory_usage_mb" in metrics['metrics']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
