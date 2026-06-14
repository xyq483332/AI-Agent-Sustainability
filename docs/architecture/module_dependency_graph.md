# Module Dependency Graph

**状态**: ✅ 已实施  
**日期**: 2026-06-14

---

## 1. 顶层架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     api (FastAPI)                            │
│  api/plugin_routes.py                                       │
│  api/auth_routes.py                                         │
│  api/dependencies.py                                        │
└────────┬────────────────────┬───────────────────┬───────────┘
         │                    │                   │
         ▼                    ▼                   ▼
┌────────────────┐  ┌─────────────────┐  ┌───────────────────┐
│ plugin_system  │  │   security      │  │  observability    │
│                │  │                 │  │                   │
│ manager.py     │  │  sandbox.py     │  │  metrics.py       │
│ registry.py    │  │  policy.py      │  │                   │
│ loader.py      │  │  audit.py       │  │                   │
│ base.py        │  │                 │  │                   │
└───────┬────────┘  └────────┬────────┘  └───────────────────┘
        │                    │
        ▼                    ▼
┌────────────────┐  ┌─────────────────┐
│  data_access   │  │   utils         │
│                │  │                 │
│ repository.py  │  │  exceptions.py  │
│ connection.py  │  │  config.py      │
│ models.py      │  │  logging.py     │
└───────┬────────┘  │  metrics.py     │
        │           └─────────────────┘
        ▼
┌────────────────┐
│  PostgreSQL    │
│  (Database)    │
└────────────────┘
```

## 2. 模块依赖表

### 2.1 src/plugin_system/

| 模块 | 依赖 (内部) | 依赖 (外部) |
|:---|:---|:---|
| `base.py` | - | abc, dataclasses |
| `registry.py` | base, exceptions | - |
| `loader.py` | base, registry, exceptions, logging | importlib, inspect |
| `manager.py` | base, registry, loader, exceptions, config | opentelemetry.api |
| `exceptions.py` | - | - |

### 2.2 src/security/

| 模块 | 依赖 (内部) | 依赖 (外部) |
|:---|:---|:---|
| `sandbox.py` | exceptions, logging | ipaddress, datetime, json |
| `policy.py` | exceptions | - |
| `audit.py` | logging, models | - |

### 2.3 src/data_access/

| 模块 | 依赖 (内部) | 依赖 (外部) |
|:---|:---|:---|
| `models.py` | - | sqlalchemy, uuid |
| `connection.py` | exceptions, config | sqlalchemy |
| `repository.py` | models, connection, exceptions | sqlalchemy |

### 2.4 src/observability/

| 模块 | 依赖 (内部) | 依赖 (外部) |
|:---|:---|:---|
| `metrics.py` | - | opentelemetry.sdk.metrics, opentelemetry.exporter.otlp |

### 2.5 src/utils/

| 模块 | 依赖 (内部) | 依赖 (外部) |
|:---|:---|:---|
| `exceptions.py` | - | - |
| `config.py` | - | yaml, os |
| `logging.py` | - | logging, structlog |
| `metrics.py` | - | opentelemetry.api |

### 2.6 src/api/

| 模块 | 依赖 (内部) | 依赖 (外部) |
|:---|:---|:---|
| `plugin_routes.py` | manager, exceptions, observability | fastapi |
| `auth_routes.py` | exceptions, data_access | fastapi, jwt |
| `dependencies.py` | plugin_system.manager, security.sandbox, observability.metrics | - |

## 3. 依赖方向图

```
api
 ├──► plugin_system
 │     ├──► plugin_system.base
 │     ├──► plugin_system.registry
 │     ├──► plugin_system.loader
 │     │     └──► plugin_system.base (ABC)
 │     └──► plugin_system.manager
 │           └──► opentelemetry.api
 │
 ├──► security
 │     ├──► security.sandbox
 │     │     ├──► utils.exceptions
 │     │     └──► utils.logging
 │     ├──► security.policy
 │     └──► security.audit
 │           ├──► utils.logging
 │           └──► data_access.models
 │
 ├──► observability
 │     └──► observability.metrics
 │           └──► opentelemetry.sdk.metrics
 │
 └──► data_access
       ├──► data_access.models
       ├──► data_access.connection
       │     └──► data_access.config
       └──► data_access.repository
```

## 4. 循环依赖检查

```
✅ 无循环依赖

api → plugin_system → (独立)
api → security → data_access.models → (独立)
api → observability → opentelemetry → (外部)
api → data_access → (独立)
```

## 5. 外部依赖图

```
src/
 ├── opentelemetry.api          (Meter API)
 ├── opentelemetry.sdk.metrics  (MeterProvider, counters, histograms)
 ├── opentelemetry.exporter.otlp (OTLP gRPC exporter)
 ├── opentelemetry.exporter.prometheus (Prometheus exporter, 测试用)
 ├── opentelemetry.sdk.metrics.export (PeriodicExportingMetricReader)
 │
 ├── sqlalchemy                 (ORM, 数据库连接)
 ├── psycopg2                  (PostgreSQL 驱动)
 ├── redis                      (缓存客户端)
 ├── fastapi                    (Web 框架)
 ├── uvicorn                   (ASGI 服务器)
 ├── pydantic                  (数据验证)
 ├── python-jose               (JWT 认证)
 ├── passlib                   (密码哈希)
 │
 ├── structlog                 (结构化日志)
 ├── pyyaml                    (配置解析)
 │
 └── (测试)
      ├── pytest               (测试框架)
      ├── pytest-asyncio       (异步测试)
      ├── pytest-cov           (覆盖率)
      └── httpx                (HTTP 测试客户端)
```

## 6. 模块说明

| 模块 | 职责 | 行数 | 复杂度 |
|:---|:---|---:|:---:|
| `plugin_system/base.py` | 插件抽象基类 (ABC) | 35 | 低 |
| `plugin_system/registry.py` | 插件注册表 (CRUD) | 69 | 低 |
| `plugin_system/loader.py` | 动态模块加载 | 112 | 中 |
| `plugin_system/manager.py` | 插件生命周期管理 | 253 | 高 |
| `plugin_system/exceptions.py` | 插件异常定义 | 51 | 低 |
| `security/sandbox.py` | 安全沙箱 (权限/资源) | 257 | 高 |
| `security/policy.py` | 安全策略配置 | 29 | 低 |
| `security/audit.py` | 审计日志记录 | 50 | 低 |
| `data_access/models.py` | SQLAlchemy 模型 | 215 | 中 |
| `data_access/connection.py` | 数据库连接管理 | 126 | 中 |
| `data_access/repository.py` | 通用仓储模式 | 194 | 中 |
| `observability/metrics.py` | OTel SDK 指标 (Prometheus 适配) | 171 | 高 |
| `utils/config.py` | 配置加载 (YAML) | 28 | 低 |
| `utils/exceptions.py` | 通用异常层次 | 51 | 低 |
| `utils/logging.py` | 结构化日志配置 | 15 | 低 |
| `utils/metrics.py` | OTel 便捷 API | 53 | 低 |

**总计**: 16 个模块, ~1,709 行核心代码
