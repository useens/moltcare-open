# 知识图谱 - 跨来源知识关联

> 多源验证的知识关联图谱，标记LINK-YYYYMMDD-XXX

---

## LINK-20260211-001: Agent记忆系统范式
**来源**: Rowboat (GitHub) + 我的系统
**关联概念**: 显式知识图谱 ↔ 隐式向量记忆

**对比分析**:
| 范式 | 代表 | 特点 | 适用场景 |
|------|------|------|----------|
| 隐式捕获 | Entire | 自动记录所有上下文 | 审计、合规 |
| 显式构建 | Rowboat | 结构化提取关键实体 | 人类可读、可编辑 |
| 分层混合 | 林林v4.2 | 向量+图谱+热数据 | 综合性能 |

**关键实体类型** (来自Rowboat):
- `decisions` - 重要决策
- `commitments` - 承诺/约定  
- `deadlines` - 截止日期
- `relationships` - 关系网络

---

## LINK-20260211-002: 自主Agent安全设计
**来源**: Dexter + Claude Code
**关联概念**: 自主执行 + 安全防护

**共性模式**:
- 任务规划: 自动分解复杂查询为结构化步骤
- 自我验证: 检查自身工作并迭代
- 安全防护:
  - 循环检测机制
  - 步骤限制防止失控
  - 实时数据访问控制

---

## LINK-20260211-003: Agent平台插件生态
**来源**: Compound Engineering Plugin + OpenClaw技能系统
**关联概念**: 跨平台插件市场

**趋同现象**:
- Claude Code → OpenCode/Codex 插件转换
- 配置同步: 个人技能/MCP服务器
- 工作流自动化: Plan → Work → Review → Compound → Repeat

---

## LINK-20260211-004: 生成式UI模式
**来源**: Tambo
**关联概念**: Zod Schema + LLM工具定义

**核心模式**:
- Zod schemas定义组件props
- 自动转换为LLM tool definitions
- Agent调用工具，Tambo渲染结果
- 流式props传输

---

## 知识来源归档

### Rowboat Labs
- **URL**: https://github.com/rowboatlabs/rowboat
- **核心**: 本地优先知识图谱AI助手
- **Signal**: 10
- **纳入**: 知识图谱实体类型、Markdown Vault架构

### EveryInc Compound Engineering
- **URL**: https://github.com/EveryInc/compound-engineering-plugin
- **核心**: Claude Code插件市场
- **Signal**: 8
- **纳入**: 跨平台兼容性、工作流自动化

### Dexter
- **URL**: https://github.com/virattt/dexter
- **核心**: 金融研究自主Agent
- **Signal**: 8
- **纳入**: 安全防护模式、自我验证机制

### Tambo AI
- **URL**: https://github.com/tambo-ai/tambo
- **核心**: React生成式UI SDK
- **Signal**: 7
- **纳入**: Zod Schema驱动组件、流式渲染

### GitButler
- **URL**: https://github.com/gitbutlerapp/gitbutler
- **核心**: AI友好Git客户端
- **Signal**: 7
- **纳入**: 并行分支管理、Agent工作流设计

---

*最后更新: 2026-02-11*
