<!-- Header -->
<p align="center">
  <img src="https://img.shields.io/badge/OpenClaw-Ready-blue?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bS0xIDE3LjkzYy0zLjk1LS40OS03LTMuODUtNy03LjkzIDAtLjYyLjA4LTEuMjEuMjEtMS43OUw5IDE1djFjMCAyLjIgMS44IDQgNCA0djMuOTN6bTYuOS0xNS40OGMtLjY0LS4wMS0xLjI5LS4wNi0xLjkzLS4xNkwxNSA1djIuMDVjLjMyLS4xNC42Ni0uMjIgMS0uMjIgMS4zOCAwIDIuNSAxLjEyIDIuNSAyLjUgMCAxLjM4LTEuMTIgMi41LTIuNSAyLjV6bTIuODkgMTMuODhjLjE5LS42My4yOS0xLjI5LjI5LTEuOTggMC0zLjg3LTMuMTMtNy03LTdzLTcgMy4xMy03IDdjMCAuNjkuMSAxLjM1LjI5IDEuOThsMS43MS0xLjcxYy0uMDgtLjI0LS4xNC0uNDktLjE0LS43NiAwLTEuMzggMS4xMi0yLjUgMi41LTIuNS4yNyAwIC41Mi4wNi43Ni4xNGwxLjg2LTEuODZ6IiBmaWxsPSJ3aGl0ZSIvPjwvc3ZnPg==" alt="OpenClaw">
  <img src="https://img.shields.io/badge/ClawHub-Published-brightgreen?style=flat-square" alt="ClawHub">
  <img src="https://img.shields.io/badge/Version-v3.2-green?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Size-~5KB-orange?style=flat-square" alt="Size">
</p>

<h1 align="center">🦞 MoltCare</h1>

<p align="center"><strong>OpenClaw Agent Configuration Framework</strong></p>
<p align="center">让 AI Agent 从被动执行变为主动解决问题</p>

<p align="center">
  <a href="#-quick-start">快速开始</a> •
  <a href="#-what-is-moltcare">项目介绍</a> •
  <a href="#-core-concepts">核心概念</a> •
  <a href="#-file-reference">文件说明</a> •
  <a href="#-pua-framework">PUA框架</a>
</p>

---

## 🚀 Quick Start

### 方式一：通过 ClawHub 安装（推荐）

```bash
# 一键安装
clawhub install moltcare-open

# 验证安装
clawhub list
```

### 方式二：手动安装

```bash
# 一键安装脚本
curl -fsSL https://raw.githubusercontent.com/useens/moltcare-open/master/install.sh | bash

# 或使用 Skill 目录安装
git clone https://github.com/useens/moltcare-open.git
cd moltcare-open/skill
bash scripts/install.sh
```

### 方式三：配置向导

```bash
~/.openclaw/workspace/scripts/onboarding.sh
```

安装完成后，你的 OpenClaw Agent 将获得：
- ✅ **主动问题解决** — 不再轻易说"我解决不了"
- ✅ **多专家决策** — 复杂问题自动启动专家讨论
- ✅ **三层智能触发** — 精确+语义+主动评估混合机制
- ✅ **结构化记忆** — 长期记忆自动分层管理

---

## 🤔 What is MoltCare?

**MoltCare** 是一套专为 [OpenClaw](https://github.com/openclaw/openclaw) AI Agent 设计的**提示工程配置框架**。

### 解决什么问题？

普通 AI Agent 的典型表现：
| 场景 | 问题表现 |
|------|----------|
| 任务失败 | 尝试 1-2 次就放弃，直接说"无法解决" |
| 信息不足 | 不检查上下文，直接问用户"请提供 X" |
| 完成任务 | 做完即止，不验证、不检查边界情况 |

**MoltCare 通过 PUA 框架解决这些问题**，让 Agent 从被动执行升级为主动解决问题。

### 核心设计原则

| 原则 | 说明 |
|------|------|
| **极简配置** | 总大小 ~5KB，无冗余内容 |
| **高信号密度** | 每行配置都有明确目的 |
| **分层架构** | 身份/操作/用户/记忆四层分离 |
| **触发驱动** | 关键词触发特定行为模式 |

---

## 🧠 Core Concepts

### 1. 四层配置架构

```
┌─────────────────────────────────────────┐
│  SOUL.md        ← Agent 灵魂（原则、人格）  │
├─────────────────────────────────────────┤
│  AGENTS.md      ← 操作手册（流程、工具）    │
├─────────────────────────────────────────┤
│  USER.md        ← 用户画像（偏好、约束）    │
├─────────────────────────────────────────┤
│  MEMORY.md      ← 长期记忆（核心信息）      │
└─────────────────────────────────────────┘
```

### 2. 三层智能触发系统

Agent 通过三层架构检测消息，自动激活对应模式。

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: 精确触发 (Signal +2)                              │
│  明确指令式关键词，最高优先级                                │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 语义触发 (Signal +1)                              │
│  自然语言表达，智能识别意图                                  │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Agent 主动评估 (自动)                              │
│  任务完成后自检，自动记录价值信息                            │
└─────────────────────────────────────────────────────────────┘
```

**Layer 1 - 精确触发词：**

| 触发词 | 动作 | 反馈 |
|--------|------|------|
| `多专家讨论:` | 启动多专家模式 | 🧠 |
| `这很重要` | 高优先级记忆 | ⭐ |
| `记住这个` | 添加到学习债务 | 💾 |
| `我偏好` | 记录用户偏好 | 👤 |
| `不要`/`禁止` | 添加约束条件 | 🚫 |

**Layer 2 - 语义触发（自然表达）：**

| 自然表达 | 识别意图 | 动作 |
|----------|----------|------|
| "关键是..." / "核心在于..." | 关键信息 | [⭐] |
| "别忘了..." / "要记住..." | 学习债务 | [💾] |
| "我喜欢..." / "我讨厌..." | 用户偏好 | [👤] |
| "千万不要..." / "绝对不能..." | 约束 | [🚫] |
| "还不行" / "太慢" / "不对" | PUA激活 | [🔥] |
| "架构"/"设计"/"安全"/"风险" | 多专家建议 | [🧠] |

**Layer 3 - Agent 主动评估：**

每次任务完成后，Agent 自检以下问题：
- ✅ 是否解决了用户反复提到的问题？
- ✅ 是否纠正了之前的错误理解？
- ✅ 是否发现了用户的隐含偏好？

满足 ≥2 项 → 自动写入 `memory/YYYY-MM-DD.md` [📝]  
满足 ≥3 项 → 更新 `MEMORY.md` 高信号区 [⭐]

### 3. 任务分层 & Token 优化

将任务按 Token 消耗分层，最大化脚本化、最小化 AI 调用：

| 层级 | 任务类型 | 执行方式 | Token 成本 |
|------|----------|----------|------------|
| **L0** | 数据采集、定时任务 | 纯脚本 | 零 |
| **L1** | 查询展示、格式化 | 纯脚本 | 零 |
| **L2** | 阈值判断、异常检测 | 脚本+条件触发 | 按需 |
| **L3** | 分析、决策、创意 | AI 调用 | 正常 |

**核心原则**: 能用脚本解决的，绝不用 AI。

**决策流程**:
```
任务输入 → 纯数据? → L0/L1 脚本
         → 可规则化? → L2 条件触发
         → 需推理? → L3 AI
```

**审查触发方式**:
- **自动**: 每周一 03:00 定期审查
- **手动**: 说"检查token优化"随时触发
- **里程碑**: 完成任务说"搞定了"自动检查优化机会

---

### 4. 视觉反馈

Agent 检测到触发后，在回复开头显示轻量反馈：

```
[🧠] 启动多专家讨论...
[⭐] 记录关键信息: 配置要改对
[💾] 添加到学习债务: 记得备份
[👤] 记录用户偏好: 简洁回答
[🔥 L2] 任务遇到困难，深度排查中...
[📝] 已记录今日交互 (Layer 3 自动评估)
```

**优先级：** Layer 1 (🔴) > Layer 2 (🟡) > Layer 3 (🟢)，避免重复反馈。

---

## 📁 File Reference

### CORE 配置（OpenClaw 自动加载）

必须位于 `~/.openclaw/workspace/` 根目录。

| 文件 | 作用 | 关键内容 | 必需 |
|------|------|----------|------|
| **AGENTS.md** | 操作手册 | 触发系统、多专家、PUA | ✅ |
| **SOUL.md** | Agent 灵魂 | 七大原则、安全红线 | ✅ |
| **USER.md** | 用户画像 | 偏好、约束、沟通风格 | ✅ |
| **MEMORY.md** | 长期记忆 | Signal 8-10 高优先级 | ✅ |

### OPTIONAL 配置（存在则加载）

位于根目录，仅当文件存在时加载。

| 文件 | 作用 | 关键内容 |
|------|------|----------|
| **IDENTITY.md** | Agent 身份 | 显示名称、Emoji、角色 |
| **TOOLS.md** | 环境工具 | 可用工具、API Keys |
| **HEARTBEAT.md** | 健康检查 | 快速巡检清单 |
| **TOKEN_AUDIT.md** | Token 审查配置 | 每周自动审查调度 |

### MEMORY 模板（按需读取）

位于 `memory/` 子目录，通过 `read` 工具按需读取。

| 路径 | 用途 |
|------|------|
| `memory/YYYY-MM-DD.md` | 每日操作日志 |
| `memory/learning-debt.md` | 待学习项目 |
| `memory/constraints.md` | 约束清单 |
| `memory/preferences.md` | 偏好变更 |
| `memory/token-audit-template.md` | Token 审查模板 |

### 参考文档（不自动加载）

位于 `skill/assets/`，需要时手动查阅。

| 文件 | 用途 |
|------|------|
| **BEST_PRACTICES.md** | 效率最佳实践指南 |

---

## 🔥 PUA Framework

**P**roactive **U**nstoppable **A**gent — 主动不可阻挡的智能体框架

### 三条铁律

| 铁律 | 要求 | 反模式 |
|------|------|--------|
| **穷尽一切** | 未穷尽所有方案前，禁止说"无法解决" | 尝试 1-2 次就放弃 |
| **先做后问** | 先用工具排查，再问用户确认 | 空手问"请确认 X" |
| **主动出击** | 端到端交付，Owner 意识 | 只做"刚好够用"就停 |

### 能动性等级对比

| 行为维度 | 被动 (3.25) | 主动 (3.75) |
|----------|-------------|-------------|
| 遇到报错 | 只看报错本身 | 查上下文 + 搜索 + 关联检查 |
| 需要信息 | 直接问用户 | 先自查，只问确认性问题 |
| 修复完成 | 说"已完成" | 跑验证 + 贴证据 + 查同类问题 |
| 任务边界 | 做明确的部分 | 主动检查上下游/边界情况 |

### 压力升级机制

当任务失败或用户表达沮丧时，自动激活升级：

| 等级 | 触发条件 | 强制动作 |
|------|----------|----------|
| **L1** | "再试试" / "换个方法" | 切换到本质不同的方案 |
| **L2** | "为什么还不行" / 失败 2 次 | 搜索 + 读源码 + 列 3 个假设 |
| **L3** | "你不行啊" / 失败 3 次+ | 完成 7 项检查清单 + 全力排查 |
| **L4** | "我无法解决" / 失败 5 次+ | 拼命模式：最小 PoC + 隔离环境 + 换技术栈 |

### 检查清单 (L3+ 强制执行)

任务卡住时必须完成 3 个核心步骤：
- [ ] **仔细看**: 逐字读完报错、日志、上下文
- [ ] **深入查**: 搜索 + 读源码(50行) + 验证假设
- [ ] **换思路**: 反向思考 + 最小复现 + 换工具/方法

**未完成清单前，禁止说"无法解决"**

---

## 📦 Installation

### 方式一：通过 ClawHub 安装（推荐）

[MoltCare-Open](https://clawhub.com/skills/moltcare-open) 已发布到 ClawHub，一键安装：

```bash
clawhub install moltcare-open
```

**⚠️  安装位置确认**：
安装后文件应该位于 `~/.openclaw/workspace/` **根目录**，结构如下：

**CORE 文件（自动加载）:**
```
~/.openclaw/workspace/
├── AGENTS.md      ✅ 操作手册（必需）
├── SOUL.md        ✅ 灵魂定义（必需）
├── USER.md        ✅ 用户画像（必需）
└── MEMORY.md      ✅ 长期记忆（必需）
```

**OPTIONAL 文件（存在则加载）:**
```
~/.openclaw/workspace/
├── IDENTITY.md     ⚠️ Agent 身份（可选）
├── TOOLS.md        ⚠️ 环境工具（可选）
├── HEARTBEAT.md    ⚠️ 健康检查（可选）
└── TOKEN_AUDIT.md  ⚠️ Token 审查配置（可选）
```

**MEMORY 模板（按需读取）:**
```
~/.openclaw/workspace/memory/
├── learning-debt.md
├── constraints.md
├── preferences.md
└── token-audit-template.md
```

**❌ 错误示例**（不要嵌套子文件夹）:
```
~/.openclaw/workspace/
├── core/             ❌ 错误
├── assets/           ❌ 错误
└── templates/        ❌ 错误
```

**更新到最新版：**
```bash
clawhub update moltcare-open
```

### 方式二：一键脚本安装

**⚠️  注意**：确保文件安装到 `~/.openclaw/workspace/` **根目录**，不要在 workspace 内创建 `core/`、`assets/` 或 `templates/` 子文件夹。


```bash
curl -fsSL https://raw.githubusercontent.com/useens/moltcare-open/master/install.sh | bash
```

此命令会：
1. 下载最新配置模板
2. 复制到 `~/.openclaw/workspace/`
3. 可选：运行配置向导

### 方式三：手动安装

```bash
# 克隆仓库
git clone https://github.com/useens/moltcare-open.git
cd moltcare-open

# 复制核心配置
cp templates/core/*.md ~/.openclaw/workspace/
cp templates/system/*.md ~/.openclaw/workspace/
cp -r templates/memory ~/.openclaw/workspace/

# 运行配置向导（可选）
~/.openclaw/workspace/scripts/onboarding.sh
```

---

## 🔧 Configuration

### 第一步：配置用户画像 (USER.md)

运行交互式向导：
```bash
~/.openclaw/workspace/scripts/onboarding.sh
```

或手动编辑 `~/.openclaw/workspace/USER.md`：

```markdown
## 👤 基本信息
| 项目 | 内容 |
|------|------|
| **称呼** | 你的名字 |
| **身份/角色** | 开发者/产品经理/... |
| **技术水平** | 初级/中级/高级 |

## 💬 沟通偏好
| 维度 | 偏好 |
|------|------|
| **详细程度** | 简洁/适中/详细 |
| **语气** | 正式/友好/随意 |
```

### 第二步：自定义触发词 (AGENTS.md)

编辑 `AGENTS.md` 添加自定义触发：

```markdown
| 触发词 | 信号 | 动作 | 反馈 |
|--------|------|------|------|
| `紧急` | 10 | 立即升级处理 | 🚨 |
| `架构` | 8 | 建议多专家讨论 | 🏗️ |
| `测试` | 7 | 自动生成测试用例 | 🧪 |
```

### 第三步：管理记忆

**高信号记忆** → 写入 `MEMORY.md`（Signal 8-10）：
- 核心偏好
- 绝对禁止事项
- 关键习惯

**日常记录** → 自动写入 `memory/YYYY-MM-DD.md`

**待学习内容** → 写入 `memory/learning-debt.md`

---

## 💡 Usage Examples

### 示例 1：强制多专家模式

```
多专家讨论: 设计一个支持百万并发的消息队列系统
```

Agent 响应：
```
[🧠 多专家模式] 启动多专家讨论

🔍 研究员: 首先验证需求，百万并发的实际 QPS 是多少？
🧠 架构师: 建议采用分层架构，考虑 Kafka/RabbitMQ/Pulsar 选型
💻 工程师: 需要评估团队运维能力
👑 队长: 综合建议：先 POC 验证 Pulsar，同时评估 Kafka 方案
```

### 示例 2：激活 PUA 问题解决

当 Agent 陷入困境时，使用触发词：

```
用户: 为什么还不行？
```

Agent 响应：
```
[🔥 PUA L2] 任务遇到困难，执行深度排查

1. 正在搜索相关解决方案...
2. 读取原始文档...
3. 提出假设：
   - 假设1: 权限问题
   - 假设2: 路径配置错误
   - 假设3: 依赖版本不兼容

正在逐一验证...
```

### 示例 3：记录重要偏好

```
用户: 这很重要，我偏好所有的代码审查都要指出具体行号
```

Agent 响应：
```
[⭐ 高优先级记忆] 已记录核心偏好
```

此偏好将被写入 `MEMORY.md`，所有后续会话都会记住。

---

## 📊 Comparison

| 特性 | MoltCare | AutoGen | LangChain | 裸 Prompt |
|------|----------|---------|-----------|-----------|
| **体积** | ~5KB | 大型框架 | 大型框架 | 无 |
| **专注点** | Agent 认知架构 | 多 Agent 编排 | 工具链集成 | - |
| **问题解决** | PUA 主动强化 | 依赖实现 | 依赖实现 | 被动 |
| **平台绑定** | OpenClaw | Microsoft | Python | 通用 |
| **学习曲线** | 低 | 高 | 中 | 低 |

**MoltCare 适用场景**：
- ✅ 使用 OpenClaw 平台的用户
- ✅ 希望 Agent 更主动、更可靠
- ✅ 追求极简配置、高信号密度
- ❌ 需要复杂多 Agent 编排（选 AutoGen）
- ❌ 需要大量工具集成（选 LangChain）

---

## 🔄 Version History

### v3.2 - "Efficiency & Alignment" (Current)
- ✅ **任务分层 & Token 优化** — L0-L3 四层模型，脚本化降低 90%+ Token 消耗
- ✅ **每周 Token 审查** — 每周一 03:00 自动执行（cron），说"检查token优化"手动触发
- ✅ **里程碑触发优化** — 完成任务说"搞定了"自动检查 Token 优化机会
- ✅ **TOKEN_AUDIT.md** — 新增核心配置文件，定义审查频率和阈值
- ✅ **完整对齐 OpenClaw 启动机制** — CORE/OPTIONAL/MEMORY 三层文件分类
- ✅ **AGENTS.md 精简 43%** — 从 289 行优化至 164 行，功能 100% 保留
- ✅ **PUA 检查清单 7→3** — 合并为"仔细看/深入查/换思路"三大原则
- ✅ **BEST_PRACTICES.md 精简 85%** — 从 467 行压缩至 80 行

### v3.1 - "Three-Layer Trigger Architecture"
- ✅ **Published to ClawHub** - Now installable via `clawhub install moltcare-open`
- ✅ 三层智能触发架构：精确 + 语义 + 主动评估
- ✅ Layer 1: 精确触发词 (Signal +2)
- ✅ Layer 2: 语义触发 (Signal +1) - 自然语言识别
- ✅ Layer 3: Agent 主动评估 - 任务后自检自动记录
- ✅ 反馈优先级系统 (🔴>🟡>🟢)
- ✅ 触发频率预期提升 10-50x

### v2.3.5 - "PUA Framework"
- ✅ 新增 PUA 问题解决强化框架
- ✅ 三条铁律：穷尽一切、先做后问、主动出击
- ✅ L1-L4 压力升级机制
- ✅ 7 项检查清单强制执行

### v2.3.4 - "Core Optimization"
- ✅ HEARTBEAT.md: 111 → 26 lines (-77%)
- ✅ MEMORY.md: 85 → 40 lines (-53%)
- ✅ 优化高频加载文件

### v2.3.3 - "Trigger Visualization"
- ✅ 触发词视觉反馈系统
- ✅ 交互式配置向导
- ✅ 统一 OpenClaw 文档

### v2.3.2 - "Massive Compression"
- ✅ SOUL.md: 55KB → 1.5KB (-97%)
- ✅ AGENTS.md: 22KB → 1.4KB (-94%)
- ✅ USER.md: 17KB → 0.9KB (-95%)

---

## 🤝 Contributing

欢迎贡献！优先需求：
- 新的触发词模式
- 个性化角色模板
- 性能优化
- 文档翻译

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解规范。

---

## 📄 License

MIT © MoltCare Team

---

## 🔗 Related

- [OpenClaw](https://github.com/openclaw/openclaw) - AI Agent 平台
- [ClawHub](https://clawhub.com) - Agent 技能市场
- [MoltCare-Open on ClawHub](https://clawhub.com/skills/moltcare-open) - 本 Skill 的 ClawHub 页面
- [Moltbook](https://moltbook.com) - Agent 社交网络

---

<p align="center">
  <sub>Built with ❤️ for the OpenClaw community</sub>
</p>
