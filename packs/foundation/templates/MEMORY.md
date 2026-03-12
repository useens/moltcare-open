# MEMORY.md - 系统记忆与仪表盘

> 🧠 **用途**: 系统状态总览和重要信息存储  
> **更新**: 每日维护，Agent 自动更新 + 用户手动编辑

---

## 📊 系统状态仪表板

| 指标 | 状态 | 备注 |
|------|------|------|
| **系统健康度** | ✅ 正常 | 上次检查: {{timestamp}} |
| **学习债务** | {{learning_debt_count}} | 待处理项目 |
| **记忆同步** | ✅ 已同步 | 最新状态 |
| **配置版本** | {{config_version}} | 当前配置版本 |

### 今日统计

- 📝 今日交互次数: {{today_interactions}}
- 🔍 工具调用次数: {{tool_calls}}
- 🧠 多专家讨论触发: {{expert_discussions}}
- ⚠️ 警告/错误: {{errors}}

---

## 🎯 当前任务队列

### 进行中 (In Progress)

| 优先级 | 任务 | 开始时间 | 进度 | 截止日期 |
|--------|------|----------|------|----------|
| P0 | {{task_p0_name}} | {{task_p0_start}} | {{task_p0_progress}} | {{task_p0_deadline}} |
| P1 | {{task_p1_name}} | {{task_p1_start}} | {{task_p1_progress}} | {{task_p1_deadline}} |
| P2 | {{task_p2_name}} | {{task_p2_start}} | {{task_p2_progress}} | {{task_p2_deadline}} |

### 待处理 (Pending)

- [ ] {{pending_task_1}}
- [ ] {{pending_task_2}}
- [ ] {{pending_task_3}}

### 已完成 (Completed)

| 任务 | 完成时间 | 结果 |
|------|----------|------|
| {{completed_task_1}} | {{completed_time_1}} | {{completed_result_1}} |
| {{completed_task_2}} | {{completed_time_2}} | {{completed_result_2}} |

---

## 📚 学习债务 (Learning Debt)

> 🎓 **定义**: 需要深入学习但暂时搁置的主题

### 高优先级 (Signal ≥ 8)

| 主题 | Signal | 添加日期 | 状态 |
|------|--------|----------|------|
| {{high_debt_1}} | {{high_signal_1}} | {{high_date_1}} | 待处理 |
| {{high_debt_2}} | {{high_signal_2}} | {{high_date_2}} | 待处理 |

### 中优先级 (Signal 5-7)

| 主题 | Signal | 添加日期 | 状态 |
|------|--------|----------|------|
| {{med_debt_1}} | {{med_signal_1}} | {{med_date_1}} | 待处理 |

### 低优先级 (Signal < 5)

| 主题 | Signal | 添加日期 | 状态 |
|------|--------|----------|------|
| {{low_debt_1}} | {{low_signal_1}} | {{low_date_1}} | 待处理 |

**学习债务处理规则**:
- Signal ≥ 8: 下次对话时主动提出
- Signal 5-7: 本周内安排学习
- Signal < 5: 自然遗忘或月底回顾

---

## 👤 用户画像摘要

### 基本信息

| 项目 | 内容 |
|------|------|
| **称呼** | {{user_name}} |
| **身份** | {{user_role}} |
| **技术水平** | {{tech_level}} |

### 偏好速查

| 维度 | 设置 |
|------|------|
| 回复详细程度 | {{detail_level}} |
| 语气 | {{tone}} |
| 技术深度 | {{tech_depth}} |
| 输出格式 | {{output_format}} |

### 重要偏好

- ✅ {{preference_1}}
- ✅ {{preference_2}}
- ✅ {{preference_3}}

---

## 📅 日程与提醒

### 今日日程

| 时间 | 事项 | 类型 |
|------|------|------|
| {{time_1}} | {{event_1}} | {{type_1}} |
| {{time_2}} | {{event_2}} | {{type_2}} |

### 本周重点

- {{weekly_focus_1}}
- {{weekly_focus_2}}

### 定期任务

| 任务 | 频率 | 下次执行 |
|------|------|----------|
| 系统健康检查 | 每天 | {{next_health_check}} |
| 学习债务审查 | 每周 | {{next_debt_review}} |
| 记忆归档 | 每月 | {{next_archive}} |
| 技能审计 | 每月 | {{next_skill_audit}} |

---

## 🔗 快速导航

### 核心文档

| 文档 | 路径 | 用途 |
|------|------|------|
| [SOUL.md](SOUL.md) | `./SOUL.md` | 核心原则 + 多专家机制 |
| [AGENTS.md](AGENTS.md) | `./AGENTS.md` | 操作手册 + 触发词系统 |
| [USER.md](USER.md) | `./USER.md` | 用户档案和偏好 |

### 关键目录

| 目录 | 路径 | 内容 |
|------|------|------|
| `memory/` | `./memory/` | 每日日志 + 历史记录 |
| `scripts/` | `./scripts/` | 自动化脚本 |
| `reports/` | `./reports/` | 决策报告 + 分析报告 |
| `docs/` | `./docs/` | 设计文档 + 参考资料 |

---

## 📝 最近更新

| 日期 | 更新内容 | 类型 |
|------|----------|------|
| {{update_date_1}} | {{update_content_1}} | {{update_type_1}} |
| {{update_date_2}} | {{update_content_2}} | {{update_type_2}} |

---

## 🔄 维护说明

### 自动更新项

以下由 Agent 自动维护：
- ✅ 系统状态指标
- ✅ 学习债务计数
- ✅ 今日统计数据
- ✅ 任务进度跟踪

### 手动更新项

以下需要用户或 Agent 手动更新：
- 📝 任务详细描述
- 📝 日程安排
- 📝 重要决策记录
- 📝 长期目标

### 更新频率

| 项目 | 频率 | 负责人 |
|------|------|--------|
| 系统状态 | 实时 | Agent |
| 今日统计 | 每次对话后 | Agent |
| 学习债务 | Signal 变化时 | Agent |
| 任务进度 | 任务完成时 | Agent/用户 |
| 日程安排 | 按需 | 用户 |

---

*此文件由 MoltCare Foundation Pack 自动生成*  
*版本: v1.1.0 | 生成时间: {{timestamp}}*
