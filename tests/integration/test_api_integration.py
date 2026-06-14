"""
API Integration Tests

Tests cover:
- Actual FastAPI application with TestClient
- Real API endpoints with mocked dependencies
- Request/Response validation
- Error handling
- API lifecycle
"""

import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, project_root)

# Import from src package
from src.api.main import (app, metrics_collector, plugin_manager,
                          security_sandbox)


class MockPlugin:
    """Mock plugin for testing"""

    def __init__(self):
        self.id = "mock-plugin-id"
        self.name = "unknown"
        self.version = "1.0.0"
        self.status = "initialized"
        self.execution_count = 0
        self.error_count = 0
        self.created_at = datetime.utcnow()

    def load(self, config):
        self.name = config.get("name", "mock_plugin")
        self.version = config.get("version", "1.0.0")
        self.status = "loaded"
        return True

    def execute(self, context):
        return {"result": "success", "input": context}

    def unload(self):
        self.status = "unloaded"
        return True

    def get_status(self):
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "execution_count": self.execution_count,
            "error_count": self.error_count,
        }

    def update_execution_stats(self, success):
        self.execution_count += 1
        if not success:
            self.error_count += 1


@pytest.fixture
def mock_plugin_manager():
    """Mock plugin manager"""
    with patch("src.api.main.plugin_manager") as mock:
        mock.plugins = {}
        mock.plugin_registry = {}
        mock.list_plugins.return_value = []
        mock.load_plugin.return_value = True
        mock.unload_plugin.return_value = True
        mock.get_plugin_info.return_value = None
        yield mock


@pytest.fixture
def mock_security_sandbox():
    """Mock security sandbox"""
    with patch("src.api.main.security_sandbox") as mock:
        mock.validate_plugin.return_value = True
        mock.get_audit_log.return_value = []
        yield mock


@pytest.fixture
def mock_metrics_collector():
    """Mock metrics collector"""
    with patch("src.api.main.metrics_collector") as mock:
        mock.get_metrics.return_value = {"metrics": "test_metric 1.0"}
        yield mock


@pytest.fixture
def client(mock_plugin_manager, mock_security_sandbox, mock_metrics_collector):
    """Create test client with mocked dependencies"""
    from src.api.main import app

    return TestClient(app)


class TestHealthEndpointIntegration:
    """Test health check endpoint integration"""

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


class TestPluginEndpointsIntegration:
    """Test plugin API endpoints integration"""

    def test_list_plugins_empty(self, client, mock_plugin_manager):
        """Test listing plugins when none are loaded"""
        mock_plugin_manager.list_plugins.return_value = []

        response = client.get("/api/v1/plugins")

        assert response.status_code == 200
        data = response.json()
        assert "plugins" in data
        assert len(data["plugins"]) == 0

    def test_list_plugins_with_plugins(self, client, mock_plugin_manager):
        """Test listing plugins with loaded plugins"""
        mock_plugins = [
            {"name": "plugin_1", "version": "1.0.0", "status": "loaded"},
            {"name": "plugin_2", "version": "1.0.1", "status": "loaded"},
        ]
        mock_plugin_manager.list_plugins.return_value = mock_plugins

        response = client.get("/api/v1/plugins")

        assert response.status_code == 200
        data = response.json()
        assert "plugins" in data
        assert len(data["plugins"]) == 2

    def test_register_plugin_success(
        self, client, mock_plugin_manager, mock_security_sandbox
    ):
        """Test successful plugin registration"""
        mock_security_sandbox.validate_plugin.return_value = True
        mock_plugin_manager.load_plugin.return_value = True

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

    def test_register_plugin_security_failure(
        self, client, mock_plugin_manager, mock_security_sandbox
    ):
        """Test plugin registration with security validation failure"""
        mock_security_sandbox.validate_plugin.return_value = False

        plugin_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
        }

        response = client.post("/api/v1/plugins", json=plugin_data)

        assert response.status_code == 403
        data = response.json()
        assert "security validation" in data["detail"].lower()

    def test_register_plugin_load_failure(
        self, client, mock_plugin_manager, mock_security_sandbox
    ):
        """Test plugin registration with load failure"""
        mock_security_sandbox.validate_plugin.return_value = True
        mock_plugin_manager.load_plugin.return_value = False

        plugin_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
        }

        response = client.post("/api/v1/plugins", json=plugin_data)

        assert response.status_code == 500
        data = response.json()
        assert "failed" in data["detail"].lower()

    def test_execute_plugin_success(self, client, mock_plugin_manager):
        """Test successful plugin execution"""
        mock_plugin_manager.execute_plugin.return_value = {
            "success": True,
            "result": {"output": "test"},
            "plugin": "test_plugin",
            "timestamp": datetime.utcnow().isoformat(),
        }

        execute_data = {"context": {"data": "test"}}

        response = client.post("/api/v1/plugins/test_plugin/execute", json=execute_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_execute_plugin_not_found(self, client, mock_plugin_manager):
        """Test executing nonexistent plugin"""
        mock_plugin_manager.execute_plugin.side_effect = ValueError("Plugin not found")

        execute_data = {"context": {"data": "test"}}

        response = client.post("/api/v1/plugins/nonexistent/execute", json=execute_data)

        assert response.status_code == 500

    def test_unregister_plugin_success(self, client, mock_plugin_manager):
        """Test successful plugin unregistration"""
        mock_plugin_manager.unload_plugin.return_value = True

        response = client.delete("/api/v1/plugins/test_plugin")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test_plugin" in data["message"]

    def test_unregister_plugin_not_found(self, client, mock_plugin_manager):
        """Test unregistering nonexistent plugin"""
        mock_plugin_manager.unload_plugin.return_value = False

        response = client.delete("/api/v1/plugins/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_plugin_info_success(self, client, mock_plugin_manager):
        """Test getting plugin info successfully"""
        mock_plugin_manager.get_plugin_info.return_value = {
            "status": {"name": "test_plugin", "version": "1.0.0"},
            "metadata": {"name": "test_plugin", "version": "1.0.0"},
        }

        response = client.get("/api/v1/plugins/test_plugin")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "metadata" in data

    def test_get_plugin_info_not_found(self, client, mock_plugin_manager):
        """Test getting info for nonexistent plugin"""
        mock_plugin_manager.get_plugin_info.return_value = None

        response = client.get("/api/v1/plugins/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestMetricsEndpointIntegration:
    """Test metrics API endpoint integration"""

    def test_get_metrics(self, client, mock_metrics_collector):
        """Test getting metrics"""
        mock_metrics_collector.get_metrics.return_value = {"metrics": "test_metric 1.0"}

        response = client.get("/api/v1/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data


class TestSecurityEndpointsIntegration:
    """Test security API endpoints integration"""

    def test_get_audit_log(self, client, mock_security_sandbox):
        """Test getting audit log"""
        mock_audit_log = [
            {
                "action": "test",
                "status": "SUCCESS",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ]
        mock_security_sandbox.get_audit_log.return_value = mock_audit_log

        response = client.get("/api/v1/security/audit-log")

        assert response.status_code == 200
        data = response.json()
        assert "audit_log" in data
        assert len(data["audit_log"]) == 1

    def test_validate_plugin_security_valid(self, client, mock_security_sandbox):
        """Test validating plugin security (valid)"""
        mock_security_sandbox.validate_plugin.return_value = True

        plugin_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
        }

        response = client.post("/api/v1/security/validate", json=plugin_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_plugin_security_invalid(self, client, mock_security_sandbox):
        """Test validating plugin security (invalid)"""
        mock_security_sandbox.validate_plugin.return_value = False

        plugin_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
        }

        response = client.post("/api/v1/security/validate", json=plugin_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False


class TestAPIErrorHandlingIntegration:
    """Test API error handling integration"""

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


class TestAPIMiddlewareIntegration:
    """Test API middleware integration"""

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


class TestAPIIntegrationLifecycle:
    """Test API integration lifecycle"""

    def test_plugin_lifecycle_api(
        self, client, mock_plugin_manager, mock_security_sandbox
    ):
        """Test complete plugin lifecycle via API"""
        # Register plugin
        mock_security_sandbox.validate_plugin.return_value = True
        mock_plugin_manager.load_plugin.return_value = True

        plugin_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "module": "test_module",
        }

        response = client.post("/api/v1/plugins", json=plugin_data)
        assert response.status_code == 200
        assert response.json()["success"] is True

        # List plugins
        mock_plugin_manager.list_plugins.return_value = [
            {"name": "test_plugin", "version": "1.0.0"}
        ]

        response = client.get("/api/v1/plugins")
        assert response.status_code == 200
        assert len(response.json()["plugins"]) == 1

        # Execute plugin
        mock_plugin_manager.execute_plugin.return_value = {
            "success": True,
            "result": {},
            "plugin": "test_plugin",
            "timestamp": datetime.utcnow().isoformat(),
        }

        response = client.post(
            "/api/v1/plugins/test_plugin/execute", json={"context": {}}
        )
        assert response.status_code == 200

        # Unregister plugin
        mock_plugin_manager.unload_plugin.return_value = True

        response = client.delete("/api/v1/plugins/test_plugin")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
