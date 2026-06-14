# Integration Architecture

**状态**: ✅ 已实施  
**日期**: 2026-06-14

---

## 1. 集成概览

```
┌──────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                    │
│                      GET / POST / PUT / DELETE                │
└──────┬───────────────────┬───────────────────┬───────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│   Plugin     │  │  Security    │  │  Observability   │
│   System     │  │  Sandbox     │  │  (OTel SDK)      │
│              │  │              │  │                  │
│  Manager ◄───┼──┤  validate()  │  │  Counter()       │
│  Registry    │  │  log_event() │  │  Histogram()     │
│  Loader      │  │  check_*()   │  │  Gauge()         │
└──────┬───────┘  └──────┬───────┘  └────────┬─────────┘
       │                 │                    │
       ▼                 ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│  PostgreSQL  │  │  Audit Log   │  │  OTel Collector  │
│              │  │  (DB + File) │  │  → Prometheus    │
└──────────────┘  └──────────────┘  └──────────────────┘
```

## 2. 子系统间接口

### 2.1 API → Plugin System

| 接口 | 协议 | 说明 |
|:---|:---|:---|
| `PluginManager.list_plugins()` | Python 调用 | 列出已注册插件 |
| `PluginManager.get_plugin_info(id)` | Python 调用 | 获取插件详情 |
| `PluginManager.execute_plugin(id, params)` | Python 调用 | 执行插件 |
| `PluginManager.load_plugin(module_path)` | Python 调用 | 动态加载插件 |
| `PluginManager.unload_plugin(id)` | Python 调用 | 卸载插件 |

### 2.2 Plugin System → Security Sandbox

| 接口 | 协议 | 说明 |
|:---|:---|:---|
| `SecuritySandbox.validate_plugin(metadata)` | Python 调用 | 执行前权限验证 |
| `SecuritySandbox.check_network_access(ip)` | Python 调用 | 网络访问检查 |
| `SecuritySandbox.check_file_access(path, mode)` | Python 调用 | 文件访问检查 |
| `SecuritySandbox.log_security_event(type, severity, details)` | Python 调用 | 安全事件记录 |

**调用流程**:
```
API Request
  → PluginManager.execute_plugin()
    → SecuritySandbox.validate_plugin()  ← 权限验证
      → PluginBase.execute()             ← 插件执行
    → SecuritySandbox.log_security_event()  ← 审计记录
  → MetricsCollector.record_execution()  ← 指标记录
```

### 2.3 Application → Observability

| 接口 | 协议 | 说明 |
|:---|:---|:---|
| `Meter.create_counter(name)` | OTel API | 创建计数器 |
| `Meter.create_histogram(name)` | OTel API | 创建直方图 |
| `Meter.create_gauge(name)` | OTel API | 创建仪表 |
| OTLP gRPC Push | OTLP | 指标推送到 Collector |

### 2.4 Application → Database

| 接口 | 协议 | 说明 |
|:---|:---|:---|
| SQL Query | PostgreSQL | 插件 CRUD |
| SQL Query | PostgreSQL | 用户认证 |
| SQL Query | PostgreSQL | 审计日志写入 |
| SQL Query | PostgreSQL | 安全事件记录 |

## 3. 数据流

### 3.1 插件执行数据流

```
1. HTTP Request → FastAPI Router
2. FastAPI → Authentication Middleware (JWT验证)
3. FastAPI → PluginManager.execute_plugin()
4. PluginManager → SecuritySandbox.validate_plugin()
5. SecuritySandbox → Check permissions (DB查询)
6. SecuritySandbox → Check resource limits
7. SecuritySandbox → Check network/file ACL
8. PluginManager → PluginBase.execute()
9. PluginManager → SecuritySandbox.log_security_event()
10. PluginManager → MetricsCollector.record_execution()
11. OTel SDK → OTLP gRPC → OTel Collector
12. OTel Collector → Prometheus Exporter
13. HTTP Response → Client
```

### 3.2 指标数据流

```
1. PluginManager → Meter.create_counter("plugin_execution_total")
2. OTel SDK → PeriodicExportingMetricReader (5s interval)
3. Reader → OTLPMetricExporter
4. Exporter → OTLP gRPC → OTel Collector :4317
5. OTel Collector → Memory Limiter (256MB limit)
6. OTel Collector → Batch Processor (5s timeout)
7. OTel Collector → Resource Processor (add namespace)
8. OTel Collector → Prometheus Exporter (:8889)
9. Prometheus → Scrape (:8889, 10s interval)
10. Grafana → Query Prometheus → Dashboard
```

## 4. 集成模式

### 4.1 同步调用

| 调用方 | 被调用方 | 模式 | 超时 |
|:---|:---|:---|:---:|
| API → PluginManager | 同步 RPC | 直接调用 | 30s |
| PluginManager → Sandbox | 同步 RPC | 直接调用 | 5s |
| Plugin → Database | 同步 RPC | SQLAlchemy | 10s |

### 4.2 异步调用

| 调用方 | 被调用方 | 模式 | 说明 |
|:---|:---|:---|:---|
| OTel SDK → Collector | 异步推送 | OTLP gRPC | 5s 批量推送 |
| Prometheus → Collector | 异步拉取 | HTTP scrape | 10s 拉取间隔 |

### 4.3 事件驱动

| 事件 | 生产者 | 消费者 | 通道 |
|:---|:---|:---|:---|
| 插件执行完成 | PluginManager | MetricsCollector | 内存 (同步) |
| 安全事件 | SecuritySandbox | AuditLog | DB (同步) |
| 告警触发 | Prometheus | Grafana / Webhook | HTTP |

## 5. 依赖注入

```python
# src/api/dependencies.py

def get_plugin_manager() -> PluginManager:
    """获取插件管理器单例"""
    return PluginManager()

def get_security_sandbox() -> SecuritySandbox:
    """获取安全沙箱单例"""
    return SecuritySandbox(config=load_sandbox_config())

def get_metrics_collector() -> MetricsCollector:
    """获取指标收集器单例"""
    return MetricsCollector(service_name="plugin-system")
```

## 6. 容错机制

| 机制 | 触发条件 | 行为 | 恢复 |
|:---|:---|:---|:---|
| 插件超时 | 执行 > 30s | 强制终止 | 自动重试 1 次 |
| 数据库断连 | 连接池耗尽 | 返回 503 | 连接池自动恢复 |
| OTel Collector 不可达 | 连接失败 | 丢弃指标 | 重试 + 本地缓冲 |
| 资源超限 | 内存 > 80% | 拒绝新插件 | 释放后恢复 |

## 7. 接口版本管理

| 版本 | 路径前缀 | 状态 | 说明 |
|:---|:---|:---:|:---|
| v1 | `/api/v1/` | ✅ 活跃 | 当前生产版本 |
| v2 | `/api/v2/` | ⏳ 规划 | 未来增强版本 |

**版本兼容策略**:
- 新版本发布后，旧版本保留 6 个月
- 破坏性变更必须通过新版本号
- 废弃端点返回 `Sunset` 和 `Deprecation` 头
