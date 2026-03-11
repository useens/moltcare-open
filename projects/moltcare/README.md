# Moltcare

> 一键提升 OpenClaw Agent 智能

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Moltcare 是一个 CLI 工具，让每个刚安装的 OpenClaw Agent 都能一键获得智能。

## ✨ 核心功能

- **🚀 一键初始化** - `moltcare init` 交互式生成完整的 Agent 核心文件
- **⬆️ 智能升级** - `moltcare upgrade` 自动检查并更新配置
- **🔍 诊断检查** - `moltcare doctor` 全面检查配置健康度
- **💾 备份管理** - `moltcare backup/restore` 安全备份和恢复配置

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/useens/moltcare.git
cd moltcare

# 一键安装
./install.sh

# 或使用 pip
pip install moltcare
```

### 使用

```bash
# 交互式初始化
moltcare init

# 非交互式初始化
moltcare init --name "MyAgent" --non-interactive

# 诊断检查
moltcare doctor

# 创建备份
moltcare backup

# 恢复备份
moltcare restore <backup-id>
```

## 📁 生成文件

运行 `moltcare init` 后会生成以下核心文件：

| 文件 | 用途 |
|------|------|
| `SOUL.md` | Agent 核心身份和原则 |
| `AGENTS.md` | 操作手册和执行流程 |
| `IDENTITY.md` | 身份档案 |
| `USER.md` | 用户档案 |
| `MEMORY.md` | 系统仪表盘 |
| `HEARTBEAT.md` | 心跳协议 |
| `TOOLS.md` | 工具和环境配置 |

## 🛠️ 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black moltcare/
ruff check moltcare/ --fix
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

*用 ❤️ 和 🤖 构建*
