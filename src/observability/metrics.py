"""
Metrics Collector

Collects and exports metrics for monitoring.
"""

from typing import Dict, Any, List
from datetime import datetime
import json
import threading
import time

class MetricsCollector:
    """Collects and manages metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        self.lock = threading.Lock()
        
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            key = self._make_key(name, labels)
            self.counters[key] = self.counters.get(key, 0) + value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        with self.lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Observe a value in a histogram"""
        with self.lock:
            key = self._make_key(name, labels)
            if key not in self.histograms:
                self.histograms[key] = []
            self.histograms[key].append(value)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics in Prometheus format"""
        with self.lock:
            metrics = []
            
            # Add counters
            for key, value in self.counters.items():
                name, labels = self._parse_key(key)
                metrics.append(f"{name} {value}")
            
            # Add gauges
            for key, value in self.gauges.items():
                name, labels = self._parse_key(key)
                metrics.append(f"{name} {value}")
            
            # Add histograms (simplified)
            for key, values in self.histograms.items():
                name, labels = self._parse_key(key)
                if values:
                    avg = sum(values) / len(values)
                    metrics.append(f"{name}_avg {avg}")
                    metrics.append(f"{name}_count {len(values)}")
            
            return {"metrics": "\n".join(metrics)}
    
    def reset(self):
        """Reset all metrics"""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Make a unique key for a metric"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def _parse_key(self, key: str) -> tuple:
        """Parse a metric key into name and labels"""
        if "{" in key:
            name = key.split("{")[0]
            labels = key.split("{")[1].rstrip("}")
            return name, labels
        return key, None


class PluginMetrics:
    """Plugin-specific metrics collector"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    def record_plugin_load(self, plugin_name: str, duration_ms: float):
        """Record plugin load time"""
        self.collector.observe_histogram(
            "plugin_load_duration_ms",
            duration_ms,
            {"plugin": plugin_name}
        )
    
    def record_plugin_execution(self, plugin_name: str, duration_ms: float, success: bool):
        """Record plugin execution"""
        self.collector.observe_histogram(
            "plugin_execution_duration_ms",
            duration_ms,
            {"plugin": plugin_name, "success": str(success)}
        )
        
        self.collector.increment_counter(
            "plugin_execution_total",
            1,
            {"plugin": plugin_name, "success": str(success)}
        )
    
    def record_security_validation(self, plugin_name: str, duration_ms: float, passed: bool):
        """Record security validation"""
        self.collector.observe_histogram(
            "security_validation_duration_ms",
            duration_ms,
            {"plugin": plugin_name, "passed": str(passed)}
        )
        
        self.collector.increment_counter(
            "security_validation_total",
            1,
            {"plugin": plugin_name, "passed": str(passed)}
        )
    
    def set_plugin_memory_usage(self, plugin_name: str, memory_mb: float):
        """Set plugin memory usage"""
        self.collector.set_gauge(
            "plugin_memory_usage_mb",
            memory_mb,
            {"plugin": plugin_name}
        )
