# ADR-002: Security Sandbox Design

**状态**: ✅ 已实施  
**日期**: 2026-06-14  
**决策者**: CTO, Security Director

---

## 背景

插件系统允许加载和执行第三方代码，这带来了严重的安全风险：
- 恶意插件可能窃取数据或破坏系统
- 有缺陷的插件可能耗尽系统资源
- 插件可能尝试越权访问文件系统或网络

需要一个隔离执行环境来保护宿主系统。

## 决策

采用**多层沙箱隔离**策略，而非操作系统级容器隔离。

### 架构设计

```
┌─────────────────────────────────────────────────┐
│              SecuritySandbox                     │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Resource │  │ File ACL │  │ Network ACL  │  │
│  │ Limiter  │  │          │  │              │  │
│  │ ─ CPU    │  │ ─ Read   │  │ ─ CIDR白名单 │  │
│  │ ─ Memory │  │ ─ Write  │  │ ─ 端口限制   │  │
│  │ ─ Time   │  │ ─ Exec   │  │ ─ 协议限制   │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │Permission│  │  Audit   │  │   Process    │  │
│  │ Validator│  │  Logger  │  │   Guard      │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────┘
```

### 关键设计

| 组件 | 实现 | 说明 |
|:---|:---|:---|
| `validate_plugin()` | 权限验证 | 检查插件声明的权限是否被批准 |
| `check_network_access()` | CIDR 匹配 | 验证目标 IP 是否在白名单内 |
| `check_file_access()` | 路径前缀匹配 | 验证文件路径是否在允许目录内 |
| `log_security_event()` | 结构化日志 | 记录所有安全相关操作 |

## 备选方案

### 方案 A: 进程内沙箱 (选中)
- **优点**: 低延迟 (~1ms)，低资源开销，简单部署
- **缺点**: 隔离性弱于容器，依赖 Python 进程内控制
- **适用**: 标准插件执行

### 方案 B: Docker 容器隔离
- **优点**: 强隔离 (namespace + cgroup)，完全资源隔离
- **缺点**: 高延迟 (~100ms 启动)，高资源开销，部署复杂
- **适用**: 高安全需求插件 (未来扩展)

### 方案 C: WebAssembly 沙箱
- **优点**: 接近原生性能，强隔离，语言中立
- **缺点**: 生态不成熟，Python 支持有限
- **适用**: 高性能安全执行 (长期探索)

## 实现

### 核心类: `SecuritySandbox`

```python
class SecuritySandbox:
    def __init__(self, config: SandboxConfig):
        self.approved_dangerous_permissions = config.approved_dangerous
        self.network_whitelist = config.network_whitelist
        self.file_whitelist = config.file_whitelist

    def validate_plugin(self, plugin_metadata) -> bool:
        """验证插件权限是否被批准"""

    def check_network_access(self, target_ip: str) -> bool:
        """检查网络访问权限 (CIDR 匹配)"""

    def check_file_access(self, file_path: str, mode: str) -> bool:
        """检查文件访问权限"""

    def log_security_event(self, event_type: str, severity: str, details: dict):
        """记录安全事件"""
```

### 安全策略配置

```python
@dataclass
class SandboxConfig:
    max_cpu_cores: float = 1.0
    max_memory_mb: int = 256
    max_execution_time_s: int = 30
    approved_dangerous: list = field(default_factory=list)
    network_whitelist: list = field(default_factory=lambda: ["127.0.0.1/32"])
    file_whitelist: list = field(default_factory=lambda: ["/tmp/plugins/"])
```

## 后果

### 正面
- ✅ 插件执行延迟极低 (~1ms 验证开销)
- ✅ 资源限制有效防止 DoS
- ✅ 审计日志满足合规要求
- ✅ 实现简单，易于维护

### 负面
- ⚠️ Python 进程内隔离有限，无法阻止 GIL 绕过
- ⚠️ 文件系统 ACL 依赖路径前缀匹配，符号链接可能绕过
- ⚠️ 未来高安全需求可能需要升级到容器隔离

### 风险缓解
- 网络 ACL 使用 `ipaddress` 模块的 CIDR 匹配，避免路径遍历
- 审计日志写入独立文件 + 数据库，防篡改
- 预留 Docker 容器隔离作为未来升级路径

## 验证

### 测试覆盖
- `test_sandbox_validate_plugin`: 权限验证
- `test_sandbox_validate_plugin_with_dangerous_permissions`: 危险权限拒绝
- `test_sandbox_validate_plugin_with_approved_dangerous_permissions`: 已批准危险权限
- `test_sandbox_network_whitelist`: 网络白名单
- `test_sandbox_file_whitelist`: 文件白名单
- `test_sandbox_audit_log`: 审计日志

### 验收结果
- 7/7 安全沙箱测试通过 ✅
- 8/8 安全沙箱 AC 验收通过 ✅

## 参考

- Security Requirements: `docs/security/security_requirements.md`
- Security Sandbox AC: `docs/ac/security_sandbox_ac.md`
- Implementation: `src/security/sandbox.py`
