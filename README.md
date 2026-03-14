<!-- SEO Header -->
<p align="center">
  <img src="https://img.shields.io/badge/OpenClaw-Ready-blue?style=flat-square" alt="OpenClaw">
  <img src="https://img.shields.io/badge/Version-v2.3.5-green?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License">
</p>

<h1 align="center">🦞 MoltCare</h1>
<p align="center"><strong>OpenClaw Agent Configuration Framework</strong></p>
<p align="center">
  <a href="#-quick-start">快速开始</a> •
  <a href="#-what-is-moltcare">介绍</a> •
  <a href="#-features">特性</a> •
  <a href="#-file-structure">文件结构</a>
</p>

---

## 🚀 Quick Start

```bash
curl -fsSL https://raw.githubusercontent.com/useens/moltcare-open/master/install.sh | bash
```

安装完成后，运行配置向导：
```bash
~/.openclaw/workspace/scripts/onboarding.sh
```

---

## 🤔 What is MoltCare?

**MoltCare** 是一套专为 [OpenClaw](https://github.com/openclaw/openclaw) AI Agent 设计的高性能配置框架。

> 核心理念：**极简配置，最大效能**

| 特性 | 描述 |
|------|------|
| ⚡ 轻量核心 | 5KB 总配置体积 |
| 🎯 高信号密度 | 每行配置都有明确用途 |
| 🔧 生产就绪 | 经过实战检验的 Agent 编排模式 |
| 🧠 认知架构 | 内置多专家决策系统 |

---

## ✨ Features

### 智能触发系统

| 触发词 | 信号等级 | 动作 |
|--------|----------|------|
| `多专家讨论:` | 高 | 启动多专家模式 🧠 |
| `这很重要` | 高 | 高优先级记忆 ⭐ |
| `记住这个` | 中 | 添加到学习债务 💾 |
| `我偏好` | 中 | 记录用户偏好 👤 |
| `你不行` | 压力 | 激活 PUA 问题解决模式 🔥 |

### PUA 问题解决强化 (v2.3.5 新增)

当任务陷入困境时，自动激活问题解决强化模式：

- **三条铁律**: 穷尽一切方案、先做后问、主动出击
- **压力升级**: L1-L4 四级压力响应机制
- **7项检查清单**: 确保问题彻底解决

---

## 📁 File Structure

```
~/.openclaw/workspace/
├── SOUL.md          # Agent 灵魂定义 (原则、角色、安全)
├── AGENTS.md        # 操作手册 (触发词、流程、工具)
├── USER.md          # 用户画像 (偏好、技术栈、约束)
├── MEMORY.md        # 长期记忆 (高信号核心记忆)
├── HEARTBEAT.md     # 健康检查 (轻量巡检)
├── TOOLS.md         # 环境工具清单
└── memory/          # 每日日志与学习债务
    ├── YYYY-MM-DD.md
    └── learning-debt.md
```

### 配置文件说明

| 文件 | 用途 | 加载频率 |
|------|------|----------|
| SOUL.md | Agent 人格与核心原则 | 每次会话 |
| AGENTS.md | 操作流程与触发系统 | 每次会话 |
| USER.md | 用户偏好与约束 | 每次会话 |
| MEMORY.md | 核心长期记忆 | 每次会话 |
| HEARTBEAT.md | 健康检查清单 | 手动触发 |

---

## 📦 Installation

### 方式一：一键安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/useens/moltcare-open/master/install.sh | bash
```

### 方式二：手动安装

```bash
git clone https://github.com/useens/moltcare-open.git
cp moltcare-open/templates/core/*.md ~/.openclaw/workspace/
cp -r moltcare-open/templates/memory ~/.openclaw/workspace/
```

---

## 🔧 Configuration

### 1. 配置用户画像

运行交互式向导：
```bash
~/.openclaw/workspace/scripts/onboarding.sh
```

或手动编辑 `USER.md`：
- 你的称呼与角色
- 技术栈偏好
- 沟通风格
- 约束与禁忌

### 2. 自定义触发词

编辑 `AGENTS.md` 添加自定义触发：

```markdown
| 触发词 | 信号 | 动作 |
|--------|------|------|
| `紧急` | 10 | 立即升级处理 |
| `架构` | 8 | 建议多专家讨论 |
```

### 3. 管理记忆

- **高信号记忆** → `MEMORY.md`
- **日常记录** → `memory/YYYY-MM-DD.md`
- **待学习内容** → `memory/learning-debt.md`

---

## 🔄 Version History

| 版本 | 日期 | 主要更新 |
|------|------|----------|
| v2.3.5 | 2026-03-14 | 新增 PUA 问题解决强化框架 |
| v2.3.4 | 2026-03-14 | 高频文件优化 (MEMORY/HEARTBEAT 精简 50%+) |
| v2.3.3 | 2026-03-14 | 触发词可视化反馈系统 |
| v2.3.2 | 2026-03-14 | 核心文件大幅压缩 (减少 95% 体积) |

---

## 🛠️ Advanced Usage

### 强制多专家模式

在消息开头添加触发词：
```
多专家讨论: 设计一个分布式系统...
```

### 激活 PUA 问题解决模式

当 Agent 陷入困境时，使用以下表达：
- "再试试" / "换个方法" → L1 切换方案
- "为什么还不行" → L2 深度排查
- "你不行啊" → L3 全面检查

---

## 🤝 Contributing

欢迎贡献！感兴趣的方向：
- 新的触发词模式
- 个性化角色模板
- 性能优化
- 文档翻译

---

## 📄 License

MIT © MoltCare Team

---

<p align="center">
  <sub>Built with ❤️ for the OpenClaw community</sub>
</p>
