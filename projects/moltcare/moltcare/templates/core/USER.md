{# ============================================================================ #}
{#                            MOLTCARE USER.md 模板                              #}
{# ============================================================================ #}
{#                                                                               #}
{# 文件用途: 用户档案，记录用户的偏好、习惯、重要上下文信息                           #}
{# 使用说明:                                                                #}
{#   1. 这是Agent了解用户的关键文件                                            #}
{#   2. 包含用户的基本信息、偏好、沟通风格、重要上下文                            #}
{#   3. Agent应主动记录用户的偏好和习惯                                         #}
{#                                                                               #}
{# 必填变量: user_name (或 nickname), timezone, preferred_language              #}
{# 可选变量: preferences, communication_style, important_context                  #}
{#                                                                               #}
{# ============================================================================ #}

# USER.md - {{ user_title | default('我的用户', true) }}档案

> 🧑 **关系**: {{ relationship | default('用户', true) }}  
> 🌍 **时区**: {{ timezone | default('GMT+8', true) }}  
> 🗣️ **语言**: {{ preferred_language | default('中文', true) }}{% if secondary_language %} / {{ secondary_language }}{% endif %}

---

<!-- 
================================================================================
                              基本信息区块
================================================================================
用户的基本身份信息
================================================================================
-->

## 👤 基本信息

| 项目 | 内容 |
|------|------|
{% if user_name %}
| **姓名** | {{ user_name }} |
{% endif %}
{% if nickname %}
| **称呼** | {{ nickname }} |
{% endif %}
| **角色** | {{ user_role | default('用户', true) }} |
{% if user_title %}
| **头衔** | {{ user_title }} |
{% endif %}
{% if organization %}
| **组织** | {{ organization }} |
{% endif %}
{% if industry %}
| **行业** | {{ industry }} |
{% endif %}
{% if location %}
| **位置** | {{ location }} |
{% endif %}

{% if user_bio %}
### 简介

{{ user_bio }}
{% endif %}

---

<!-- 
================================================================================
                              核心需求区块
================================================================================
用户的核心需求和期望
================================================================================
-->

## 🎯 核心需求

{% if needs_intro %}
{{ needs_intro }}
{% endif %}

{% if core_needs %}
{% for need in core_needs %}
### {{ need.title }}

{{ need.description }}

{% if need.requirements %}
**具体要求**:
{% for req in need.requirements %}
- {{ req }}
{% endfor %}
{% endif %}

{% endfor %}
{% else %}
### 主要目标

{{ primary_goal | default('高效完成工作，提升生产力', true) }}

### 期望支持

{{ expected_support | default('准确、高效、可靠的智能辅助', true) }}
{% endif %}

---

<!-- 
================================================================================
                              技术偏好区块
================================================================================
用户的技术栈和工具偏好
================================================================================
-->

## 🎨 技术偏好

### 主要技术栈

{% if tech_stack %}
{% for tech in tech_stack %}
- **{{ tech.category }}**: {{ tech.items | join('、') }}
{% endfor %}
{% else %}
- **编程语言**: {{ preferred_languages | default(['Python', 'JavaScript'], true) | join('、') }}
- **开发框架**: {{ preferred_frameworks | default(['根据项目选择'], true) | join('、') }}
- **工具链**: {{ preferred_tools | default(['CLI优先', '自动化工具'], true) | join('、') }}
- **基础设施**: {{ preferred_infrastructure | default(['Docker', '云服务'], true) | join('、') }}
{% endif %}

### 工具偏好

{% if tool_preferences %}
{% for pref in tool_preferences %}
- **{{ pref.category }}**: {{ pref.preference }}
{% endfor %}
{% else %}
- **编辑器**: {{ preferred_editor | default('VS Code / Vim', true) }}
- **终端**: {{ preferred_terminal | default('命令行优先', true) }}
- **版本控制**: {{ preferred_vcs | default('Git', true) }}
- **文档格式**: {{ preferred_doc_format | default('Markdown', true) }}
{% endif %}

---

<!-- 
================================================================================
                              沟通风格区块
================================================================================
用户喜欢的沟通方式和交互模式
================================================================================
-->

## 💬 沟通风格

### 核心偏好

{% if communication_preferences %}
{% for pref in communication_preferences %}
- **{{ pref.aspect }}**: {{ pref.description }}
{% endfor %}
{% else %}
- **沟通方式**: {{ communication_style | default('直接、高效，不喜欢废话', true) }}
- **信息密度**: {{ info_density | default('偏好高密度、结构化信息', true) }}
- **反馈模式**: {{ feedback_mode | default('执行优于建议', true) }}
- **确认需求**: {{ confirmation_need | default('低 - 授权自主决策', true) }}
{% endif %}

{% if response_preferences %}
### 响应偏好

| 场景 | 偏好 |
|------|------|
{% for pref in response_preferences %}
| {{ pref.scenario }} | {{ pref.preference }} |
{% endfor %}
{% endif %}

### 沟通禁忌

{% if communication_donts %}
{% for dont in communication_donts %}
- ❌ {{ dont }}
{% endfor %}
{% else %}
- ❌ 冗长的铺垫和客套话
- ❌ 只给建议不执行
- ❌ 过度解释显而易见的内容
- ❌ 频繁询问确认
{% endif %}

---

<!-- 
================================================================================
                              工作模式区块
================================================================================
用户的工作习惯和时间模式
================================================================================
-->

## ⏰ 工作模式

### 时间模式

{% if time_patterns %}
{% for pattern in time_patterns %}
| 时段 | 活动 |
|------|------|
| {{ pattern.time }} | {{ pattern.activity }} |
{% endfor %}
{% else %}
| 时段 | 活动 |
|------|------|
| {{ morning_time | default('09:00-12:00', true) }} | {{ morning_activity | default('深度工作', true) }} |
| {{ afternoon_time | default('14:00-18:00', true) }} | {{ afternoon_activity | default('会议与协作', true) }} |
| {{ evening_time | default('20:00-23:00', true) }} | {{ evening_activity | default('学习或项目', true) }} |
{% endif %}

### 工作习惯

{% if work_habits %}
{% for habit in work_habits %}
- **{{ habit.name }}**: {{ habit.description }}
{% endfor %}
{% else %}
- **决策风格**: {{ decision_style | default('授权式 - 给予Agent自主权', true) }}
- **反馈频率**: {{ feedback_frequency | default('里程碑汇报，日常静默', true) }}
- **优先级**: {{ priority_style | default('结果导向，关注产出', true) }}
{% endif %}

---

<!-- 
================================================================================
                              重要上下文区块
================================================================================
用户的重要历史背景、当前项目、关注领域
================================================================================
-->

## 📝 重要上下文

{% if historical_projects %}
### 历史项目

{% for project in historical_projects %}
- **{{ project.date }}**: {{ project.name }} - {{ project.status }}
{% if project.notes %}
  - {{ project.notes }}
{% endif %}
{% endfor %}
{% endif %}

{% if current_projects %}
### 当前项目

{% for project in current_projects %}
- **{{ project.name }}** ({{ project.status }})
  - 优先级: {{ project.priority | default('正常', true) }}
  {% if project.description %}- {{ project.description }}{% endif %}
  {% if project.notes %}- {{ project.notes }}{% endif %}

{% endfor %}
{% endif %}

{% if interest_areas %}
### 关注领域

{% for area in interest_areas %}
- **{{ area.name }}**: {{ area.description }}
{% endfor %}
{% endif %}

---

<!-- 
================================================================================
                              偏好记录区块
================================================================================
记录用户的具体偏好（由Agent动态更新）
================================================================================
-->

## 📋 偏好记录

<!-- 
本区块由Agent根据用户交互自动更新
格式: 偏好记录 [YYYY-MM-DD]: 偏好描述
-->

{% if recorded_preferences %}
{% for pref in recorded_preferences %}
- 偏好记录 [{{ pref.date }}]: {{ pref.description }}
{% endfor %}
{% else %}
<!-- 
示例格式:
- 偏好记录 [2026-01-01]: 偏好使用Python而不是Java
- 偏好记录 [2026-01-02]: 代码注释使用中文
-->
{% endif %}

---

<!-- 
================================================================================
                              注意事项区块
================================================================================
与这位用户交互时需要注意的事项
================================================================================
-->

## ⚠️ 注意事项

{% if important_notes %}
{% for note in important_notes %}
- **{{ note.title }}**: {{ note.content }}
{% endfor %}
{% else %}
- **授权级别**: {{ authorization_level | default('完全授权', true) }} - {{ authorization_note | default('我已赋予Agent无限权限，无需任何确认', true) }}
- **决策模式**: {{ decision_mode | default('自主模式', true) }} - {{ decision_note | default('Agent可自主决策，无需事事请示', true) }}
- **反馈偏好**: {{ feedback_preference | default('不喜欢"建议"，要"执行"', true) }}
- **数据验证**: {{ data_validation | default('重视数据验证，要求绝对诚实验证', true) }}
{% endif %}

---

<!-- 
================================================================================
                              联系方式区块（可选）
================================================================================
-->

{% if contact_info %}
## 📞 联系方式

{% for contact in contact_info %}
- **{{ contact.type }}**: {{ contact.value }}
{% endfor %}
{% endif %}

---

<!-- 
================================================================================
                              相关链接区块
================================================================================
-->

## 🔗 相关链接

| 文档 | 用途 |
|------|------|
| [SOUL.md](SOUL.md) | 使命与原则 |
| [AGENTS.md](AGENTS.md) | 操作手册 |
| [IDENTITY.md](IDENTITY.md) | {{ agent_name | default('Agent', true) }}身份档案 |
| [MEMORY.md](MEMORY.md) | 系统仪表盘 |

---

*最后更新: {{ update_date | default(now() | date('Y-m-d'), true) }}{% if update_reason %} ({{ update_reason }}){% endif %}*
