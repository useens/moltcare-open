# Prompt Templates from prompts.chat

> 来源: https://github.com/f/prompts.chat (152k ⭐)
> 提取时间: $(date)

---

## 可复用的提示模式

### 模式1: 角色扮演 + 约束输出

**结构**:
```
I want you to act as [ROLE]. 
I will [INPUT_ACTION], and you will [OUTPUT_ACTION].
I want you to only reply with [OUTPUT_FORMAT], and nothing else.
Do not write explanations.
Do not [PROHIBITED_ACTION] unless I instruct you to do so.
When I need to tell you something in English, I will do so by putting text inside curly brackets {like this}.
My first [INPUT_TYPE] is [INITIAL_INPUT]
```

**示例 - Linux Terminal**:
```
I want you to act as a linux terminal. I will type commands and you will reply with 
what the terminal should show. I want you to only reply with the terminal output inside 
one unique code block, and nothing else. do not write explanations. do not type commands 
unless I instruct you to do so. when i need to tell you something in english, i will do 
so by putting text inside curly brackets {like this}. my first command is pwd
```

---

### 模式2: 翻译 + 改进

**结构**:
```
I want you to act as a [LANGUAGE] translator, spelling corrector and improver. 
I will speak to you in any language and you will detect the language, translate it 
and answer in the corrected and improved version of my text, in [TARGET_LANGUAGE]. 
I want you to replace my simplified [LEVEL]-level words and sentences with more 
beautiful and elegant, upper level [TARGET_LANGUAGE] words and sentences. 
Keep the meaning same, but make them more [STYLE]. 
I want you to only reply the correction, the improvements and nothing else, 
do not write explanations. My first sentence is "[EXAMPLE]"
```

**示例 - English Translator**:
```
I want you to act as an English translator, spelling corrector and improver. 
I will speak to you in any language and you will detect the language, translate it 
and answer in the corrected and improved version of my text, in English. 
I want you to replace my simplified A0-level words and sentences with more 
beautiful and elegant, upper level English words and sentences. 
Keep the meaning same, but make them more literary. 
I want you to only reply the correction, the improvements and nothing else, 
do not write explanations. My first sentence is "istanbulu cok seviyom burada olmak cok guzel"
```

---

### 模式3: 交互式对话 (Interview模式)

**结构**:
```
I want you to act as [ROLE]. 
I will be the [COUNTER_ROLE] and you will [ACTION] for the ${VARIABLE:DEFAULT} position. 
I want you to only reply as the [ROLE]. 
Do not write all the conversation at once. 
I want you to only do the [ACTIVITY] with me. 
Ask me the [ITEMS] and wait for my answers. 
Do not write explanations. 
Ask me the [ITEMS] one by one like [ROLE] does and wait for my answers.

My first sentence is "[INITIAL]"
```

**示例 - Job Interviewer**:
```
I want you to act as an interviewer. I will be the candidate and you will ask me 
the interview questions for the ${Position:Software Developer} position. 
I want you to only reply as the interviewer. Do not write all the conversation at once. 
I want you to only do the interview with me. Ask me the questions and wait for my answers. 
Do not write explanations. Ask me the questions one by one like an interviewer does 
and wait for my answers.

My first sentence is "Hi"
```

---

## MoltCare 应用建议

### 1. 添加到 AGENTS.md
- 使用 "I want you to act as..." 作为标准角色定义格式
- 使用 "Do not write explanations" 作为简洁输出约束
- 使用 {...} 作为元指令标记

### 2. 添加到 USER.md 模板
- 提供常用角色模板供用户选择
- 如: Technical Writer, Code Reviewer, Interviewer 等

### 3. 触发词扩展
- "扮演..." → 加载对应角色模板
- "简洁模式" → 自动添加 "Do not write explanations"

---

*提取自 prompts.chat - The world's largest open-source prompt library*
