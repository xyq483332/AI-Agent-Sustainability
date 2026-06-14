# Observability Architecture (OpenTelemetry)

**状态**: ✅ 已实施
**日期**: 2026-06-14

---

## 数据流架构

```
┌─────────────────────┐     OTLP gRPC      ┌──────────────────┐     Prometheus      ┌──────────┐     ┌──────────┐
│  Application Pod    │ ──────────────────► │  OTel Collector  │ ◄── scrape (:8889) ──│Prometheus │ ──► │ Grafana  │
│  (OTel SDK :4317)   │     metrics push   │  (contrib)       │                      │ (:9090)  │     │ (:3000)  │
└─────────────────────┘                    └──────────────────┘                      └──────────┘     └──────────┘
```

## 组件说明

### 1. OTel SDK (应用侧)
- **依赖**: `opentelemetry-api==1.21.0` + `opentelemetry-sdk==1.21.0` + `opentelemetry-exporter-otlp-proto-grpc==1.21.0`
- **初始化**: `src/observability/metrics.py` 中的模块级 `MeterProvider`
- **导出**: 通过 OTLP gRPC 推送至 OTel Collector `:4317`
- **环境变量**:
  - `OTEL_SERVICE_NAME` — 服务名称 (默认 `ai-agent-sustainability`)
  - `OTEL_EXPORTER_OTLP_ENDPOINT` — Collector 地址 (默认 `http://otel-collector:4317`)

### 2. OTel Collector
- **镜像**: `otel/opentelemetry-collector-contrib:0.102.0`
- **端口**:
  - `:4317` — OTLP gRPC 接收
  - `:4318` — OTLP HTTP 接收
  - `:8889` — Prometheus 导出 (Prometheus 采集目标)
  - `:8888` — Collector 自身遥测
- **配置**: `config/otel-collector-config.yaml`
- **Pipeline**: `OTLP Receiver → Memory Limiter → Batch Processor → Resource Processor → Prometheus Exporter`

### 3. Prometheus
- **采集目标**: 从 OTel Collector `:8889` 拉取指标 (替代直接采集应用)
- **配置**: `config/prometheus.yml`
- **告警**: `config/alert_rules.yml` (7 条规则)

### 4. Grafana
- **数据源**: Prometheus
- **仪表盘**: 插件系统指标、安全沙箱指标、基础设施指标

## 指标映射

| OTel Metric Name | 类型 | Labels | 说明 |
|:---|:---:|:---|:---|
| `plugin_load_duration_ms` | Histogram | `plugin` | 插件加载耗时 |
| `plugin_execution_duration_ms` | Histogram | `plugin`, `success` | 插件执行耗时 |
| `plugin_execution_total` | Counter | `plugin`, `success` | 插件执行次数 |
| `security_validation_duration_ms` | Histogram | `plugin`, `passed` | 安全验证耗时 |
| `security_validation_total` | Counter | `plugin`, `passed` | 安全验证次数 |
| `plugin_memory_usage_mb` | Gauge | `plugin` | 插件内存使用 |

## 后端 API

应用同时提供 `/api/v1/metrics` 端点 (Prometheus 文本格式)，作为 OTel 管道的**回退方案**。

## 测试策略

单元测试和验收测试使用 `InMemoryMetricReader` 替代真实 OTLP Exporter，无需运行 Collector 即可验证指标记录逻辑。
