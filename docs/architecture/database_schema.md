# Database Schema

**状态**: ✅ 已实施  
**日期**: 2026-06-14  
**数据库**: PostgreSQL 15  
**初始化脚本**: `config/init.sql`

---

## 1. ER 图

```
┌──────────────┐       ┌───────────────────┐       ┌──────────────┐
│    users     │       │    user_roles     │       │    roles     │
├──────────────┤       ├───────────────────┤       ├──────────────┤
│ id (PK)      │◄──┐   │ user_id (FK,PK)   │   ┌──►│ id (PK)      │
│ username     │   └───│ role_id (FK,PK)   │───┘   │ name         │
│ email        │       │ granted_at        │       │ description  │
│ password_hash│       │ granted_by (FK)   │       │ permissions  │
│ status       │       └───────────────────┘       │ created_at   │
│ created_at   │                                   └──────────────┘
│ last_login   │
│ metadata     │
└──────┬───────┘
       │
       │ user_id
       ▼
┌──────────────┐       ┌───────────────────┐       ┌──────────────┐
│ audit_logs   │       │   plugins         │       │ plugin_deps  │
├──────────────┤       ├───────────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)           │◄──────│ plugin_id(FK)│
│ user_id (FK) │       │ name              │       │ dependency_id│
│ action       │       │ version           │       │ version_con  │
│ resource_type│       │ description       │       │ required     │
│ resource_id  │       │ module_path       │       │ created_at   │
│ details      │       │ author_id (FK)    │       └──────────────┘
│ ip_address   │       │ status            │
│ user_agent   │       │ created_at        │
│ created_at   │       │ updated_at        │
└──────────────┘       │ metadata          │
                       └──────┬────────────┘
                              │
                              │ plugin_id
                              ▼
                       ┌───────────────────┐
                       │ security_events   │
                       ├───────────────────┤
                       │ id (PK)           │
                       │ event_type        │
                       │ severity          │
                       │ plugin_id (FK)    │
                       │ user_id (FK)      │
                       │ details           │
                       │ resolved          │
                       │ resolved_by (FK)  │
                       │ resolved_at       │
                       │ created_at        │
                       └───────────────────┘
```

## 2. 表结构

### 2.1 plugins

插件注册表，存储所有已注册插件的元数据。

| 列名 | 类型 | 约束 | 说明 |
|:---|:---|:---|:---|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | 主键 |
| `name` | VARCHAR(100) | NOT NULL | 插件名称 |
| `version` | VARCHAR(20) | NOT NULL | 语义版本号 |
| `description` | TEXT | - | 插件描述 |
| `module_path` | VARCHAR(500) | NOT NULL | Python 模块路径 |
| `author_id` | UUID | FK → users(id) | 作者 |
| `status` | VARCHAR(20) | DEFAULT 'pending' | 状态: pending/active/error/disabled |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |
| `metadata` | JSONB | - | 扩展元数据 (permissions, dependencies, limits) |

**约束**: UNIQUE(name, version)

**索引**: idx_plugins_name, idx_plugins_status, idx_plugins_metadata (GIN)

### 2.2 plugin_dependencies

插件依赖关系表。

| 列名 | 类型 | 约束 | 说明 |
|:---|:---|:---|:---|
| `id` | UUID | PK | 主键 |
| `plugin_id` | UUID | FK → plugins(id) ON DELETE CASCADE | 依赖方 |
| `dependency_id` | UUID | FK → plugins(id) | 被依赖方 |
| `version_constraint` | VARCHAR(50) | - | 版本约束 (如 `>=1.0.0`) |
| `required` | BOOLEAN | DEFAULT true | 是否必须 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 2.3 users

用户账户表。

| 列名 | 类型 | 约束 | 说明 |
|:---|:---|:---|:---|
| `id` | UUID | PK | 主键 |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL | 邮箱 |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt 密码哈希 |
| `status` | VARCHAR(20) | DEFAULT 'active' | 状态: active/inactive/locked |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 注册时间 |
| `last_login` | TIMESTAMP | - | 最后登录时间 |
| `metadata` | JSONB | - | 扩展信息 |

### 2.4 roles

角色定义表。

| 列名 | 类型 | 约束 | 说明 |
|:---|:---|:---|:---|
| `id` | UUID | PK | 主键 |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | 角色名 |
| `description` | TEXT | - | 角色描述 |
| `permissions` | JSONB | - | 权限列表 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**预定义角色**:
- `admin`: 所有权限
- `plugin_developer`: plugin:read, plugin:write, plugin:execute
- `user`: plugin:read, plugin:execute

### 2.5 user_roles

用户-角色关联表 (多对多)。

| 列名 | 类型 | 约束 | 说明 |
|:---|:---|:---|:---|
| `user_id` | UUID | FK → users(id) ON DELETE CASCADE, PK | 用户 |
| `role_id` | UUID | FK → roles(id) ON DELETE CASCADE, PK | 角色 |
| `granted_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 授权时间 |
| `granted_by` | UUID | FK → users(id) | 授权人 |

### 2.6 audit_logs

审计日志表，记录所有安全相关操作。

| 列名 | 类型 | 约束 | 说明 |
|:---|:---|:---|:---|
| `id` | UUID | PK | 主键 |
| `user_id` | UUID | FK → users(id) | 操作用户 |
| `action` | VARCHAR(50) | NOT NULL | 操作类型 |
| `resource_type` | VARCHAR(50) | - | 资源类型 |
| `resource_id` | UUID | - | 资源 ID |
| `details` | JSONB | - | 操作详情 |
| `ip_address` | INET | - | 客户端 IP |
| `user_agent` | TEXT | - | 客户端 UA |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 操作时间 |

**索引**: idx_audit_user, idx_audit_action, idx_audit_resource, idx_audit_created

### 2.7 security_events

安全事件表。

| 列名 | 类型 | 约束 | 说明 |
|:---|:---|:---|:---|
| `id` | UUID | PK | 主键 |
| `event_type` | VARCHAR(50) | NOT NULL | 事件类型 |
| `severity` | VARCHAR(20) | NOT NULL | 严重级别: critical/high/medium/low |
| `plugin_id` | UUID | FK → plugins(id) | 关联插件 |
| `user_id` | UUID | FK → users(id) | 关联用户 |
| `details` | JSONB | - | 事件详情 |
| `resolved` | BOOLEAN | DEFAULT false | 是否已解决 |
| `resolved_by` | UUID | FK → users(id) | 解决人 |
| `resolved_at` | TIMESTAMP | - | 解决时间 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 发生时间 |

**索引**: idx_security_event_type, idx_security_severity, idx_security_plugin

## 3. JSONB 字段结构

### 3.1 plugins.metadata

```json
{
  "permissions": ["plugin:read", "plugin:execute", "network:access"],
  "dependencies": ["base-plugin>=1.0.0"],
  "resource_limits": {
    "max_memory_mb": 256,
    "max_execution_time_s": 30,
    "max_cpu_cores": 1.0
  },
  "tags": ["ai", "nlp", "data-processing"],
  "license": "Apache-2.0"
}
```

### 3.2 roles.permissions

```json
{
  "plugin:read": true,
  "plugin:write": false,
  "plugin:execute": true,
  "network:access": false,
  "file:read": false,
  "file:write": false,
  "system:admin": false
}
```

### 3.3 audit_logs.details

```json
{
  "plugin_name": "my-plugin",
  "plugin_version": "1.0.0",
  "execution_duration_ms": 150,
  "success": true,
  "resource_usage": {
    "memory_mb": 64,
    "cpu_percent": 15
  }
}
```

## 4. 索引策略

| 表 | 索引 | 类型 | 用途 |
|:---|:---|:---:|:---|
| plugins | idx_plugins_name | B-tree | 按名称查询 |
| plugins | idx_plugins_status | B-tree | 按状态过滤 |
| plugins | idx_plugins_metadata | GIN | JSONB 字段查询 |
| audit_logs | idx_audit_user | B-tree | 按用户查询 |
| audit_logs | idx_audit_action | B-tree | 按操作类型查询 |
| audit_logs | idx_audit_resource | B-tree | 按资源查询 |
| audit_logs | idx_audit_created | B-tree | 按时间范围查询 |
| security_events | idx_security_event_type | B-tree | 按事件类型查询 |
| security_events | idx_security_severity | B-tree | 按严重级别过滤 |
| security_events | idx_security_plugin | B-tree | 按插件查询 |
