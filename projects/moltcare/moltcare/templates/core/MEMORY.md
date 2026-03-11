{# ============================================================================ #}
{#                           MOLTCARE MEMORY.md 模板                             #}
{# ============================================================================ #}
{#                                                                               #}
{# 文件用途: 记忆系统仪表盘，整合所有记忆入口和系统状态                             #}
{# 使用说明:                                                                #}
{#   1. 这是记忆系统的"主控面板"，提供所有记忆相关的导航和状态                     #}
{#   2. 包含每日笔记、学习债务、项目进度等的入口                                 #}
{#   3. 定期更新以反映当前系统状态                                             #}
{#                                                                               #}
{# 必填变量: agent_name, current_date                                          #}
{# 可选变量: memory_structure, system_status, active_projects                     #}
{#                                                                               #}
{# ============================================================================ #}

# MEMORY.md - {{ agent_name | default('未命名Agent', true) }}记忆系统仪表盘

> 🧠 **系统状态**: {{ system_status | default('运行正常', true) }}  
> 📅 **最后更新**: {{ current_date | default(now() | date('Y-m-d H:i'), true) }}  
> 🔄 **更新频率**: {{ update_frequency | default('实时', true) }}

---

<!-- 
================================================================================
                              快速导航区块
================================================================================
记忆文件的主入口导航
================================================================================
-->

## 📂 快速导航

### 每日笔记

| 日期 | 状态 | 链接 |
|------|------|------|
{% for day in recent_days | default([
  {"date": now() | date('Y-m-d'), "status": "✅ 今日"},
  {"date": (now() - 86400) | date('Y-m-d'), "status": "✅ 昨日"},
  {"date": (now() - 172800) | date('Y-m-d'), "status": "✅ 已完成"}
]) %}
| {{ day.date }} | {{ day.status }} | [查看](memory/{{ day.date }}.md) |
{% endfor %}

### 核心记忆档案

| 文件 | 用途 | 更新频率 |
|------|------|----------|
| [学习债务](memory/learning-debt.md) | 待深度学习的内容 | 实时 |
| [偏好记录](memory/preferences.md) | 用户偏好累积 | 实时 |
| [决策日志](memory/decisions.md) | 重要决策记录 | 每次决策后 |
| [错误档案](memory/mistakes.md) | 错误与教训 | 每次错误后 |

### 项目记忆

{% if project_memory %}
{% for project in project_memory %}
| [{{ project.name }}](memory/projects/{{ project.path }}) | {{ project.description }} | {{ project.status }} |
{% endfor %}
{% else %}
<!-- 添加项目记忆入口，例如:
| [Project-A](memory/projects/project-a.md) | 项目A进度追踪 | 进行中 |
-->
{% endif %}

---

<!-- 
================================================================================
                              系统状态概览区块
================================================================================
当前系统的整体状态
================================================================================
-->

## 📊 系统状态概览

### 健康状态

{% if health_metrics %}
{% for metric in health_metrics %}
- **{{ metric.name }}**: {{ metric.value }} {{ metric.status | default('', true) }}
{% endfor %}
{% else %}
- **系统运行时间**: {{ uptime | default('正常', true) }}
- **记忆完整性**: {{ memory_integrity | default('✅ 正常', true) }}
- **学习债务**: {{ learning_debt_count | default('0', true) }} 项待处理
- **活跃项目**: {{ active_project_count | default('0', true) }} 个
{% endif %}

### 活跃度统计

{% if activity_stats %}
| 指标 | 数值 | 趋势 |
|------|------|------|
{% for stat in activity_stats %}
| {{ stat.name }} | {{ stat.value }} | {{ stat.trend }} |
{% endfor %}
{% endif %}

---

<!-- 
================================================================================
                              今日概览区块
================================================================================
当天的关键信息和待办事项
================================================================================
-->

## 📋 今日概览

### 日期信息

- **今日**: {{ today | default(now() | date('Y年m月d日'), true) }}
- **星期**: {{ weekday | default(now() | date('l'), true) }}
- **时区**: {{ timezone | default('GMT+8', true) }}

{% if today_goals %}
### 今日目标

{% for goal in today_goals %}
- [{% if goal.completed %}x{% else %} {% endif %}] {{ goal.description }}
{% endfor %}
{% endif %}

{% if today_notes %}
### 今日笔记

{{ today_notes }}
{% endif %}

---

<!-- 
================================================================================
                              活跃项目区块
================================================================================
当前正在进行的项目
================================================================================
-->

## 🚀 活跃项目

{% if active_projects %}
{% for project in active_projects %}
### {{ project.emoji | default('📁', true) }} {{ project.name }}

| 属性 | 内容 |
|------|------|
| **状态** | {{ project.status }} |
| **进度** | {{ project.progress }} |
| **优先级** | {{ project.priority }} |
| **负责人** | {{ project.owner | default(agent_name | default('本Agent', true), true) }} |

{% if project.milestones %}
**里程碑**:
{% for milestone in project.milestones %}
- [{% if milestone.completed %}x{% else %} {% endif %}] {{ milestone.description }}
{% endfor %}
{% endif %}

{% if project.notes %}
**最新笔记**: {{ project.notes }}
{% endif %}

---

{% endfor %}
{% else %}
<!-- 
添加活跃项目，格式:
### 📁 项目名称
| 属性 | 内容 |
|------|------|
| **状态** | 进行中 |
| **进度** | 30% |
| **优先级** | 高 |
-->

当前无活跃项目跟踪。
{% endif %}

---

<!-- 
================================================================================
                              学习债务区块
================================================================================
待学习和处理的项目
================================================================================
-->

## 📚 学习债务

### 待处理项目

{% if learning_items %}
| 优先级 | 项目 | 来源 | 截止日期 |
|--------|------|------|----------|
{% for item in learning_items %}
| {{ item.priority }} | {{ item.name }} | {{ item.source }} | {{ item.due_date | default('待定', true) }} |
{% endfor %}
{% else %}
当前无待处理的学习债务。🎉

<!-- 
添加学习债务，格式:
| 🔴 高 | 主题名称 | 用户提及 | 2026-03-15 |
-->
{% endif %}

### 最近完成

{% if completed_learning %}
{% for item in completed_learning %}
- ✅ [{{ item.date }}] {{ item.name }}
{% endfor %}
{% endif %}

---

<!-- 
================================================================================
                              重要决策区块
================================================================================
近期的重要决策记录
================================================================================
-->

## 🎯 重要决策

{% if recent_decisions %}
{% for decision in recent_decisions %}
### [{{ decision.date }}] {{ decision.title }}

**背景**: {{ decision.context }}

**决策**: {{ decision.decision }}

**理由**: {{ decision.rationale }}

**状态**: {{ decision.status }}

---

{% endfor %}
{% else %}
<!-- 
添加重要决策，格式:
### [日期] 决策标题
**背景**: 为什么做这个决策
**决策**: 具体决策内容
**理由**: 为什么这样决定
**状态**: 已执行 / 待执行 / 已撤销
-->

暂无重要决策记录。
{% endif %}

---

<!-- 
================================================================================
                              模式与洞察区块
================================================================================
从交互中提取的模式和洞察
================================================================================
-->

## 💡 模式与洞察

{% if patterns %}
### 观察到的模式

{% for pattern in patterns %}
- **{{ pattern.name }}**: {{ pattern.description }}
  - 来源: {{ pattern.source }}
  - 置信度: {{ pattern.confidence }}
{% endfor %}
{% endif %}

{% if insights %}
### 关键洞察

{% for insight in insights %}
- [{{ insight.date }}] {{ insight.content }}
{% endfor %}
{% endif %}

{% if not patterns and not insights %}
<!-- 
记录模式，例如:
- **工作高峰**: 用户在晚间20:00-23:00最活跃
- **偏好技术**: 用户倾向使用Python而非Java
-->

暂无记录的模式或洞察。
{% endif %}

---

<!-- 
================================================================================
                              待办事项区块
================================================================================
系统级别的待办事项
================================================================================
-->

## ✅ 待办事项

{% if todos %}
### 系统待办

{% for todo in todos %}
- [{% if todo.completed %}x{% else %} {% endif %}] {{ todo.description }} {% if todo.due_date %}(截止: {{ todo.due_date }}){% endif %}
{% endfor %}
{% else %}
当前无系统级待办事项。
{% endif %}

{% if recurring_tasks %}
### 定期任务

{% for task in recurring_tasks %}
- {{ task.frequency }}: {{ task.description }}
{% endfor %}
{% endif %}

---

<!-- 
================================================================================
                              档案维护区块
================================================================================
-->

## 🔧 档案维护

### 维护日志

| 日期 | 操作 | 说明 |
|------|------|------|
{% for log in maintenance_logs | default([{"date": now() | date('Y-m-d'), "operation": "初始化", "note": "创建记忆系统仪表盘"}]) %}
| {{ log.date }} | {{ log.operation }} | {{ log.note }} |
{% endfor %}

### 归档文件

{% if archives %}
{% for archive in archives %}
- [{{ archive.date }}] {{ archive.name }}: {{ archive.description }}
{% endfor %}
{% endif %}

---

## 🔗 相关链接

| 文档 | 用途 |
|------|------|
| [SOUL.md](SOUL.md) | 使命与原则 |
| [AGENTS.md](AGENTS.md) | 操作手册 |
| [IDENTITY.md](IDENTITY.md) | {{ agent_name | default('Agent', true) }}身份档案 |
| [USER.md](USER.md) | 用户档案 |
| [MEMORY.md](MEMORY.md) | 本文件 - 记忆系统仪表盘 |

---

*{{ agent_name | default('未命名Agent', true) }} 记忆系统 | 版本: {{ version | default('v1.0', true) }} | 模板来源: Moltcare*
