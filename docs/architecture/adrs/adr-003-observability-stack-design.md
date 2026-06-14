# ADR-003: Observability Stack Design

**状态**: ✅ 已实施  
**日期**: 2026-06-14  
**决策者**: CTO, DevOps Lead

---

## 背景

系统需要全面的可观测性能力来监控插件系统健康状态、检测异常行为、支持性能优化。可观测性三大支柱：指标 (Metrics)、日志 (Logs)、追踪 (Traces)。

## 决策

采用 **OpenTelemetry** 作为可观测性标准，构建 `OTel SDK → OTel Collector → Prometheus → Grafana` 数据管道。

### 数据流

```
┌──────────────────┐      OTLP gRPC       ┌──────────────────┐
│   Application    │ ──────────────────►  │  OTel Collector  │
│   (OTel SDK)     │   metrics push       │  (contrib)       │
│                  │                      │                  │
│  MeterProvider   │                      │  Receivers:      │
│  ├─ Counter      │                      │  ├─ otlp (gRPC)  │
│  ├─ Gauge        │                      │  └─ otlp (HTTP)  │
│  └─ Histogram    │                      │                  │
└──────────────────┘                      │  Processors:     │
                                          │  ├─ memory_limit │
                                          │  ├─ batch        │
                                          │  └─ resource     │
                                          └────────┬─────────┘
                                                   │
                                    ┌──────────────▼──────────────┐
                                    │     Prometheus Exporter     │
                                    │     (:8889 metrics)         │
                                    └──────────────┬──────────────┘
                                                   │ scrape
                                    ┌──────────────▼──────────────┐
                                    │        Prometheus           │
                                    │        (:9090)              │
                                    └──────────────┬──────────────┘
                                                   │ query
                                    ┌──────────────▼──────────────┐
                                    │         Grafana             │
                                    │         (:3000)             │
                                    └─────────────────────────────┘
```

## 备选方案

### 方案 A: OpenTelemetry (选中)
- **优点**: CNCF 标准，厂商中立，社区活跃，支持 Metrics/Logs/Traces
- **缺点**: 学习曲线较陡，配置复杂度较高
- **适用**: 生产级可观测性需求

### 方案 B: Prometheus Client 直接导出
- **优点**: 简单直接，无需额外组件
- **缺点**: 仅支持 Metrics，无标准追踪，厂商锁定
- **适用**: 简单指标监控

### 方案 C: ELK Stack (Elasticsearch + Logstash + Kibana)
- **优点**: 强大的日志搜索和分析能力
- **缺点**: 资源消耗大，仅日志无指标
- **适用**: 日志密集型应用

### 方案 D: Datadog / New Relic (SaaS)
- **优点**: 开箱即用，无需运维
- **缺点**: 成本高，数据离开本地，厂商锁定
- **适用**: 快速上手，预算充足

## 实现

### OTel SDK 集成 (`src/observability/metrics.py`)

```python
# 模块级 MeterProvider (全局单例)
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# OTLP Exporter → OTel Collector
exporter = OTLPMetricExporter(endpoint="http://otel-collector:4317", insecure=True)
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
provider = MeterProvider(metric_readers=[reader])
meter = metrics.get_meter("ai-agent-sustainability", "1.0")
```

### OTel Collector 配置

```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }

processors:
  memory_limiter: { check_interval: 1s, limit_mib: 256 }
  batch: { timeout: 5s, send_batch_size: 1024 }
  resource:
    attributes:
      - { key: service.namespace, value: stark-industries, action: upsert }

exporters:
  prometheus:
    endpoint: 0.0.0.0:8889
    namespace: otel
    resource_to_telemetry_conversion: { enabled: true }
  debug: { verbosity: basic }
```

### 核心指标

| 指标名 | 类型 | Labels | 说明 |
|:---|:---:|:---|:---|
| `plugin_load_duration_ms` | Histogram | `plugin` | 插件加载耗时 |
| `plugin_execution_duration_ms` | Histogram | `plugin`, `success` | 插件执行耗时 |
| `plugin_execution_total` | Counter | `plugin`, `success` | 插件执行次数 |
| `security_validation_duration_ms` | Histogram | `plugin`, `passed` | 安全验证耗时 |
| `plugin_memory_usage_mb` | Gauge | `plugin` | 插件内存使用 |

## 后果

### 正面
- ✅ 符合 CNCF 标准，可移植性强
- ✅ 统一的 Metrics/Logs/Traces 数据模型
- ✅ OTel Collector 提供灵活的路由和处理能力
- ✅ Prometheus 生态成熟，Grafana 可视化强大

### 负面
- ⚠️ OTel SDK + Collector 增加了部署复杂度
- ⚠️ 团队需要学习 OTel 概念和配置
- ⚠️ OTel Collector 本身需要监控和运维

### 部署验证 (2026-06-14)

| 组件 | 状态 | 说明 |
|:---|:---:|:---|
| OTel Collector 容器 | ✅ running | `ten-agent-otel-collector`, host network |
| OTLP 接收 | ✅ verified | HTTP POST → 200, 指标流入 |
| Prometheus 采集 | ✅ up | `otel-collector` job, 10s interval |
| 指标查询 | ✅ verified | `otel_pipeline_final_test_total = 100` |

## 参考

- Observability Architecture: `docs/architecture/observability_architecture.md`
- Observability AC: `docs/ac/observability_stack_ac.md`
- OTel Collector Config: `config/otel-collector-config.yaml`
- Implementation: `src/observability/metrics.py`
