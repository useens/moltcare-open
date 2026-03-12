# 测试自动化指南

> MoltCare test-pack-enhanced 自动生成

## 🎯 测试金字塔

```
       /\
      /  \    E2E 测试 (少而精)
     /____\
    /      \  集成测试 (中等数量)
   /________\
  /          \ 单元测试 (大量)
 /____________\
```

**比例建议：** 70% 单元测试 + 20% 集成测试 + 10% E2E 测试

## 📝 单元测试最佳实践

### 1. 测试结构 (AAA 模式)

```python
def test_user_creation():
    # Arrange - 准备
    user_data = {
        "name": "John Doe",
        "email": "john@example.com"
    }
    
    # Act - 执行
    user = User.create(**user_data)
    
    # Assert - 验证
    assert user.name == "John Doe"
    assert user.email == "john@example.com"
    assert user.id is not None
```

### 2. 使用 Fixtures

```python
import pytest
from datetime import datetime

@pytest.fixture
def sample_user():
    """创建测试用户."""
    return User(
        id=1,
        name="Test User",
        email="test@example.com",
        created_at=datetime.now()
    )

@pytest.fixture
def mock_db():
    """模拟数据库."""
    db = MockDatabase()
    yield db
    db.cleanup()

# 使用 fixture
def test_user_save(sample_user, mock_db):
    sample_user.save(db=mock_db)
    assert mock_db.find(User, id=1) is not None
```

### 3. 参数化测试

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("World", "WORLD"),
    ("", ""),
    ("123", "123"),
])
def test_to_uppercase(input, expected):
    assert to_uppercase(input) == expected
```

### 4. 异常测试

```python
def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        divide(10, 0)

def test_invalid_input_type():
    with pytest.raises(TypeError):
        process_data(None)
```

## 🏭 测试数据工厂

### 使用 factory_boy

```python
import factory
from factory import Faker

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    id = factory.Sequence(lambda n: n)
    name = Faker('name')
    email = Faker('email')
    age = factory.Faker('random_int', min=18, max=80)
    is_active = True

class PostFactory(factory.Factory):
    class Meta:
        model = Post
    
    id = factory.Sequence(lambda n: n)
    title = Faker('sentence')
    content = Faker('text')
    author = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date_time')

# 使用工厂
user = UserFactory()  # 创建单个用户
users = UserFactory.create_batch(10)  # 创建 10 个用户

# 覆盖属性
admin = UserFactory(name="Admin", email="admin@example.com")

# 关联对象
post = PostFactory(author__name="特定作者")
```

### 测试数据策略

```python
# conftest.py
import pytest

@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录."""
    return Path(__file__).parent / "data"

@pytest.fixture
def json_data(test_data_dir):
    """加载 JSON 测试数据."""
    def _load(filename):
        with open(test_data_dir / filename) as f:
            return json.load(f)
    return _load

# 使用
def test_api_response(json_data):
    expected = json_data("expected_response.json")
    assert api.call() == expected
```

## 🔗 集成测试

### API 集成测试

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """创建测试客户端."""
    from main import app
    return TestClient(app)

def test_create_user(client):
    response = client.post(
        "/users/",
        json={"name": "John", "email": "john@example.com"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "John"

def test_get_user(client):
    # 先创建用户
    create_resp = client.post("/users/", json={"name": "Jane", "email": "jane@example.com"})
    user_id = create_resp.json()["id"]
    
    # 再获取
    get_resp = client.get(f"/users/{user_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == "jane@example.com"
```

### 数据库集成测试

```python
@pytest.fixture(scope="function")
def db_session():
    """每个测试函数的数据库会话."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

def test_user_persistence(db_session):
    user = User(name="Test", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    
    found = db_session.query(User).filter_by(email="test@example.com").first()
    assert found is not None
    assert found.name == "Test"
```

## 📊 覆盖率检查

### 配置 .coveragerc

```ini
[run]
source = src
branch = True
omit = 
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*

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

[html]
directory = reports/coverage_html

[xml]
output = reports/coverage.xml
```

### 运行覆盖率

```bash
# 运行测试并生成覆盖率
pytest --cov=src --cov-report=term-missing

# 生成 HTML 报告
pytest --cov=src --cov-report=html

# 生成 XML 报告 (用于 CI)
pytest --cov=src --cov-report=xml

# 检查是否达到阈值
pytest --cov=src --cov-fail-under=80
```

## ⚡ 性能测试

### 使用 pytest-benchmark

```python
import pytest

def test_function_performance(benchmark):
    result = benchmark(target_function, arg1, arg2)
    assert result is not None

# 自定义性能测试
def test_sort_performance(benchmark):
    data = [random.randint(0, 1000) for _ in range(10000)]
    
    result = benchmark(sorted, data)
    
    # 验证结果正确
    assert result == sorted(data)
```

### 使用 locust 进行负载测试

```python
# locustfile.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    
    @task(3)
    def view_items(self):
        self.client.get("/api/items")
    
    @task(1)
    def create_item(self):
        self.client.post("/api/items", json={
            "name": "Test Item",
            "price": 29.99
        })

# 运行
# locust -f locustfile.py --host=http://localhost:8000
```

## 🎭 Mock 和 Patch

### 基础 Mock

```python
from unittest.mock import Mock, patch, MagicMock

def test_external_api_call():
    # 创建 mock
    mock_response = Mock()
    mock_response.json.return_value = {"status": "ok"}
    mock_response.status_code = 200
    
    with patch('requests.get', return_value=mock_response):
        result = fetch_data("http://api.example.com")
        assert result["status"] == "ok"
```

### Patch 装饰器

```python
@patch('module.external_service')
def test_service_integration(mock_service):
    mock_service.process.return_value = {"result": "success"}
    
    result = process_order(order_id=123)
    
    assert result == {"result": "success"}
    mock_service.process.assert_called_once_with(order_id=123)
```

### Patch 多个对象

```python
@patch('module.email_service')
@patch('module.payment_gateway')
def test_order_completion(mock_payment, mock_email):
    mock_payment.charge.return_value = True
    mock_email.send.return_value = True
    
    complete_order(order_id=123)
    
    mock_payment.charge.assert_called_once()
    mock_email.send.assert_called_once()
```

## 🔧 测试配置

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html

markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    e2e: marks tests as end-to-end tests
```

### conftest.py

```python
import pytest

# 全局 fixtures
@pytest.fixture(scope="session")
def event_loop():
    """用于异步测试的事件循环."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# 自定义标记
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")

# 自定义命令行选项
def pytest_addoption(parser):
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="run slow tests"
    )

def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
```

## 🚀 运行测试

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_users.py

# 运行特定类
pytest tests/test_users.py::TestUserModel

# 运行特定测试
pytest tests/test_users.py::TestUserModel::test_create

# 运行标记的测试
pytest -m unit
pytest -m "not slow"
pytest -m integration

# 并行运行
pytest -n auto

# 失败时停止
pytest -x
pytest --maxfail=3

# 只运行上次失败的
pytest --lf

# 调试模式
pytest --pdb
```

## ✅ 测试检查清单

- [ ] 测试命名清晰 (test_做什么_在什么条件下_预期结果)
- [ ] 每个测试只验证一个概念
- [ ] 使用 fixtures 共享测试数据
- [ ] 清理测试数据 (使用 yield fixtures)
- [ ] 测试边界条件 (空值、最大值、异常)
- [ ] 不要测试实现细节，测试行为
- [ ] 保持测试独立，不依赖执行顺序
- [ ] 覆盖率 >= 80%
- [ ] 测试运行时间 < 1 分钟

---

*此指南由 MoltCare test-pack-enhanced 自动生成*
*测试是代码质量的保险*
