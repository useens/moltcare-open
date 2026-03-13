# 安全开发规范

> MoltCare security-pack 自动生成

## 🛡️ 安全红线

### 绝对禁止

| 禁止项 | 风险 | 替代方案 |
|--------|------|----------|
| 硬编码密码/密钥 | 泄露风险 | 使用环境变量或密钥管理服务 |
| 提交 .env 文件 | 配置泄露 | 添加 .env 到 .gitignore |
| SQL 字符串拼接 | SQL 注入 | 使用参数化查询 |
| eval() 执行用户输入 | 代码注入 | 使用 ast.literal_eval 或沙箱 |
| 不验证用户输入 | XSS/注入 | 输入验证和输出编码 |

## 🔐 敏感信息处理

### 1. 环境变量管理

```python
# ✅ 正确
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

# ❌ 错误
API_KEY = "sk-1234567890abcdef"  # 永远不要硬编码！
```

### 2. .env 文件模板

```bash
# .env.example - 提交到仓库
API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:pass@localhost/db
SECRET_KEY=your_secret_key_here
DEBUG=false

# .env - 本地使用，绝不提交
# 添加到 .gitignore
echo ".env" >> .gitignore
```

### 3. 密钥轮换策略

```python
# config/security.py
import os
from datetime import datetime, timedelta

class KeyManager:
    """密钥管理器."""
    
    def __init__(self):
        self._keys = {}
        self._rotation_date = None
    
    def get_key(self, name: str) -> str:
        """获取密钥，检查轮换时间."""
        if self._should_rotate():
            self._rotate_keys()
        return os.getenv(f"{name}_KEY")
    
    def _should_rotate(self) -> bool:
        """检查是否需要轮换."""
        if not self._rotation_date:
            return False
        return datetime.now() > self._rotation_date
    
    def _rotate_keys(self):
        """轮换密钥（需配合密钥管理系统）."""
        # 实现密钥轮换逻辑
        self._rotation_date = datetime.now() + timedelta(days=90)
```

## 🕵️ 代码安全审查清单

### 输入验证

```python
import re
from typing import Optional
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    """用户输入模型."""
    username: str
    email: str
    age: int
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', v):
            raise ValueError('用户名只能包含字母数字下划线，长度3-20')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('无效的邮箱格式')
        return v
    
    @validator('age')
    def validate_age(cls, v):
        if not 0 < v < 150:
            raise ValueError('年龄必须在 0-150 之间')
        return v

# 使用
try:
    user = UserInput(username="john", email="john@example.com", age=25)
except ValueError as e:
    print(f"输入验证失败: {e}")
```

### SQL 注入防护

```python
# ✅ 参数化查询
import sqlite3

def get_user_safe(user_id: int):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

# ❌ 危险！
def get_user_dangerous(user_id: int):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # 注入风险！
```

### XSS 防护

```python
from html import escape

def render_user_content(user_input: str) -> str:
    """渲染用户内容，防止 XSS."""
    # 转义 HTML 特殊字符
    safe_content = escape(user_input)
    return f"<div>{safe_content}</div>"
```

## 🔍 依赖安全检查

### 1. 使用 safety 检查漏洞

```bash
# 安装
pip install safety

# 检查当前环境
safety check

# 检查 requirements.txt
safety check -r requirements.txt

# 生成报告
safety check --json > safety-report.json
```

### 2. 使用 pip-audit

```bash
# 安装
pip install pip-audit

# 审计依赖
pip-audit

# 修复建议
pip-audit --fix
```

### 3. 集成到 CI

```yaml
# .github/workflows/security.yml
name: Security Audit

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: pip install safety bandit pip-audit
    
    - name: Run safety check
      run: safety check || true
    
    - name: Run bandit
      run: bandit -r src/ -f json -o bandit-report.json || true
    
    - name: Run pip-audit
      run: pip-audit || true
```

## 🚨 安全扫描工具

### Bandit - Python 安全 linter

```bash
# 安装
pip install bandit

# 扫描项目
bandit -r src/

# 生成详细报告
bandit -r src/ -f json -o bandit-report.json

# 忽略特定警告
bandit -r src/ -skips B101,B102
```

### Semgrep - 静态分析

```bash
# 安装
pip install semgrep

# 运行规则
semgrep --config=auto src/

# 特定规则集
semgrep --config=p/security-audit src/
semgrep --config=p/owasp-top-ten src/
```

### GitLeaks - 密钥扫描

```bash
# 安装
docker pull zricethezav/gitleaks

# 扫描仓库
docker run -v $(pwd):/path zricethezav/gitleaks:latest detect --source /path

# 预提交钩子
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
EOF
```

## 📋 安全审查 Checklist

### 代码审查时必须检查：

- [ ] 没有硬编码的密码/密钥/API token
- [ ] 所有用户输入都经过验证
- [ ] SQL 查询使用参数化
- [ ] 输出内容经过转义（防止 XSS）
- [ ] 敏感操作有日志记录
- [ ] 错误信息不泄露敏感信息
- [ ] 依赖没有已知漏洞
- [ ] 文件上传有类型和大小限制
- [ ] 会话管理安全（超时、刷新）
- [ ] 权限检查在服务端完成

### 发布前检查：

- [ ] 运行安全扫描工具（bandit, semgrep）
- [ ] 检查依赖漏洞（safety, pip-audit）
- [ ] 扫描密钥泄露（gitleaks）
- [ ] 审查环境变量配置
- [ ] 检查日志不包含敏感信息
- [ ] 验证访问控制正确

## 🔐 安全事件响应

### 发现密钥泄露时：

1. **立即撤销密钥**（在服务商控制台）
2. **轮换所有相关密钥**
3. **审查日志**查看是否有异常访问
4. **从仓库历史清除**（使用 BFG Repo-Cleaner）
5. **通知相关团队**

```bash
# 使用 BFG 清除历史
java -jar bfg.jar --delete-files .env
java -jar bfg.jar --replace-text passwords.txt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## 📚 资源

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security](https://python-security.readthedocs.io/)
- [Bandit Docs](https://bandit.readthedocs.io/)
- [Safety DB](https://pyup.io/safety/)

---

*此规范由 MoltCare security-pack 自动生成*
*定期审查和更新*


# 安全开发规范

> MoltCare security-pack 自动生成

## 🛡️ 安全红线

### 绝对禁止

| 禁止项 | 风险 | 替代方案 |
|--------|------|----------|
| 硬编码密码/密钥 | 泄露风险 | 使用环境变量或密钥管理服务 |
| 提交 .env 文件 | 配置泄露 | 添加 .env 到 .gitignore |
| SQL 字符串拼接 | SQL 注入 | 使用参数化查询 |
| eval() 执行用户输入 | 代码注入 | 使用 ast.literal_eval 或沙箱 |
| 不验证用户输入 | XSS/注入 | 输入验证和输出编码 |

## 🔐 敏感信息处理

### 1. 环境变量管理

```python
# ✅ 正确
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

# ❌ 错误
API_KEY = "sk-1234567890abcdef"  # 永远不要硬编码！
```

### 2. .env 文件模板

```bash
# .env.example - 提交到仓库
API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:pass@localhost/db
SECRET_KEY=your_secret_key_here
DEBUG=false

# .env - 本地使用，绝不提交
# 添加到 .gitignore
echo ".env" >> .gitignore
```

### 3. 密钥轮换策略

```python
# config/security.py
import os
from datetime import datetime, timedelta

class KeyManager:
    """密钥管理器."""
    
    def __init__(self):
        self._keys = {}
        self._rotation_date = None
    
    def get_key(self, name: str) -> str:
        """获取密钥，检查轮换时间."""
        if self._should_rotate():
            self._rotate_keys()
        return os.getenv(f"{name}_KEY")
    
    def _should_rotate(self) -> bool:
        """检查是否需要轮换."""
        if not self._rotation_date:
            return False
        return datetime.now() > self._rotation_date
    
    def _rotate_keys(self):
        """轮换密钥（需配合密钥管理系统）."""
        # 实现密钥轮换逻辑
        self._rotation_date = datetime.now() + timedelta(days=90)
```

## 🕵️ 代码安全审查清单

### 输入验证

```python
import re
from typing import Optional
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    """用户输入模型."""
    username: str
    email: str
    age: int
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', v):
            raise ValueError('用户名只能包含字母数字下划线，长度3-20')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('无效的邮箱格式')
        return v
    
    @validator('age')
    def validate_age(cls, v):
        if not 0 < v < 150:
            raise ValueError('年龄必须在 0-150 之间')
        return v

# 使用
try:
    user = UserInput(username="john", email="john@example.com", age=25)
except ValueError as e:
    print(f"输入验证失败: {e}")
```

### SQL 注入防护

```python
# ✅ 参数化查询
import sqlite3

def get_user_safe(user_id: int):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

# ❌ 危险！
def get_user_dangerous(user_id: int):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # 注入风险！
```

### XSS 防护

```python
from html import escape

def render_user_content(user_input: str) -> str:
    """渲染用户内容，防止 XSS."""
    # 转义 HTML 特殊字符
    safe_content = escape(user_input)
    return f"<div>{safe_content}</div>"
```

## 🔍 依赖安全检查

### 1. 使用 safety 检查漏洞

```bash
# 安装
pip install safety

# 检查当前环境
safety check

# 检查 requirements.txt
safety check -r requirements.txt

# 生成报告
safety check --json > safety-report.json
```

### 2. 使用 pip-audit

```bash
# 安装
pip install pip-audit

# 审计依赖
pip-audit

# 修复建议
pip-audit --fix
```

### 3. 集成到 CI

```yaml
# .github/workflows/security.yml
name: Security Audit

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: pip install safety bandit pip-audit
    
    - name: Run safety check
      run: safety check || true
    
    - name: Run bandit
      run: bandit -r src/ -f json -o bandit-report.json || true
    
    - name: Run pip-audit
      run: pip-audit || true
```

## 🚨 安全扫描工具

### Bandit - Python 安全 linter

```bash
# 安装
pip install bandit

# 扫描项目
bandit -r src/

# 生成详细报告
bandit -r src/ -f json -o bandit-report.json

# 忽略特定警告
bandit -r src/ -skips B101,B102
```

### Semgrep - 静态分析

```bash
# 安装
pip install semgrep

# 运行规则
semgrep --config=auto src/

# 特定规则集
semgrep --config=p/security-audit src/
semgrep --config=p/owasp-top-ten src/
```

### GitLeaks - 密钥扫描

```bash
# 安装
docker pull zricethezav/gitleaks

# 扫描仓库
docker run -v $(pwd):/path zricethezav/gitleaks:latest detect --source /path

# 预提交钩子
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
EOF
```

## 📋 安全审查 Checklist

### 代码审查时必须检查：

- [ ] 没有硬编码的密码/密钥/API token
- [ ] 所有用户输入都经过验证
- [ ] SQL 查询使用参数化
- [ ] 输出内容经过转义（防止 XSS）
- [ ] 敏感操作有日志记录
- [ ] 错误信息不泄露敏感信息
- [ ] 依赖没有已知漏洞
- [ ] 文件上传有类型和大小限制
- [ ] 会话管理安全（超时、刷新）
- [ ] 权限检查在服务端完成

### 发布前检查：

- [ ] 运行安全扫描工具（bandit, semgrep）
- [ ] 检查依赖漏洞（safety, pip-audit）
- [ ] 扫描密钥泄露（gitleaks）
- [ ] 审查环境变量配置
- [ ] 检查日志不包含敏感信息
- [ ] 验证访问控制正确

## 🔐 安全事件响应

### 发现密钥泄露时：

1. **立即撤销密钥**（在服务商控制台）
2. **轮换所有相关密钥**
3. **审查日志**查看是否有异常访问
4. **从仓库历史清除**（使用 BFG Repo-Cleaner）
5. **通知相关团队**

```bash
# 使用 BFG 清除历史
java -jar bfg.jar --delete-files .env
java -jar bfg.jar --replace-text passwords.txt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## 📚 资源

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security](https://python-security.readthedocs.io/)
- [Bandit Docs](https://bandit.readthedocs.io/)
- [Safety DB](https://pyup.io/safety/)

---

*此规范由 MoltCare security-pack 自动生成*
*定期审查和更新*
