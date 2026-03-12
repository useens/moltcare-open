#!/bin/bash
# dev-pack 安装脚本

echo "🔧 配置开发环境..."

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✓ Python $PYTHON_VERSION"

# 检查是否已安装推荐工具
echo ""
echo "检查开发工具..."

TOOLS=("ruff" "black" "mypy" "pytest")
for tool in "${TOOLS[@]}"; do
    if command -v $tool &> /dev/null; then
        echo "  ✓ $tool 已安装"
    else
        echo "  ⚠ $tool 未安装，建议: pip install $tool"
    fi
done

# 创建 .pre-commit-config.yaml 模板
if [ ! -f ".pre-commit-config.yaml" ]; then
    cat > .pre-commit-config.yaml << 'EOF'
# MoltCare dev-pack 生成的 pre-commit 配置
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
  
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
EOF
    echo "✓ 创建 .pre-commit-config.yaml"
fi

# 创建 Makefile 模板
if [ ! -f "Makefile" ]; then
    cat > Makefile << 'EOF'
# MoltCare dev-pack 生成的 Makefile
.PHONY: test lint format check install-dev

install-dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest -v --cov=src --cov-report=term-missing

lint:
	ruff check src tests
	mypy src

format:
	ruff format src tests

check: lint test
	@echo "✓ 所有检查通过"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov

help:
	@echo "可用命令:"
	@echo "  make install-dev  - 安装开发依赖"
	@echo "  make test         - 运行测试"
	@echo "  make lint         - 代码检查"
	@echo "  make format       - 格式化代码"
	@echo "  make check        - 运行所有检查"
	@echo "  make clean        - 清理临时文件"
EOF
    echo "✓ 创建 Makefile"
fi

# 创建 pyproject.toml 基础配置
if [ ! -f "pyproject.toml" ] && [ ! -f "setup.py" ]; then
    cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "your-project"
version = "0.1.0"
description = "项目描述"
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov",
    "ruff",
    "mypy",
    "pre-commit",
]

[tool.ruff]
target-version = "py38"
line-length = 100
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
EOF
    echo "✓ 创建 pyproject.toml 模板"
fi

echo ""
echo "🎉 dev-pack 配置完成!"
echo ""
echo "下一步:"
echo "  1. 安装开发依赖: pip install -e \".[dev]\""
echo "  2. 安装 pre-commit: pre-commit install"
echo "  3. 查看指南: cat PYTHON_GUIDE.md"
echo "  4. 开始开发: make test"
