"""
Plugin Manager

Manages plugin lifecycle, loading, and execution.
"""

import importlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugin lifecycle and execution"""

    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, Any] = {}
        self.plugin_registry: Dict[str, Dict] = {}

    def load_plugin(self, plugin_path: str) -> bool:
        """Load a plugin from the specified path"""
        try:
            # Read plugin metadata
            with open(plugin_path, "r") as f:
                meta = json.load(f)

            # Validate metadata
            if not self._validate_metadata(meta):
                raise ValueError("Invalid plugin metadata")

            # Load plugin module
            plugin_module = importlib.import_module(meta["module"])
            plugin_class = getattr(plugin_module, "Plugin")

            # Create plugin instance
            plugin = plugin_class()
            plugin.name = meta["name"]
            plugin.version = meta["version"]

            # Register plugin
            self.plugins[meta["name"]] = plugin
            self.plugin_registry[meta["name"]] = meta

            logger.info(f"Loaded plugin: {meta['name']} v{meta['version']}")
            return True

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_path}: {str(e)}")
            return False

    def execute_plugin(
        self, plugin_name: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a loaded plugin"""
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin {plugin_name} not found")

        plugin = self.plugins[plugin_name]

        try:
            # Update status
            plugin.status = "executing"

            # Execute plugin
            result = plugin.execute(context)

            # Update stats
            plugin.update_execution_stats(success=True)
            plugin.status = "completed"

            return {
                "success": True,
                "result": result,
                "plugin": plugin_name,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            plugin.update_execution_stats(success=False)
            plugin.status = "error"

            logger.error(f"Plugin {plugin_name} execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "plugin": plugin_name,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        if plugin_name not in self.plugins:
            return False

        try:
            plugin = self.plugins[plugin_name]
            plugin.unload()
            del self.plugins[plugin_name]
            del self.plugin_registry[plugin_name]

            logger.info(f"Unloaded plugin: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {str(e)}")
            return False

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins"""
        return [plugin.get_status() for plugin in self.plugins.values()]

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a plugin"""
        if plugin_name not in self.plugins:
            return None

        plugin = self.plugins[plugin_name]
        meta = self.plugin_registry.get(plugin_name, {})

        return {"status": plugin.get_status(), "metadata": meta}

    def _validate_metadata(self, meta: Dict) -> bool:
        """Validate plugin metadata"""
        required_fields = ["name", "version", "module", "lifecycles"]
        return all(field in meta for field in required_fields)
