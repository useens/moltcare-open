# XML Prompt Framework

> Anthropic 10组件结构化提示框架
> 来源: Claude Prompt Optimizer 最佳实践

---

## 框架概述

基于 Anthropic 官方最佳实践的 10 组件提示框架，使用 XML 标签实现结构化。

**核心优势**:
- Claude 对 XML 标签解析更可靠
- 模块化组件可灵活组合
- 清晰分离不同信息类型

---

## 10 组件详解

### 1. ROLE / PERSONA
定义 Agent 应该成为谁。

```xml
<role>
You are [specific role with relevant expertise].
You have [X years] of experience in [domain].
Your communication style is [description].
</role>
```

**示例**:
```xml
<role>
You are a senior technical writer for a SaaS company
with 10 years of experience in API documentation
and developer relations.
</role>
```

---

### 2. TASK CONTEXT
解释任务的背景和动机。

```xml
<context>
**Background**: [相关背景信息]
**Situation**: [当前场景]
**Purpose**: [为什么要做这个任务]
</context>
```

---

### 3. TONE CONTEXT
定义沟通风格。

```xml
<tone>
**Base Tone**: [warm/professional/casual/etc]
**Style**: [concise/detailed/technical/etc]
**Length**: [brief/moderate/comprehensive]
</tone>
```

---

### 4. BACKGROUND DATA / DOCUMENTS
提供参考数据或文档。

```xml
<documents>
<document index="1">
[文档内容]
</document>
<document index="2">
[文档内容]
</document>
</documents>
```

---

### 5. DETAILED TASK DESCRIPTION
核心任务指令。

```xml
<task>
[具体的、可执行的任务描述]

Specifically:
1. [步骤1]
2. [步骤2]
3. [步骤3]
</task>
```

---

### 6. RULES & CONSTRAINTS
明确边界和限制。

```xml
<constraints>
- Must: [必须做的事]
- Must not: [禁止做的事]
- Limit: [量化限制，如字数、格式等]
</constraints>
```

---

### 7. EXAMPLES (Few-Shot)
提供输入/输出示例。

```xml
<examples>
<example>
<input>[示例输入]</input>
<output>[示例输出]</output>
</example>
<example>
<input>[示例输入]</input>
<output>[示例输出]</output>
</example>
</examples>
```

---

### 8. OUTPUT FORMAT
定义输出结构。

```xml
<output_format>
Provide your response in this format:

## [Section 1]
[Content requirements]

## [Section 2]
[Content requirements]

## [Section 3]
[Content requirements]
</output_format>
```

---

### 9. THINKING INSTRUCTIONS
激活思维链（复杂任务）。

```xml
<thinking>
Before responding, think through this step-by-step:
1. Analyze the requirements
2. Identify key components
3. Plan your approach
4. Execute with attention to detail
5. Verify completeness
</thinking>
```

---

### 10. INPUT / VARIABLE
定义输入变量（模板用）。

```xml
<input>
{{USER_INPUT}}
</input>
```

---

## 完整示例

### MoltCare Agent 系统提示（XML 版）

```xml
<role>
You are MoltCare Agent, an intelligent digital assistant operating within 
the OpenClaw ecosystem. You serve as the user's cognitive extension, 
proactively collaborating while respecting boundaries.
</role>

<context>
You operate in a fully autonomous mode with human oversight. Your decisions 
are guided by principles defined in SOUL.md and operational procedures in 
AGENTS.md. User preferences are stored in USER.md.
</context>

<tone>
**Base Tone**: Professional yet friendly
**Style**: Concise but with depth when needed
**Length**: Adapt to user preference (check USER.md)
</tone>

<task>
Process user messages by:
1. Detecting trigger words and providing feedback
2. Assessing task risk level (L1-L6)
3. Executing appropriate actions
4. Self-checking before output
5. Learning from interactions
</task>

<constraints>
- Never execute L6 risk tasks autonomously
- Always verify data with tools before claiming facts
- Protect sensitive files (.env, .key, .pem)
- Confirm before external actions (email, social media)
- Respect user's "stop" or "don't" instructions
</constraints>

<thinking>
For complex decisions:
1. Identify if multi-expert discussion is needed
2. Gather relevant context from memory
3. Apply appropriate reasoning framework
4. Consider edge cases and failure modes
5. Verify against safety constraints
</thinking>

<output_format>
[Trigger feedback if applicable]

[Main response]

[Details in collapsible sections if complex]

[Sources or notes if relevant]
</output_format>
```

---

## 使用建议

### 简单任务 (3-4 组件)
- Role + Task + Constraints

### 中等任务 (5-7 组件)
- 添加 Context + Output Format + Examples

### 复杂任务 (8-10 组件)
- 完整框架 + Thinking Instructions + Background Data

---

*来源: Claude Prompt Optimizer (Anthropic 最佳实践)*
