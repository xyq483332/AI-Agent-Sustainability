# OTel Collector 部署验证报告

**日期**: 2026-06-14 22:30 (Asia/Shanghai)  
**状态**: ✅ **全部通过**

---

## 1. OTel Collector 容器部署

| 项目 | 值 |
|:---|:---|
| 容器名 | `ten-agent-otel-collector` |
| 镜像 | `otel/opentelemetry-collector-contrib:0.102.0` |
| 网络模式 | `host` (直接绑定主机端口) |
| 重启策略 | `unless-stopped` |
| 内存限制 | 512MB |
| CPU 限制 | 1 core |
| 配置主机路径 | `/volume1/docker/otel-collector/config.yaml` |
| 配置容器路径 | `/etc/otelcol-contrib/config.yaml` (RO) |

### 端口映射 (Host Network)

| 端口 | 用途 | 状态 |
|:---:|:---|:---:|
| 4317 | OTLP gRPC Receiver | ✅ |
| 4318 | OTLP HTTP Receiver | ✅ |
| 8889 | Prometheus Exporter (scrape target) | ✅ |
| 8881 | Internal Telemetry (非 8888，端口冲突) | ✅ |

---

## 2. Prometheus 配置更新

| 项目 | 值 |
|:---|:---|
| 配置主机路径 | `/volume1/docker/qwenpaw/monitoring/prometheus/prometheus.yml` |
| 新增 job | `otel-collector` (:8889, 10s) |
| 新增 job | `otel-collector-telemetry` (:8881, 30s) |
| 采集目标 IP | `<host-gateway>` (Docker 网关) |

### Prometheus Targets 最终状态

| Job | Instance | Health |
|:---|:---|:---:|
| otel-collector | host-gateway:8889 | ✅ up |
| otel-collector-telemetry | host-gateway:8881 | ✅ up |
| qwenpaw-metrics | host-gateway:9101 | ✅ up |
| ten-agent-health | host-gateway:9101 | ✅ up |
| ten-agent-circuit-breaker | host-gateway:9101 | ✅ up |
| ten-agent-memory | host-gateway:9101 | ✅ up |
| node-exporter | node-exporter:9100 | ✅ up |
| knowledge-metrics | ten-agent-knowledge-metrics:9103 | ✅ up |

---

## 3. 端到端数据流验证

```
App (OTel SDK)
  ↓ OTLP HTTP POST /v1/metrics
OTel Collector (:4318)
  ↓ batch + memory_limiter + resource
Prometheus Exporter (:8889)
  ↓ Prometheus scrape
Prometheus (:9090)
  ↓ PromQL query
✅ otel_otel_pipeline_final_test_total = 100
```

---

## 4. 部署过程中发现并修复的问题

| # | 问题 | 根因 | 修复 |
|:---:|:---|:---|:---|
| 1 | 配置文件挂载失败 "not a directory" | qwenpaw 容器内 `/volume1/docker/otel-collector/` 是 overlay FS，非主机路径 | 用临时 alpine 容器通过主机 bind mount 写入 |
| 2 | `config.yaml` 是目录而非文件 | 之前 `mkdir` + `echo >` 命令在容器内创建了同名目录 | `rm -rf` 后重建为文件 |
| 3 | 容器启动 400: port 8888 already in use | NAS 主机端口 8888 已被占用 | telemetry 端口改为 8881 |
| 4 | 端口 4318/8889 未绑定到主机 | 镜像 `ExposedPorts` 不含这些端口，`PortBindings` 无效 | 改用 `NetworkMode: host` |
| 5 | Prometheus 报 "duplicate label names" | `const_labels` 与 `resource_to_telemetry_conversion` 冲突 | 移除 `const_labels` |
| 6 | Prometheus 目标 down | `host.docker.internal` 在 Linux Docker 中不可解析 | 改用网关 IP `<host-gateway>` |
| 7 | Prometheus YAML 语法错误 | OTel targets 被错误插入 `global:` 段 | 移至 `scrape_configs:` 段 |

---

## 5. 项目文件更新

| 文件 | 变更 |
|:---|:---|
| `config/otel-collector-config.yaml` | 移除 const_labels, telemetry port 8888→8881 |
| `config/prometheus.yml` | 更新注释和目标端口 8888→8881 |
| `docker-compose.yml` | 更新 OTel Collector: config 路径、端口 |

## 6. 测试结果

```
58 passed in 0.13s ✅
```
