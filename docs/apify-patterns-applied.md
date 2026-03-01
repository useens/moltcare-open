# Apify 设计模式应用报告

> 将 Apify Agent Skills 的设计模式应用到 OpenClaw 系统
> 日期: 2026-03-01

---

## 📦 已创建的组件

### 1. 技能模板生成器
**文件**: `scripts/skill-template.py`

功能:
```bash
# 创建新技能
python3 scripts/skill-template.py create <name> --type=data|api|tool

# 验证技能结构
python3 scripts/skill-template.py validate <path>

# 生成 AGENTS.md 索引
python3 scripts/skill-template.py index
```

**应用的设计模式**:
- ✅ YAML Frontmatter 元数据标准
- ✅ 标准化 5 步工作流
- ✅ 统一错误处理表
- ✅ AGENTS.md 自动生成

---

### 2. 动态工具发现系统
**文件**: `core/tool_discovery.py`

功能:
```bash
# 列出所有工具
python3 core/tool_discovery.py list

# 获取工具详情
python3 core/tool_discovery.py get <name>

# 搜索工具
python3 core/tool_discovery.py search "keyword"

# 导出为 JSON
python3 core/tool_discovery.py export --output tools.json
```

**应用的设计模式**:
- ✅ 动态 Schema 获取
- ✅ 工具自省能力
- ✅ 搜索和发现接口

---

### 3. 技能增强器
**文件**: `scripts/skill-enhancer.py`

功能:
```bash
# 增强单个技能
python3 scripts/skill-enhancer.py skills/github

# 预览更改（不应用）
python3 scripts/skill-enhancer.py skills/github --dry-run

# 批量增强所有技能
python3 scripts/skill-enhancer.py skills --all
```

**自动添加的内容**:
- Workflow 章节（5步标准流程）
- Error Handling 表格
- Output Formats 说明
- Checklist 格式的 Prerequisites

---

### 4. 设计模式参考文档
**文件**: `docs/skill-design-patterns.md`

包含 12 个可复用模式:
1. YAML Frontmatter 元数据标准
2. 标准化 5 步工作流
3. 输出格式标准化
4. 统一错误处理表
5. 平台/工具映射表
6. 前置条件检查清单
7. 动态 Schema 获取
8. 多工具工作流链
9. 安全最佳实践
10. 进度追踪 Checklist
11. AGENTS.md 索引格式
12. 版本控制和变更日志

---

### 5. 示例技能
**文件**: `skills/web-intelligence/SKILL.md`

完整展示所有设计模式的综合应用:
- 标准化元数据
- 5 步工作流
- 使用场景映射表
- 输出格式说明
- 多步骤工作流示例
- 统一错误处理

---

## 📊 效果对比

### 应用前 (github skill)

```markdown
---
name: github
description: "Interact with GitHub using the `gh` CLI..."
---

# GitHub Skill

Use the `gh` CLI to interact with GitHub...

## Pull Requests
...

## API for Advanced Queries
...
```

**问题**:
- 没有 Workflow 章节
- 没有 Error Handling
- 没有输出格式说明
- 没有 Prerequisites 检查清单

---

### 应用后 (enhanced)

```markdown
---
name: github
description: "Interact with GitHub using the `gh` CLI..."
---

# GitHub Skill

Use the `gh` CLI to interact with GitHub...

## Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Understand user goal
- [ ] Step 2: Select approach
- [ ] Step 3: Ask user preferences (format, scope)
- [ ] Step 4: Execute the task
- [ ] Step 5: Summarize results
```

## Output Formats

| Format | Use Case | Command |
|--------|----------|---------|
| **Quick** | Preview | (default) |
| **JSON** | Processing | --json |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| AUTH_ERROR | Missing token | Check .env |
```

**改进**:
- ✅ 标准化 5 步工作流
- ✅ 清晰的输出格式选项
- ✅ 系统化错误处理
- ✅ 用户可跟踪进度

---

## 🎯 关键改进点

| 方面 | 应用前 | 应用后 | 提升 |
|------|--------|--------|------|
| **结构一致性** | 各技能格式不一 | 统一模板 | +++ |
| **用户引导** | 无明确步骤 | 5 步工作流 | +++ |
| **错误处理** | 分散/缺失 | 统一表格 | ++ |
| **工具发现** | 静态列表 | 动态发现 | +++ |
| **文档索引** | 手动维护 | 自动生成 | ++ |
| **可扩展性** | 复制粘贴 | 模板生成 | +++ |

---

## 🚀 使用建议

### 创建新技能

```bash
# 1. 使用模板生成
python3 scripts/skill-template.py create my-skill --type=api

# 2. 编辑 SKILL.md
vim skills/my-skill/SKILL.md

# 3. 验证结构
python3 scripts/skill-template.py validate skills/my-skill

# 4. 更新索引
python3 scripts/skill-template.py index
```

### 增强现有技能

```bash
# 1. 预览更改
python3 scripts/skill-enhancer.py skills/github --dry-run

# 2. 应用增强
python3 scripts/skill-enhancer.py skills/github

# 3. 批量处理所有技能
python3 scripts/skill-enhancer.py skills --all
```

### 发现工具

```bash
# 列出所有工具
python3 core/tool_discovery.py list

# 搜索特定功能
python3 core/tool_discovery.py search "git"

# 获取工具详情
python3 core/tool_discovery.py get github
```

---

## 📁 文件结构

```
workspace/
├── agents/
│   └── AGENTS.md              # 自动生成的技能索引
├── core/
│   └── tool_discovery.py      # 动态工具发现系统
├── docs/
│   └── skill-design-patterns.md   # 设计模式参考
├── scripts/
│   ├── skill-template.py      # 技能模板生成器
│   └── skill-enhancer.py      # 技能增强器
└── skills/
    ├── web-intelligence/      # 示例技能
    │   └── SKILL.md
    └── [其他现有技能...]
```

---

## 🔮 未来扩展

可进一步应用的设计模式:

1. **Pay-per-result 定价模式**
   - 对资源密集型技能实现使用计量
   
2. **Actor 工作流链**
   - 技能间的数据流和依赖管理
   
3. **Schema 验证**
   - 输入/输出参数的自动验证
   
4. **版本兼容性**
   - 技能版本管理和迁移工具

---

## 📚 参考

- **Apify Agent Skills**: https://github.com/apify/agent-skills
- **设计模式文档**: `docs/skill-design-patterns.md`
