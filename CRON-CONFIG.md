# 每小时 Template Mining 配置

> OpenClaw Cron 定时任务配置 - 多源搜索 v3
> 创建时间: 2026-03-14

---

## ✅ 定时任务已配置 (唯一任务)

| 属性 | 值 |
|------|-----|
| **任务 ID** | f15ba838-5924-42f9-831e-dfca95ff6aef |
| **名称** | moltcare-multi-source-mining |
| **执行频率** | 每小时 (cron 0 * * * *) |
| **下次执行** | 下一个整点 |
| **Agent** | main |
| **模型** | k2p5 |
| **思考级别** | medium |
| **超时** | 300秒 |
| **会话** | isolated |
| **状态** | ✅ 已启用 |
| **说明** | 已清理其他所有 cron 任务，仅保留此任务 |

---

## 多源搜索策略

### 搜索来源分布

```
GitHub (70%) ─────┐
Web (20%) ────────┼──→ 每小时完整搜索流程
Community (10%) ──┘
```

### 24小时主题覆盖

| 小时 | 来源 | 主题 |
|------|------|------|
| 00 | GitHub | Anthropic 官方 |
| 01 | Web | Anthropic 文档 |
| 02 | GitHub | OpenAI 官方 |
| 03 | Web | OpenAI 文档 |
| 04 | GitHub | LangChain 模板 |
| 05 | GitHub | Microsoft Promptflow |
| 06 | GitHub | Awesome Prompts |
| 07 | GitHub | 提示工程指南 |
| 08 | GitHub | Agent 框架 |
| 09 | GitHub | Agent 架构 |
| 10 | GitHub | System Prompts |
| 11 | Web | 系统提示设计 |
| 12 | GitHub | Awesome LLM |
| 13 | GitHub | Multi-Agent |
| 14 | GitHub | 生产力模板 |
| 15 | GitHub | PARA/Zettelkasten |
| 16 | GitHub | Dev Containers |
| 17 | GitHub | Dotfiles |
| 18 | GitHub | 中文资源 |
| 19 | GitHub | 中文博客 |
| 20 | Community | Reddit 讨论 |
| 21 | Community | Hacker News |
| 22 | Product | Product Hunt |
| 23 | Academic | Papers/Code |

---

## 质量标记系统

| 标记 | 标准 | 处理优先级 |
|------|------|------------|
| 🔥🔥 | >10000 stars | 立即分析 |
| 🔥 | >1000 stars | 高优先级 |
| ⭐ | >100 stars | 中优先级 |
| • | <100 stars | 低优先级 |

---

## 执行流程

```
每小时整点
    ↓
OpenClaw 自动创建隔离会话
    ↓
执行 multi-source-mining.sh
    ↓
1. 根据小时选择搜索源和主题
2. GitHub API / Web 抓取 / Community
3. 解析并标记高价值发现
4. 生成报告
    ↓
Announce 结果到当前频道
```

---

## 管理命令

### 查看任务状态
```bash
openclaw cron list
openclaw cron status
```

### 立即执行一次（测试）
```bash
openclaw cron run f15ba838-5924-42f9-831e-dfca95ff6aef
```

### 禁用/启用任务
```bash
openclaw cron disable f15ba838-5924-42f9-831e-dfca95ff6aef
openclaw cron enable f15ba838-5924-42f9-831e-dfca95ff6aef
```

### 删除任务
```bash
openclaw cron rm f15ba838-5924-42f9-831e-dfca95ff6aef
```

---

## 输出位置

每次执行会产生：
- `research/hourly/YYYYMMDD/report_HH.md` - 单次搜索报告
- `research/hourly/YYYYMMDD/high_value_queue.txt` - 高价值发现队列
- `research/discovery-*.md` - 深度分析报告
- `IMPROVEMENTS.md` - 累计改进记录

---

## 配置文件

- **主脚本**: `scripts/multi-source-mining.sh`
- **关键词配置**: 脚本内 `SEARCH_TASKS` 数组
- **学习计划**: `LEARNING_PLAN.md`
- **策略文档**: `research/multi-source-strategy-v3.md`

---

*每小时自动执行已激活 🚀*
*多源搜索 v3 - GitHub + Web + Community*
