# TDD 快速参考

> MoltCare dev-pack 自动生成

## 🔄 Red-Green-Refactor 循环

```
Red    → 写一个失败的测试
Green  → 写最少代码让测试通过
Refactor → 重构，保持测试通过
```

## 📝 测试模板

```python
# test_feature.py
import pytest
from my_module import MyClass

class TestMyClass:
    """测试 MyClass."""
    
    @pytest.fixture
    def instance(self):
        """创建测试实例."""
        return MyClass(config="test")
    
    def test_should_do_something_when_condition(self, instance):
        """当满足条件时，应该做某事."""
        # Arrange
        input_data = {"key": "value"}
        expected = "result"
        
        # Act
        result = instance.process(input_data)
        
        # Assert
        assert result == expected
    
    def test_should_raise_error_when_invalid_input(self, instance):
        """当输入无效时，应该抛出异常."""
        with pytest.raises(ValueError, match="无效输入"):
            instance.process(None)
```

## 🎯 测试原则

### FIRST 原则
- **F**ast - 测试要快
- **I**ndependent - 测试独立
- **R**epeatable - 可重复
- **S**elf-validating - 自验证（布尔结果）
- **T**imely - 及时编写

### AAA 模式
```python
def test_example():
    # Arrange - 准备
    calculator = Calculator()
    
    # Act - 执行
    result = calculator.add(2, 3)
    
    # Assert - 验证
    assert result == 5
```

## 🛠️ 常用 pytest 功能

```python
# 参数化测试
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add(a, b, expected):
    assert add(a, b) == expected

# 跳过测试
@pytest.mark.skip(reason="功能未完成")
def test_future_feature():
    pass

# 预期失败
@pytest.mark.xfail(reason="已知问题 #123")
def test_known_issue():
    assert problematic_function() == expected

# 固件 (Fixture)
@pytest.fixture(scope="module")
def database():
    db = create_test_db()
    yield db
    db.cleanup()

# Mock
from unittest.mock import Mock, patch

def test_with_mock():
    mock_api = Mock()
    mock_api.get.return_value = {"data": "test"}
    
    result = process_data(mock_api)
    
    mock_api.get.assert_called_once()
    assert result == expected

# 使用 patch
@patch("mymodule.requests.get")
def test_api_call(mock_get):
    mock_get.return_value.json.return_value = {"key": "value"}
    
    result = fetch_data()
    
    assert result["key"] == "value"
```

## 📊 运行测试

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest test_feature.py

# 运行特定类
pytest test_feature.py::TestMyClass

# 运行特定测试
pytest test_feature.py::TestMyClass::test_method

# 显示详细输出
pytest -v

# 显示覆盖率
pytest --cov=src --cov-report=html

# 只运行失败的测试
pytest --lf

# 并行运行
pytest -n auto
```

## ⚠️ 常见反模式

```python
# ❌ 不要测试私有方法
def test__private_method():  # 错误
    pass

# ❌ 不要测试实现细节，测试行为
def test_list_has_item():  # 错误：检查内部状态
    assert len(my_list._items) == 1

def test_list_contains_item():  # 正确：检查行为
    assert "item" in my_list

# ❌ 不要使用随机数据
def test_random():  # 错误
    import random
    value = random.randint(1, 100)
    assert process(value) == expected  # 不稳定

# ❌ 不要依赖外部状态
def test_with_db():  # 错误：依赖真实数据库
    result = query_production_db()
    assert result is not None
```

## 🔥 快速开始命令

```bash
# 1. 安装 pytest
pip install pytest pytest-cov

# 2. 创建测试目录
mkdir tests
touch tests/__init__.py

# 3. 编写第一个测试
cat > tests/test_example.py << 'EOF'
def test_simple():
    assert True
EOF

# 4. 运行测试
pytest -v
```

---

*此指南由 MoltCare dev-pack 自动生成*
