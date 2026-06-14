"""
AI Agent Sustainable Evolution - Observability Stack

This module implements the observability stack with:
- OpenTelemetry SDK for metrics collection
- OTLP gRPC export to OTel Collector
- Prometheus-compatible export via OTel Collector
- Logging, Tracing (extensible)

Data flow:
  App → OTel SDK → OTLP gRPC (:4317) → OTel Collector → Prometheus (:8889) → Grafana
"""

__version__ = "1.0.0"
__author__ = "Stark Industries AI Team"
