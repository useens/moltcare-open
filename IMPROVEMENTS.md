# MoltCare 改进记录

> 基于全网模板挖掘的持续升级

---

## v2.3.4 (2026-03-14) - 本次升级

### 升级来源 1
- **Claude Prompt Optimizer** (CheswickDEV) - Anthropic 官方最佳实践
- **Överblick** (jensabrahamsson) - 安全优先多身份框架

### 升级来源 2 (真正应用 prompts.chat)
- **prompts.chat** (152,283 ⭐) - 世界最大开源提示库
- **awesome-chatgpt-prompts-zh** (58,715 ⭐) - 中文场景指南

---

## 新增内容

### 1. XML Prompt Framework ⭐
**文件**: `templates/xml-prompt-framework.md`

Anthropic 10组件结构化提示框架

### 2. 安全检查阶段
**文件**: `templates/core/AGENTS.md` (v2.3.4)

新增输入/输出安全检查 (Överblick SafeLLM Pipeline)

### 3. 角色定义标准 ⭐⭐ (真正应用)
**文件**: `templates/core/SOUL.md` (v2.3.4)

基于 prompts.chat 最佳实践：
- 标准角色模板格式 [ROLE][CONTEXT][CONSTRAINTS][INITIAL]
- 简洁模式定义
- 角色扮演触发词

### 4. 角色模板库 ⭐⭐ (真正应用)
**文件**: `templates/core/AGENTS.md` (v2.3.4)

新增内容:
- **角色扮演触发词**: "扮演..." / "作为..." / "简洁模式" / "像...一样"
- **5个即用角色模板**:
  1. 技术专家 (Technical Expert)
  2. 代码审查者 (Code Reviewer)
  3. 面试官 (Interviewer)
  4. 翻译改进者 (Translator)
  5. 简洁模式 (Concise Mode)

### 5. 提取精华文件
**文件**: `templates/extracted-prompts-chat.md`

包含:
- 3种可复用提示模式 (角色扮演、翻译改进、交互式对话)
- 完整结构示例
- MoltCare 应用建议

---

## 什么是"真正应用"

**不只是保存文件，而是整合到系统行为中：**

| 发现 | 提取 | 应用 |
|------|------|------|
| prompts.chat 152k ⭐ | 保存到 extracted-prompts-chat.md | ❌ 只是提取 |
| 角色扮演模式 | 分析模式结构 | ✅ 整合到 SOUL.md |
| 简洁模式 | 提取约束语句 | ✅ 整合到 AGENTS.md 触发词 |
| 5个角色模板 | 整理模板内容 | ✅ 添加到 AGENTS.md 模板库 |

**应用效果**:
- 用户说 "扮演技术专家" → 系统自动加载技术专家角色约束
- 用户说 "简洁模式" → 自动添加 "只回复结果，不写解释"
- 用户说 "像面试官一样问我" → 进入交互式面试模式

这才是真正的"应用到模板库"

---

## 历史改进

### v2.3.3 (2026-03-11)
- 触发词可视化反馈机制
- 可选的配置向导
- 改进的安装后引导

### v2.3.2
- 初始精简版本

---

## 下一步 (待挖掘)

- [ ] Personality YAML 配置格式
- [ ] 多身份系统架构
- [ ] 插件系统接口
- [ ] 6阶段 SafeLLM 完整实现
- [ ] 更多 prompts.chat 角色模板

---

*升级引擎: 每小时 Template Mining*
