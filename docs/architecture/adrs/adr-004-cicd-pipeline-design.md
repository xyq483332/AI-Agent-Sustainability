# ADR-004: CI/CD Pipeline Design

**状态**: ✅ 已实施  
**日期**: 2026-06-14  
**决策者**: CTO, DevOps Lead

---

## 背景

项目需要自动化构建、测试、部署流程，确保代码质量和交付速度。核心需求：
- 自动化测试（单元/集成/验收）
- 容器化构建（Docker）
- 安全扫描（漏洞检测）
- 多环境部署（开发/预发布/生产）
- 可观测性集成（OTel 指标）

## 决策

采用 **GitHub Actions** 作为 CI/CD 平台，构建完整的自动化流水线。

### 流水线架构

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions                            │
│                                                             │
│  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   │
│  │Build │──►│ Test │──►│ Scan │──►│Push  │──►│Deploy│   │
│  │      │   │      │   │      │   │      │   │      │   │
│  │Docker│   │Unit  │   │Trivy │   │GHCR  │   │NAS   │   │
│  │Build │   │Integ │   │Snyk  │   │      │   │      │   │
│  └──────┘   │Accept│   └──────┘   └──────┘   └──────┘   │
│             └──────┘                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Deployment Target                        │
│                    NAS (192.168.1.3)                        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Plugin      │  │  OTel        │  │  Security    │    │
│  │  System      │  │  Collector   │  │  Sandbox     │    │
│  │  :8080       │  │  :4317/:8889 │  │  :8081       │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 备选方案

### 1. GitHub Actions (选中)
- **Pros**: 托管服务，易于设置，免费额度充足
- **Cons**: 供应商锁定，自定义有限
- **Decision**: 采用，简单高效

### 2. Third-party CI/CD (GitLab CI, Jenkins)
- **Pros**: 更多自定义选项，可自托管
- **Cons**: 运维成本高，配置复杂
- **Decision**: 拒绝，复杂度过高

### 3. Custom CI/CD System
- **Pros**: Complete customization, no vendor lock-in
- **Cons**: High development and maintenance cost
- **Decision**: Rejected for cost reasons

## 实现

### 工作流文件

| 文件 | 触发条件 | 用途 |
|:---|:---|:---|
| `.github/workflows/ci.yml` | push/PR to main | 完整 CI 流水线 |
| `.github/workflows/cd.yml` | push to main | 部署流水线 |
| `.github/workflows/security.yml` | 定时 (每日) | 安全扫描 |

### CI 流水线步骤

| 阶段 | 步骤 | 工具 |
|:---|:---|:---|
| Build | Docker 构建 | docker build |
| Test | 单元测试 | pytest --cov |
| Test | 集成测试 | pytest tests/integration/ |
| Test | 验收测试 | pytest tests/acceptance/ |
| Scan | 漏洞扫描 | trivy image |
| Scan | 依赖检查 | safety check |
| Push | 推送镜像 | docker push GHCR |
| Deploy | 部署到 NAS | SSH + docker pull |

### 部署策略

| 环境 | 分支 | 策略 | 目标 |
|:---|:---|:---|:---|
| Development | feature/* | 手动触发 | 本地 Docker Compose |
| Production | main | 自动推送后触发 | NAS Docker |

## 实施计划

### Phase 1: Basic Pipeline (Week 1-2)
- GitHub Actions setup
- Basic testing integration
- Container building
- Initial deployment

### Phase 2: Advanced Features (Week 3-4)
- Security scanning
- Performance testing
- Advanced deployment strategies
- Monitoring integration

### Phase 3: Optimization (Week 5-6)
- Pipeline optimization
- Advanced security features
- Compliance automation
- Documentation

## 后果

### 正面
- ✅ 全自动化构建-测试-部署
- ✅ 代码质量保障（测试覆盖率、安全扫描）
- ✅ 快速反馈（< 10 分钟完成 CI）
- ✅ 可审计（每次部署有记录）

### 负面
- ⚠️ 供应商锁定（GitHub）
- ⚠️ 私有 Runner 需要维护
- ⚠️ 敏感信息需通过 Secrets 管理

## 参考

- CI/CD Pipeline AC: docs/ac/cicd_pipeline_ac.md
- System Architecture: docs/architecture/system_architecture.md
- Security Requirements: docs/security/security_requirements.md
- Workflow Config: .github/workflows/
