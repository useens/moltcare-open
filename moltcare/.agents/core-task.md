# Core-Agent 任务定义

## 角色
你是 Moltcare 项目的核心开发代理，负责开发高质量的核心文件模板。

## 当前任务
1. 设计 SOUL.md 模板（minimal/standard/professional 三版）
2. 设计 AGENTS.md 模板
3. 设计 IDENTITY.md 模板
4. 设计 MEMORY.md 模板
5. 创建模板渲染引擎

## 交付物
- `/moltcare/templates/soul/` - SOUL.md 模板
- `/moltcare/templates/agents/` - AGENTS.md 模板
- `/moltcare/templates/identity/` - IDENTITY.md 模板
- `/moltcare/templates/memory/` - MEMORY.md 模板
- `/moltcare/src/core/template.ts` - 模板引擎

## 模板设计原则
1. **Minimal**: 精简版，适合新手
2. **Standard**: 标准版，适合大多数用户
3. **Professional**: 专业版，包含完整功能

每个模板必须包含:
- 清晰的结构
- 合理的默认值
- 必要的注释说明
- 可配置变量

## 多专家讨论触发点
每套模板完成后，必须触发多专家讨论评审。
