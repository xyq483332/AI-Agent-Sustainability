"""
API Dependencies

Dependency injection for FastAPI endpoints.
"""

from ..plugins.manager import PluginManager
from ..security.sandbox import SecuritySandbox
from ..observability.metrics import MetricsCollector, PluginMetrics


def get_plugin_manager() -> PluginManager:
    """Get plugin manager instance"""
    return PluginManager()


def get_security_sandbox() -> SecuritySandbox:
    """Get security sandbox instance"""
    return SecuritySandbox()


def get_metrics_collector() -> MetricsCollector:
    """Get metrics collector instance"""
    return MetricsCollector()


def get_plugin_metrics(collector: MetricsCollector) -> PluginMetrics:
    """Get plugin metrics instance"""
    return PluginMetrics(collector)
