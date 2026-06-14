"""
Unit Tests for Security Sandbox
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from security.sandbox import SecuritySandbox


def test_sandbox_initialization():
    """Test security sandbox initialization"""
    sandbox = SecuritySandbox()
    
    assert sandbox.max_cpu_percent == 50
    assert sandbox.max_memory_mb == 256
    assert sandbox.max_execution_time == 30
    assert len(sandbox.network_whitelist) == 0
    assert len(sandbox.file_read_whitelist) == 0


def test_sandbox_validate_plugin():
    """Test plugin validation"""
    sandbox = SecuritySandbox()
    
    # Valid plugin metadata
    valid_meta = {
        "name": "test_plugin",
        "version": "1.0.0",
        "module": "test_module",
        "permissions": ["read_memory"],
        "security": {
            "network_whitelist": [],
            "file_read_paths": []
        }
    }
    
    assert sandbox.validate_plugin(valid_meta) is True


def test_sandbox_validate_plugin_with_dangerous_permissions():
    """Test plugin validation with dangerous permissions"""
    sandbox = SecuritySandbox()
    
    # Plugin with dangerous permissions but not approved
    dangerous_meta = {
        "name": "dangerous_plugin",
        "version": "1.0.0",
        "module": "dangerous_module",
        "permissions": ["write_memory", "execute_shell"],
        "security": {
            "approved": False
        }
    }
    
    assert sandbox.validate_plugin(dangerous_meta) is False


def test_sandbox_validate_plugin_with_approved_dangerous_permissions():
    """Test plugin validation with approved dangerous permissions"""
    sandbox = SecuritySandbox()
    
    # Plugin with dangerous permissions and approved
    approved_meta = {
        "name": "approved_plugin",
        "version": "1.0.0",
        "module": "approved_module",
        "permissions": ["write_memory"],
        "security": {
            "approved": True
        }
    }
    
    assert sandbox.validate_plugin(approved_meta) is True


def test_sandbox_network_whitelist():
    """Test network whitelist functionality"""
    sandbox = SecuritySandbox()
    
    # Add hosts to whitelist
    sandbox.restrict_network_access(["10.0.0.0/8", "localhost"])
    
    assert sandbox.is_host_allowed("10.0.0.1") is True
    assert sandbox.is_host_allowed("localhost") is True
    assert sandbox.is_host_allowed("evil.com") is False


def test_sandbox_file_whitelist():
    """Test file whitelist functionality"""
    sandbox = SecuritySandbox()
    
    # Add paths to whitelist
    sandbox.restrict_file_access(
        read_paths=["/volume1/docker/qwenpaw/", "/tmp/"],
        write_paths=["/tmp/output/"]
    )
    
    assert sandbox.is_path_readable("/volume1/docker/qwenpaw/file.txt") is True
    assert sandbox.is_path_readable("/etc/passwd") is False
    assert sandbox.is_path_writable("/tmp/output/file.txt") is True
    assert sandbox.is_path_writable("/etc/file.txt") is False


def test_sandbox_audit_log():
    """Test audit logging"""
    sandbox = SecuritySandbox()
    
    # Perform some operations
    sandbox.validate_plugin({
        "name": "test_plugin",
        "permissions": [],
        "security": {}
    })
    
    # Check audit log
    audit_log = sandbox.get_audit_log()
    assert len(audit_log) > 0
    assert audit_log[0]['event_type'] == 'plugin_validation'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
