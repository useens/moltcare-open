# 🦞 MoltCare Foundation Pack v2.3.3

> **OpenClaw Agent 核心配置模板** —— 精简高效版

## 更新日志

**v2.3.3 - P1 优化**：
- ✅ 新增触发词可视化反馈机制（🧠⭐🚫💾📝👤）
- ✅ 新增可选的配置向导 (`scripts/onboarding.sh`)
- ✅ 安装后自动提示配置向导（10秒超时跳过）
- ✅ 优化消息处理流程，添加触发词反馈步骤
- ✅ 统一 OpenClaw 说明（集中在 AGENTS.md）
- ✅ 简化 Signal 系统为"重要度"分级
- ✅ 删除子代理策略细节，保留核心概念
- 总大小：6.4KB → ~5KB

**v2.3.2 - P0 优化**：
- SOUL.md: 55KB → 1.5KB (-97%)
- AGENTS.md: 22KB → 1.4KB (-94%)
- USER.md: 17KB → 0.9KB (-95%)

---

## 这是什么？

MoltCare Foundation Pack 提供精简的 Markdown 配置文件模板，用于 OpenClaw Agent 的认知框架搭建。

**核心价值：**
- ✅ 精简核心原则，无冗余示例
- ✅ 快速加载，信息密度高
- ✅ 即拷即用，1 分钟完成配置

---

## 📦 包含的模板

安装后，文件会放到以下位置（**粗体**表示必须安装到根目录的文件）：

```
~/.openclaw/workspace/
├── 📄 SOUL.md              **Agent 灵魂定义**（根目录）
├── 📄 AGENTS.md            **操作手册**（根目录）
├── 📄 USER.md              **用户画像**（根目录）
├── 📄 MEMORY.md            **记忆系统**（根目录）
├── 📄 HEARTBEAT.md         **状态报告模板**（根目录）
├── 📄 TOOLS.md             **环境工具清单**（根目录）
├── 📄 DECISION_LOG.md      **决策记录**（根目录）
├── 📄 ERROR_LOG.md         **错误与教训**（根目录）
├── 📄 DAILY_TEMPLATE.md    **每日日志模板**（根目录）
├── 📁 memory/              **记忆工具**（子目录）
│   ├── learning-debt.md
│   ├── constraints.md
│   └── preferences.md
└── 📁 docs/                **集成文档**（可选子目录）
    ├── INTEGRATION.md
    ├── INTEGRATION_QUICKSTART.md
    ├── INTEGRATION_MECHANISM.md
    └── INTEGRATION_TROUBLESHOOTING.md
```

**⚠️ 重要：SOUL.md、AGENTS.md、USER.md 必须放在 workspace 根目录，否则 OpenClaw 无法自动加载！**

---

## 🚀 快速开始

### 方式一：一键安装（推荐）

```bash
# 直接安装到 OpenClaw workspace 根目录
curl -fsSL https://raw.githubusercontent.com/useens/moltcare-open/main/install.sh | bash

# 或安装到自定义目录
curl -fsSL https://raw.githubusercontent.com/useens/moltcare-open/main/install.sh | bash -s -- /path/to/your/workspace
```

### 方式二：手动复制

```bash
# 1. 克隆仓库
git clone https://github.com/useens/moltcare-open.git /tmp/moltcare

# 2. 复制核心文件到 workspace 根目录（Agent 必须识别的位置）
cp /tmp/moltcare/templates/core/*.md ~/.openclaw/workspace/          # SOUL.md, AGENTS.md, USER.md
cp /tmp/moltcare/templates/system/*.md ~/.openclaw/workspace/        # MEMORY.md, HEARTBEAT.md
cp /tmp/moltcare/tools/*.md ~/.openclaw/workspace/                   # TOOLS.md, DECISION_LOG.md, etc.

# 3. 创建 memory/ 子目录
cp -r /tmp/moltcare/templates/memory ~/.openclaw/workspace/memory/

# 4. （可选）复制文档
cp -r /tmp/moltcare/docs ~/.openclaw/workspace/
```

---

## 📋 配置说明

### 1. SOUL.md（Agent 灵魂）
定义 Agent 的核心身份、七大原则、多专家决策机制。

**关键章节：**
- 七大绝对原则
- 多专家决策机制（研究员/架构师/工程师/伦理员/队长）
- 自动触发词系统

### 2. AGENTS.md（操作手册）
Agent 的工作流程、触发词系统、安全红线。

**关键章节：**
- 启动必做检查清单
- 消息处理流程
- 触发词系统（Signal 分级）
- Multi-Agent 执行细则

### 3. USER.md（用户画像）
由用户填写个人信息、工作偏好、技术栈、授权边界。

**必须填写：**
- 用户基本信息
- 工作偏好（授权级别、汇报频率）
- 技术栈
- 约束与边界

---

## 🔄 更新模板

```bash
# 重新运行安装脚本
curl -fsSL https://raw.githubusercontent.com/useens/moltcare-open/main/install.sh | bash

# 备份现有配置
cp ~/.openclaw/workspace/SOUL.md ~/.openclaw/workspace/SOUL.md.backup

# 复制新模板（保留 USER.md 中的个人配置）
cp ~/.moltcare/templates/core/SOUL.md ~/.openclaw/workspace/
cp ~/.moltcare/templates/core/AGENTS.md ~/.openclaw/workspace/
```

---

## 🎯 触发词系统

MoltCare 内置自动触发机制，Agent 识别关键词自动执行动作：

### 核心触发词

| 触发词 | Signal | 动作 | 反馈 |
|--------|--------|------|------|
| `多专家讨论:` | 10 | 强制启动多专家讨论 | 🧠 |
| `这很重要` | 9 | 高优先级记录 | ⭐ |
| `记住这个` | 8 | 记录到学习债务 | 💾 |
| `别忘记` | 7 | 创建待办任务 | 📝 |
| `我偏好` | 6 | 记录用户偏好 | 👤 |
| `不要`/`禁止` | 高 | 添加约束条件 | 🚫 |

### 触发词可视化反馈

当 Agent 检测到触发词时，会在回复开头显示轻量反馈：

```
[🧠 多专家模式] 这里是回复内容...
[⭐ 高优先级记忆] 已记录重要信息
```

**设计原则**：
- 简洁单行，不干扰主要内容
- 首次检测时显示，避免重复
- 多触发词时只显示最高优先级（🧠 > ⭐ > 🚫 > 💾 > 📝 > 👤）

---

## 🚀 配置向导（可选）

安装后运行配置向导，快速设置 USER.md：

```bash
# 运行交互式配置向导
~/.openclaw/workspace/scripts/onboarding.sh
```

向导会询问：
- 基本信息（名字、角色、领域）
- 技术栈（语言、框架）
- 沟通偏好（详细程度、语气、技术深度）
- 决策偏好（风险确认级别）

**特点**：
- ✅ 完全可选，可随时手动编辑 USER.md
- ✅ 10秒超时自动跳过，不强制打断
- ✅ 生成完整的 USER.md 配置文件

---

## 📄 License

MIT © MoltCare Team
