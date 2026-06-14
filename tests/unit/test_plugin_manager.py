"""
Comprehensive Unit Tests for Plugin Manager

Tests cover:
- Plugin loading/unloading lifecycle
- Plugin execution
- Plugin metadata validation
- Plugin listing and info retrieval
- Error handling and edge cases
"""

import pytest
import sys
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

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


class FailingMockPlugin(PluginBase):
    """Mock plugin that fails on execute"""
    
    def load(self, config):
        self.name = config.get('name', 'failing_plugin')
        self.version = config.get('version', '1.0.0')
        self.status = 'loaded'
        return True
    
    def execute(self, context):
        raise RuntimeError("Plugin execution failed")
    
    def unload(self):
        self.status = 'unloaded'
        return True


class TestPluginManagerInitialization:
    """Test PluginManager initialization"""
    
    def test_default_initialization(self):
        """Test default initialization"""
        manager = PluginManager()
        
        assert manager.plugin_dir == "plugins"
        assert len(manager.plugins) == 0
        assert len(manager.plugin_registry) == 0
    
    def test_custom_initialization(self):
        """Test custom initialization with plugin_dir"""
        manager = PluginManager(plugin_dir="/custom/path")
        
        assert manager.plugin_dir == "/custom/path"
        assert len(manager.plugins) == 0
        assert len(manager.plugin_registry) == 0


class TestPluginMetadataValidation:
    """Test plugin metadata validation"""
    
    def test_valid_metadata(self):
        """Test validation with valid metadata"""
        manager = PluginManager()
        
        valid_meta = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
            "lifecycles": ["load", "execute", "unload"]
        }
        
        assert manager._validate_metadata(valid_meta) is True
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields"""
        manager = PluginManager()
        
        # Missing 'name'
        meta_missing_name = {
            "version": "1.0.0",
            "module": "test_module",
            "lifecycles": ["load", "execute", "unload"]
        }
        assert manager._validate_metadata(meta_missing_name) is False
        
        # Missing 'version'
        meta_missing_version = {
            "name": "test_plugin",
            "module": "test_module",
            "lifecycles": ["load", "execute", "unload"]
        }
        assert manager._validate_metadata(meta_missing_version) is False
        
        # Missing 'module'
        meta_missing_module = {
            "name": "test_plugin",
            "version": "1.0.0",
            "lifecycles": ["load", "execute", "unload"]
        }
        assert manager._validate_metadata(meta_missing_module) is False
        
        # Missing 'lifecycles'
        meta_missing_lifecycles = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module"
        }
        assert manager._validate_metadata(meta_missing_lifecycles) is False
    
    def test_empty_metadata(self):
        """Test validation with empty metadata"""
        manager = PluginManager()
        
        assert manager._validate_metadata({}) is False
    
    def test_extra_fields_ignored(self):
        """Test validation with extra fields (should be ignored)"""
        manager = PluginManager()
        
        meta_with_extras = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
            "lifecycles": ["load", "execute", "unload"],
            "extra_field": "extra_value",
            "another_extra": 123
        }
        
        assert manager._validate_metadata(meta_with_extras) is True


class TestPluginLoading:
    """Test plugin loading"""
    
    def test_load_plugin_success(self):
        """Test successful plugin loading"""
        manager = PluginManager()
        
        # Create a temporary plugin directory
        temp_dir = tempfile.mkdtemp()
        plugin_dir = os.path.join(temp_dir, "test_plugin")
        os.makedirs(plugin_dir)
        
        # Create plugin metadata file
        meta = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_plugin.plugin",
            "lifecycles": ["load", "execute", "unload"]
        }
        
        meta_file = os.path.join(plugin_dir, "plugin.json")
        with open(meta_file, 'w') as f:
            json.dump(meta, f)
        
        # Mock the importlib.import_module
        with patch('plugins.manager.importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_module.Plugin = MockPlugin
            mock_import.return_value = mock_module
            
            # Load plugin
            success = manager.load_plugin(meta_file)
            
            assert success is True
            assert "test_plugin" in manager.plugins
            assert "test_plugin" in manager.plugin_registry
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_load_plugin_invalid_metadata(self):
        """Test loading plugin with invalid metadata"""
        manager = PluginManager()
        
        # Create a temporary plugin directory
        temp_dir = tempfile.mkdtemp()
        plugin_dir = os.path.join(temp_dir, "test_plugin")
        os.makedirs(plugin_dir)
        
        # Create invalid plugin metadata file (missing required fields)
        meta = {
            "name": "test_plugin"
            # Missing version, module, lifecycles
        }
        
        meta_file = os.path.join(plugin_dir, "plugin.json")
        with open(meta_file, 'w') as f:
            json.dump(meta, f)
        
        # Load plugin (should fail)
        success = manager.load_plugin(meta_file)
        
        assert success is False
        assert "test_plugin" not in manager.plugins
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_load_plugin_nonexistent_file(self):
        """Test loading plugin from nonexistent file"""
        manager = PluginManager()
        
        # Load plugin from nonexistent file
        success = manager.load_plugin("/nonexistent/path/plugin.json")
        
        assert success is False
        assert len(manager.plugins) == 0
    
    def test_load_plugin_import_error(self):
        """Test loading plugin with import error"""
        manager = PluginManager()
        
        # Create a temporary plugin directory
        temp_dir = tempfile.mkdtemp()
        plugin_dir = os.path.join(temp_dir, "test_plugin")
        os.makedirs(plugin_dir)
        
        # Create plugin metadata file
        meta = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "nonexistent_module",
            "lifecycles": ["load", "execute", "unload"]
        }
        
        meta_file = os.path.join(plugin_dir, "plugin.json")
        with open(meta_file, 'w') as f:
            json.dump(meta, f)
        
        # Mock the importlib.import_module to raise ImportError
        with patch('plugins.manager.importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            
            # Load plugin (should fail)
            success = manager.load_plugin(meta_file)
            
            assert success is False
            assert len(manager.plugins) == 0
        
        # Cleanup
        shutil.rmtree(temp_dir)


class TestPluginExecution:
    """Test plugin execution"""
    
    def test_execute_plugin_success(self):
        """Test successful plugin execution"""
        manager = PluginManager()
        
        # Add a mock plugin directly
        mock_plugin = MockPlugin()
        mock_plugin.name = "test_plugin"
        mock_plugin.version = "1.0.0"
        manager.plugins["test_plugin"] = mock_plugin
        manager.plugin_registry["test_plugin"] = {
            "name": "test_plugin",
            "version": "1.0.0"
        }
        
        # Execute plugin
        context = {"data": "test_data"}
        result = manager.execute_plugin("test_plugin", context)
        
        assert result["success"] is True
        assert result["plugin"] == "test_plugin"
        assert result["result"]["result"] == "success"
        assert result["result"]["input"] == context
        assert "timestamp" in result
    
    def test_execute_plugin_not_found(self):
        """Test executing nonexistent plugin"""
        manager = PluginManager()
        
        # Execute nonexistent plugin (should raise ValueError)
        with pytest.raises(ValueError) as exc_info:
            manager.execute_plugin("nonexistent_plugin", {})
        
        assert "not found" in str(exc_info.value)
    
    def test_execute_plugin_failure(self):
        """Test plugin execution failure"""
        manager = PluginManager()
        
        # Add a failing mock plugin
        mock_plugin = FailingMockPlugin()
        mock_plugin.name = "failing_plugin"
        mock_plugin.version = "1.0.0"
        manager.plugins["failing_plugin"] = mock_plugin
        manager.plugin_registry["failing_plugin"] = {
            "name": "failing_plugin",
            "version": "1.0.0"
        }
        
        # Execute plugin (should fail)
        result = manager.execute_plugin("failing_plugin", {})
        
        assert result["success"] is False
        assert result["plugin"] == "failing_plugin"
        assert "error" in result
        assert "timestamp" in result
    
    def test_execute_plugin_updates_stats(self):
        """Test that plugin execution updates statistics"""
        manager = PluginManager()
        
        # Add a mock plugin
        mock_plugin = MockPlugin()
        mock_plugin.name = "test_plugin"
        mock_plugin.version = "1.0.0"
        manager.plugins["test_plugin"] = mock_plugin
        manager.plugin_registry["test_plugin"] = {
            "name": "test_plugin",
            "version": "1.0.0"
        }
        
        # Execute plugin multiple times
        for i in range(3):
            manager.execute_plugin("test_plugin", {"iteration": i})
        
        # Check stats
        assert mock_plugin.execution_count == 3
        assert mock_plugin.error_count == 0
    
    def test_execute_plugin_updates_status(self):
        """Test that plugin execution updates status"""
        manager = PluginManager()
        
        # Add a mock plugin
        mock_plugin = MockPlugin()
        mock_plugin.name = "test_plugin"
        mock_plugin.version = "1.0.0"
        manager.plugins["test_plugin"] = mock_plugin
        manager.plugin_registry["test_plugin"] = {
            "name": "test_plugin",
            "version": "1.0.0"
        }
        
        # Execute plugin
        manager.execute_plugin("test_plugin", {})
        
        # Check status
        assert mock_plugin.status == "completed"


class TestPluginUnloading:
    """Test plugin unloading"""
    
    def test_unload_plugin_success(self):
        """Test successful plugin unloading"""
        manager = PluginManager()
        
        # Add a mock plugin
        mock_plugin = MockPlugin()
        mock_plugin.name = "test_plugin"
        mock_plugin.version = "1.0.0"
        manager.plugins["test_plugin"] = mock_plugin
        manager.plugin_registry["test_plugin"] = {
            "name": "test_plugin",
            "version": "1.0.0"
        }
        
        # Unload plugin
        success = manager.unload_plugin("test_plugin")
        
        assert success is True
        assert "test_plugin" not in manager.plugins
        assert "test_plugin" not in manager.plugin_registry
    
    def test_unload_plugin_not_found(self):
        """Test unloading nonexistent plugin"""
        manager = PluginManager()
        
        # Unload nonexistent plugin
        success = manager.unload_plugin("nonexistent_plugin")
        
        assert success is False
    
    def test_unload_plugin_error(self):
        """Test plugin unloading with error"""
        manager = PluginManager()
        
        # Add a mock plugin
        mock_plugin = MockPlugin()
        mock_plugin.name = "test_plugin"
        mock_plugin.version = "1.0.0"
        manager.plugins["test_plugin"] = mock_plugin
        manager.plugin_registry["test_plugin"] = {
            "name": "test_plugin",
            "version": "1.0.0"
        }
        
        # Mock the unload method to raise an exception
        with patch.object(mock_plugin, 'unload') as mock_unload:
            mock_unload.side_effect = RuntimeError("Unload failed")
            
            # Unload plugin (should fail)
            success = manager.unload_plugin("test_plugin")
            
            assert success is False
            # Plugin should still be in the manager
            assert "test_plugin" in manager.plugins
            assert "test_plugin" in manager.plugin_registry


class TestPluginListing:
    """Test plugin listing"""
    
    def test_list_plugins_empty(self):
        """Test listing plugins when none are loaded"""
        manager = PluginManager()
        
        plugins = manager.list_plugins()
        
        assert isinstance(plugins, list)
        assert len(plugins) == 0
    
    def test_list_plugins_with_loaded_plugins(self):
        """Test listing plugins with loaded plugins"""
        manager = PluginManager()
        
        # Add multiple mock plugins
        for i in range(3):
            mock_plugin = MockPlugin()
            mock_plugin.name = f"plugin_{i}"
            mock_plugin.version = f"1.0.{i}"
            manager.plugins[f"plugin_{i}"] = mock_plugin
            manager.plugin_registry[f"plugin_{i}"] = {
                "name": f"plugin_{i}",
                "version": f"1.0.{i}"
            }
        
        # List plugins
        plugins = manager.list_plugins()
        
        assert isinstance(plugins, list)
        assert len(plugins) == 3
        
        # Check that all plugins are in the list
        plugin_names = [p["name"] for p in plugins]
        assert "plugin_0" in plugin_names
        assert "plugin_1" in plugin_names
        assert "plugin_2" in plugin_names


class TestPluginInfoRetrieval:
    """Test plugin info retrieval"""
    
    def test_get_plugin_info_not_found(self):
        """Test getting info for nonexistent plugin"""
        manager = PluginManager()
        
        info = manager.get_plugin_info("nonexistent_plugin")
        
        assert info is None
    
    def test_get_plugin_info_found(self):
        """Test getting info for existing plugin"""
        manager = PluginManager()
        
        # Add a mock plugin
        mock_plugin = MockPlugin()
        mock_plugin.name = "test_plugin"
        mock_plugin.version = "1.0.0"
        manager.plugins["test_plugin"] = mock_plugin
        manager.plugin_registry["test_plugin"] = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
            "lifecycles": ["load", "execute", "unload"]
        }
        
        # Get plugin info
        info = manager.get_plugin_info("test_plugin")
        
        assert info is not None
        assert "status" in info
        assert "metadata" in info
        assert info["metadata"]["name"] == "test_plugin"
        assert info["metadata"]["version"] == "1.0.0"


class TestPluginManagerEdgeCases:
    """Test edge cases and error handling"""
    
    def test_concurrent_plugin_operations(self):
        """Test concurrent plugin operations"""
        manager = PluginManager()
        
        # Add multiple plugins
        for i in range(5):
            mock_plugin = MockPlugin()
            mock_plugin.name = f"plugin_{i}"
            mock_plugin.version = f"1.0.{i}"
            manager.plugins[f"plugin_{i}"] = mock_plugin
            manager.plugin_registry[f"plugin_{i}"] = {
                "name": f"plugin_{i}",
                "version": f"1.0.{i}"
            }
        
        # Execute all plugins
        for i in range(5):
            result = manager.execute_plugin(f"plugin_{i}", {"iteration": i})
            assert result["success"] is True
        
        # Unload all plugins
        for i in range(5):
            success = manager.unload_plugin(f"plugin_{i}")
            assert success is True
        
        # Verify all plugins are unloaded
        assert len(manager.plugins) == 0
        assert len(manager.plugin_registry) == 0
    
    def test_plugin_name_case_sensitivity(self):
        """Test plugin name case sensitivity"""
        manager = PluginManager()
        
        # Add a plugin with lowercase name
        mock_plugin = MockPlugin()
        mock_plugin.name = "test_plugin"
        mock_plugin.version = "1.0.0"
        manager.plugins["test_plugin"] = mock_plugin
        manager.plugin_registry["test_plugin"] = {
            "name": "test_plugin",
            "version": "1.0.0"
        }
        
        # Try to get info with different case
        info = manager.get_plugin_info("Test_Plugin")
        
        # Should return None (case sensitive)
        assert info is None
    
    def test_plugin_metadata_types(self):
        """Test plugin metadata with various types"""
        manager = PluginManager()
        
        # Metadata with various types
        meta = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
            "lifecycles": ["load", "execute", "unload"],
            "permissions": ["read", "write"],
            "security": {
                "sandbox": True,
                "max_memory": 256
            }
        }
        
        # Validate metadata
        assert manager._validate_metadata(meta) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
