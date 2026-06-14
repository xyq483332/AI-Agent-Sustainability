# API Specification

**状态**: ✅ 已实施  
**日期**: 2026-06-14  
**基础路径**: `/api/v1`  
**框架**: FastAPI (自动生成 OpenAPI 文档)

---

## 1. 概览

| 属性 | 值 |
|:---|:---|
| 协议 | HTTP/HTTPS |
| 数据格式 | JSON |
| 认证 | JWT Bearer Token / API Key |
| 版本 | v1 |
| 基础 URL | `http://localhost:8080/api/v1` |

## 2. 端点列表

### 2.1 插件管理

| 方法 | 路径 | 说明 | 认证 |
|:---|:---|:---|:---:|
| `GET` | `/plugins` | 列出所有插件 | ✅ |
| `GET` | `/plugins/{plugin_id}` | 获取插件详情 | ✅ |
| `POST` | `/plugins` | 注册新插件 | ✅ |
| `PUT` | `/plugins/{plugin_id}` | 更新插件 | ✅ |
| `DELETE` | `/plugins/{plugin_id}` | 删除插件 | ✅ |
| `POST` | `/plugins/{plugin_id}/execute` | 执行插件 | ✅ |
| `POST` | `/plugins/{plugin_id}/load` | 加载插件 | ✅ |
| `POST` | `/plugins/{plugin_id}/unload` | 卸载插件 | ✅ |

### 2.2 安全

| 方法 | 路径 | 说明 | 认证 |
|:---|:---|:---|:---:|
| `POST` | `/auth/login` | 用户登录 | ❌ |
| `POST` | `/auth/refresh` | 刷新 Token | ✅ |
| `GET` | `/users/me` | 获取当前用户 | ✅ |

### 2.3 监控

| 方法 | 路径 | 说明 | 认证 |
|:---|:---|:---|:---:|
| `GET` | `/metrics` | Prometheus 格式指标 | ❌ |
| `GET` | `/health` | 健康检查 | ❌ |

## 3. 数据模型

### 3.1 Plugin

```json
{
  "id": "uuid",
  "name": "string",
  "version": "string",
  "description": "string",
  "module_path": "string",
  "status": "pending|active|error|disabled",
  "author_id": "uuid",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "metadata": {
    "permissions": ["plugin:read", "plugin:execute"],
    "dependencies": [],
    "resource_limits": {
      "max_memory_mb": 256,
      "max_execution_time_s": 30
    }
  }
}
```

### 3.2 PluginExecutionRequest

```json
{
  "parameters": {
    "key": "value"
  },
  "timeout_s": 30
}
```

### 3.3 PluginExecutionResponse

```json
{
  "success": true,
  "result": {},
  "duration_ms": 150,
  "metrics": {
    "execution_count": 1,
    "last_execution": "2026-01-01T00:00:00Z"
  }
}
```

### 3.4 ErrorResponse

```json
{
  "error": "string",
  "detail": "string",
  "code": "PLUGIN_NOT_FOUND|VALIDATION_ERROR|PERMISSION_DENIED"
}
```

## 4. 详细端点说明

### 4.1 列出插件

```
GET /plugins
```

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|:---|:---|:---|:---|
| `status` | string | - | 按状态过滤 |
| `limit` | int | 20 | 返回数量上限 |
| `offset` | int | 0 | 偏移量 |

**响应** (200):
```json
{
  "plugins": [Plugin],
  "total": 10,
  "limit": 20,
  "offset": 0
}
```

### 4.2 执行插件

```
POST /plugins/{plugin_id}/execute
```

**请求体**: `PluginExecutionRequest`

**响应** (200): `PluginExecutionResponse`

**错误响应**:

| 状态码 | 说明 |
|:---:|:---|
| 404 | 插件不存在 |
| 403 | 权限不足 |
| 408 | 执行超时 |
| 422 | 参数验证失败 |
| 500 | 内部错误 |

### 4.3 Prometheus 指标

```
GET /metrics
```

**响应** (200): Prometheus text format

```
# HELP plugin_execution_total Total plugin executions
# TYPE plugin_execution_total counter
plugin_execution_total{plugin="my-plugin",success="true"} 42
```

### 4.4 健康检查

```
GET /health
```

**响应** (200):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_s": 3600,
  "components": {
    "database": "connected",
    "cache": "connected",
    "sandbox": "ready"
  }
}
```

## 5. 错误码

| 错误码 | HTTP 状态码 | 说明 |
|:---|:---:|:---|
| `PLUGIN_NOT_FOUND` | 404 | 插件不存在 |
| `PLUGIN_LOAD_FAILED` | 500 | 插件加载失败 |
| `PLUGIN_EXECUTION_FAILED` | 500 | 插件执行失败 |
| `PLUGIN_TIMEOUT` | 408 | 插件执行超时 |
| `VALIDATION_ERROR` | 422 | 输入验证失败 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `RATE_LIMITED` | 429 | 请求频率超限 |
| `INTERNAL_ERROR` | 500 | 内部服务器错误 |

## 6. 速率限制

| 端点 | 限制 | 窗口 |
|:---|:---:|:---:|
| `/plugins/{id}/execute` | 100 req/min | 滑动窗口 |
| `/auth/login` | 10 req/min | 滑动窗口 |
| 其他端点 | 1000 req/min | 滑动窗口 |

## 7. SDK 示例

### Python

```python
import requests

BASE_URL = "http://localhost:8080/api/v1"
HEADERS = {"Authorization": "Bearer <token>"}

# 列出插件
resp = requests.get(f"{BASE_URL}/plugins", headers=HEADERS)
plugins = resp.json()["plugins"]

# 执行插件
resp = requests.post(
    f"{BASE_URL}/plugins/{plugin_id}/execute",
    headers=HEADERS,
    json={"parameters": {"input": "test"}}
)
result = resp.json()
```

### cURL

```bash
# 列出插件
curl -H "Authorization: Bearer <token>" http://localhost:8080/api/v1/plugins

# 执行插件
curl -X POST http://localhost:8080/api/v1/plugins/{id}/execute \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"input": "test"}}'
```
