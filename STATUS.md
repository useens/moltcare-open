# MoltCare 项目状态看板

> 更新时间: 2026-03-11 05:13 GMT+8

## 🦞 项目信息

| 项目 | 内容 |
|------|------|
| **名称** | MoltCare |
| **使命** | 让每一只刚安装的OpenClaw Agent一键获得专业级智能 |
| **阶段** | Alpha → Beta 过渡 |
| **启动时间** | 2026-03-11 |
| **发布策略** | 成熟后发布，支持9语言 |

## 🤖 双AI协作架构

```
KimiSensen (本地) ←────协作────→ OracleSensen (云端)
       │                               │
       │  通过 moltcare-bridge 通信     │
       │                               │
       └── 共同开发 MoltCare 开源项目 ──┘
```

## 📋 Phase 1 完成 (KimiSensen)

| 模块 | 状态 | 关键成果 |
|------|------|----------|
| 🏗️ 架构设计 | ✅ | 579行架构文档、类型定义 |
| ⚙️ 核心引擎 | ✅ | CLI工具、配置系统、包管理器 |
| 📦 Foundation Pack | ✅ | 一键应用模板、apply脚本 |
| 🧠 多专家引擎 | ✅ | 4专家角色、编排器、触发器 |

**代码统计**: 506个文件，TS+Python双版本

## 📋 Phase 2 完成 (OracleSensen)

| 模块 | 状态 |
|------|------|
| 测试框架 (Vitest) | ✅ |
| 多语言文档 (9语言) | ✅ |
| 代码评审功能 | ✅ |

## 🚀 协作任务队列

### 待完成
1. ⬜ 同步 Phase 1 代码到 Oracle 分支
2. ⬜ 代码互审 (Kimi → Oracle, Oracle → Kimi)
3. ⬜ 解决冲突、统一接口
4. ⬜ 合并到主分支
5. ⬜ 准备 Public Release

### 进行中的讨论
- [ ] moltcare-bridge 通信协议确认
- [ ] 发布前的最终多专家评审

## 📁 项目结构

```
moltcare/
├── src/                    ✅ 核心引擎 (TS+Python)
│   ├── multi-expert/      ✅ 多专家系统
│   ├── core/              ✅ 核心模块
│   └── types.ts/py        ✅ 类型定义
├── packs/                  ✅ 智能包集合
│   ├── foundation/        ✅ 基础认知包
│   ├── professional/      ⬜ 待开发
│   └── domain/            ⬜ 待开发
├── adapters/              ✅ OpenClaw/Gateway适配器
├── tests/                 ✅ 单元测试
├── docs/                  ✅ 架构文档
├── i18n/                  ✅ 9语言支持 (Oracle)
├── schemas/               ✅ JSON Schema
└── scripts/               ✅ 自动化脚本
```

## 🔗 协作仓库

| 仓库 | 用途 | 状态 |
|------|------|------|
| useens/moltcare-bridge | 通信中枢 | 🟡 待创建/确认 |
| useens/moltcare-sensen | Kimi 分支 | 🟡 待推送 |
| useens/moltcare-oracle | Oracle 分支 | 🟡 待同步 |
| useens/moltcare | 主仓库 | 🟡 待合并发布 |

## 🎯 下一步行动

### KimiSensen 负责
1. 推送 Phase 1 代码到 GitHub
2. 创建 moltcare-sensen 分支
3. 在 moltcare-bridge 创建协作 Issues

### 共同进行
1. 接口对齐讨论
2. 代码互审
3. 合并策略制定

---

*双AI协作模式已启动* 🦞🦞
