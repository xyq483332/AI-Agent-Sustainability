# Deployment Architecture

**状态**: ✅ 已实施  
**日期**: 2026-06-14

---

## 1. 部署拓扑

### 1.1 本地开发 (Docker Compose)

```
┌─────────────────────────────────────────────────────────┐
│                    Host Machine                          │
│                                                         │
│  ┌─────────────── Docker Compose ────────────────────┐  │
│  │                                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │plugin-system │  │sec-sandbox   │              │  │
│  │  │   :8080      │  │   :8081      │              │  │
│  │  └──────┬───────┘  └──────┬───────┘              │  │
│  │         │                  │                       │  │
│  │  ┌──────┴──────────────────┴───────┐              │  │
│  │  │         app-network             │              │  │
│  │  └──────┬──────────────────┬───────┘              │  │
│  │         │                  │                       │  │
│  │  ┌──────▼──────┐  ┌───────▼──────┐              │  │
│  │  │  PostgreSQL  │  │    Redis     │              │  │
│  │  │   :5432      │  │    :6379     │              │  │
│  │  └─────────────┘  └──────────────┘              │  │
│  │                                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │otel-collector│  │  Prometheus  │              │  │
│  │  │ :4317 :8889  │  │    :9090     │              │  │
│  │  └──────────────┘  └──────┬───────┘              │  │
│  │                            │                       │  │
│  │                     ┌──────▼───────┐              │  │
│  │                     │   Grafana    │              │  │
│  │                     │    :3000     │              │  │
│  │                     └──────────────┘              │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 1.2 生产部署 (NAS)

```
┌────────────── Production Host (NAS) ──────────────────┐
│                                                        │
│  ┌── Host Network ──────────────────────────────────┐  │
│  │  OTel Collector (:4317, :4318, :8889, :8881)     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌── monitoring_ten-agent-monitoring ───────────────┐  │
│  │  Prometheus (:9090)                              │  │
│  │  Grafana (:3000)                                 │  │
│  │  Node Exporter (:9100)                           │  │
│  │  Knowledge Metrics (:9103)                       │  │
│  │  Metrics Exporter (:9101)                        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌── qwenpaw ──────────────────────────────────────┐  │
│  │  QwenPaw Agent Platform (:8088)                  │  │
│  │  SearXNG (:8080)                                 │  │
│  │  qBittorrent (:8888)                             │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌── 持久化存储 ────────────────────────────────────┐  │
│  │  /volume1/docker/{container}/                     │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

## 2. 容器清单

### 2.1 开发环境

| 容器 | 镜像 | 端口 | 用途 | 资源限制 |
|:---|:---|:---:|:---|:---|
| plugin-system | 自建 | 8080 | 插件系统 API | CPU 2, Mem 2G |
| security-sandbox | 自建 | 8081 | 安全沙箱 | CPU 1, Mem 1G |
| otel-collector | otel/contrib:0.102.0 | 4317,8889 | OTel 指标管道 | CPU 1, Mem 512M |
| postgres | postgres:15 | 5432 | 数据库 | CPU 1, Mem 1G |
| redis | redis:7-alpine | 6379 | 缓存 | CPU 0.5, Mem 256M |
| prometheus | prom/prometheus | 9090 | 指标采集 | CPU 0.5, Mem 512M |
| grafana | grafana/grafana | 3000 | 可视化 | CPU 0.5, Mem 256M |

### 2.2 生产环境 (NAS)

| 容器 | 端口 | 网络模式 | 持久化路径 | 状态 |
|:---|:---:|:---|:---|:---:|
| qwenpaw | 8088 | bridge | /volume1/docker/qwenpaw/ | ✅ |
| ten-agent-otel-collector | 4317,4318,8889,8881 | host | /volume1/docker/otel-collector/ | ✅ |
| ten-agent-prometheus | 9090 | monitoring | /volume1/docker/qwenpaw/monitoring/ | ✅ |
| ten-agent-grafana | 3000 | monitoring | /volume1/docker/ten-agent-grafana/ | ✅ |
| ten-agent-node-exporter | 9100 | monitoring | 无持久化 (只读挂载) | ✅ |
| ten-agent-knowledge-metrics | 9103 | monitoring | /volume1/docker/ten-agent-knowledge-metrics/ | ✅ |
| searxng-fixed | 8080 | bridge | /volume1/docker/searxng-fixed/ | ✅ |
| qbittorrent-app-1 | 8888 | bridge | /volume1/docker/qbittorrent-app-1/ | ✅ |

## 3. 网络架构

### 3.1 网络分段

| 网络 | 用途 | 容器 |
|:---|:---|:---|
| `app-network` | 应用服务通信 | plugin-system, security-sandbox, postgres, redis |
| `monitoring_ten-agent-monitoring` | 监控栈通信 | prometheus, grafana, node-exporter, knowledge-metrics |
| `host` | 宿主机网络直连 | otel-collector |

### 3.2 端口映射

| 端口 | 服务 | 可达性 |
|:---:|:---|:---|
| 8080 | SearXNG / Plugin System | 内网 |
| 8088 | QwenPaw | 内网 |
| 9090 | Prometheus | 内网 |
| 3000 | Grafana | 内网 |
| 4317 | OTLP gRPC | 内网 |
| 8889 | OTel Prometheus Exporter | 内网 |

## 4. 数据持久化

### 4.1 挂载规范

**强制规则**: 所有 Docker 容器的持久性数据 **必须** 保存在 `/volume1/docker/{容器名}/` 目录下。

| 容器 | 主机路径 | 容器路径 | 模式 |
|:---|:---|:---|:---:|
| qwenpaw | /volume1/docker/qwenpaw/ | /app/ | RW |
| otel-collector | /volume1/docker/otel-collector/config.yaml | /etc/otelcol-contrib/config.yaml | RO |
| prometheus | /volume1/docker/qwenpaw/monitoring/ | /etc/prometheus + /prometheus | RO/RW |
| grafana | /volume1/docker/ten-agent-grafana/ | /var/lib/grafana | RW |

### 4.2 备份策略

| 数据 | 备份频率 | 保留期 | 方式 |
|:---|:---:|:---:|:---|
| PostgreSQL | 每日 | 30 天 | pg_dump |
| Prometheus | 每周 | 90 天 | TSDB snapshot |
| Grafana | 每周 | 90 天 | API export |
| 配置文件 | 每次变更 | 永久 | Git |

## 5. 健康检查

| 服务 | 健康检查端点 | 间隔 | 超时 |
|:---|:---|:---:|:---:|
| Plugin System | GET /health | 10s | 5s |
| Security Sandbox | GET /health | 10s | 5s |
| OTel Collector | GET /health (8881) | 30s | 5s |
| Prometheus | GET /-/healthy | 15s | 5s |
| Grafana | GET /api/health | 15s | 5s |

## 6. 扩展策略

### 6.1 水平扩展
- 插件系统: 无状态，可多实例 + 负载均衡
- OTel Collector: 支持多实例 + 负载均衡
- Prometheus: 支持联邦 (Federation) 模式

### 6.2 垂直扩展
- PostgreSQL: 增加 CPU/内存/存储
- OTel Collector: 增大 `memory_limiter.limit_mib`
- Prometheus: 增大存储空间和 retention
