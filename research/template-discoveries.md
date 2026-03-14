# 模板发现日志

> 记录全网搜索发现的优秀模板
> 位置: moltcare-open/research/template-discoveries.md

---

## 2026-03-11 | 第一次全网搜索

**搜索关键词**: 
- Anthropic prompt engineering best practices
- AutoGPT CrewAI agent framework role definition
- system prompt best examples

**发现数量**: 8 个优质仓库

---

## 🏆 高价值发现

### 1. prompt-blueprint (thibaultyou)
**链接**: https://github.com/thibaultyou/prompt-blueprint
**类型**: Prompt Engineering Toolkit
**⭐ 优秀之处**:
- **7阶段专业流程**: 需求收集 → 任务分解 → 框架选择 → 三重草稿 → 评估综合 → QA → 交付
- **统一的 Best Practices Guide**: 整合了 Anthropic, OpenAI, Google 的最佳实践
- **Prompt Engineering Agent**: 能将简单需求转化为生产级 prompt 的 AI Agent
- **企业级输出架构**: 包含角色定义、任务目标、操作上下文、输出规格、质量控制清单

**可借鉴元素**:
- [ ] **7阶段工作流程** → 可优化 AGENTS.md 的多专家流程
- [ ] **Context Architecture Pattern** → [ROLE] [CONTEXT] [TASK] [FORMAT] 结构化
- [ ] **Triple-Draft Development** → A/B/C 变体（效率/可靠性/创新）
- [ ] **Quality Control Checklist** → 添加到 SOUL.md 的自检环节
- [ ] **Executive Summary + Technical Spec + Benchmarks** → 输出格式标准

---

### 2. unified-best-practices__claude_sonnet_4.md
**来源**: prompt-blueprint/guides/
**类型**: Comprehensive Guide
**⭐ 优秀之处**:
- **7大基础原则**:
  1. 清晰和具体性 (Clarity and Specificity)
  2. 战略性上下文提供 (Strategic Context Provision)
  3. 结构化分解 (Structured Decomposition)
  4. 示例驱动学习 (Example-Driven Learning)
  5. 积极指令框架 (Positive Instruction Framing)
  6. 迭代优化 (Iterative Refinement)
  7. 输出格式工程 (Output Format Engineering)
- **Context Architecture Pattern**: [ROLE] [CONTEXT] [TASK] [FORMAT]
- **Few-Shot Architecture**: Instruction + Examples + New Input

**可借鉴元素**:
- [ ] **Context Architecture Pattern** → SOUL.md 的多专家输出格式
- [ ] **Few-Shot Architecture** → AGENTS.md 的示例驱动学习
- [ ] **Example Quality Criteria** → Representative/Diverse/Correct/Consistent
- [ ] **Decomposition Strategies** → Sequential/Hierarchical Breakdown

---

### 3. PromptCraft∞ Elite Agent
**来源**: prompt-blueprint/meta-prompts/
**类型**: Meta-Prompt / AI Agent
**⭐ 优秀之处**:
- **7阶段专业流程**: 比 MoltCare 的 5 专家更全面
- **核心能力定义**: Universal Compatibility, Enterprise Quality, Domain Mastery
- **扩展技术库**: Constitutional Chain-of-Thought, Self-Consistency Ensemble, Tree-of-Thought Plus
- **企业框架**: ROI-Optimized, Compliance-First, Scalability Architecture
- **专业输出架构**: Executive Summary + Technical Specs + Performance Benchmarks + Troubleshooting

**可借鉴元素**:
- [ ] **扩展专家团队**: 从 5 专家 → 7 阶段（可考虑添加 QA Expert, Performance Analyst）
- [ ] **专业输出包**: 包含执行摘要、技术规格、性能基准、故障排除指南
- [ ] **跨模型智能**: 自动检测平台并优化（GPT-4/Claude/Gemini）
- [ ] **动态质量适应**: 性能监控 + 自动改进触发器

---

### 4. agent-crox (pranjal-namdeo)
**链接**: https://github.com/pranjal-namdeo/agent-crox
**类型**: Multi-Agent System
**⭐ 优秀之处**:
- 使用 CrewAI 设计、审查和优化 prompts 和 agent roles
- 专门用于 agent 角色设计的 multi-agent 系统

**可借鉴元素**:
- [ ] CrewAI 的 agent 角色定义模式
- [ ] Agent 间的协作流程（设计 → 审查 → 优化）

---

### 5. openclaw-skills (mikkoxu2311)
**链接**: https://github.com/mikkoxu2311/openclaw-skills
**类型**: OpenClaw Skill Collection
**⭐ 优秀之处**:
- 遵循 Anthropic best practices
- 为 OpenClaw 设计的技能集合
- 生产力、工作效率、学习工作流

**可借鉴元素**:
- [ ] 其他人为 OpenClaw 设计的技能模式
- [ ] 与 MoltCare 的集成可能性

---

### 6. crewai-agentic-starter (walterreid)
**链接**: https://github.com/walterreid/crewai-agentic-starter
**类型**: Agent Role Definition
**⭐ 优秀之处**:
- JSON 文件定义 agent roles, goals, backstories, tool access, delegation permissions
- 5 个 agent 示例: Brand Analyst, Creative Synthesizer, Vignette Designer, Visual Stylist, Prompt Architect

**可借鉴元素**:
- [ ] **结构化角色定义**: role + goal + backstory + tools + delegation
- [ ] JSON 格式的 agent 配置
- [ ] 角色间的权限委托机制

---

### 7. AnthropicAcademy (dustindoesdata)
**链接**: https://github.com/dustindoesdata/AnthropicAcademy
**类型**: Learning Resource
**⭐ 优秀之处**:
- Anthropic Academy 的学习笔记
- Prompt engineering, model behavior, responsible AI development
- Building with Claude 的实践

**可借鉴元素**:
- [ ] Anthropic 官方培训课程的核心概念
- [ ] Responsible AI development 原则

---

### 8. prompt-wizard (lhy818)
**链接**: https://github.com/lhy818/prompt-wizard
**类型**: Prompt Generation Tool
**⭐ 优秀之处**:
- 将用户需求转化为有效 prompts
- 整合了 10 个领先的 Prompt Engineering 资源

**可借鉴元素**:
- [ ] 需求到 prompt 的自动转换逻辑
- [ ] 多资源整合的方法

---

## 📊 发现统计

| 类别 | 数量 | 最高价值 |
|------|------|----------|
| Prompt Engineering Framework | 3 | prompt-blueprint |
| Agent Role Definition | 2 | agent-crox, crewai-agentic-starter |
| Learning Resource | 2 | AnthropicAcademy, unified-best-practices |
| Tool/Template | 2 | prompt-wizard, openclaw-skills |

---

## 🎯 下一步行动

### 立即应用 (本周)
- [ ] 将 **Context Architecture Pattern** ([ROLE][CONTEXT][TASK][FORMAT]) 应用到 SOUL.md
- [ ] 添加 **Quality Control Checklist** 到 AGENTS.md 的自检环节
- [ ] 在 USER.md 模板中加入 **Agent Role Definition** 结构

### 短期验证 (2周内)
- [ ] 测试 **7阶段工作流程** vs 当前 5 专家模式
- [ ] 验证 **Triple-Draft Development** 在 moltcare 中的适用性
- [ ] 实验 **Few-Shot Architecture** 在触发词识别中的应用

### 长期迭代 (月度)
- [ ] 整合 **跨模型智能** 检测和优化
- [ ] 建立 **性能监控 + 自动改进** 机制
- [ ] 开发 **专业输出包** 标准模板

---

## 💡 关键洞察

1. **结构化优于复杂化**: prompt-blueprint 的 7 阶段流程比增加更多专家更有效
2. **Context Architecture 是标准**: [ROLE][CONTEXT][TASK][FORMAT] 模式被多个顶级资源采用
3. **质量清单不可或缺**: 所有优秀模板都有明确的自检/QA环节
4. **输出标准化**: Executive Summary + Technical Spec + Benchmarks 是专业标准
5. **跨平台兼容**: 优秀 prompts 都考虑 GPT-4/Claude/Gemini 的适配

---

*下一批搜索: 2026-03-18 | 重点关注: LangChain Hub, Dify workflows, 官方 System Prompts*
