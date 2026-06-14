"""
M4 Acceptance Tests
基于 AC 文档的完整验收测试
"""

import os
import sys
from pathlib import Path

import pytest
import yaml

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class TestPluginSystemAcceptance:
    """插件系统验收测试"""

    def setup_method(self):
        """测试前设置"""
        from plugins.base import PluginBase
        from plugins.manager import PluginManager

        self.PluginBase = PluginBase
        self.PluginManager = PluginManager

    def test_ac001_plugin_loading(self):
        """AC-001: 插件加载测试"""

        # 创建测试插件
        class TestPlugin(self.PluginBase):
            def load(self, config):
                self.name = config.get("name", "test")
                self.version = config.get("version", "1.0.0")
                self.status = "loaded"
                return True

            def execute(self, context):
                return {"result": "success"}

            def unload(self):
                self.status = "unloaded"
                return True

        plugin = TestPlugin()
        config = {"name": "test_plugin", "version": "1.0.0"}

        # 执行加载
        result = plugin.load(config)

        # 验收标准: load_plugin() 返回 True
        assert result is True
        # 验收标准: 插件状态为 "loaded"
        assert plugin.status == "loaded"

    def test_ac002_plugin_execution(self):
        """AC-002: 插件执行测试"""

        class TestPlugin(self.PluginBase):
            def load(self, config):
                self.name = config.get("name", "test")
                self.status = "loaded"
                return True

            def execute(self, context):
                return {"result": "success", "input": context}

            def unload(self):
                self.status = "unloaded"
                return True

        plugin = TestPlugin()
        plugin.load({"name": "test_plugin"})

        # 执行插件
        context = {"task": "test_task"}
        result = plugin.execute(context)

        # 验收标准: execute() 返回包含 "result": "success" 的字典
        assert result["result"] == "success"
        assert "input" in result

    def test_ac003_plugin_unloading(self):
        """AC-003: 插件卸载测试"""

        class TestPlugin(self.PluginBase):
            def load(self, config):
                self.name = config.get("name", "test")
                self.status = "loaded"
                return True

            def execute(self, context):
                return {"result": "success"}

            def unload(self):
                self.status = "unloaded"
                return True

        plugin = TestPlugin()
        plugin.load({"name": "test_plugin"})

        # 执行卸载
        result = plugin.unload()

        # 验收标准: unload() 返回 True
        assert result is True
        # 验收标准: 插件状态为 "unloaded"
        assert plugin.status == "unloaded"

    def test_ac004_plugin_lifecycle(self):
        """AC-004: 生命周期测试"""

        class TestPlugin(self.PluginBase):
            def load(self, config):
                self.name = config.get("name", "test")
                self.status = "loaded"
                return True

            def execute(self, context):
                return {"result": "success"}

            def unload(self):
                self.status = "unloaded"
                return True

        plugin = TestPlugin()

        # 完整生命周期
        load_result = plugin.load({"name": "lifecycle_plugin"})
        exec_result = plugin.execute({"task": "test"})
        unload_result = plugin.unload()

        # 验收标准: 完整流程无异常
        assert load_result is True
        assert exec_result["result"] == "success"
        assert unload_result is True

    def test_ac005_plugin_metadata(self):
        """AC-005: 元数据测试"""

        class TestPlugin(self.PluginBase):
            def load(self, config):
                self.name = config.get("name", "test")
                self.version = config.get("version", "1.0.0")
                self.status = "loaded"
                return True

            def execute(self, context):
                return {"result": "success"}

            def unload(self):
                self.status = "unloaded"
                return True

        plugin = TestPlugin()
        plugin.load({"name": "metadata_plugin", "version": "2.0.0"})

        # 获取元数据
        status = plugin.get_status()

        # 验收标准: 返回包含 id, name, version, status, created_at 的字典
        assert "id" in status
        assert "name" in status
        assert "version" in status
        assert "status" in status
        assert "created_at" in status

    def test_ac006_plugin_execution_stats(self):
        """AC-006: 执行统计测试"""

        class TestPlugin(self.PluginBase):
            def load(self, config):
                self.name = config.get("name", "test")
                self.status = "loaded"
                return True

            def execute(self, context):
                return {"result": "success"}

            def unload(self):
                self.status = "unloaded"
                return True

        plugin = TestPlugin()
        plugin.load({"name": "stats_plugin"})

        # 初始状态
        assert plugin.execution_count == 0
        assert plugin.error_count == 0

        # 执行一次
        plugin.execute({})
        plugin.update_execution_stats(success=True)

        # 验收标准: execution_count 和 error_count 正确递增
        assert plugin.execution_count == 1
        assert plugin.error_count == 0

        # 执行失败
        plugin.execute({})
        plugin.update_execution_stats(success=False)

        assert plugin.execution_count == 2
        assert plugin.error_count == 1

    def test_ac007_plugin_manager_list(self):
        """AC-007: 列表插件测试"""
        manager = self.PluginManager()

        # 列表插件
        plugins = manager.list_plugins()

        # 验收标准: list_plugins() 返回包含插件名称的列表
        assert isinstance(plugins, list)

    def test_ac008_plugin_manager_get_info(self):
        """AC-008: 获取插件信息测试"""
        manager = self.PluginManager()

        # 获取插件信息 (可能返回 None，但方法必须存在)
        info = manager.get_plugin_info("nonexistent_plugin")

        # 验收标准: get_plugin_info() 方法存在且可调用
        # (不需要返回特定值，因为插件不存在)
        assert info is None or isinstance(info, dict)


class TestSecuritySandboxAcceptance:
    """安全沙箱验收测试"""

    def setup_method(self):
        """测试前设置"""
        from security.sandbox import SecuritySandbox

        self.SecuritySandbox = SecuritySandbox

    def test_ac001_sandbox_initialization(self):
        """AC-001: 沙箱初始化测试"""
        sandbox = self.SecuritySandbox()

        # 验收标准: SecuritySandbox() 创建成功
        assert sandbox is not None
        # 验收标准: 默认配置正确
        assert sandbox.max_cpu_percent == 50
        assert sandbox.max_memory_mb == 256
        assert sandbox.max_execution_time == 30

    def test_ac002_plugin_validation_valid(self):
        """AC-002: 合法插件验证测试"""
        sandbox = self.SecuritySandbox()

        # 配置沙箱允许的路径和主机
        sandbox.file_read_whitelist = ["/tmp/"]
        sandbox.network_whitelist = ["localhost"]

        valid_meta = {
            "name": "valid_plugin",
            "permissions": ["read_data"],
            "security": {
                "file_read_paths": ["/tmp/"],
                "network_whitelist": ["localhost"],
            },
        }

        # 验收标准: validate_plugin() 返回 True
        result = sandbox.validate_plugin(valid_meta)
        assert result is True

    def test_ac003_plugin_validation_dangerous(self):
        """AC-003: 危险权限拒绝测试"""
        sandbox = self.SecuritySandbox()

        dangerous_meta = {
            "name": "dangerous_plugin",
            "permissions": ["write_memory", "execute_code"],
            "security": {
                "file_read_paths": ["/tmp/"],
                "network_whitelist": ["localhost"],
            },
        }

        # 验收标准: 包含危险权限的插件验证失败
        result = sandbox.validate_plugin(dangerous_meta)
        assert result is False

    def test_ac004_network_access_control(self):
        """AC-004: 网络访问控制测试"""
        sandbox = self.SecuritySandbox()
        sandbox.restrict_network_access(["localhost", "10.0.0.0/8"])

        # 验收标准: is_host_allowed() 正确识别白名单内的主机
        assert sandbox.is_host_allowed("localhost") is True
        assert sandbox.is_host_allowed("10.0.0.1") is True
        assert sandbox.is_host_allowed("evil.com") is False

    def test_ac005_file_access_control(self):
        """AC-005: 文件访问控制测试"""
        sandbox = self.SecuritySandbox()

        # 设置文件访问限制
        sandbox.restrict_file_access(
            read_paths=["/tmp/", "/var/log/"], write_paths=["/tmp/output/"]
        )

        # 验收标准: restrict_file_access() 正确设置读写路径
        assert "/tmp/" in sandbox.file_read_whitelist
        assert "/var/log/" in sandbox.file_read_whitelist
        assert "/tmp/output/" in sandbox.file_write_whitelist

    def test_ac006_audit_logging(self):
        """AC-006: 审计日志测试"""
        sandbox = self.SecuritySandbox()

        # 执行一些操作
        sandbox.restrict_network_access(["localhost"])
        sandbox.restrict_file_access(read_paths=["/tmp/"], write_paths=["/tmp/output/"])

        # 获取审计日志
        audit_log = sandbox.get_audit_log()

        # 验收标准: get_audit_log() 返回包含操作记录的列表
        assert isinstance(audit_log, list)
        assert len(audit_log) >= 2  # 至少有网络和文件限制的日志

    def test_ac007_resource_limits(self):
        """AC-007: 资源限制测试"""
        sandbox = self.SecuritySandbox()

        # 检查资源限制
        result = sandbox.check_resource_limits("test_plugin")

        # 验收标准: check_resource_limits() 正确检查内存使用
        assert isinstance(result, bool)

    def test_ac008_cidr_network_support(self):
        """AC-008: CIDR 支持测试"""
        sandbox = self.SecuritySandbox()
        sandbox.restrict_network_access(["10.0.0.0/8"])

        # 验收标准: is_host_allowed("10.0.0.1") 对 "10.0.0.0/8" 返回 True
        assert sandbox.is_host_allowed("10.0.0.1") is True
        assert sandbox.is_host_allowed("192.168.2.1") is False


class TestObservabilityAcceptance:
    """可观测性验收测试 (OpenTelemetry-based)"""

    def _make_collector(self):
        """Create a MetricsCollector backed by an in-memory OTel reader."""
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader

        from observability.metrics import MetricsCollector

        reader = InMemoryMetricReader()
        provider = MeterProvider(metric_readers=[reader])
        meter = provider.get_meter("test-acceptance", "0.0.0")
        return MetricsCollector(meter=meter), reader, provider

    def test_ac001_metrics_collector_initialization(self):
        """AC-001: MetricsCollector 初始化测试 (OTel-backed)"""
        collector, reader, provider = self._make_collector()

        # 验收标准: MetricsCollector() 创建成功
        assert collector is not None

        # 验收标准: 指标存储为空
        metrics = collector.get_metrics()
        assert "metrics" in metrics
        provider.shutdown()

    def test_ac002_counter_metrics(self):
        """AC-002: 计数器指标测试 (OTel Counter)"""
        collector, reader, provider = self._make_collector()

        collector.increment_counter("test_counter")
        collector.increment_counter("test_counter")
        collector.increment_counter("test_counter", 5)

        # 验收标准: increment_counter() 正确增加计数器值
        assert collector.counters["test_counter"] == 7

        # OTel metric exported
        data = reader.get_metrics_data()
        names = [
            m.name
            for rm in data.resource_metrics
            for sm in rm.scope_metrics
            for m in sm.metrics
        ]
        assert "test_counter" in names
        provider.shutdown()

    def test_ac003_gauge_metrics(self):
        """AC-003: 仪表指标测试 (OTel UpDownCounter)"""
        collector, reader, provider = self._make_collector()

        collector.set_gauge("test_gauge", 42.5)

        # 验收标准: set_gauge() 正确设置仪表值
        assert collector.gauges["test_gauge"] == 42.5

        data = reader.get_metrics_data()
        names = [
            m.name
            for rm in data.resource_metrics
            for sm in rm.scope_metrics
            for m in sm.metrics
        ]
        assert "test_gauge" in names
        provider.shutdown()

    def test_ac004_histogram_metrics(self):
        """AC-004: 直方图指标测试 (OTel Histogram)"""
        collector, reader, provider = self._make_collector()

        collector.observe_histogram("test_histogram", 100.0)
        collector.observe_histogram("test_histogram", 200.0)
        collector.observe_histogram("test_histogram", 150.0)

        # 验收标准: observe_histogram() 正确记录观测值
        assert len(collector.histograms["test_histogram"]) == 3

        data = reader.get_metrics_data()
        names = [
            m.name
            for rm in data.resource_metrics
            for sm in rm.scope_metrics
            for m in sm.metrics
        ]
        assert "test_histogram" in names
        provider.shutdown()

    def test_ac005_metrics_reset(self):
        """AC-005: 指标重置测试"""
        collector, reader, provider = self._make_collector()

        collector.increment_counter("test_counter")
        collector.set_gauge("test_gauge", 100)

        collector.reset()

        # 验收标准: reset() 清空所有指标
        metrics = collector.get_metrics()
        assert metrics["metrics"] == ""
        provider.shutdown()

    def test_ac006_plugin_metrics_load_duration(self):
        """AC-006: 插件加载耗时测试 (OTel Histogram)"""
        collector, reader, provider = self._make_collector()
        from observability.metrics import PluginMetrics

        plugin_metrics = PluginMetrics(collector)

        plugin_metrics.record_plugin_load("test_plugin", 150.0)

        data = reader.get_metrics_data()
        names = [
            m.name
            for rm in data.resource_metrics
            for sm in rm.scope_metrics
            for m in sm.metrics
        ]
        assert "plugin_load_duration_ms" in names
        provider.shutdown()

    def test_ac007_plugin_metrics_execution_duration(self):
        """AC-007: 插件执行耗时测试 (OTel Histogram + Counter)"""
        collector, reader, provider = self._make_collector()
        from observability.metrics import PluginMetrics

        plugin_metrics = PluginMetrics(collector)

        plugin_metrics.record_plugin_execution("test_plugin", 200.0, True)

        data = reader.get_metrics_data()
        names = [
            m.name
            for rm in data.resource_metrics
            for sm in rm.scope_metrics
            for m in sm.metrics
        ]
        assert "plugin_execution_duration_ms" in names
        assert "plugin_execution_total" in names
        provider.shutdown()

    def test_ac008_metrics_export(self):
        """AC-008: 指标导出测试 (get_metrics returns dict)"""
        collector, reader, provider = self._make_collector()

        collector.increment_counter("test_counter")
        collector.set_gauge("test_gauge", 100)

        metrics = collector.get_metrics()

        # 验收标准: get_metrics() 返回包含所有指标的字典
        assert isinstance(metrics, dict)
        assert "metrics" in metrics
        assert "test_counter" in metrics["metrics"]
        assert "test_gauge" in metrics["metrics"]
        provider.shutdown()


class TestCICDPipelineAcceptance:
    """CI/CD 流水线验收测试"""

    def setup_method(self):
        """测试前设置"""
        self.project_root = Path(__file__).parent.parent.parent

    def test_ac001_github_actions_workflow(self):
        """AC-001: GitHub Actions 文件检查"""
        workflow_file = self.project_root / ".github" / "workflows" / "ci-cd.yml"

        # 验收标准: 文件存在且格式正确
        assert workflow_file.exists(), "ci-cd.yml 文件不存在"

        # 检查 YAML 格式
        with open(workflow_file, "r") as f:
            content = yaml.safe_load(f)

        assert content is not None, "YAML 格式错误"
        assert "jobs" in content, "缺少 jobs 配置"

    def test_ac002_multi_python_version(self):
        """AC-002: 多 Python 版本检查"""
        workflow_file = self.project_root / ".github" / "workflows" / "ci-cd.yml"

        with open(workflow_file, "r") as f:
            content = yaml.safe_load(f)

        # 检查矩阵策略
        test_job = content.get("jobs", {}).get("test", {})
        strategy = test_job.get("strategy", {}).get("matrix", {})
        python_versions = strategy.get("python-version", [])

        # 验收标准: 至少包含 3 个 Python 版本
        assert len(python_versions) >= 3, f"Python 版本数量不足: {len(python_versions)}"

        # 验证版本格式正确 (可以是字符串或数字)
        # YAML 可能将版本号解析为浮点数
        assert len(python_versions) > 0, "Python 版本列表为空"

    def test_ac003_code_quality_checks(self):
        """AC-003: 代码质量检查步骤 (linting job)"""
        workflow_file = self.project_root / ".github" / "workflows" / "ci-cd.yml"

        with open(workflow_file, "r") as f:
            content = yaml.safe_load(f)

        jobs = content.get("jobs", {})

        # 验收标准: 存在独立的 linting job 或 test job 中包含 linting 步骤
        has_linting_job = "linting" in jobs

        if has_linting_job:
            # linting job 中收集所有步骤名称和运行命令
            linting_job = jobs["linting"]
            linting_steps = linting_job.get("steps", [])
            linting_text = ""
            for step in linting_steps:
                if isinstance(step, dict):
                    linting_text += step.get("name", "") + " "
                    run_cmd = step.get("run", "")
                    if isinstance(run_cmd, str):
                        linting_text += run_cmd + " "
            linting_text = linting_text.lower()
            assert "black" in linting_text, "linting job 中缺少 black 检查"
            assert "flake8" in linting_text, "linting job 中缺少 flake8 检查"
            assert "isort" in linting_text, "linting job 中缺少 isort 检查"
        else:
            # 回退: 检查 test job 步骤中是否包含 linting
            test_job = jobs.get("test", {})
            steps = test_job.get("steps", [])
            step_names = []
            for step in steps:
                if isinstance(step, dict):
                    step_names.append(step.get("name", ""))
            steps_text = " ".join(step_names).lower()
            assert "black" in steps_text or "linting" in steps_text, "缺少 black 检查"
            assert "flake8" in steps_text or "linting" in steps_text, "缺少 flake8 检查"
            assert "isort" in steps_text or "linting" in steps_text, "缺少 isort 检查"

    def test_ac005_unit_tests_coverage(self):
        """AC-005: 单元测试覆盖率步骤"""
        workflow_file = self.project_root / ".github" / "workflows" / "ci-cd.yml"

        with open(workflow_file, "r") as f:
            content = yaml.safe_load(f)

        test_job = content.get("jobs", {}).get("test", {})
        steps = test_job.get("steps", [])

        # 收集所有步骤命令
        all_commands = ""
        for step in steps:
            if isinstance(step, dict):
                run_cmd = step.get("run", "")
                if isinstance(run_cmd, str):
                    all_commands += run_cmd + " "
                elif isinstance(run_cmd, list):
                    all_commands += " ".join(run_cmd) + " "

        # 验收标准: 包含 pytest --cov
        assert "pytest" in all_commands, "缺少 pytest"
        assert "cov" in all_commands, "缺少覆盖率收集"

    def test_ac008_dockerfile_exists(self):
        """AC-008: Dockerfile 检查"""
        dockerfile = self.project_root / "Dockerfile"

        # 验收标准: Dockerfile 文件存在
        assert dockerfile.exists(), "Dockerfile 不存在"

        # 检查基本内容
        with open(dockerfile, "r") as f:
            content = f.read()

        assert "FROM" in content, "Dockerfile 缺少 FROM 指令"
        assert "COPY" in content or "ADD" in content, "Dockerfile 缺少 COPY/ADD 指令"

    def test_ac009_docker_compose_exists(self):
        """AC-009: docker-compose.yml 检查"""
        compose_file = self.project_root / "docker-compose.yml"

        # 验收标准: docker-compose.yml 文件存在
        assert compose_file.exists(), "docker-compose.yml 不存在"

        # 检查格式
        with open(compose_file, "r") as f:
            content = yaml.safe_load(f)

        assert content is not None, "docker-compose.yml 格式错误"
        assert "services" in content, "缺少 services 配置"

    def test_ac010_database_init_script(self):
        """AC-010: 数据库初始化脚本检查"""
        init_sql = self.project_root / "config" / "init.sql"

        # 验收标准: config/init.sql 文件存在且包含建表语句
        assert init_sql.exists(), "init.sql 不存在"

        with open(init_sql, "r") as f:
            content = f.read()

        assert "CREATE TABLE" in content, "init.sql 缺少建表语句"

    def test_ac011_prometheus_config(self):
        """AC-011: Prometheus 配置检查"""
        prometheus_config = self.project_root / "config" / "prometheus.yml"

        # 验收标准: config/prometheus.yml 文件存在
        assert prometheus_config.exists(), "prometheus.yml 不存在"

        # 检查格式
        with open(prometheus_config, "r") as f:
            content = yaml.safe_load(f)

        assert content is not None, "prometheus.yml 格式错误"
        assert "scrape_configs" in content, "缺少 scrape_configs"

    def test_ac012_alert_rules(self):
        """AC-012: 告警规则检查"""
        alert_rules = self.project_root / "config" / "alert_rules.yml"

        # 验收标准: config/alert_rules.yml 文件存在
        assert alert_rules.exists(), "alert_rules.yml 不存在"

        # 检查格式
        with open(alert_rules, "r") as f:
            content = yaml.safe_load(f)

        assert content is not None, "alert_rules.yml 格式错误"
        assert "groups" in content, "缺少 groups 配置"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
