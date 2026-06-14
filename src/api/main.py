"""
API Main Application

FastAPI application for plugin system API.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import uvicorn

from ..plugins.manager import PluginManager
from ..security.sandbox import SecuritySandbox
from ..observability.metrics import MetricsCollector, PluginMetrics

# Initialize FastAPI app
app = FastAPI(
    title="AI Agent Sustainable Evolution API",
    description="Plugin management and security sandbox API",
    version="1.0.0"
)

# Initialize components
plugin_manager = PluginManager()
security_sandbox = SecuritySandbox()
metrics_collector = MetricsCollector()
plugin_metrics = PluginMetrics(metrics_collector)


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
            "security": request.security
        }
        
        if not security_sandbox.validate_plugin(plugin_meta):
            raise HTTPException(status_code=403, detail="Plugin failed security validation")
        
        # Load plugin
        success = plugin_manager.load_plugin(request.module)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to load plugin")
        
        return PluginResponse(
            success=True,
            message=f"Plugin {request.name} registered successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/plugins/{plugin_name}/execute")
async def execute_plugin(plugin_name: str, request: PluginExecuteRequest):
    """Execute a plugin"""
    try:
        result = plugin_manager.execute_plugin(plugin_name, request.context)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/plugins/{plugin_name}")
async def unregister_plugin(plugin_name: str):
    """Unregister a plugin"""
    success = plugin_manager.unload_plugin(plugin_name)
    if not success:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    return PluginResponse(
        success=True,
        message=f"Plugin {plugin_name} unregistered successfully"
    )


@app.get("/api/v1/plugins/{plugin_name}")
async def get_plugin_info(plugin_name: str):
    """Get plugin information"""
    info = plugin_manager.get_plugin_info(plugin_name)
    if not info:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
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
        "security": request.security
    }
    
    is_valid = security_sandbox.validate_plugin(plugin_meta)
    return {"valid": is_valid}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
