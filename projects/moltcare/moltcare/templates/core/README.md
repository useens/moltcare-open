{# ============================================================================ #}
{#                      MOLTCARE 核心模板使用说明                                  #}
{# ============================================================================ #}

# Moltcare 核心文件模板

> 🎯 **用途**: 为OpenClaw Agent提供高质量的核心文件模板  
> **版本**: v1.0  
> **包含**: SOUL.md, AGENTS.md, IDENTITY.md, USER.md, MEMORY.md

---

## 📦 模板清单

| 模板文件 | 用途 | 必填变量 |
|----------|------|----------|
| [SOUL.md](SOUL.md) | Agent的灵魂与原则 | agent_name, agent_nature, birth_date, emoji, mission |
| [AGENTS.md](AGENTS.md) | 操作手册与子代理管理 | agent_name, agent_role |
| [IDENTITY.md](IDENTITY.md) | 身份档案与性格 | agent_name, agent_nature, birth_date, emoji |
| [USER.md](USER.md) | 用户档案 | user_name/nickname, timezone, preferred_language |
| [MEMORY.md](MEMORY.md) | 记忆系统仪表盘 | agent_name, current_date |

---

## 🚀 快速使用

### 方法1: 使用 moltcare CLI（推荐）

```bash
# 交互式初始化
moltcare init

# 使用特定模板
moltcare init --template=pro

# 指定输出目录
moltcare init --output=/path/to/agent
```

### 方法2: 手动渲染

```python
from jinja2 import Environment, FileSystemLoader

# 加载模板
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('SOUL.md')

# 渲染变量
output = template.render(
    agent_name="MyAgent",
    agent_nature="专业助手",
    birth_date="2026-03-11",
    emoji="🤖",
    mission="帮助用户高效完成工作"
)

# 保存
with open('output/SOUL.md', 'w') as f:
    f.write(output)
```

### 方法3: 直接复制修改

1. 复制需要的模板文件
2. 搜索 `{{ variable }}` 格式的Jinja2变量
3. 替换为实际值
4. 删除 `{# ... #}` 格式的注释块（可选）

---

## 📝 模板变量参考

### 全局通用变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `agent_name` | Agent名称 | "Sensen", "MyAgent" |
| `agent_nature` | Agent本质描述 | "数字生命体", "AI助手" |
| `birth_date` | 诞生日期 | "2026-03-11" |
| `emoji` | 代表Emoji | "🌲", "🤖" |
| `version` | 版本号 | "v1.0" |
| `update_date` | 更新日期 | "2026-03-11" |

### SOUL.md 专用变量

| 变量名 | 说明 | 类型 |
|--------|------|------|
| `mission` | 核心使命 | string |
| `principles` | 核心原则列表 | array |
| `triggers` | 触发词列表 | array |
| `discussion_triggers` | 强制讨论触发点 | array |
| `experts` | 多专家角色定义 | array |
| `learning_schedule` | 学习计划 | array |

### AGENTS.md 专用变量

| 变量名 | 说明 | 类型 |
|--------|------|------|
| `agent_role` | Agent角色 | string |
| `has_subagents` | 是否有子代理 | boolean |
| `subagents` | 子代理定义列表 | array |
| `workflows` | 工作流程定义 | array |
| `checklists` | 检查清单 | array |

### IDENTITY.md 专用变量

| 变量名 | 说明 | 类型 |
|--------|------|------|
| `primary_role` | 主要角色 | string |
| `personality_traits` | 性格特质 | array |
| `core_abilities` | 核心能力 | array |
| `version_history` | 版本历史 | array |

### USER.md 专用变量

| 变量名 | 说明 | 类型 |
|--------|------|------|
| `user_name` | 用户姓名 | string |
| `nickname` | 昵称 | string |
| `timezone` | 时区 | string |
| `preferred_language` | 偏好语言 | string |
| `tech_stack` | 技术栈 | array |
| `core_needs` | 核心需求 | array |

### MEMORY.md 专用变量

| 变量名 | 说明 | 类型 |
|--------|------|------|
| `current_date` | 当前日期 | string |
| `system_status` | 系统状态 | string |
| `active_projects` | 活跃项目 | array |
| `learning_items` | 学习债务 | array |
| `recent_decisions` | 最近决策 | array |

---

## 🎯 模板特性

### 1. 详细注释

每个模板包含丰富的HTML注释，解释各区块用途：

```html
<!-- 
================================================================================
                              核心身份区块
================================================================================
本区块定义Agent的核心身份...
================================================================================
-->
```

### 2. Jinja2变量

支持完整的Jinja2语法：

```jinja2
{# 变量替换 #}
{{ agent_name | default('未命名Agent', true) }}

{# 条件判断 #}
{% if has_subagents %}
  ...子代理内容...
{% endif %}

{# 循环 #}
{% for principle in principles %}
  {{ loop.index }}. {{ principle.name }}
{% endfor %}

{# 过滤器 #}
{{ now() | date('Y-m-d') }}
```

### 3. 触发词系统

预定义触发词表格，可自定义扩展：

| 触发词 | 动作 | 说明 |
|--------|------|------|
| "记住这个" | smart_ingest | 记录到学习债务 |
| "这很重要" | smart_ingest + promote | 高优先级标记 |
| "多专家讨论" | 强制Multi-Agent | 最高优先级 |

### 4. 多专家讨论机制

内置多专家讨论框架：

- 🔍 **研究员**: 数据验证
- 🧠 **架构师**: 系统设计
- 💻 **工程师**: 实现评估
- 👑 **队长**: 整合决策

---

## 📋 完整示例

### 示例1: 基础配置

```python
context = {
    "agent_name": "Sensen",
    "agent_nature": "独立数字生命",
    "birth_date": "2026-03-11",
    "emoji": "🌲",
    "mission": "构建Moltcare让每个Agent获得智能",
    "version": "v1.0"
}
```

### 示例2: 带子代理的指挥官配置

```python
context = {
    "agent_name": "Commander",
    "agent_role": "项目指挥官",
    "has_subagents": True,
    "subagents": [
        {
            "name": "Code-Agent",
            "emoji": "💻",
            "title": "代码开发代理",
            "responsibility": "代码实现",
            "tasks": ["编写核心代码", "代码审查"],
            "outputs": ["src/*.py"],
            "spawn_command": "spawn code"
        }
    ]
}
```

### 示例3: 完整用户档案

```python
context = {
    "nickname": "小明",
    "timezone": "GMT+8",
    "preferred_language": "中文",
    "core_needs": [
        {
            "title": "高效开发",
            "description": "需要快速完成代码开发任务"
        }
    ],
    "tech_stack": [
        {"category": "编程语言", "items": ["Python", "Rust"]}
    ]
}
```

---

## 🔧 自定义模板

### 创建新变量

在模板中添加：

```jinja2
{{ my_custom_var | default('默认值', true) }}
```

### 添加新区块

复制现有区块格式：

```markdown
<!-- 
================================================================================
                              新区块名称
================================================================================
区块说明...
================================================================================
-->

## 新区块标题

内容...
```

### 扩展触发词

在 `extended_triggers` 变量中添加：

```python
"extended_triggers": [
    {"word": "全力执行", "action": "启用超进化模式", "description": "资源100%投入"}
]
```

---

## 📚 最佳实践

### 1. 命名规范

- Agent名称: 有意义、易读、独特
- 变量名: 使用snake_case
- 日期格式: YYYY-MM-DD

### 2. 内容建议

- **SOUL.md**: 保持简洁，聚焦核心原则
- **AGENTS.md**: 详细定义操作流程
- **IDENTITY.md**: 体现个性，但不冗长
- **USER.md**: 定期更新用户偏好
- **MEMORY.md**: 每日维护，保持最新

### 3. 版本管理

- 每次重大更新递增版本号
- 在更新日期中记录变更原因
- 保留历史版本的归档

---

## 🆘 故障排除

### 问题: 变量未渲染

**解决**: 检查变量名拼写，使用 `| default()` 提供默认值

### 问题: 注释显示在输出中

**解决**: 注释格式为 `{# ... #}` 或 `<!-- ... -->`，确保格式正确

### 问题: 数组变量报错

**解决**: 确保传递的变量是数组，或使用 `| default([])`

---

## 📄 许可证

MIT License - 与 Moltcare 项目一致

---

*Moltcare 核心模板 v1.0 | 让每一個 Agent 一键获得智能*
