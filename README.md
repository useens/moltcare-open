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

## 快速开始

```bash
# 查看帮助
moltcare --help

# 初始化配置
moltcare init

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
          curl -fsSL https://raw.githubusercontent.com/useens/moltcare/main/install.sh | bash
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

## 多专家决策系统

MoltCare 内置多专家决策机制，当检测到以下关键词时自动触发：

| 触发词 | 说明 |
|--------|------|
| `多专家讨论:` | 强制启动多专家讨论 |
| `设计/架构` | 自动触发架构师参与 |
| `对比/评估` | 自动触发研究员参与 |

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1.0 | 2026-03-12 | 纯 Python CLI，移除 npm 依赖 |
| v1.0.0 | 2026-03-11 | 首个稳定版本 |

## 许可证

MIT License

---

*MoltCare - 每一只 Agent 都值得专业级智能*
