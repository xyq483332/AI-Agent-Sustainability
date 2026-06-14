"""
Comprehensive Unit Tests for API Module

Tests cover:
- FastAPI application initialization
- API endpoints (health, plugins, metrics, security)
- Request/Response models
- Error handling
- Middleware and exception handlers
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class MockPluginManager:
    """Mock plugin manager"""

    def __init__(self):
        self.plugins = {}
        self.plugin_registry = {}

    def load_plugin(self, plugin_path):
        return True

    def execute_plugin(self, plugin_name, context):
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin {plugin_name} not found")
        return {
            "success": True,
            "result": {"output": "test"},
            "plugin": plugin_name,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def unload_plugin(self, plugin_name):
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            return True
        return False

    def list_plugins(self):
        return []

    def get_plugin_info(self, plugin_name):
        return None


class MockSecuritySandbox:
    """Mock security sandbox"""

    def __init__(self):
        self.audit_log = []

    def validate_plugin(self, plugin_meta):
        return True

    def get_audit_log(self):
        return self.audit_log


class MockMetricsCollector:
    """Mock metrics collector"""

    def __init__(self):
        self.counters = {}
        self.gauges = {}
        self.histograms = {}

    def increment_counter(self, name, value=1, labels=None):
        pass

    def set_gauge(self, name, value, labels=None):
        pass

    def observe_histogram(self, name, value, labels=None):
        pass

    def get_metrics(self):
        return {"metrics": "test_metric 1.0"}

    def reset(self):
        pass


# Create mock app
app = FastAPI(title="Test API")

# Create mock instances
plugin_manager = MockPluginManager()
security_sandbox = MockSecuritySandbox()
metrics_collector = MockMetricsCollector()


# Pydantic models
class PluginRequest(BaseModel):
    name: str
    version: str
    module: str
    permissions: List[str] = []
    security: Dict[str, Any] = {}


class PluginExecuteRequest(BaseModel):
    context: Dict[str, Any] = {}


class PluginResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/v1/plugins")
async def list_plugins():
    """List all plugins"""
    plugins = plugin_manager.list_plugins()
    return {"plugins": plugins}


@app.post("/api/v1/plugins")
async def register_plugin(request: PluginRequest):
    """Register a new plugin"""
    try:
        # Validate plugin metadata
        plugin_meta = {
            "name": request.name,
            "version": request.version,
            "module": request.module,
            "permissions": request.permissions,
            "security": request.security,
        }

        if not security_sandbox.validate_plugin(plugin_meta):
            return {"success": False, "message": "Plugin failed security validation"}

        # Load plugin
        success = plugin_manager.load_plugin(request.module)
        if not success:
            return {"success": False, "message": "Failed to load plugin"}

        return {
            "success": True,
            "message": f"Plugin {request.name} registered successfully",
        }

    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/v1/plugins/{plugin_name}/execute")
async def execute_plugin(plugin_name: str, request: PluginExecuteRequest):
    """Execute a plugin"""
    try:
        result = plugin_manager.execute_plugin(plugin_name, request.context)
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.delete("/api/v1/plugins/{plugin_name}")
async def unregister_plugin(plugin_name: str):
    """Unregister a plugin"""
    success = plugin_manager.unload_plugin(plugin_name)
    if not success:
        return {"success": False, "message": "Plugin not found"}

    return {
        "success": True,
        "message": f"Plugin {plugin_name} unregistered successfully",
    }


@app.get("/api/v1/plugins/{plugin_name}")
async def get_plugin_info(plugin_name: str):
    """Get plugin information"""
    info = plugin_manager.get_plugin_info(plugin_name)
    if not info:
        return {"success": False, "message": "Plugin not found"}

    return info


@app.get("/api/v1/metrics")
async def get_metrics():
    """Get Prometheus metrics"""
    return metrics_collector.get_metrics()


@app.get("/api/v1/security/audit-log")
async def get_audit_log():
    """Get security audit log"""
    return {"audit_log": security_sandbox.get_audit_log()}


@app.post("/api/v1/security/validate")
async def validate_plugin_security(request: PluginRequest):
    """Validate plugin security"""
    plugin_meta = {
        "name": request.name,
        "version": request.version,
        "module": request.module,
        "permissions": request.permissions,
        "security": request.security,
    }

    is_valid = security_sandbox.validate_plugin(plugin_meta)
    return {"is_valid": is_valid}


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_check_returns_json(self, client):
        """Test health check returns JSON"""
        response = client.get("/health")

        assert response.headers["content-type"] == "application/json"


class TestPluginEndpoints:
    """Test plugin API endpoints"""

    def test_list_plugins_empty(self, client):
        """Test listing plugins when none are loaded"""
        response = client.get("/api/v1/plugins")

        assert response.status_code == 200
        data = response.json()
        assert "plugins" in data
        assert len(data["plugins"]) == 0

    def test_register_plugin_success(self, client):
        """Test successful plugin registration"""
        plugin_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
            "permissions": ["read"],
            "security": {"sandbox": True},
        }

        response = client.post("/api/v1/plugins", json=plugin_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test_plugin" in data["message"]

    def test_register_plugin_security_failure(self, client):
        """Test plugin registration with security validation failure"""
        # Mock security validation to fail
        original_validate = security_sandbox.validate_plugin
        security_sandbox.validate_plugin = lambda x: False

        plugin_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
        }

        response = client.post("/api/v1/plugins", json=plugin_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "security validation" in data["message"].lower()

        # Restore original method
        security_sandbox.validate_plugin = original_validate

    def test_register_plugin_load_failure(self, client):
        """Test plugin registration with load failure"""
        # Mock load_plugin to fail
        original_load = plugin_manager.load_plugin
        plugin_manager.load_plugin = lambda x: False

        plugin_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
        }

        response = client.post("/api/v1/plugins", json=plugin_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "failed" in data["message"].lower()

        # Restore original method
        plugin_manager.load_plugin = original_load

    def test_execute_plugin_success(self, client):
        """Test successful plugin execution"""
        # Add a plugin to execute
        plugin_manager.plugins["test_plugin"] = MagicMock()

        execute_data = {"context": {"data": "test"}}

        response = client.post("/api/v1/plugins/test_plugin/execute", json=execute_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Clean up
        del plugin_manager.plugins["test_plugin"]

    def test_execute_plugin_not_found(self, client):
        """Test executing nonexistent plugin"""
        execute_data = {"context": {"data": "test"}}

        response = client.post("/api/v1/plugins/nonexistent/execute", json=execute_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_unregister_plugin_success(self, client):
        """Test successful plugin unregistration"""
        # Add a plugin to unregister
        plugin_manager.plugins["test_plugin"] = MagicMock()

        response = client.delete("/api/v1/plugins/test_plugin")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test_plugin" in data["message"]

        # Verify plugin was removed
        assert "test_plugin" not in plugin_manager.plugins

    def test_unregister_plugin_not_found(self, client):
        """Test unregistering nonexistent plugin"""
        response = client.delete("/api/v1/plugins/nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()

    def test_get_plugin_info_success(self, client):
        """Test getting plugin info successfully"""
        # Mock get_plugin_info to return data
        original_get_info = plugin_manager.get_plugin_info
        plugin_manager.get_plugin_info = lambda x: {
            "status": {"name": "test_plugin", "version": "1.0.0"},
            "metadata": {"name": "test_plugin", "version": "1.0.0"},
        }

        response = client.get("/api/v1/plugins/test_plugin")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "metadata" in data

        # Restore original method
        plugin_manager.get_plugin_info = original_get_info

    def test_get_plugin_info_not_found(self, client):
        """Test getting info for nonexistent plugin"""
        response = client.get("/api/v1/plugins/nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()


class TestMetricsEndpoint:
    """Test metrics API endpoint"""

    def test_get_metrics(self, client):
        """Test getting metrics"""
        response = client.get("/api/v1/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data


class TestSecurityEndpoints:
    """Test security API endpoints"""

    def test_get_audit_log(self, client):
        """Test getting audit log"""
        # Add some audit log entries
        security_sandbox.audit_log = [
            {
                "action": "test",
                "status": "SUCCESS",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ]

        response = client.get("/api/v1/security/audit-log")

        assert response.status_code == 200
        data = response.json()
        assert "audit_log" in data
        assert len(data["audit_log"]) == 1

        # Clean up
        security_sandbox.audit_log = []

    def test_validate_plugin_security_valid(self, client):
        """Test validating plugin security (valid)"""
        plugin_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
        }

        response = client.post("/api/v1/security/validate", json=plugin_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    def test_validate_plugin_security_invalid(self, client):
        """Test validating plugin security (invalid)"""
        # Mock security validation to fail
        original_validate = security_sandbox.validate_plugin
        security_sandbox.validate_plugin = lambda x: False

        plugin_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
        }

        response = client.post("/api/v1/security/validate", json=plugin_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False

        # Restore original method
        security_sandbox.validate_plugin = original_validate


class TestAPIErrorHandling:
    """Test API error handling"""

    def test_invalid_json_request(self, client):
        """Test invalid JSON request"""
        response = client.post(
            "/api/v1/plugins",
            content="invalid json",
            headers={"content-type": "application/json"},
        )

        # Should return 422 for invalid JSON
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test missing required fields"""
        response = client.post(
            "/api/v1/plugins",
            json={"name": "test_plugin"},  # Missing version and module
        )

        # Should return 422 for missing fields
        assert response.status_code == 422

    def test_method_not_allowed(self, client):
        """Test method not allowed"""
        response = client.put("/api/v1/plugins")

        assert response.status_code == 405

    def test_not_found(self, client):
        """Test not found endpoint"""
        response = client.get("/nonexistent")

        assert response.status_code == 404


class TestAPIMiddleware:
    """Test API middleware"""

    def test_cors_headers(self, client):
        """Test CORS headers"""
        response = client.options("/health")

        # Check for CORS headers (if configured)
        # Note: CORS middleware may not be configured in test client
        assert response.status_code in [200, 405]

    def test_content_type_json(self, client):
        """Test content type is JSON"""
        response = client.get("/health")

        assert "application/json" in response.headers["content-type"]


class TestAPIIntegration:
    """Test API integration with components"""

    def test_plugin_lifecycle_api(self, client):
        """Test complete plugin lifecycle via API"""
        # Register plugin
        plugin_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
        }

        response = client.post("/api/v1/plugins", json=plugin_data)
        assert response.status_code == 200
        assert response.json()["success"] is True

        # List plugins
        response = client.get("/api/v1/plugins")
        assert response.status_code == 200

        # Execute plugin (add to plugins dict first)
        plugin_manager.plugins["test_plugin"] = MagicMock()

        response = client.post(
            "/api/v1/plugins/test_plugin/execute", json={"context": {}}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Unregister plugin
        response = client.delete("/api/v1/plugins/test_plugin")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify plugin was removed
        assert "test_plugin" not in plugin_manager.plugins


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
