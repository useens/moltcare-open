# Template Mining 关键词策略 v2

> 优化搜索关键词，提高发现质量

---

## 问题分析

### 原关键词的问题
1. **太泛** - "prompt engineering" 返回结果太多，质量参差不齐
2. **重复** - 多个关键词指向同一类资源
3. **缺少细分** - 没有针对具体模板类型
4. **缺少中文** - 忽略了中文社区的优质资源

---

## 新关键词策略

### A类: 高质量特定资源 (优先级最高)

| 时间 | 关键词 | 预期发现 |
|------|--------|----------|
| 00 | anthropic-cookbook prompts system | Anthropic 官方示例 |
| 01 | openai-cookbook prompt engineering | OpenAI 官方指南 |
| 02 | langchain-ai langchain-hub templates | LangChain 官方模板 |
| 03 | microsoft promptflow samples | 微软 Promptflow |

### B类: 框架特定实现 (高价值)

| 时间 | 关键词 | 预期发现 |
|------|--------|----------|
| 04 | crewai-ai agents examples | CrewAI 官方示例 |
| 05 | autogpt core prompts | AutoGPT 核心提示 |
| 06 | dify-ai workflow templates | Dify 工作流模板 |
| 07 | n8n-ai agent workflows | N8N AI 工作流 |

### C类: 系统提示合集 (直接可用)

| 时间 | 关键词 | 预期发现 |
|------|--------|----------|
| 08 | awesome-chatgpt-prompts | 经典提示合集 |
| 09 | system-prompts claude | 系统提示库 |
| 10 | best-system-prompts llm | 最佳系统提示 |
| 11 | llm-prompt-templates | LLM 模板合集 |

### D类: 角色定义模式 (架构学习)

| 时间 | 关键词 | 预期发现 |
|------|--------|----------|
| 12 | ai-agent-persona yaml | AI 角色 YAML |
| 13 | agent-character-definition | Agent 角色定义 |
| 14 | llm-prompt-personality | 提示个性定义 |
| 15 | cognitive-architecture agent | 认知架构 |

### E类: 生产力/工作流模板 (实用)

| 时间 | 关键词 | 预期发现 |
|------|--------|----------|
| 16 | obsidian-templates productivity | Obsidian 模板 |
| 17 | para-method templates | PARA 方法模板 |
| 18 | zettelkasten templates | 卡片盒模板 |
| 19 | second-brain templates | 第二大脑模板 |

### F类: 开发模板/脚手架 (工程化)

| 时间 | 关键词 | 预期发现 |
|------|--------|----------|
| 20 | devcontainer templates vscode | 开发容器模板 |
| 21 | dotfiles manager templates | 配置管理模板 |
| 22 | cookiecutter templates python | 项目脚手架 |
| 23 | github-copilot prompts | Copilot 提示 |

---

## 搜索优化技巧

### GitHub 搜索语法
```
# 高星标仓库
stars:>100 prompt engineering

# 最近更新
pushed:>2024-01-01 agent framework

# 特定语言
language:markdown system prompt

# 优质来源
org:anthropics prompt
org:openai cookbook
org:microsoft samples
```

### 直接访问高价值来源
1. **github.com/anthropics/prompt-eng-interactive-tutorial**
2. **github.com/openai/openai-cookbook/tree/main/examples**
3. **github.com/langchain-ai/langchain-hub**
4. **github.com/crewai-ai/crewai-examples**

---

## 质量评估标准

发现仓库后立即评估：
- [ ] ⭐ > 100 stars?
- [ ] 最近 3 个月有更新?
- [ ] 有清晰的文档?
- [ ] 有可复制的模板?
- [ ] 来自知名组织/作者?

符合 3 项以上才标记为高价值 ⭐⭐⭐

---

## 立即测试新策略

让我用新关键词执行一次搜索测试...
