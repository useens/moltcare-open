# Template Mining 多源搜索策略 v3

> 扩展搜索来源，不仅限于 GitHub

---

## 搜索来源分布

### 1. GitHub (40%) - 代码/模板资源
- 官方仓库 (Anthropic, OpenAI, LangChain)
- Awesome 合集
- 开源 Agent 框架
- Prompt 模板库

### 2. Web 搜索 (30%) - 博客/文档/教程
- 官方文档最佳实践
- 技术博客深度文章
- 案例研究
- 更新比 GitHub 更快

### 3. 社区平台 (20%) - 讨论/经验
- Reddit (r/ChatGPT, r/ClaudeAI, r/LocalLLaMA)
- Hacker News
- Discord 社区
- Twitter/X 技巧分享

### 4. 学术/产品 (10%) - 前沿/创新
- Papers With Code
- arXiv 论文
- Product Hunt 新工具
- 官方博客更新

---

## 按来源分类的关键词

### A. GitHub 精准搜索 (每3小时一次)
```
anthropics/prompt-eng-interactive-tutorial
openai-cookbook examples
awesome-chatgpt-prompts
system-prompts-leaks
agency-agents
```

### B. Web 搜索 - 官方文档 (每3小时一次)
```
site:docs.anthropic.com prompt engineering
site:platform.openai.com prompt best practices
site:blog.langchain.dev agent patterns
site:microsoft.github.io promptflow
```

### C. Web 搜索 - 技术博客 (每3小时一次)
```
"prompt engineering" "best practices" 2024
"system prompt" "template" "anthropic"
"agent framework" "cognitive architecture"
"multi-agent" "role definition" patterns
```

### D. 社区讨论 (每6小时一次)
```
reddit ChatGPT prompts best practices
hacker news prompt engineering techniques
Twitter AI agent personality prompts
```

---

## 24小时轮询计划

| 小时 | 来源 | 关键词类型 |
|------|------|------------|
| 00 | GitHub | Anthropic 官方 |
| 01 | Web | Anthropic 文档 |
| 02 | GitHub | OpenAI 官方 |
| 03 | Web | OpenAI 文档 |
| 04 | GitHub | LangChain 模板 |
| 05 | Web | LangChain 博客 |
| 06 | GitHub | Awesome Prompts |
| 07 | Web | 提示工程最佳实践 |
| 08 | GitHub | Agent 框架 |
| 09 | Web | Agent 架构模式 |
| 10 | GitHub | System Prompts |
| 11 | Web | 系统提示设计 |
| 12 | GitHub | CrewAI/AutoGPT |
| 13 | Web | Multi-agent 模式 |
| 14 | GitHub | 生产力模板 |
| 15 | Web | Obsidian/PARA 模板 |
| 16 | GitHub | 脚手架/工具 |
| 17 | Web | DevContainer/配置 |
| 18 | GitHub | 中文资源 |
| 19 | Web | 中文博客 |
| 20 | Community | Reddit 讨论 |
| 21 | Community | HN 讨论 |
| 22 | Product | Product Hunt |
| 23 | Academic | Papers With Code |

---

## 搜索实现策略

### GitHub API (已可用)
```bash
curl -sL "https://api.github.com/search/repositories?q=..."
```

### Web 搜索 (需要 API Key)
```bash
# Brave Search API (需要配置)
openclaw configure --section web
# 然后使用 web_search 工具
```

### 直接抓取 (备选)
```bash
# 特定网站直接抓取
curl -sL "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering" | grep -oP '(?<=<h2>).*?(?=</h2>)'
```

---

## 质量评估 (多维度)

发现资源后从以下维度评估：

| 维度 | 权重 | 评估标准 |
|------|------|----------|
| **Popularity** | 30% | ⭐/👍/upvotes 数量 |
| **Recency** | 20% | 最近更新时间 |
| **Authority** | 25% | 官方/知名作者 |
| **Utility** | 25% | 可直接应用程度 |

**总分 > 70 分 = 高价值 ⭐⭐⭐**

---

## 执行计划

### 当前限制
- web_search 需要 Brave API Key
- 需要配置: `openclaw configure --section web`

### 备选方案
1. **纯 GitHub 阶段** (现在)
   - 使用 GitHub API 搜索
   - 覆盖 ~40% 优质资源

2. **混合阶段** (配置后)
   - GitHub + Web 搜索
   - 覆盖 ~70% 优质资源

3. **完整阶段** (理想)
   - GitHub + Web + Community
   - 覆盖 ~90% 优质资源

---

## 下一步

是否需要：
1. **配置 Brave API Key** 启用 web_search?
2. **先使用 GitHub + 直接抓取** 作为过渡?
3. **添加其他搜索脚本** (Reddit API, HN API)?

---

*多源搜索策略 v3*
