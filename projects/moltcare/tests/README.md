# Moltcare 测试框架

## 测试结构

```
tests/
├── README.md                    # 本文件
├── conftest.py                  # pytest配置和fixtures
├── run_tests.sh                 # 本地测试脚本
├── __init__.py
├── unit/                        # 单元测试
│   ├── __init__.py
│   ├── test_cli.py             # CLI测试 (20+ 测试)
│   ├── test_init.py            # init命令测试
│   ├── test_upgrade.py         # upgrade命令测试
│   └── test_backup.py          # backup/restore测试
├── integration/                 # 集成测试
│   ├── __init__.py
│   ├── test_integration.py     # 端到端集成测试
│   └── test_scenarios.py       # 真实场景测试
└── examples/                    # 示例Agent配置
    ├── basic-agent/            # 基础示例 (7个核心文件)
    └── advanced-agent/         # 高级示例 (7个核心文件)
```

## 运行测试

### 运行所有测试
```bash
pytest tests/
```

### 运行单元测试
```bash
pytest tests/unit/
```

### 运行集成测试
```bash
pytest tests/integration/
```

### 使用本地脚本
```bash
./tests/run_tests.sh
```

### 生成覆盖率报告
```bash
pytest --cov=moltcare --cov-report=html
```

## 测试统计

- **单元测试**: 39个
- **集成测试**: 30个
- **总计**: 69个测试
- **CLI覆盖率**: 96%

## CI/CD

GitHub Actions工作流配置: `.github/workflows/test.yml`

包含:
- Python 3.8-3.12 矩阵测试
- 代码质量检查 (flake8, black, isort)
- 安全审计 (bandit)
- 示例配置验证
