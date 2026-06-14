# ADR-001: Plugin System Design

**状态**: ✅ 已实施  
**日期**: 2026-06-14  
**决策者**: CTO, CPO

---

## 背景

系统需要支持第三方插件的动态加载和执行，以实现可持续迭代能力。核心需求：
- 插件热加载/卸载（无需重启）
- 安全隔离（权限控制、资源限制）
- 依赖管理（插件间依赖）
- 版本控制（语义版本号）
- 可观测性（执行指标、审计日志）

## 决策

采用**模块级插件 + 安全沙箱**架构，而非容器级隔离。

### 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                    │
│                  /api/v1/plugins/*                       │
└──────────┬──────────────────────────────────┬────────────┘
           │                                  │
           ▼                                  ▼
┌──────────────────────┐        ┌──────────────────────────┐
│   PluginManager      │        │   SecuritySandbox        │
│                      │───────►│                          │
│  - execute_plugin()  │        │  - validate_plugin()     │
│  - load_plugin()     │        │  - check_network()       │
│  - unload_plugin()   │        │  - check_file_access()   │
└──────────┬───────────┘        │  - log_security_event()  │
           │                    └──────────────────────────┘
           ▼
┌──────────────────────┐        ┌──────────────────────────┐
│   PluginLoader       │        │   PluginRegistry         │
│                      │───────►│                          │
│  - load_module()     │        │  - register_plugin()     │
│  - instantiate()     │        │  - get_plugin_info()     │
│  - validate()        │        │  - list_plugins()        │
└──────────────────────┘        └──────────┬───────────────┘
                                           │
                                           ▼
                                ┌──────────────────────────┐
                                │   PostgreSQL Database    │
                                │   plugins table          │
                                └──────────────────────────┘
```

### 核心设计原则

| 原则 | 实现 |
|:---|:---|
| 抽象基类 | `PluginBase(ABC)` 定义统一接口 |
| 依赖注入 | FastAPI Depends 注入管理器/沙箱 |
| 单一职责 | Manager/Loader/Registry/Sandbox 各司其职 |
| 开闭原则 | 新插件无需修改核心代码 |

## 备选方案

### 1. 进程内模块加载 (选中)
- **优点**: 低延迟 (~10ms 加载)，低资源开销，简单部署
- **缺点**: 隔离性弱于容器，依赖 Python GIL
- **适用**: 标准插件，信任级别较高

### 2. Microservices Architecture
- **Pros**: Better isolation, independent scaling
- **Cons**: Higher complexity, network overhead
- **Decision**: Partially adopted - plugin execution is microservice-like

### 3. Container-based Plugins
- **Pros**: Complete isolation, resource control
- **Cons**: Higher overhead, slower startup
- **Decision**: Rejected for standard plugins, available for high-security needs

## 实现

### 核心类

| 类 | 职责 | 行数 |
|:---|:---|---:|
| `PluginBase` | 插件抽象基类 (ABC) | 35 |
| `PluginRegistry` | 插件注册表 (CRUD) | 69 |
| `PluginLoader` | 动态模块加载 | 112 |
| `PluginManager` | 生命周期管理 | 253 |
| `SecuritySandbox` | 权限/资源验证 | 257 |

### 插件接口

```python
class PluginBase(ABC):
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行插件逻辑"""
        pass

    def get_metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        pass

    def initialize(self, context: Dict[str, Any]) -> None:
        """初始化插件"""
        pass

    def cleanup(self) -> None:
        """清理资源"""
        pass
```

## 实施计划

### Phase 1: Core Plugin System (Week 1-2)
- Plugin loader and registry
- Basic security sandbox
- Metadata validation
- Initial test suite

### Phase 2: Advanced Features (Week 3-4)
- Dependency management
- Version control
- Performance monitoring
- Security auditing

### Phase 3: Optimization (Week 5-6)
- Performance tuning
- Scalability improvements
- Advanced security features
- Documentation and examples

## 后果

### 正面
- ✅ 插件加载延迟极低 (~10ms)
- ✅ 统一接口，易于开发新插件
- ✅ 安全沙箱提供基本隔离
- ✅ 依赖注入便于测试

### 负面
- ⚠️ 进程内隔离有限，恶意插件可能影响宿主
- ⚠️ 单点故障风险（所有插件在同一进程）
- ⚠️ Python GIL 限制并发

## 参考

- Plugin System AC: docs/ac/plugin_system_ac.md
- Security Requirements: docs/security/security_requirements.md
- API Specification: docs/api/api_specification.md
- Implementation: src/plugin_system/
