"""
Security Sandbox

Provides isolated execution environment for plugins with:
- Resource limiting (CPU, memory, network)
- File system access control
- Network restrictions
- Audit logging
"""

import os
import resource
import socket
from typing import Dict, List, Set, Any
from datetime import datetime, timezone
import logging
import json

logger = logging.getLogger(__name__)

class SecuritySandbox:
    """Security sandbox for plugin execution"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.audit_log: List[Dict] = []
        
        # Resource limits
        self.max_cpu_percent = self.config.get('max_cpu_percent', 50)
        self.max_memory_mb = self.config.get('max_memory_mb', 256)
        self.max_execution_time = self.config.get('max_execution_time', 30)
        
        # Access control
        self.network_whitelist: Set[str] = set(self.config.get('network_whitelist', []))
        self.file_read_whitelist: Set[str] = set(self.config.get('file_read_whitelist', []))
        self.file_write_whitelist: Set[str] = set(self.config.get('file_write_whitelist', []))
        
    def validate_plugin(self, plugin_meta: Dict[str, Any]) -> bool:
        """Validate plugin security constraints"""
        try:
            # Validate permissions
            if not self._validate_permissions(plugin_meta):
                return False
            
            # Validate network access
            if not self._validate_network_access(plugin_meta):
                return False
            
            # Validate file system access
            if not self._validate_file_access(plugin_meta):
                return False
            
            # Log successful validation
            self._audit_log('plugin_validation', 'SUCCESS', plugin_meta)
            return True
            
        except Exception as e:
            self._audit_log('plugin_validation', 'FAILED', {'error': str(e)})
            return False
    
    def check_resource_limits(self, plugin_name: str) -> bool:
        """Check if plugin is within resource limits"""
        try:
            # Get current resource usage
            usage = resource.getrusage(resource.RUSAGE_SELF)
            
            # Check memory usage (in MB)
            memory_mb = usage.ru_maxrss / 1024 / 1024
            if memory_mb > self.max_memory_mb:
                self._audit_log('resource_check', 'FAILED', {
                    'plugin': plugin_name,
                    'memory_mb': memory_mb,
                    'limit_mb': self.max_memory_mb
                })
                return False
            
            # Log successful check
            self._audit_log('resource_check', 'SUCCESS', {
                'plugin': plugin_name,
                'memory_mb': memory_mb
            })
            return True
            
        except Exception as e:
            self._audit_log('resource_check', 'ERROR', {'error': str(e)})
            return False
    
    def restrict_network_access(self, allowed_hosts: List[str]) -> None:
        """Restrict network access to allowed hosts only"""
        self.network_whitelist = set(allowed_hosts)
        self._audit_log('network_restriction', 'UPDATED', {'hosts': allowed_hosts})
    
    def restrict_file_access(self, read_paths: List[str], write_paths: List[str]) -> None:
        """Restrict file system access"""
        self.file_read_whitelist = set(read_paths)
        self.file_write_whitelist = set(write_paths)
        self._audit_log('file_restriction', 'UPDATED', {
            'read_paths': read_paths,
            'write_paths': write_paths
        })
    
    def is_host_allowed(self, hostname: str) -> bool:
        """Check if a host is in the whitelist"""
        # Check exact match
        if hostname in self.network_whitelist:
            return True
        
        # Check wildcard
        if '*' in self.network_whitelist:
            return True
        
        # Check CIDR range
        for allowed in self.network_whitelist:
            if '/' in allowed:
                try:
                    import ipaddress
                    network = ipaddress.ip_network(allowed, strict=False)
                    ip = ipaddress.ip_address(hostname)
                    if ip in network:
                        return True
                except (ValueError, TypeError):
                    # Not a valid IP/CIDR, skip
                    pass
        
        return False
    
    def is_path_readable(self, path: str) -> bool:
        """Check if a path is readable"""
        return any(path.startswith(allowed) for allowed in self.file_read_whitelist)
    
    def is_path_writable(self, path: str) -> bool:
        """Check if a path is writable"""
        return any(path.startswith(allowed) for allowed in self.file_write_whitelist)
    
    def _validate_permissions(self, plugin_meta: Dict) -> bool:
        """Validate plugin permissions"""
        permissions = plugin_meta.get('permissions', [])
        
        # Define dangerous permissions
        dangerous_permissions = ['write_memory', 'execute_shell', 'network_access']
        
        # Check for dangerous permissions without justification
        for perm in permissions:
            if perm in dangerous_permissions:
                # Require explicit approval for dangerous permissions
                if not plugin_meta.get('security', {}).get('approved', False):
                    self._audit_log('permission_check', 'DENIED', {
                        'permission': perm,
                        'reason': 'Requires explicit approval'
                    })
                    return False
        
        return True
    
    def _validate_network_access(self, plugin_meta: Dict) -> bool:
        """Validate network access configuration"""
        security_config = plugin_meta.get('security', {})
        network_whitelist = security_config.get('network_whitelist', [])
        
        # Check if all requested hosts are allowed
        for host in network_whitelist:
            if not self.is_host_allowed(host):
                self._audit_log('network_check', 'DENIED', {
                    'host': host,
                    'reason': 'Not in whitelist'
                })
                return False
        
        return True
    
    def _validate_file_access(self, plugin_meta: Dict) -> bool:
        """Validate file system access configuration"""
        security_config = plugin_meta.get('security', {})
        file_read_paths = security_config.get('file_read_paths', [])
        
        # Check if all requested paths are allowed
        for path in file_read_paths:
            if not self.is_path_readable(path):
                self._audit_log('file_check', 'DENIED', {
                    'path': path,
                    'reason': 'Not in read whitelist'
                })
                return False
        
        return True
    
    def _audit_log(self, event_type: str, status: str, details: Dict) -> None:
        """Log security audit event"""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': event_type,
            'status': status,
            'details': details
        }
        self.audit_log.append(log_entry)
        logger.info(f"Security audit: {event_type} - {status}")
    
    def get_audit_log(self) -> List[Dict]:
        """Get audit log entries"""
        return self.audit_log.copy()
    
    def clear_audit_log(self) -> None:
        """Clear audit log"""
        self.audit_log.clear()
