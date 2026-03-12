# Python 开发规范

> MoltCare dev-pack 自动生成

## 🎯 核心原则

### 1. 代码风格 (PEP 8)

```python
# ✅ 正确
class MyClass:
    """类文档字符串."""
    
    def __init__(self, name: str) -> None:
        self.name = name
    
    def process(self, data: dict) -> list:
        """处理数据并返回列表."""
        return [item for item in data if item.get('valid')]

# ❌ 错误
class myclass:
    def __init__(self,name):
        self.name=name
    def process(self,data):
        return [item for item in data if item.get('valid')]
```

### 2. 类型注解

```python
from typing import Optional, List, Dict, Any

def fetch_data(
    url: str, 
    timeout: int = 30,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """获取数据.
    
    Args:
        url: API URL
        timeout: 超时时间(秒)
        headers: 请求头
        
    Returns:
        解析后的 JSON 数据
        
    Raises:
        TimeoutError: 请求超时
    """
    pass
```

### 3. 错误处理

```python
# ✅ 具体异常
from requests.exceptions import Timeout, ConnectionError

def safe_fetch(url: str) -> dict:
    try:
        return requests.get(url, timeout=30).json()
    except Timeout:
        logger.warning(f"请求超时: {url}")
        return {}
    except ConnectionError as e:
        logger.error(f"连接失败: {e}")
        raise

# ❌ 不要捕获所有异常
try:
    do_something()
except Exception:  # 太宽泛
    pass
```

### 4. 日志使用

```python
import logging

logger = logging.getLogger(__name__)

# ✅ 正确
logger.info("处理完成: %d 条记录", count)
logger.warning("配置缺失: %s", config_key)
logger.error("操作失败: %s", e, exc_info=True)

# ❌ 错误
print(f"处理完成: {count}")  # 不要用 print
```

## 🔄 TDD 流程

### Red-Green-Refactor

```python
# 1. Red - 先写失败的测试
def test_calculate_discount():
    assert calculate_discount(100, 0.2) == 80

# 2. Green - 实现最简代码
def calculate_discount(price: float, rate: float) -> float:
    return price * (1 - rate)

# 3. Refactor - 优化代码
```

### 测试结构

```python
import pytest

class TestDataProcessor:
    """数据处理器测试."""
    
    @pytest.fixture
    def processor(self):
        return DataProcessor()
    
    def test_process_valid_data(self, processor):
        # Arrange
        data = {"id": 1, "name": "test"}
        
        # Act
        result = processor.process(data)
        
        # Assert
        assert result.is_valid
        assert result.id == 1
    
    def test_process_invalid_data_raises(self, processor):
        with pytest.raises(ValueError, match="无效数据"):
            processor.process(None)
```

## 📝 Git 工作流

### 分支命名

```
feature/add-login        # 新功能
bugfix/fix-memory-leak   # Bug 修复
refactor/simplify-api    # 重构
docs/update-readme       # 文档
hotfix/security-patch    # 紧急修复
```

### 提交信息规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型：**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具

**示例：**
```
feat(auth): 添加 JWT 认证

- 实现 token 生成和验证
- 添加登录接口
- 更新中间件

Closes #123
```

## 🔍 代码审查清单

### Self-Review 检查项

- [ ] 代码是否符合 PEP 8
- [ ] 是否有类型注解
- [ ] 是否有适当的错误处理
- [ ] 是否有单元测试
- [ ] 文档字符串是否完整
- [ ] 是否有不必要的注释
- [ ] 是否有性能问题
- [ ] 是否引入安全风险

### PR 模板

```markdown
## 变更内容
- 功能 A 实现
- 修复 Bug B

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试通过

## 检查清单
- [ ] 代码审查完成
- [ ] 文档已更新
- [ ] CHANGELOG 已更新
```

## 🛠️ 推荐工具

| 工具 | 用途 | 安装 |
|------|------|------|
| ruff | 快速 linter | `pip install ruff` |
| black | 代码格式化 | `pip install black` |
| mypy | 类型检查 | `pip install mypy` |
| pytest | 测试框架 | `pip install pytest` |
| pre-commit | Git hooks | `pip install pre-commit` |

### Pre-commit 配置

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
```

---

*此规范由 MoltCare dev-pack 自动生成*
*版本: 1.0.0 | 建议定期更新*
