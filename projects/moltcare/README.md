# Moltcare

让所有刚安装好的 Agent 一键提升智能 / One-click intelligence upgrade for new OpenClaw installations

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-purple)

---

## 📖 简介 / Introduction

**Moltcare** 是专为 OpenClaw 新用户设计的配置优化工具。很多刚安装完 OpenClaw 的用户会发现，核心配置文件（如 `SOUL.md`, `AGENTS.md` 等）质量参差不齐，导致 Agent 智能度不足。

Moltcare 可以：
- 🔍 **诊断** 配置文件质量
- 🚀 **一键升级** 使用最佳实践模板
- 🛡️ **保留个性化** 智能合并，不会丢失你的自定义内容
- 🌍 **多语言支持** 中英等 9 种语言

**Moltcare** is an OpenClaw configuration optimization tool designed specifically for new users. Many fresh OpenClaw installations suffer from poorly configured core files (like `SOUL.md`, `AGENTS.md`, etc.), leading to subpar agent intelligence.

Moltcare can:
- 🔍 **Diagnose** configuration file quality
- 🚀 **Upgrade** with best practice templates in one click
- 🛡️ **Preserve customization** Smart merging without losing your custom content
- 🌍 **Multi-language support** 9 languages including Chinese and English

## 🎯 核心价值 / Core Value

### Problem / 问题
新安装的 OpenClaw 用户的7个核心配置文件往往：
- ❌ 内容过少或占位符未填写
- ❌ 结构混乱，缺少关键章节
- ❌ 使用默认模板，未个性化
- ❌ 缺少最佳实践指导

### Solution / 方案
Moltcare 提供三层架构：
1. **诊断层** - 质量评分 + 问题识别
2. **修复层** - 智能替换最佳实践模板
3. **验证层** - 语法/逻辑检查 + 建议优化

## 📦 安装 / Installation

```bash
pip install moltcare
```

或从源码安装 / Or install from source:

```bash
git clone https://github.com/useens/moltcare.git
cd moltcare
pip install -e .
```

## 🚀 快速开始 / Quick Start

### 1. 诊断配置 / Diagnose Configuration

```bash
moltcare diagnose
```

输出示例 / Example Output:

```
🔍 正在诊断 OpenClaw 配置文件...

📊 诊断报告
==================================================
总体评分: 45/100
发现问题: 8 个
建议优化: 2 项

⚠️ 发现的问题:
  - [SOUL.md] 内 容过少 (15/50 行)
  - [IDENTITY.md] 包含待补充内容占位符
  - [USER.md] 可能使用默认模板（未个性化）

💡 优化建议:
  - 建议运行 `moltcare upgrade` 提升配置质量
```

### 2. 升级配置 / Upgrade Configuration

```bash
moltcare upgrade
```

或先预览变更（推荐）/ Or preview changes first (recommended):

```bash
moltcare upgrade --dry-run
```

升级完成后 / After upgrade:

```
✅ 升级完成！
   处理文件: 7
   备份位置: ~/.openclaw/.openclaw/backups/moltcare/20260310-234500
```

### 3. 验证配置 / Validate Configuration

```bash
moltcare validate
```

## 📁 项目结构 / Project Structure

```
moltcare/
├── src/
│   └── moltcare/
│       ├── __init__.py      # 包初始化
│       ├── cli.py           # 命令行工具
│       ├── diagnostic.py    # 诊断引擎
│       ├── merger.py        # 智能合并器
│       └── validator.py     # 配置验证器
├── templates/
│   └── core/               # 7个核心文件模板
│       ├── SOUL.md
│       ├── AGENTS.md
│       ├── IDENTITY.md
│       ├── MEMORY.md
│       ├── HEARTBEAT.md
│       ├── TOOLS.md
│       └── USER.md
├── diagnostics/            # 诊断规则扩展
├── merger/                 # 合并算法扩展
├── tests/                  # 测试文件
├── docs/                   # 文档
├── l10n/                   # 多语言翻译
└── README.md
```

## 🔧 配置文件 / Core Files

Moltcare 优化的7个核心配置文件：

| 文件 | 用途 | 权重 |
|------|------|------|
| `SOUL.md` | Agent 核心原则和哲学 | 20% |
| `AGENTS.md` | 操作手册和触发词 | 15% |
| `IDENTITY.md` | 身份定义和定位 | 15% |
| `MEMORY.md` | 系统仪表盘 | 10% |
| `HEARTBEAT.md` | 心跳检查协议 | 10% |
| `TOOLS.md` | 工具配置 | 10% |
| `USER.md` | 用户档案和偏好 | 20% |

## 🤝 贡献 / Contributing

我们欢迎贡献！请查看 [CONTRIBUTING.md](docs/CONTRIBUTING.md) 获取详细信息。

We welcome contributions! Please check [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

## 📄 许可证 / License

MIT License - 查看 [LICENSE](LICENSE) 文件

## 🌟 Roadmap

- [ ] 第1期：MVP（核心诊断+升级）✅（当前/Current）
- [ ] 第2期：多语言支持（英语、日语、韩语等）
- [ ] 第3期：高级诊断规则和修复建议
- [ ] 第4期：可视化报告
- [ ] 第5期：Web UI 界面

## 📬 联系 / Contact

- GitHub: https://github.com/useens/moltcare
- Issue: https://github.com/useens/moltcare/issues

---

**让 Agent 更智能，从配置开始 / Make agents smarter, starting with configuration**
