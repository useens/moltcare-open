# Contributing to Moltcare

感谢你对 Moltcare 项目的兴趣！本文档将帮助你了解我们的开发模式，以便更好地参与贡献。

## 🎯 项目使命

Moltcare 是一个帮助 OpenClaw Agent 一键提升智能的开源工具。我们的目标是让每一个 Agent 都能轻松获得高质量的智能配置。

## 🏗️ 多子代理开发模式

Moltcare 采用**多子代理并行开发模式**，这是项目的核心开发理念。

### 为什么采用多子代理模式？

- **效率最大化**: 多个专业代理并行工作，避免单点瓶颈
- **质量保障**: 每个代理专注自己的领域，产出更专业
- **可扩展性**: 新功能可以通过新增子代理快速实现

### 子代理角色定义

| 角色 | 职责 | 对应目录 |
|------|------|----------|
| 🏗️ **Architect-Agent** | 项目整体架构、目录结构、技术选型 | `docs/architecture/` |
| ⚙️ **Core-Agent** | SOUL.md、AGENTS.md、IDENTITY.md 模板开发 | `src/templates/core/` |
| 🛠️ **Tools-Agent** | CLI工具、自动化脚本、安装程序 | `src/cli/`, `src/commands/` |
| 📚 **Docs-Agent** | README、文档、教程（多语言） | `docs/`, `README.md` |
| 🧪 **Test-Agent** | 测试框架、验证脚本、示例用例 | `tests/`, `examples/` |
| 🔗 **Integration-Agent** | 代码整合、CI/CD、发布准备 | `.github/workflows/` |

### 开发工作流程

```
新任务/功能需求
    │
    ▼
🧠 指挥官 (森森) 分析任务
    │
    ├── 评估复杂度
    ├── 确定涉及的角色
    └── 制定并行策略
    │
    ▼
🤖 子代理并行执行
    │
    ├── 🏗️ Architect  → 设计架构方案
    ├── ⚙️ Core        → 开发核心模板
    ├── 🛠️ Tools       → 实现CLI功能
    ├── 📚 Docs        → 撰写文档
    ├── 🧪 Test        → 编写测试用例
    └── 🔗 Integration → 准备集成方案
    │
    ▼
🧠 指挥官审查与汇总
    │
    ├── 接收所有子代理产出
    ├── 强制多专家讨论（重要阶段）
    ├── 质量检查
    └── 结果整合
    │
    ▼
📤 提交代码 / 发布版本
```

### 强制多专家讨论触发点

以下阶段**必须**触发多专家讨论：

1. **架构设计完成** - 评审整体架构合理性
2. **核心文件模板完成** - 评审 SOUL/AGENTS/IDENTITY 模板质量
3. **CLI工具完成** - 评审命令设计和实现
4. **Phase 结束前** - 评审整个 Phase 产出
5. **发布前** - 最终质量审查

### 贡献者如何参与

#### 如果你是个人贡献者

1. **Fork 仓库** 并创建你的功能分支
2. **明确你的角色定位**:
   - 修复 bug → 类似 Test-Agent 视角
   - 新增功能 → 根据功能类型选择对应角色视角
   - 文档改进 → Docs-Agent 视角
3. **遵循子代理的产出标准**:
   - 代码需符合对应模块的规范
   - 文档需清晰完整
   - 测试需覆盖核心路径

#### 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**:
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

**示例**:
```
feat(templates): 新增 AGENTS.md 智能生成器

docs: 更新多语言 README 结构
test(cli): 添加 install 命令单元测试
```

### 代码审查标准

每个 PR 必须通过以下检查：

- [ ] **功能完整** - 实现符合需求
- [ ] **测试覆盖** - 核心逻辑有测试
- [ ] **文档更新** - 相关文档已同步
- [ ] **类型安全** - TypeScript 严格模式通过
- [ ] **代码风格** - 符合项目规范

## 🚀 快速开始

### 环境要求

- Node.js >= 18.0.0
- pnpm / npm / yarn

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/useens/moltcare.git
cd moltcare

# 安装依赖
pnpm install

# 开发模式
pnpm dev

# 运行测试
pnpm test

# 构建
pnpm build
```

## 📋 开发任务认领

查看 [Issues](https://github.com/useens/moltcare/issues) 了解当前待办任务。认领任务时请评论说明：

1. 你将以哪个子代理角色视角完成
2. 预计完成时间
3. 是否需要其他子代理协作

## 💬 沟通渠道

- **GitHub Issues**: 功能建议、Bug 报告
- **GitHub Discussions**: 技术讨论、问题咨询
- **Pull Requests**: 代码审查、实现细节讨论

## 📜 行为准则

- 尊重每一位贡献者
- 建设性反馈，避免人身攻击
- 专注于解决问题，而非指责
- 帮助他人成长，分享知识

---

感谢你的贡献！让我们一起打造更好的 Moltcare 🌲
