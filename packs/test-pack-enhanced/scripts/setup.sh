#!/bin/bash
# test-pack-enhanced 安装脚本

echo "🧪 配置测试自动化环境..."

# 创建测试目录结构
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/e2e
mkdir -p tests/fixtures
mkdir -p tests/factories
echo "✓ 创建 tests/ 目录结构"

# 创建 conftest.py
cat > tests/conftest.py << 'EOF'
"""pytest 全局配置和 fixtures."""

import pytest
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def project_root():
    """返回项目根目录."""
    return ROOT_DIR


@pytest.fixture(scope="session")
def test_data_dir():
    """返回测试数据目录."""
    data_dir = Path(__file__).parent / "fixtures" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def sample_data(test_data_dir):
    """加载测试数据的辅助函数."""
    import json
    
    def _load(filename):
        filepath = test_data_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
        return {}
    
    return _load
EOF
echo "✓ 创建 tests/conftest.py"

# 创建测试工厂示例
cat > tests/factories/__init__.py << 'EOF'
"""测试数据工厂."""

# 示例工厂，根据项目修改
# import factory
# 
# class UserFactory(factory.Factory):
#     class Meta:
#         model = User
#     
#     id = factory.Sequence(lambda n: n)
#     name = factory.Faker('name')
#     email = factory.Faker('email')
EOF
echo "✓ 创建 tests/factories/__init__.py"

# 创建示例单元测试
cat > tests/unit/test_example.py << 'EOF'
"""单元测试示例."""

import pytest


class TestExample:
    """示例测试类."""
    
    def test_basic_assertion(self):
        """测试基本断言."""
        assert True
    
    def test_string_operations(self):
        """测试字符串操作."""
        text = "Hello, World!"
        assert text.upper() == "HELLO, WORLD!"
        assert "World" in text
    
    @pytest.mark.parametrize("input,expected", [
        ("hello", "HELLO"),
        ("world", "WORLD"),
        ("", ""),
    ])
    def test_parametrized(self, input, expected):
        """参数化测试示例."""
        assert input.upper() == expected


def test_with_fixture(sample_data):
    """使用 fixture 的测试."""
    # sample_data 是从 conftest.py 导入的 fixture
    pass
EOF
echo "✓ 创建 tests/unit/test_example.py"

# 创建 pytest.ini
cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts = 
    -v
    --tb=short
    --strict-markers

markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (may use database/API)
    e2e: End-to-end tests (full system)
    slow: Slow tests (skip by default)
    smoke: Smoke tests (quick sanity check)

filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
EOF
echo "✓ 创建 pytest.ini"

# 创建 .coveragerc
cat > .coveragerc << 'EOF'
[run]
source = src
branch = True
omit = 
    */tests/*
    */test_*
    */venv/*
    */__pycache__/*
    */migrations/*
    */alembic/*

[report]
precision = 2
fail_under = 80
show_missing = True
skip_covered = False
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = reports/coverage_html

[xml]
output = reports/coverage.xml
EOF
echo "✓ 创建 .coveragerc"

# 创建测试运行脚本
cat > scripts/run-tests.sh << 'EOF'
#!/bin/bash
# 测试运行脚本

set -e

echo "🧪 运行测试套件..."
echo ""

# 默认运行所有测试
MODE=${1:-"all"}

case "$MODE" in
    unit)
        echo "运行单元测试..."
        pytest -m unit -v
        ;;
    integration)
        echo "运行集成测试..."
        pytest -m integration -v
        ;;
    e2e)
        echo "运行 E2E 测试..."
        pytest -m e2e -v
        ;;
    smoke)
        echo "运行冒烟测试..."
        pytest -m smoke -v
        ;;
    coverage)
        echo "运行测试并生成覆盖率报告..."
        pytest --cov=src --cov-report=term-missing --cov-report=html
        echo ""
        echo "覆盖率报告: reports/coverage_html/index.html"
        ;;
    ci)
        echo "运行 CI 测试..."
        pytest -m "not slow" --cov=src --cov-fail-under=80 --cov-report=xml
        ;;
    all|*)
        echo "运行所有测试..."
        pytest -v
        ;;
esac

echo ""
echo "✅ 测试完成"
EOF
chmod +x scripts/run-tests.sh
echo "✓ 创建 scripts/run-tests.sh"

# 创建 Makefile 测试命令
if [ -f "Makefile" ]; then
    if ! grep -q "^test:" Makefile; then
        cat >> Makefile << 'EOF'

# Test commands
test:
	pytest -v

test-unit:
	pytest -m unit -v

test-integration:
	pytest -m integration -v

test-coverage:
	pytest --cov=src --cov-report=term-missing --cov-report=html

test-ci:
	pytest -m "not slow" --cov=src --cov-fail-under=80
EOF
        echo "✓ 更新 Makefile 添加测试命令"
    fi
else
    cat > Makefile << 'EOF'
.PHONY: test test-unit test-integration test-coverage test-ci

test:
	pytest -v

test-unit:
	pytest -m unit -v

test-integration:
	pytest -m integration -v

test-coverage:
	pytest --cov=src --cov-report=term-missing --cov-report=html

test-ci:
	pytest -m "not slow" --cov=src --cov-fail-under=80
EOF
    echo "✓ 创建 Makefile 测试命令"
fi

# 创建 Locust 性能测试文件
cat > tests/locustfile.py << 'EOF'
"""性能测试配置."""

from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    """网站用户行为模拟."""
    
    wait_time = between(1, 5)
    
    @task(3)
    def view_index(self):
        """访问首页."""
        self.client.get("/")
    
    @task(2)
    def view_api(self):
        """访问 API."""
        self.client.get("/api/status")
    
    @task(1)
    def create_item(self):
        """创建资源."""
        self.client.post("/api/items", json={
            "name": "Test Item",
            "value": 100
        })
EOF
echo "✓ 创建 tests/locustfile.py"

echo ""
echo "🎉 test-pack-enhanced 配置完成!"
echo ""
echo "已创建:"
echo "  📁 tests/unit/          - 单元测试"
echo "  📁 tests/integration/   - 集成测试"
echo "  📁 tests/e2e/          - E2E 测试"
echo "  📁 tests/factories/    - 测试数据工厂"
echo "  📁 tests/fixtures/     - 测试数据"
echo "  📄 tests/conftest.py   - pytest 配置"
echo "  📄 pytest.ini          - pytest 设置"
echo "  📄 .coveragerc         - 覆盖率配置"
echo ""
echo "使用方法:"
echo "  ./scripts/run-tests.sh           # 运行所有测试"
echo "  ./scripts/run-tests.sh unit      # 运行单元测试"
echo "  ./scripts/run-tests.sh coverage  # 生成覆盖率报告"
echo "  make test                        # 快捷命令"
echo ""
echo "性能测试:"
echo "  locust -f tests/locustfile.py --host=http://localhost:8000"
echo ""
echo "查看指南:"
echo "  cat TESTING_GUIDE.md"
