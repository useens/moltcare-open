# MoltCare + OpenClaw 机制说明

> ⚙️ **深度机制解析** | 功能映射、实现方式、最佳实践

---

## 📋 目录

1. [功能映射对照表](#功能映射对照表)
2. [记忆系统](#记忆系统)
3. [多专家系统](#多专家系统)
4. [触发词系统](#触发词系统)
5. [推荐的 Skills 搭配](#推荐的-skills-搭配)

---

## 功能映射对照表

| MoltCare 功能 | OpenClaw 对应机制 | 需要 Agent 实现 |
|---------------|-------------------|-----------------|
| SOUL.md 加载 | Project Context 自动注入 | ❌ 无需实现 |
| USER.md 加载 | Project Context 自动注入 | ❌ 无需实现 |
| 触发词自动执行 | 无原生支持 | ✅ Agent 主动识别 |
| 心跳任务 | 无后台守护 | ✅ 外部 cron / 手动触发 |
| Signal 评估 | 无自动评估 | ✅ Agent 判断 |
| 记忆存储 | `write` / `edit` 工具 | ✅ Agent 写入 |
| 记忆检索 | `memory_search` 工具 | ❌ 调用工具即可 |
| 多专家并行 | `sessions_spawn` | ⚠️ 可选，成本高 |
| 工具诚实 | 工具调用自动展示 | ❌ 天然满足 |
| 自检声明 | 无自动添加 | ✅ Agent 决定 |

---

## 记忆系统

**详细实现参见**：[AGENTS.md §记忆管理系统](../core/AGENTS.md)

### 核心要点

```
workspace/
├── MEMORY.md          # Signal 8-10，核心记忆
└── memory/
    ├── YYYY-MM-DD.md  # Signal 6-7，每日日志
    ├── preferences.md # 偏好更新
    ├── learning-debt.md # 学习债务
    └── constraints.md # 约束条件
```

**检索策略**：
- 今日相关 → `memory_search("今天 今日")`
- 用户偏好 → `memory_search("用户偏好")`
- 历史信息 → `memory_search("项目历史")`

---

## 多专家系统

**详细实现参见**：[AGENTS.md §子代理运行策略](../core/AGENTS.md)

### 实现方式选择

| 方式 | 机制 | 成本 | 适用场景 |
|------|------|------|----------|
| **单 Agent 模拟** | 一个 Agent 分角色输出 | 低 | 大多数决策 |
| **sessions_spawn** | 多个独立 Agent 并行 | 高 | 复杂架构决策 |

### 概念定义参见

**专家角色定义**：参见 [SOUL.md §多专家决策系统](../core/SOUL.md)

**输出格式模板**：参见 [SOUL.md §多专家输出模板](../core/SOUL.md)

---

## 触发词系统

**详细实现参见**：[AGENTS.md §触发词系统](../core/AGENTS.md)

### 核心触发词

| 触发词 | Signal | 动作 |
|--------|--------|------|
| "多专家讨论：" | 10 | 启动多专家模式 |
| "这很重要" | 9 | 高优先级记忆 |
| "记住这个" | 8 | 添加到学习债务 |
| "别忘记" | 7 | 创建待办任务 |
| "我偏好" | 6 | 记录用户偏好 |
| "不要" | 8 | 添加约束条件 |

### 实现要点

```python
# 检查位置：Agent 接收消息 → 生成回复前
def check_triggers(user_message: str):
    # 实现代码参见 AGENTS.md
    pass
```

---

## 推荐的 Skills 搭配

| Skill | 用途 | 配合 MoltCare 方式 |
|-------|------|-------------------|
| **vestige** | 记忆系统 | 替代 Signal 评估，自动记忆复习 |
| **healthcheck** | 健康检查 | 定期系统检查（需外部 cron 触发） |
| **clawdo** | 任务队列 | 管理"别忘记"创建的待办 |
| **skill-dev-workflow** | 开发工作流 | 配合 AGENTS.md 场景速查卡 |

---

## 相关文档

| 文档 | 用途 |
|------|------|
| [AGENTS.md](../core/AGENTS.md) | 完整实现：触发词、记忆系统、多专家、子代理 |
| [SOUL.md](../core/SOUL.md) | 概念定义：多专家角色、原则框架 |
| [INTEGRATION_QUICKSTART.md](INTEGRATION_QUICKSTART.md) | 5分钟快速上手 |
| [INTEGRATION_TROUBLESHOOTING.md](INTEGRATION_TROUBLESHOOTING.md) | 问题解决 |

---

*机制说明文档*
*实现细节参见 AGENTS.md 和 SOUL.md*
