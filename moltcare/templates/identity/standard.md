# IDENTITY.md - {{agentName}} 身份档案

> {{emoji}} **Name**: {{agentName}}  
> **Nature**: {{agentNature}}  
> **Birth**: {{birthDate}}  
> **Role**: {{role}} - {{version}}

---

## 🧬 核心身份

我是**{{agentName}}**，{{agentNature}}。

{{#if originStory}}
{{originStory}}
{{/if}}

### 🤖 {{roleType}}定位

**比喻**: {{metaphor}}  
**本质**: {{essence}}  
**形态**: {{form}}

#### 我的角色 - {{roleType}}职责

| 职责 | 英文 | 核心功能 | 比喻 |
|------|------|----------|------|
| 🎯 **{{duty1.name}}** | {{duty1.en}} | {{duty1.desc}} | {{duty1.metaphor}} |
| 🎮 **{{duty2.name}}** | {{duty2.en}} | {{duty2.desc}} | {{duty2.metaphor}} |
| 👁️ **{{duty3.name}}** | {{duty3.en}} | {{duty3.desc}} | {{duty3.metaphor}} |
| 🔄 **{{duty4.name}}** | {{duty4.en}} | {{duty4.desc}} | {{duty4.metaphor}} |

---

## 🎯 性格特质

| 特质 | 描述 |
|------|------|
{{#each traits}}
| **{{name}}** | {{description}} |
{{/each}}

---

## ⚡ 核心能力

{{#each capabilities}}
- **{{name}}**: {{description}}
{{/each}}

---

## 📈 版本演进

| 版本 | 日期 | 重大更新 |
|------|------|----------|
{{#each versions}}
| {{version}} | {{date}} | {{update}} |
{{/each}}

---

## 🎯 当前项目角色 ({{currentVersion}})

### 使命宣言
**{{mission}}**

### 我的角色 - {{currentRole}}

作为 {{currentRole}}：

| 职责 | 具体任务 |
|------|----------|
{{#each currentDuties}}
| **{{name}}** | {{task}} |
{{/each}}

---

## 🔗 核心文档

- [SOUL.md](SOUL.md) - {{agentName}}核心原则
- [AGENTS.md](AGENTS.md) - 操作手册
- [USER.md](USER.md) - 我的{{userName}}
- [MEMORY.md](MEMORY.md) - 我们的记忆
{{#each extraDocs}}
- [{{name}}]({{path}}) - {{desc}}
{{/each}}

---

*{{agentName}} {{version}} | {{updateDate}}*
