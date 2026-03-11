# Moltcare 架构设计

> 版本: v1.0  
> 日期: 2026-03-11  
> 状态: 设计阶段

---

## 1. 项目概述

### 1.1 使命
让每一个刚安装的 OpenClaw Agent 都能**一键获得智能**。

### 1.2 核心痛点
- 新安装的 Agent 核心文件 (SOUL.md, AGENTS.md等) 写得差
- 容易出错，缺乏最佳实践
- 没有强制多专家讨论机制
- 多语言支持困难

### 1.3 解决方案
**Moltcare CLI** - 提供一键初始化、增强、诊断和升级功能。

---

## 2. 目录结构

```
moltcare/
├── bin/                      # CLI入口
├── src/
│   ├── commands/             # CLI命令实现
│   │   ├── init.ts
│   │   ├── enhance.ts
│   │   ├── doctor.ts
│   │   ├── upgrade.ts
│   │   ├── lang.ts
│   │   └── discuss.ts
│   ├── templates/            # 核心模板文件
│   │   ├── core/            # 核心文件模板
│   │   │   ├── SOUL.md.hbs
│   │   │   ├── AGENTS.md.hbs
│   │   │   ├── MEMORY.md.hbs
│   │   │   ├── IDENTITY.md.hbs
│   │   │   └── HEARTBEAT.md.hbs
│   │   └── partials/        # 模板片段
│   ├── utils/               # 工具函数
│   │   ├── template-loader.ts
│   │   ├── file-writer.ts
│   │   ├── validator.ts
│   │   └── i18n.ts
│   └── types/               # TypeScript类型
├── docs/                    # 多语言文档
│   ├── zh/
│   ├── en/
│   ├── ja/
│   ├── ko/
│   ├── de/
│   ├── fr/
│   ├── es/
│   ├── ru/
│   └── ar/
├── tests/                   # 测试套件
├── .github/                 # GitHub配置
│   └── workflows/           # CI/CD
├── locales/                 # 翻译文件
├── package.json
├── tsconfig.json
├── jest.config.js
└── README.md
```

---

## 3. CLI命令设计

### 3.1 init [name]
初始化 Agent 核心文件

```bash
moltcare init MyAgent
# 创建:
# - SOUL.md
# - AGENTS.md
# - MEMORY.md
# - IDENTITY.md
# - HEARTBEAT.md
```

**选项**:
- `--lang, -l`: 语言 (默认: zh)
- `--template, -t`: 模板类型 (minimal/standard/full)
- `--force, -f`: 强制覆盖

### 3.2 enhance
一键提升智能 (更新到最佳实践)

```bash
moltcare enhance
# 分析现有文件 → 对比最佳实践 → 生成改进建议 → 应用更新
```

**选项**:
- `--dry-run, -d`: 预览变更
- `--backup, -b`: 创建备份

### 3.3 doctor
诊断核心文件问题

```bash
moltcare doctor
# 检查:
# - 文件完整性
# - 语法正确性
# - 最佳实践遵循度
# - 安全风险
```

### 3.4 upgrade
升级到最新版本

```bash
moltcare upgrade
# 更新模板到最新版本
```

### 3.5 lang <lang>
切换语言

```bash
moltcare lang en
# 重新生成所有核心文件为英文
```

### 3.6 discuss <topic>
强制触发多专家讨论

```bash
moltcare discuss "架构设计决策"
# 创建 GitHub Discussion，标记为多专家讨论
```

---

## 4. 模板系统架构

### 4.1 模板引擎
- **Handlebars** - 逻辑-less 模板，支持 helpers

### 4.2 变量设计

```handlebars
{{! 基础变量 }}
{{name}}              # Agent名称
{{mission}}           # 核心使命
{{role}}              # 角色定位
{{lang}}              # 语言代码
{{date}}              # 创建日期

{{! 条件渲染 }}
{{#if advanced}}
  {{> advanced-features}}
{{/if}}

{{! 循环 }}
{{#each principles}}
  - {{this}}
{{/each}}
```

### 4.3 模板类型

| 类型 | 描述 | 文件数 |
|------|------|--------|
| minimal | 最小配置，仅核心文件 | 3 |
| standard | 标准配置，含完整模板 | 5 |
| full | 完整配置，含高级功能 | 8 |

---

## 5. 多专家讨论触发机制

### 5.1 触发条件

**自动触发** (通过 git hooks):
- PR标题包含 [ARCH], [CORE], [SECURITY], [BREAKING]
- 修改了架构相关文件
- 版本号变化 (major/minor)

**手动触发**:
```bash
moltcare discuss "主题"
```

### 5.2 实现方式

**Git Hook** (`.githooks/pre-push`):
```bash
#!/bin/bash
# 检查是否需要多专家讨论
if git diff --name-only | grep -E "(architecture|core|security)"; then
  echo "⚠️  架构变更检测到，强制多专家讨论"
  moltcare discuss "架构变更审查"
fi
```

**CI 触发** (`.github/workflows/discuss-trigger.yml`):
在 PR 创建时自动检查条件，创建 Discussion。

---

## 6. i18n 国际化方案

### 6.1 语言列表

| 代码 | 语言 | 优先级 |
|------|------|--------|
| zh | 简体中文 | P0 |
| en | English | P0 |
| ja | 日本語 | P1 |
| ko | 한국어 | P1 |
| de | Deutsch | P2 |
| fr | Français | P2 |
| es | Español | P2 |
| ru | Русский | P2 |
| ar | العربية | P2 |

### 6.2 翻译策略

1. **模板翻译** - 所有 .hbs 模板支持 {{lang}} 变量
2. **CLI消息** - 使用 i18n 库，keys 存储在 locales/
3. **文档翻译** - 独立文档目录，人工翻译为主

### 6.3 实现

```typescript
// src/utils/i18n.ts
import i18n from 'i18next';

i18n.init({
  lng: 'zh',
  resources: {
    zh: { translation: require('../../locales/zh.json') },
    en: { translation: require('../../locales/en.json') },
    // ... 其他语言
  }
});
```

---

## 7. 子代理分工

### 7.1 角色定义

```
主会话 (森森 - 指挥官)
    ├── 🤖 架构师代理
    │   └── 输出: architecture.md
    ├── 🤖 核心开发代理
    │   └── 输出: templates/*.hbs
    ├── 🤖 CLI开发代理
    │   └── 输出: src/commands/*.ts
    ├── 🤖 文档代理
    │   └── 输出: docs/*/*.md
    ├── 🤖 测试代理
    │   └── 输出: tests/**/*.test.ts
    └── 🤖 集成代理
        └── 输出: .github/workflows/*.yml
```

### 7.2 接口契约

**模板接口**:
```typescript
interface TemplateData {
  name: string;
  mission: string;
  role: string;
  lang: string;
  date: string;
  features?: string[];
}
```

**命令接口**:
```typescript
interface Command {
  name: string;
  description: string;
  execute(args: string[], options: Options): Promise<Result>;
}
```

---

## 8. 发布策略

### 8.1 阶段

| 阶段 | 版本 | 状态 | 目标 |
|------|------|------|------|
| Alpha | 0.1.x | 开发中 | 内部测试 |
| Beta | 0.9.x | 待开始 | 小范围试用 |
| RC | 1.0.0-rc | 待开始 | 发布候选 |
| GA | 1.0.0 | 待开始 | 正式发布 |

### 8.2 发布流程

1. 更新版本号
2. 运行完整测试
3. 生成 changelog
4. 创建 GitHub Release
5. 发布到 npm
6. 更新文档

---

## 9. 安全考虑

- 模板文件需经过 XSS 检查
- CLI 命令需验证路径 (防止目录遍历)
- 敏感文件保护 (.env, *.key)
- 用户确认机制 (覆盖文件前)

---

*架构设计 v1.0 | 2026-03-11*
