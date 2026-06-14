# System Architecture

**状态**: ✅ 已实施  
**日期**: 2026-06-14  
**版本**: 1.0

---

## 1. 架构概览

AI Agent Sustainable Evolution 系统采用**模块化微服务架构**，由四个核心子系统组成：插件系统、安全沙箱、可观测性栈、CI/CD 流水线。

```
                        ┌──────────────────────────────────────────┐
                        │              API Gateway                  │
                        │         FastAPI (:8080)                  │
                        └──────┬───────────────┬───────────────────┘
                               │               │
                 ┌─────────────▼──┐    ┌───────▼─────────────┐
                 │  Plugin System │    │  Security Sandbox    │
                 │  ┌───────────┐ │    │  ┌────────────────┐  │
                 │  │ Manager   │ │    │  │ Resource Limits │  │
                 │  │ Registry  │ │◄──►│  │ File ACL        │  │
                 │  │ Loader    │ │    │  │ Network ACL     │  │
                 │  └───────────┘ │    │  │ Audit Log       │  │
                 └────────┬───────┘    │  └────────────────┘  │
                          │            └───────────┬───────────┘
                          │                        │
              ┌───────────▼────────────────────────▼──────────┐
              │              Observability Stack               │
              │  OTel SDK → OTLP → OTel Collector → Prometheus│
              └──────────────────────┬────────────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │      Grafana        │
                          │  Visual Dashboards  │
                          └─────────────────────┘
```

## 2. 子系统详细设计

### 2.1 Plugin System (`src/plugins/`)

**职责**: 管理 AI Agent 插件的完整生命周期。

| 组件 | 文件 | 职责 |
|:---|:---|:---|
| `PluginBase` | `base.py` | 抽象基类，定义插件接口 (load/execute/unload) |
| `PluginManager` | `manager.py` | 注册、加载、执行、卸载插件 |

**关键数据结构**:
- `PluginMetadata`: 插件元数据 (name, version, permissions, dependencies)
- `PluginStatus`: 枚举 (pending, active, error, disabled)

**设计约束**:
- 插件执行必须通过 `SecuritySandbox` 沙箱隔离
- 所有操作产生 OpenTelemetry 指标
- 插件加载时间 ≤ 500ms

### 2.2 Security Sandbox (`src/security/`)

**职责**: 为插件提供隔离执行环境，防止恶意行为。

| 能力 | 实现 | 说明 |
|:---|:---|:---|
| 资源限制 | CPU/Memory/Timeout | 防止资源耗尽攻击 |
| 文件系统访问控制 | 白名单路径 | 仅允许访问指定目录 |
| 网络访问控制 | CIDR 白名单 | 仅允许访问指定网络 |
| 权限验证 | Permission 系统 | 危险权限需显式批准 |
| 审计日志 | 结构化日志 | 记录所有安全相关操作 |

**安全策略等级**:
- `standard`: 默认策略，限制基本资源
- `elevated`: 允许更多网络访问
- `restricted`: 最严格限制，禁止所有外部访问

### 2.3 Observability Stack (`src/observability/`)

**职责**: 提供完整的可观测性能力（指标、日志、追踪）。

**数据流** (已验证 2026-06-14):
```
App (OTel SDK)
  ↓ OTLP gRPC/HTTP (:4317/:4318)
OTel Collector (contrib 0.102.0)
  ↓ memory_limiter → batch → resource processor
Prometheus Exporter (:8889)
  ↓ Prometheus scrape
Prometheus (:9090)
  ↓ PromQL query
Grafana (:3000)
```

**核心指标**:
| 指标名 | 类型 | 说明 |
|:---|:---:|:---|
| `plugin_execution_total` | Counter | 插件执行次数 |
| `plugin_execution_duration_ms` | Histogram | 插件执行耗时 |
| `plugin_load_duration_ms` | Histogram | 插件加载耗时 |
| `plugin_memory_usage_mb` | Gauge | 插件内存使用 |
| `security_validation_total` | Counter | 安全验证次数 |

### 2.4 CI/CD Pipeline (`.github/workflows/`)

**职责**: 自动化测试、安全扫描、构建和部署。

```
Code Push → Lint → Type Check → Unit Tests → Security Scan → Build Docker → Deploy
```

## 3. 数据架构

### 3.1 数据库 (PostgreSQL)

| 表 | 用途 | 关键字段 |
|:---|:---|:---|
| `plugins` | 插件注册表 | id, name, version, status, metadata |
| `plugin_dependencies` | 插件依赖关系 | plugin_id, dependency_id, version_constraint |
| `users` | 用户账户 | id, username, email, status |
| `roles` | 角色定义 | id, name, permissions (JSONB) |
| `user_roles` | 用户-角色关联 | user_id, role_id |
| `audit_logs` | 审计日志 | user_id, action, resource_type, details |
| `security_events` | 安全事件 | event_type, severity, plugin_id, resolved |

### 3.2 缓存 (Redis)

- 插件元数据缓存
- 会话管理
- 速率限制计数器

## 4. 部署架构

### 4.1 Docker Compose (本地开发)

```
┌─────────────────────────────────────────────────┐
│              docker-compose.yml                  │
├─────────────┬─────────────┬─────────────────────┤
│ plugin-system│ sec-sandbox │ otel-collector      │
│   :8080     │   :8081     │ :4317 :4318 :8889   │
├─────────────┴─────────────┴─────────────────────┤
│         PostgreSQL :5432    Redis :6379          │
├─────────────────────────────────────────────────┤
│  Prometheus :9090        Grafana :3000           │
└─────────────────────────────────────────────────┘
```

### 4.2 NAS 部署 (生产环境)

| 容器 | 端口 | 网络模式 | 说明 |
|:---|:---:|:---|:---|
| `ten-agent-otel-collector` | 4317, 4318, 8889, 8881 | host | OTel Collector |
| `ten-agent-prometheus` | 9090 | monitoring_ten-agent-monitoring | 指标采集 |
| `ten-agent-grafana` | 3000 | monitoring_ten-agent-monitoring | 可视化 |
| `ten-agent-node-exporter` | 9100 | monitoring_ten-agent-monitoring | 主机指标 |
| `ten-agent-knowledge-metrics` | 9103 | monitoring_ten-agent-monitoring | 知识指标 |

## 5. 安全架构

详见 [Security Requirements](../security/security_requirements.md)

### 5.1 安全边界

```
Internet → [Firewall] → NAS Docker Host → [Container Isolation] → App
```

### 5.2 关键安全控制

- **网络隔离**: 容器通过 Docker network 隔离
- **权限最小化**: 插件仅获得必要权限
- **输入验证**: 所有 API 输入经过验证
- **审计日志**: 所有安全操作记录到数据库
- **密钥管理**: 敏感配置通过 Docker secrets 或环境变量注入

## 6. 可扩展性设计

### 6.1 水平扩展
- 插件系统无状态，可多实例部署
- OTel Collector 支持多实例 + 负载均衡
- Prometheus 支持联邦 (Federation) 模式

### 6.2 垂直扩展
- 插件资源限制可通过配置调整
- 数据库连接池可动态调整
- OTel Collector 内存限制可按需增大

## 7. 关键 ADR 索引

| ADR | 决策 | 状态 |
|:---|:---|:---:|
| [ADR-001](adrs/adr-001-plugin-system-design.md) | 插件系统设计 | ✅ |
| [ADR-002](adrs/adr-002-security-sandbox-design.md) | 安全沙箱设计 | ✅ |
| [ADR-003](adrs/adr-003-observability-stack-design.md) | 可观测性栈设计 | ✅ |
| [ADR-004](adrs/adr-004-cicd-pipeline-design.md) | CI/CD 流水线设计 | ✅ |
