"""
Integration Tests for Plugin System
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from plugins.base import PluginBase
from plugins.manager import PluginManager
from security.sandbox import SecuritySandbox
from observability.metrics import MetricsCollector, PluginMetrics


class IntegrationPlugin(PluginBase):
    """Integration test plugin"""
    
    def load(self, config):
        self.name = config.get('name', 'integration_plugin')
        self.version = config.get('version', '1.0.0')
        self.status = 'loaded'
        return True
    
    def execute(self, context):
        # Simulate some work
        return {
            "result": "success",
            "input": context,
            "message": "Plugin executed successfully"
        }
    
    def unload(self):
        self.status = 'unloaded'
        return True


def test_plugin_lifecycle():
    """Test complete plugin lifecycle"""
    manager = PluginManager()
    sandbox = SecuritySandbox()
    metrics_collector = MetricsCollector()
    plugin_metrics = PluginMetrics(metrics_collector)
    
    # Create plugin
    plugin = IntegrationPlugin()
    
    # Load plugin
    config = {"name": "lifecycle_plugin", "version": "1.0.0"}
    assert plugin.load(config) is True
    assert plugin.status == "loaded"
    
    # Validate plugin security
    plugin_meta = {
        "name": "lifecycle_plugin",
        "version": "1.0.0",
        "module": "integration_plugin",
        "permissions": ["read_memory"],
        "security": {
            "network_whitelist": [],
            "file_read_paths": []
        }
    }
    
    assert sandbox.validate_plugin(plugin_meta) is True
    
    # Record metrics
    plugin_metrics.record_plugin_load("lifecycle_plugin", 100.0)
    
    # Execute plugin
    context = {"task": "test_task", "data": "test_data"}
    result = plugin.execute(context)
    
    assert result["result"] == "success"
    assert result["input"] == context
    
    # Update execution stats
    plugin.update_execution_stats(success=True)
    assert plugin.execution_count == 1
    
    # Record execution metrics
    plugin_metrics.record_plugin_execution("lifecycle_plugin", 200.0, True)
    
    # Unload plugin
    assert plugin.unload() is True
    assert plugin.status == "unloaded"
    
    # Verify metrics
    metrics = metrics_collector.get_metrics()
    assert "plugin_load_duration_ms" in metrics['metrics']
    assert "plugin_execution_duration_ms" in metrics['metrics']


def test_security_integration():
    """Test security sandbox integration"""
    sandbox = SecuritySandbox()
    
    # Configure security
    sandbox.restrict_network_access(["192.168.1.0/24", "localhost"])
    sandbox.restrict_file_access(
        read_paths=["/volume1/docker/qwenpaw/"],
        write_paths=["/tmp/output/"]
    )
    
    # Test valid plugin
    valid_meta = {
        "name": "valid_plugin",
        "permissions": ["read_memory"],
        "security": {
            "network_whitelist": ["192.168.1.1"],
            "file_read_paths": ["/volume1/docker/qwenpaw/config"]
        }
    }
    
    assert sandbox.validate_plugin(valid_meta) is True
    
    # Test invalid plugin
    invalid_meta = {
        "name": "invalid_plugin",
        "permissions": ["write_memory"],
        "security": {
            "approved": False
        }
    }
    
    assert sandbox.validate_plugin(invalid_meta) is False
    
    # Verify audit log - sandbox records multiple events during validation
    audit_log = sandbox.get_audit_log()
    assert len(audit_log) >= 2


def test_observability_integration():
    """Test observability stack integration"""
    collector = MetricsCollector()
    plugin_metrics = PluginMetrics(collector)
    
    # Record various metrics
    plugin_metrics.record_plugin_load("test_plugin", 150.0)
    plugin_metrics.record_plugin_execution("test_plugin", 250.0, True)
    plugin_metrics.record_security_validation("test_plugin", 50.0, True)
    plugin_metrics.set_plugin_memory_usage("test_plugin", 128.0)
    
    # Get metrics
    metrics = collector.get_metrics()
    
    # Verify all metrics are present
    assert "plugin_load_duration_ms" in metrics['metrics']
    assert "plugin_execution_duration_ms" in metrics['metrics']
    assert "security_validation_duration_ms" in metrics['metrics']
    assert "plugin_memory_usage_mb" in metrics['metrics']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
