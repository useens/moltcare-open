# 🦞 MoltCare

> 让每一只刚安装的 OpenClaw Agent 都能一键获得专业级智能

## 快速安装

### 方式一：一键脚本安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/useens/moltcare/main/install.sh | bash
```

或

```bash
wget -qO- https://raw.githubusercontent.com/useens/moltcare/main/install.sh | bash
```

### 方式二：手动安装

```bash
# 克隆仓库
git clone https://github.com/useens/moltcare.git ~/.moltcare

# 添加到 PATH
export PATH="$HOME/.moltcare:$PATH"

# 初始化
moltcare init
```

### 依赖要求

- **Python 3.8+** (必须)
- **PyYAML** (必须，会自动安装)
- Node.js (可选，用于 TypeScript 开发)

## 快速开始

```bash
# 查看帮助
moltcare --help

# 初始化配置
moltcare init

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

| 智能包 | 说明 |
|--------|------|
| **foundation** | 基础认知框架，包含 SOUL.md、AGENTS.md、USER.md 模板 |
| **openclaw-init** | OpenClaw 初始化配置，快速开始指南 |

### 创建自定义智能包

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

| 命令 | 说明 |
|------|------|
| `moltcare init` | 初始化 MoltCare 配置 |
| `moltcare list` | 列出可用智能包 |
| `moltcare apply <pack>` | 应用指定智能包 |
| `moltcare status` | 显示系统状态 |
| `moltcare doctor` | 运行健康诊断 |
| `moltcare config` | 管理配置 |

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

## 多专家决策系统

MoltCare 内置多专家决策机制，当检测到以下关键词时自动触发：

| 触发词 | 说明 |
|--------|------|
| `多专家讨论:` | 强制启动多专家讨论 |
| `设计/架构` | 自动触发架构师参与 |
| `对比/评估` | 自动触发研究员参与 |

## 许可证

MIT License

---

*MoltCare - 每一只 Agent 都值得专业级智能*
