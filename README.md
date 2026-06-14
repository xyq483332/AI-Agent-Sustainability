# AI Agent Sustainable Evolution

> **🎉 项目状态: 全部里程碑完成 (M1~M4) ✅**  
> **📊 验收测试: 33/33 通过 (100%)**  
> **📅 完成日期: 2026-06-14**

A comprehensive system for building AI agents with sustainable evolution capabilities, including plugin system, security sandbox, observability stack, and CI/CD pipeline.

## 🚀 Features

### Core Components
- **Plugin System**: Modular architecture for extending AI agent capabilities
- **Security Sandbox**: Isolated execution environment with resource limits
- **Observability Stack**: Full monitoring, logging, and alerting
- **CI/CD Pipeline**: Automated testing, security scanning, and deployment

### Key Capabilities
- ✅ Plugin lifecycle management (load/execute/unload)
- ✅ Security validation and permission management
- ✅ OpenTelemetry observability (OTel SDK → OTLP → OTel Collector → Prometheus → Grafana)
- ✅ Automated testing and deployment
- ✅ Scalable architecture

## 📁 Project Structure

```
ai-agent-sustainability/
├── src/
│   ├── api/              # FastAPI REST API
│   ├── plugins/          # Plugin system implementation
│   ├── security/         # Security sandbox
│   ├── observability/    # OpenTelemetry metrics (OTel SDK)
│   └── cicd/             # CI/CD utilities
├── tests/
│   ├── unit/             # Unit tests (InMemoryMetricReader)
│   ├── integration/      # Integration tests
│   ├── acceptance/       # Acceptance tests (AC-verified)
│   └── security/         # Security tests
├── config/
│   ├── otel-collector-config.yaml  # OTel Collector pipeline
│   ├── prometheus.yml              # Prometheus scrape config
│   ├── alert_rules.yml             # Alert rules (7 rules)
│   ├── plugin_template.json        # Plugin metadata template
│   └── init.sql                    # PostgreSQL schema
├── docs/                 # Documentation
│   ├── ac/               # Acceptance criteria
│   ├── architecture/     # Architecture docs + ADRs
│   └── api/              # API documentation
└── .github/workflows/    # GitHub Actions CI/CD
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- PostgreSQL
- Redis

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/ai-agent-sustainability.git
   cd ai-agent-sustainability
   ```

2. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Run the application**
   ```bash
   python -m src.main
   ```

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t ai-agent-sustainability .
   ```

2. **Run the container**
   ```bash
   docker run -p 8080:8080 ai-agent-sustainability
   ```

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/unit/ -v
```

### Run Integration Tests
```bash
pytest tests/integration/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## 📊 Monitoring (OpenTelemetry)

### Data Flow
```
App (OTel SDK) → OTLP gRPC → OTel Collector → Prometheus → Grafana
```

### Access Services
- **API**: http://localhost:8080
- **OTel Collector**: OTLP gRPC on `:4317`, Prometheus export on `:8889`
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### Metrics Available
- `plugin_load_duration_ms` — Plugin load time (Histogram)
- `plugin_execution_duration_ms` — Plugin execution time (Histogram)
- `plugin_execution_total` — Plugin execution count (Counter)
- `security_validation_duration_ms` — Security validation time (Histogram)
- `plugin_memory_usage_mb` — Plugin memory usage (Gauge)

### Configuration
- OTel Collector: `config/otel-collector-config.yaml`
- Prometheus: `config/prometheus.yml`
- Alert Rules: `config/alert_rules.yml` (7 rules)

## 🔒 Security

### Security Features
- Plugin sandboxing with resource limits
- Permission-based access control
- Audit logging for all operations
- Security scanning in CI/CD

### Security Configuration
See [Security Requirements](docs/security/security_requirements.md) for detailed security configuration.

## 📚 Documentation

- [System Architecture](docs/architecture/system_architecture.md)
- [Database Schema](docs/architecture/database_schema.md)
- [API Specification](docs/api/api_specification.md)
- [Plugin System AC](docs/ac/plugin_system_ac.md)

## 🚦 CI/CD Pipeline

The CI/CD pipeline includes:
1. **Code Quality**: Linting, type checking, formatting
2. **Testing**: Unit, integration, and security tests
3. **Security Scanning**: Dependency and container scanning
4. **Build**: Docker image creation
5. **Deploy**: Automated deployment to staging/production

## 📈 Metrics

### Key Performance Indicators
- Plugin load time: ≤ 500ms
- Plugin execution overhead: ≤ 50ms
- Test coverage: ≥ 85%
- Security scan pass rate: 100%

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team at dev@starkindustries.com

## 🎯 Roadmap

- [ ] Plugin marketplace
- [ ] Advanced security features
- [ ] Performance optimization
- [ ] Multi-language support
- [ ] Cloud deployment guides
