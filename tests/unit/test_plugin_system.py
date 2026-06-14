"""
Unit Tests for Plugin System
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from plugins.base import PluginBase
from plugins.manager import PluginManager


class MockPlugin(PluginBase):
    """Mock plugin for testing"""
    
    def load(self, config):
        self.name = config.get('name', 'mock_plugin')
        self.version = config.get('version', '1.0.0')
        self.status = 'loaded'
        return True
    
    def execute(self, context):
        return {"result": "success", "input": context}
    
    def unload(self):
        self.status = 'unloaded'
        return True


def test_plugin_base_initialization():
    """Test plugin base class initialization"""
    plugin = MockPlugin()
    
    assert plugin.id is not None
    assert plugin.name == "unknown"
    assert plugin.version == "1.0.0"
    assert plugin.status == "initialized"
    assert plugin.execution_count == 0
    assert plugin.error_count == 0


def test_plugin_base_status():
    """Test plugin status reporting"""
    plugin = MockPlugin()
    status = plugin.get_status()
    
    assert "id" in status
    assert "name" in status
    assert "version" in status
    assert "status" in status
    assert "created_at" in status
    assert "execution_count" in status
    assert "error_count" in status


def test_plugin_base_execution_stats():
    """Test plugin execution statistics"""
    plugin = MockPlugin()
    
    # Test successful execution
    plugin.update_execution_stats(success=True)
    assert plugin.execution_count == 1
    assert plugin.error_count == 0
    
    # Test failed execution
    plugin.update_execution_stats(success=False)
    assert plugin.execution_count == 2
    assert plugin.error_count == 1


def test_plugin_manager_initialization():
    """Test plugin manager initialization"""
    manager = PluginManager()
    
    assert manager.plugin_dir == "plugins"
    assert len(manager.plugins) == 0
    assert len(manager.plugin_registry) == 0


def test_plugin_manager_list_plugins():
    """Test listing plugins"""
    manager = PluginManager()
    plugins = manager.list_plugins()
    
    assert isinstance(plugins, list)
    assert len(plugins) == 0


def test_plugin_manager_get_plugin_info():
    """Test getting plugin info"""
    manager = PluginManager()
    info = manager.get_plugin_info("nonexistent")
    
    assert info is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
