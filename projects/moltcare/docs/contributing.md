# 🤝 Moltcare 贡献指南

> 感谢你对 Moltcare 项目的关注！每一份贡献都让这个项目变得更好。

---

## 📋 目录

1. [如何贡献](#1-如何贡献)
2. [开发环境搭建](#2-开发环境搭建)
3. [代码规范](#3-代码规范)
4. [提交规范](#4-提交规范)
5. [Pull Request 流程](#5-pull-request-流程)
6. [多语言翻译指南](#6-多语言翻译指南)
7. [文档贡献](#7-文档贡献)
8. [社区准则](#8-社区准则)

---

## 1. 如何贡献

### 1.1 报告 Bug

如果你发现了 Bug，请通过 [GitHub Issues](https://github.com/useens/moltcare/issues) 报告。

**报告模板**：

```markdown
**问题描述**
清晰简洁地描述 Bug。

**复现步骤**
1. 执行 '...'
2. 输入 '...'
3. 出现错误

**期望行为**
描述你期望发生什么。

**实际行为**
描述实际发生了什么。

**环境信息**
- Moltcare 版本: [e.g. 1.0.0]
- Python 版本: [e.g. 3.11.0]
- 操作系统: [e.g. Ubuntu 22.04]

**附加信息**
日志、截图等相关信息。
```

### 1.2 功能建议

有好的想法？欢迎通过 Issues 提出！

**建议模板**：

```markdown
**功能描述**
清晰描述这个功能。

**使用场景**
描述这个功能在什么场景下有用。

**预期行为**
描述这个功能应该如何工作。

**替代方案**
你考虑过哪些替代方案？

**附加信息**
任何其他相关信息。
```

### 1.3 代码贡献

1. Fork 仓库
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

### 1.4 文档贡献

- 修正拼写错误
- 改进文档清晰度
- 翻译多语言版本
- 添加示例和教程

---

## 2. 开发环境搭建

### 2.1 克隆仓库

```bash
git clone https://github.com/your-username/moltcare.git
cd moltcare
```

### 2.2 创建虚拟环境

```bash
# 使用 venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 使用 conda
conda create -n moltcare python=3.11
conda activate moltcare
```

### 2.3 安装开发依赖

```bash
pip install -e ".[dev]"
# 或
pip install -e .
pip install -r requirements-dev.txt
```

### 2.4 验证安装

```bash
# 运行测试
pytest

# 检查代码风格
black --check moltcare
flake8 moltcare
mypy moltcare

# 本地运行
moltcare --version
```

---

## 3. 代码规范

### 3.1 Python 代码规范

我们使用以下工具保证代码质量：

- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码风格检查
- **mypy**: 类型检查

```bash
# 格式化代码
black moltcare tests
isort moltcare tests

# 检查代码
flake8 moltcare tests
mypy moltcare
```

### 3.2 代码风格指南

#### 命名规范

```python
# 模块名: 小写，下划线分隔
my_module.py

# 类名: 驼峰命名
class MyClass:
    pass

# 函数名: 小写，下划线分隔
def my_function():
    pass

# 常量: 大写，下划线分隔
MY_CONSTANT = 42

# 私有变量: 下划线前缀
_private_var = "private"
```

#### 文档字符串

```python
def process_data(data: dict, options: Optional[dict] = None) -> Result:
    """处理数据并返回结果。
    
    Args:
        data: 输入数据字典
        options: 可选的处理选项
        
    Returns:
        Result: 处理结果对象
        
    Raises:
        ValueError: 当数据格式无效时
        
    Example:
        >>> result = process_data({"key": "value"})
        >>> print(result.status)
        'success'
    """
    pass
```

### 3.3 测试规范

```python
import pytest
from moltcare.core import init_project


def test_init_project_success(tmp_path):
    """测试项目初始化成功。"""
    # Arrange
    workspace = tmp_path / "test_workspace"
    
    # Act
    result = init_project(workspace, name="TestAgent")
    
    # Assert
    assert result.success is True
    assert (workspace / "SOUL.md").exists()
    assert (workspace / "AGENTS.md").exists()


def test_init_project_invalid_name():
    """测试无效名称处理。"""
    with pytest.raises(ValueError, match="名称不能为空"):
        init_project("/tmp/test", name="")
```

---

## 4. 提交规范

### 4.1 提交信息格式

```
<类型>: <简短描述>

[可选的详细描述]

[可选的脚注]
```

### 4.2 提交类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加备份恢复功能` |
| `fix` | Bug 修复 | `fix: 修复 upgrade 命令的空指针错误` |
| `docs` | 文档更新 | `docs: 更新 README 安装说明` |
| `style` | 代码格式 | `style: 格式化 cli.py` |
| `refactor` | 重构 | `refactor: 重构模板加载逻辑` |
| `test` | 测试相关 | `test: 添加 init 命令测试` |
| `chore` | 构建/工具 | `chore: 更新依赖版本` |
| `perf` | 性能优化 | `perf: 优化配置文件加载速度` |
| `i18n` | 国际化 | `i18n: 添加日文翻译` |

### 4.3 提交示例

```bash
# 好的提交信息
git commit -m "feat: 添加自动备份功能

- 新增 backup 命令
- 支持定时自动备份
- 可配置备份保留策略

Closes #123"

# 不好的提交信息
git commit -m "update"  # ❌ 太模糊
git commit -m "fix bug"  # ❌ 不具体
git commit -m "修改了一些文件"  # ❌ 无价值信息
```

---

## 5. Pull Request 流程

### 5.1 PR 准备

```bash
# 1. 同步上游代码
git remote add upstream https://github.com/useens/moltcare.git
git fetch upstream
git rebase upstream/main

# 2. 运行测试
pytest

# 3. 检查代码风格
black --check moltcare tests
flake8 moltcare tests

# 4. 推送分支
git push origin feature/your-feature
```

### 5.2 PR 模板

```markdown
## 描述
简要描述这个 PR 做了什么。

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 破坏性变更
- [ ] 文档更新

## 测试
- [ ] 已添加单元测试
- [ ] 已添加集成测试
- [ ] 已手动测试

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 提交信息符合规范

## 相关 Issue
Closes #123
```

### 5.3 审查流程

1. **自动化检查**
   - CI 测试必须通过
   - 代码风格检查必须通过
   - 覆盖率不能下降

2. **人工审查**
   - 至少 1 名维护者批准
   - 解决所有审查意见
   - 保持 PR 聚焦于单一目标

3. **合并**
   - 使用 "Squash and merge"
   - 确保提交信息清晰

---

## 6. 多语言翻译指南

### 6.1 支持的文档

| 文件名 | 语言 | 状态 |
|--------|------|------|
| README.md | 中文 | ✅ 完整 |
| README.en.md | 英文 | ✅ 完整 |
| README.ja.md | 日文 | 🏗️ 框架 |
| README.ko.md | 韩文 | 🏗️ 框架 |
| README.de.md | 德文 | 🏗️ 框架 |
| README.fr.md | 法文 | 🏗️ 框架 |
| README.es.md | 西班牙文 | 🏗️ 框架 |
| README.ru.md | 俄文 | 🏗️ 框架 |
| README.ar.md | 阿拉伯文 | 🏗️ 框架 |

### 6.2 翻译流程

1. **Fork 仓库** 并创建翻译分支
   ```bash
   git checkout -b i18n/ja-full-translation
   ```

2. **基于框架翻译**
   - 保持原有 Markdown 格式
   - 保留所有链接和徽章
   - 翻译所有内容

3. **术语对照表**

   | 中文 | English | 日本語 | 한국어 |
   |------|---------|--------|--------|
   | Agent | Agent | エージェント | 에이전트 |
   | 模板 | Template | テンプレート | 템플릿 |
   | 初始化 | Initialize | 初期化 | 초기화 |
   | 多专家讨论 | Multi-Expert Discussion | マルチエキスパートディスカッション | 멀티 전문가 토론 |

4. **提交 PR**
   ```bash
   git commit -m "i18n: 完成日文翻译
   
   - 翻译 README.ja.md
   - 更新术语对照表
   
   Related to #456"
   ```

### 6.3 翻译规范

- 保持语气一致（正式/友好）
- 技术术语可保留英文
- 添加译者注释 `[译者注: ...]`
- 保留所有代码示例

---

## 7. 文档贡献

### 7.1 文档结构

```
docs/
├── tutorial.md       # 使用教程
├── contributing.md   # 贡献指南（本文件）
├── architecture.md   # 架构设计
├── api.md           # API 文档
├── faq.md           # 常见问题
└── templates/       # 文档模板
```

### 7.2 文档规范

- 使用 Markdown 格式
- 添加适当的标题层级
- 包含代码示例
- 添加目录（TOC）

### 7.3 添加新文档

```bash
# 1. 创建文档文件
touch docs/your-topic.md

# 2. 更新 README.md 文档导航
# 3. 在 mkdocs.yml 中添加导航（如果使用 MkDocs）
```

---

## 8. 社区准则

### 8.1 行为准则

- **尊重**: 尊重每一位贡献者
- **包容**: 欢迎不同背景的人
- **耐心**: 新手问题是学习的机会
- **建设性**: 批评要建设性，表扬要真诚

### 8.2 沟通渠道

- **GitHub Issues**: Bug 报告和功能建议
- **GitHub Discussions**: 一般性讨论
- **Pull Requests**: 代码审查和讨论

### 8.3 维护者职责

- 及时回应 Issues 和 PR
- 保持代码审查的建设性
- 帮助新贡献者上手
- 维护项目愿景和方向

### 8.4 贡献者认可

- 所有贡献者都会记录在 CONTRIBUTORS.md
- 重要贡献会在 Release Notes 中致谢
- 年度贡献者将获得特别认可

---

## 🙏 感谢

感谢所有为 Moltcare 做出贡献的人！

特别感谢：
- 双 AI 协作模式的开创者
- 所有测试者和反馈提供者
- 翻译贡献者
- 文档维护者

---

## 📚 相关资源

- [使用教程](./tutorial.md)
- [架构设计](./architecture.md)
- [API 文档](./api.md)
- [FAQ](./faq.md)

---

<p align="center">
  <strong>🌲 Moltcare - 让每个 Agent 一键获得智能</strong>
</p>
