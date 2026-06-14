"""
AI Agent Sustainable Evolution - Main Application

Entry point for the application.
Initialises OTel SDK (metrics export via OTLP → OTel Collector → Prometheus).
"""

import os
import uvicorn
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .api.main import app
from .plugins.manager import PluginManager
from .security.sandbox import SecuritySandbox
from .observability.metrics import MetricsCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
plugin_manager = PluginManager()
security_sandbox = SecuritySandbox()
metrics_collector = MetricsCollector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AI Agent Sustainable Evolution System")
    logger.info(f"OTEL_SERVICE_NAME   = {os.getenv('OTEL_SERVICE_NAME', 'not set')}")
    logger.info(f"OTEL_EXPORTER_OTLP  = {os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'not set')}")

    yield

    # Shutdown
    logger.info("Shutting down AI Agent Sustainable Evolution System")


# Update app with lifespan
app.router.lifespan_context = lifespan


def main():
    """Main entry point"""
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
