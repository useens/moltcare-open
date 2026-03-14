# MoltCare 持续学习计划

> 任务来源: 用户指令 (2026-03-11)
> 目标: 全网搜索优秀模板，提取精华，升级 moltcare-open

---

## 任务定义

**任务名称**: Template Mining & Evolution
**优先级**: P1 (高优先级持续任务)
**Signal**: 9

### 目标
1. 全网搜索写得好的 Agent/Prompt/配置模板
2. 学习并提取有用元素
3. 应用于 moltcare-open 的升级维护

---

## 搜索范围

### 多源搜索策略 (v3)

| 来源 | 占比 | 内容类型 |
|------|------|----------|
| **GitHub** | 70% | 代码仓库、Awesome合集、官方资源 |
| **Web 文档** | 20% | 官方文档、技术博客、教程 |
| **社区** | 10% | Reddit、HN、Discord、Twitter |

### 核心搜索目标
| 类型 | 来源 | 关注要素 |
|------|------|----------|
| **Agent Framework** | AutoGPT, LangChain, CrewAI, Dify | 架构设计、角色定义 |
| **Prompt Templates** | PromptHero, FlowGPT, GitHub | 结构化提示、思维链 |
| **System Prompts** | Claude, GPT-4, Kimi 官方示例 | 角色定义、约束设置 |
| **配置模板** | dotfiles, devcontainers, scaffolding | 组织方式、模块化设计 |
| **认知框架** | Zettelkasten, PARA, GTD | 知识管理、工作流 |

### 重点关注的优秀项目
- [x] anthropics/prompt-eng-interactive-tutorial
- [x] openai/openai-cookbook (prompts)
- [x] awesome-chatgpt-prompts (152k stars)
- [x] system_prompts_leaks (34k stars)
- [x] agency-agents (41k stars)
- [ ] LangChain AI templates
- [ ] Dify AI workflows
- [ ] Obsidian/PARA templates
- [ ] 各大 Agent 框架的 system prompts

---

## 学习方法

### 1. 每小时自动搜索 (Hourly - 已配置 ✅)

**状态**: ✅ OpenClaw Cron 定时任务已激活 - **多源搜索 v3**
**任务 ID**: `f15ba838-5924-42f9-831e-dfca95ff6aef`

```
频率: 每小时执行完整流程
搜索源: 多源 (GitHub 70% + Web 20% + Community 10%)
脚本: scripts/multi-source-mining.sh

24小时主题覆盖:
┌─────┬─────────────────┬─────────────────┐
│ 小时 │ 来源            │ 主题            │
├─────┼─────────────────┼─────────────────┤
│ 00  │ GitHub          │ Anthropic 官方   │
│ 01  │ Web             │ Anthropic 文档   │
│ 02  │ GitHub          │ OpenAI 官方      │
│ 03  │ Web             │ OpenAI 文档      │
│ 04  │ GitHub          │ LangChain 模板   │
│ 05  │ GitHub          │ Microsoft PF     │
│ 06  │ GitHub          │ Awesome Prompts  │
│ 07  │ GitHub          │ 提示工程指南     │
│ 08  │ GitHub          │ Agent 框架       │
│ 09  │ GitHub          │ Agent 架构       │
│ 10  │ GitHub          │ System Prompts   │
│ 11  │ Web             │ 系统提示设计     │
│ 12  │ GitHub          │ Awesome LLM      │
│ 13  │ GitHub          │ Multi-Agent      │
│ 14  │ GitHub          │ 生产力模板       │
│ 15  │ GitHub          │ PARA/Zettelkasten│
│ 16  │ GitHub          │ Dev Containers   │
│ 17  │ GitHub          │ Dotfiles         │
│ 18  │ GitHub          │ 中文资源         │
│ 19  │ GitHub          │ 中文博客         │
│ 20  │ Community       │ Reddit 讨论      │
│ 21  │ Community       │ Hacker News      │
│ 22  │ Product         │ Product Hunt     │
│ 23  │ Academic        │ Papers/Code      │
└─────┴─────────────────┴─────────────────┘

质量标记:
🔥🔥 >10000 stars
🔥   >1000 stars  
⭐   >100 stars
•    <100 stars

执行方式:
- OpenClaw cron 自动触发
- 每小时整点执行
- isolated session
- 结果 announce 到当前频道

输出: 
  - research/hourly/YYYYMMDD/report_HH.md
  - research/hourly/YYYYMMDD/high_value_queue.txt
```

### 2. 人工审查与精华提取 (Per Discovery)
- 发现高价值模板后立即分析
- 提取可复用的设计模式
- 记录到 template-discoveries.md

### 3. 实验验证 (Bi-weekly)
- 提取的元素先在本地测试
- 验证有效后再合并到 moltcare-open
- 记录测试结果

### 4. 版本迭代 (Monthly)
- 每月发布 moltcare-open 更新
- 合并经过验证的改进
- 更新版本号和 CHANGELOG

---

## 记录规范

### 发现记录格式
```markdown
## [日期] 发现: [模板名称]

**来源**: [URL]
**类型**: [Agent/Prompt/Config/Framework]
**⭐ 质量**: [stars/votes]
**优秀之处**:
- 1. ...
- 2. ...

**可借鉴元素**:
- [ ] 元素1 → 应用到 [SOUL.md/AGENTS.md/USER.md/新功能]
- [ ] 元素2 → ...

**测试计划**:
- 测试方式: ...
- 预期效果: ...
```

---

## 当前待办

- [x] 配置每小时多源搜索
- [x] 优化搜索关键词策略
- [x] 扩展搜索来源 (GitHub+Web+Community)
- [ ] 深度分析已发现的高价值资源
- [ ] 建立模板评分标准

---

## 已发现高价值资源

| 资源 | 来源 | ⭐ | 价值 |
|------|------|-----|------|
| prompts.chat | GitHub | 152k | 社区提示合集 |
| awesome-chatgpt-prompts-zh | GitHub | 58k | 中文场景模板 |
| agency-agents | GitHub | 41k | AI Agent 角色定义 |
| system_prompts_leaks | GitHub | 34k | 真实系统提示 |

---

## 成功指标

| 指标 | 目标 | 当前 |
|------|------|------|
| 每周发现数 | ≥3 个优秀模板 | 4 (第一轮) |
| 每月合并数 | ≥2 个有效改进 | 2 (v2.3.4) |
| moltcare-open 版本 | 稳定迭代 | v2.3.4 |
| 搜索来源覆盖 | GitHub+Web+Community | 70%+20%+10% |

---

*此计划作为 moltcare-open 的持续进化引擎*
*多源搜索策略 v3 - 2026-03-14*
