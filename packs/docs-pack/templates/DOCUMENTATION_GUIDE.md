# 文档写作规范

> MoltCare docs-pack 自动生成

## 📝 文档类型与结构

### README.md 标准结构

```markdown
# 项目名称

> 一句话描述项目核心价值

## 简介

详细介绍项目背景、解决的问题、主要特性。

## 安装

### 系统要求
- 要求 1
- 要求 2

### 快速安装
```bash
# 安装命令
```

## 使用

### 基本用法
```python
# 代码示例
```

### 高级用法
...

## API 文档

详见 [API.md](API.md)

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

[MIT](LICENSE)
```

### API 文档结构

```markdown
# API 参考

## 模块名称

### 函数/类名称

**描述**
简要说明功能。

**参数**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | str | 是 | 名称 |
| age | int | 否 | 年龄，默认 0 |

**返回值**
| 类型 | 说明 |
|------|------|
| User | 用户对象 |

**示例**
```python
user = create_user("john", age=25)
print(user.name)  # "john"
```

**异常**
- `ValueError`: 参数无效时抛出
```

## ✍️ 写作风格指南

### 1. 使用清晰的标题

```markdown
# ✅ 正确
## 快速开始
### 安装依赖

# ❌ 错误
## 开始
### 依赖
```

### 2. 代码块标注语言

```markdown
# ✅ 正确
```python
def hello():
    pass
```

# ❌ 错误
```
def hello():
    pass
```
```

### 3. 使用表格展示对比信息

```markdown
| 特性 | 方案A | 方案B |
|------|-------|-------|
| 性能 | 快 | 慢 |
| 复杂度 | 低 | 高 |
```

### 4. 添加视觉提示

```markdown
> 💡 **提示**: 这是有用的建议

> ⚠️ **警告**: 这可能引起问题

> 🚫 **禁止**: 绝对不要这样做
```

## 🔄 CHANGELOG 规范

使用 [Keep a Changelog](https://keepachangelog.com/) 格式：

```markdown
# Changelog

## [Unreleased]

### Added
- 新增功能 A
- 新增功能 B

### Changed
- 改进功能 C 的性能

### Deprecated
- 标记功能 D 为废弃

### Removed
- 移除已废弃的功能 E

### Fixed
- 修复问题 F

### Security
- 修复安全漏洞 G

## [1.0.0] - 2024-01-15

### Added
- 首个稳定版本
- 核心功能实现

[Unreleased]: https://github.com/user/repo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/user/repo/releases/tag/v1.0.0
```

### 版本号规则 (SemVer)

```
主版本号.次版本号.修订号

1.0.0
↑ ↑ ↑
│ │ └── 修订：bug 修复
│ └──── 次版本：新增功能，向后兼容
└────── 主版本：重大变更，可能不兼容
```

## 📋 文档审查清单

### 发布前检查

- [ ] README 包含项目描述
- [ ] 安装说明清晰完整
- [ ] 使用示例可运行
- [ ] API 文档参数完整
- [ ] CHANGELOG 已更新
- [ ] 所有链接有效
- [ ] 代码块语法正确
- [ ] 无拼写错误

### 定期维护

- [ ] 更新过时的信息
- [ ] 添加新功能文档
- [ ] 修正用户反馈的问题
- [ ] 优化不清晰的部分

## 🛠️ 文档工具

### Markdown linting

```bash
# 安装
npm install -g markdownlint-cli

# 检查
markdownlint README.md

# 自动修复
markdownlint README.md --fix
```

### 拼写检查

```bash
# 安装
npm install -g cspell

# 检查
cspell README.md
```

### 链接检查

```bash
# 安装
npm install -g markdown-link-check

# 检查
markdown-link-check README.md
```

## 📊 文档指标

好文档的标准：

| 指标 | 目标 | 检查方法 |
|------|------|----------|
| 完整性 | 覆盖所有功能 | 功能清单对比 |
| 准确性 | 示例可运行 | CI 测试 |
| 清晰度 | 新用户能理解 | 用户测试 |
| 及时性 | 与代码同步 | 发布检查 |

---

*此规范由 MoltCare docs-pack 自动生成*
