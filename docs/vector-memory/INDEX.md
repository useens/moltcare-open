# Vector Memory System Documentation Index
# 向量记忆系统文档索引

> 本文档汇总向量记忆系统的所有文档位置

---

## 📁 文档结构 Document Structure

```
docs/vector-memory/
├── README.md               # 快速开始、安装说明、API参考
├── integration-guide.md    # 集成指南（替换memory_search、迁移数据）
├── architecture.md         # 架构说明（数据流、性能特点）
└── INDEX.md               # 本文档 - 索引和导航

examples/vector-memory/
├── README.md              # 示例说明
├── example_basic.py       # 基础使用示例
├── example_agent_integration.py  # Agent集成示例
└── example_migration.py   # 数据迁移示例

local-memory-system/
├── local_memory.py        # 核心实现（已更新docstring）
├── test_local_memory.py   # 测试套件
├── demo.py               # 快速演示
├── requirements.txt      # 依赖列表
└── README.md            # 本地说明
```

---

## 📖 按角色阅读指南

### 我是使用者 (End User)

想快速上手使用向量记忆系统？

**阅读顺序:**
1. [local-memory-system/README.md](../../local-memory-system/README.md) - 快速开始
2. [README.md](./README.md) - 完整使用说明和API参考
3. [../examples/vector-memory/example_basic.py](../examples/vector-memory/example_basic.py) - 运行示例

### 我是开发者 (Developer)

想将向量记忆系统集成到现有系统？

**阅读顺序:**
1. [integration-guide.md](./integration-guide.md) - 如何替换现有memory_search
2. [README.md#api参考](./README.md#api参考) - API详细说明
3. [../examples/vector-memory/example_agent_integration.py](../examples/vector-memory/example_agent_integration.py) - 集成示例

### 我是架构师 (Architect)

想了解系统设计和技术选型？

**阅读顺序:**
1. [architecture.md](./architecture.md) - 系统架构和数据流
2. [README.md#架构说明](./README.md#架构说明) - 高层架构图
3. [local_memory.py](../../local-memory-system/local_memory.py) - 实现代码

### 我是运维 (DevOps)

需要迁移现有数据或部署系统？

**阅读顺序:**
1. [integration-guide.md#迁移现有记忆数据](./integration-guide.md#迁移现有记忆数据) - 迁移指南
2. [../examples/vector-memory/example_migration.py](../examples/vector-memory/example_migration.py) - 迁移脚本
3. [README.md#配置说明](./README.md#配置说明) - 配置选项

---

## 🔍 快速导航 Quick Navigation

### 按主题 By Topic

| 主题 Topic | 文档 Document | 代码 Code |
|-----------|--------------|-----------|
| **快速开始** | [README.md](./README.md#快速开始) | [demo.py](../../local-memory-system/demo.py) |
| **API参考** | [README.md#api参考](./README.md#api参考) | [local_memory.py](../../local-memory-system/local_memory.py) |
| **架构设计** | [architecture.md](./architecture.md) | - |
| **系统集成** | [integration-guide.md](./integration-guide.md) | [example_agent_integration.py](../examples/vector-memory/example_agent_integration.py) |
| **数据迁移** | [integration-guide.md#数据迁移](./integration-guide.md#数据迁移) | [example_migration.py](../examples/vector-memory/example_migration.py) |
| **配置说明** | [integration-guide.md#配置](./integration-guide.md#配置) | - |

### 按功能 By Function

| 功能 Function | 说明 Description | 参考 Reference |
|--------------|-----------------|----------------|
| **初始化** | 创建数据库和表结构 | [README.md#初始化](./README.md#初始化) |
| **索引文件** | 将文档加入记忆系统 | [README.md#索引文件](./README.md#索引文件) |
| **语义搜索** | 向量相似度搜索 | [README.md#搜索](./README.md#搜索) |
| **关键词搜索** | 传统文本匹配 | [README.md#搜索](./README.md#搜索) |
| **关联发现** | 查找相关文档 | [README.md#关联发现](./README.md#关联发现) |
| **适配器** | 兼容旧接口 | [integration-guide.md#适配器](./integration-guide.md#适配器) |

---

## 🆕 更新日志 Changelog

### v1.0.0 (2026-02-10)

**新增:**
- ✅ 完整的文档体系（README、集成指南、架构说明）
- ✅ 代码docstring完善
- ✅ 3个实用示例（基础使用、Agent集成、数据迁移）
- ✅ 更新MEMORY.md和core-archive.md

**文档:**
- `docs/vector-memory/README.md` - 快速开始和API参考
- `docs/vector-memory/integration-guide.md` - 集成指南
- `docs/vector-memory/architecture.md` - 架构说明
- `docs/vector-memory/INDEX.md` - 文档索引（本文档）
- `examples/vector-memory/` - 示例代码目录

---

## 📞 相关链接 Related Links

- **项目目录**: `~/.openclaw/workspace/local-memory-system/`
- **文档目录**: `~/.openclaw/workspace/docs/vector-memory/`
- **示例目录**: `~/.openclaw/workspace/examples/vector-memory/`
- **核心档案**: `~/.openclaw/workspace/memory/modules/core-archive.md`
- **记忆入口**: `~/.openclaw/workspace/MEMORY.md`

---

*Last Updated: 2026-02-10*
