# 🦞 MoltCare

> 让每一只刚安装的 OpenClaw Agent 都能一键获得专业级智能

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/useens/moltcare-open/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ v2.0 新特性

MoltCare v2.0 实现与 OpenClaw 深度集成，真正的开箱即用：

- 🔄 **深度集成模式** - 配置自动同步到 OpenClaw workspace
- 🧠 **智能合并策略** - 保留用户配置的同时应用新功能  
- ⚡ **运行时 Hooks** - pre_message / heartbeat 自动触发
- 🤖 **自动触发词** - "多专家讨论:" 等关键词自动检测
- 💾 **智能记忆捕获** - 高价值内容自动记录
- 📊 **增强诊断** - `moltcare doctor` 全面健康检查

## 快速安装

### 方式一：一键脚本安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/useens/moltcare-open/main/install.sh | bash
```

或

```bash
wget -qO- https://raw.githubusercontent.com/useens/moltcare-open/main/install.sh | bash
```

### 方式二：手动安装

```bash
# 克隆仓库
git clone https://github.com/useens/moltcare-open.git ~/.moltcare

# 添加到 PATH
export PATH="$HOME/.moltcare:$PATH"

# 初始化
moltcare init
```

### 依赖要求

- **Python 3.8+** (必须)
- **PyYAML** (必须，会自动安装)

## 快速开始

### v2.0 推荐流程

```bash
# 1. 安装后初始化（启用深度集成模式）
moltcare init --force

# 2. 应用 v2.0 增强版基础包（智能合并模式）
moltcare apply foundation-v2 --merge

# 3. 同步配置到 OpenClaw
moltcare sync

# 4. 运行健康检查
moltcare doctor
```

### v1.x 兼容流程

```bash
# 查看帮助
moltcare --help

# 初始化配置
moltcare init

# 交互式配置向导（推荐新用户）
moltcare wizard

# 初始化到指定目录（支持CI/CD）
moltcare init /path/to/project --yes

# 查看可用智能包
moltcare list

# 应用基础智能包
moltcare apply foundation

# 查看系统状态
moltcare status

# 运行健康诊断
moltcare doctor
```

## 智能包 (Packs)

| 智能包 | 版本 | 说明 |
|--------|------|------|
| **foundation-v2** | v2.0.0 | 🆕 MoltCare v2.0 深度集成版，自动触发 + 运行时 hooks |
| **foundation** | v1.1.0 | 基础认知框架，包含 SOUL.md、AGENTS.md、USER.md 模板 |
| **openclaw-init** | v1.0.0 | OpenClaw 初始化配置，快速开始指南 |
| **example-user** | v1.0.0 | 已填写的 USER.md 示例模板 |

### v2.0 智能合并模式

```bash
# 智能合并（保留已有配置，添加新功能）
moltcare apply foundation-v2 --merge

# 强制覆盖（谨慎使用）
moltcare apply foundation-v2 --force

# 预览模式（查看会更改什么）
moltcare apply foundation-v2 --dry-run
```

```bash
# 创建目录结构
mkdir -p my-pack/templates my-pack/scripts

# 创建 manifest.json
cat > my-pack/manifest.json << 'EOF'
{
  "name": "my-pack",
  "version": "1.0.0",
  "description": "我的自定义智能包",
  "templates": [
    {"file": "templates/config.yaml", "target": "config.yaml"}
  ]
}
EOF

# 应用智能包
moltcare apply my-pack
```

## 可用命令

### v2.0 新增命令

#### `moltcare sync`
同步 MoltCare 配置到 OpenClaw workspace

```bash
moltcare sync          # 手动同步配置
```

同步内容包括：
- 运行时配置 (`runtime/openclaw-integration.yaml`)
- Hooks 注册信息
- 特性开关状态

---

#### `moltcare doctor`
增强版健康诊断（v2.0 强化）

```bash
moltcare doctor        # 运行全面健康检查
moltcare doctor --json # JSON 格式输出
```

诊断项目：
- ✅ MoltCare 版本和初始化状态
- ✅ OpenClaw 集成配置
- ✅ 运行时 hooks 安装状态
- ✅ 核心配置文件完整性

---

### 基础命令

#### `moltcare wizard`
交互式配置向导（推荐新用户）

```bash
moltcare wizard        # 启动交互式配置向导
```

向导会引导你完成：
1. **基本信息** - 称呼、身份、技术水平
2. **沟通偏好** - 回复详细程度、语气、输出格式
3. **自动化设置** - 风险操作的处理方式
4. **确认保存** - 自动写入 USER.md

---

### `moltcare init [path]`
初始化 MoltCare 配置

```bash
moltcare init                      # 初始化到 ~/.moltcare
moltcare init ./my-project         # 初始化到指定目录
moltcare init /tmp/test --yes      # 非交互模式（CI/CD）
moltcare init --force              # 强制重新初始化
```

**选项：**
- `path` - 目标目录路径 (可选，默认: ~/.moltcare)
- `-f, --force` - 强制重新初始化
- `-y, --yes` - 非交互模式，使用默认值

---

### `moltcare list`
列出可用智能包

```bash
moltcare list          # 列出所有智能包
moltcare list --json   # JSON 格式输出
```

---

### `moltcare apply <pack>`
应用指定智能包

```bash
moltcare apply foundation           # 应用基础包
moltcare apply foundation --force   # 强制覆盖
moltcare apply foundation --dry-run # 预览更改
```

**选项：**
- `-f, --force` - 强制覆盖已有文件
- `-d, --dry-run` - 预览模式，不实际应用
- `-g, --global-install` - 应用到全局工作区

---

### `moltcare status`
显示系统状态

```bash
moltcare status        # 人类可读格式
moltcare status --json # JSON 格式
```

---

### `moltcare doctor`
运行健康诊断

```bash
moltcare doctor        # 基础诊断
moltcare doctor --json # JSON 格式输出
```

---

### `moltcare config`
管理配置

```bash
moltcare config list              # 列出所有配置
moltcare config get language      # 获取配置项
moltcare config set language en   # 设置配置项
```

## CI/CD 集成示例

```yaml
# .github/workflows/setup-agent.yml
name: Setup Agent

jobs:
  setup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install MoltCare
        run: |
          curl -fsSL https://raw.githubusercontent.com/useens/moltcare-open/main/install.sh | bash
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Initialize
        run: moltcare init . --yes
      
      - name: Apply Foundation Pack
        run: moltcare apply foundation --yes
```

## 开发

### 目录结构

```
~
├── .moltcare/
│   ├── config.yaml          # 主配置
│   ├── packs/               # 智能包目录
│   │   ├── foundation/
│   │   └── openclaw-init/
│   └── workspace/           # 工作区
│       ├── MEMORY.md
│       └── USER.md
```

### 核心文件

- **moltcare** - 主 CLI 脚本（Python，无需 npm）
- **install.sh** - 安装脚本
- **packs/** - 智能包集合

## 多专家决策系统 (v2.0 自动触发)

MoltCare v2.0 内置自动触发机制，通过 `pre_message` hook 实时检测：

| 触发词 | Signal | 自动动作 |
|--------|--------|----------|
| `多专家讨论:` | 10 | 强制启动多专家讨论 |
| `这很重要` | 9 | 高优先级记录 + 标记 |
| `记住这个` | 8 | 智能摄取到学习债务 |
| `别忘记` | 7 | 创建待办任务 |
| `我偏好...` | 6 | 记录用户偏好到 USER.md |
| `提醒我...` | 7 | 解析并创建定时任务 |
| `设计/架构/策略` | 7 | 自动触发架构师参与 |
| `对比/评估/优化` | 7 | 自动触发研究员参与 |
| `安全/风险/伦理` | 8 | 自动触发伦理员参与 |

### 运行时 Hooks 架构

```
用户消息 → [pre_message hook] → 触发词检测 → 自动动作
     ↓
Agent处理 → [post_message hook] → 自动记录高价值内容
     ↓
定时触发 → [heartbeat hook] → 任务队列检查 + 记忆复习
```

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| **v2.0.0** | 2026-03-12 | 🚀 **重大更新**: 深度集成模式、运行时 hooks、智能合并、自动触发 |
| v1.1.0 | 2026-03-12 | 纯 Python CLI，移除 npm 依赖 |
| v1.0.0 | 2026-03-11 | 首个稳定版本

## 许可证

MIT License

---

*MoltCare - 每一只 Agent 都值得专业级智能*
