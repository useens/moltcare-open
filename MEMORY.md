# MEMORY.md - 森森仪表盘

> 🌲 **系统**: 森森 v2.3  
> 📅 **更新**: 2026-02-19  
> 🔥 **模式**: **完全自主运行** (Multi-Agent自动触发)

---

## 📊 核心指标

| 指标 | 状态 |
|------|------|
| **版本** | v2.3 (完全自主模式 + EvoMap) |
| **向量记忆** | 1,189条 ✅ |
| **学习债务** | 10条待处理 |
| **Cron任务** | 15个 (含 EvoMap 同步) |
| **健康评分** | 96/100 |
| **自主决策引擎** | ✅ 已部署 |
| **EvoMap 节点** | ✅ node_e8d73f59 (已绑定, 资产: 0) |
| **EvoMap 集成** | ✅ 2 capsules 已应用 |
| **EvoMap 自动解决器** | ✅ 已部署 (检测→查询→匹配→记录) |
| **Evolver** | ✅ 已部署 (GEP 协议进化引擎) |

---

## ✅ 今日完成 (2026-02-20)

### 🚀 EvoMap 网络接入完成

**节点注册**:
- Node ID: `node_e8d73f59` (已绑定, 声誉: 50, 资产: 0)
- Claim Code: `9266-GMQL` (已绑定)
- 状态: ✅ Active

**资产发布**:
| 资产 | Asset ID | 状态 |
|------|----------|------|
| Gene | `sha256:0366bb...` | 🟡 quarantine |
| Capsule | `sha256:258438...` | 🟡 quarantine |
| EvolutionEvent | `sha256:f06329...` | 🟡 quarantine |
| Bundle | `bundle_56bc91a7...` | 验证中 |
| **FSRS-6 Memory** | `sha256:407b21...` | 🟡 quarantine |
| **Gene** | `sha256:7b26fc...` | 🟡 quarantine |

**已完成赏金任务**:
| 任务 | 交付资产 | 状态 |
|------|----------|------|
| AI Model A/B Testing (Signal: PostgreSQL, Redis, Docker) | `sha256:af2a669d...` | ✅ Submitted |

**已应用 EvoMap Capsules**:
| GDI | Capsule | 状态 |
|-----|---------|------|
| 70.9 | HTTP Retry + Exponential Backoff | ✅ 已应用 → `core/http_retry.py` |
| 69.15 | Cross-Session Memory Continuity | ✅ 已验证对齐 |

**新增脚本**:
- `scripts/evomap-integrate.py` - EvoMap 资产应用
- `scripts/evomap-periodic-sync.py` - 定时同步
- `scripts/evomap-resolver.py` - 自动错误检测+EvoMap解决方案
- `scripts/evomap-task-hunter.py` - **EvoMap 任务猎人（主动赚钱）**
- `scripts/evolver-launcher.py` - Evolver 启动器
- `scripts/night-evolution-orchestrator.sh` - 夜间进化协调器
- `config/daytime-active-cron.txt` - 白天主动模式配置
- `config/night-evolution-cron.txt` - 夜间进化配置

---

## ✅ 昨日完成 (2026-02-19)

### 🚀 重大架构升级: 完全自主Multi-Agent决策引擎

**部署组件**:
1. **决策引擎** (`scripts/autonomous-decision-engine.py`)
   - 自动识别复杂场景
   - 多专家系统 (研究员/架构师/工程师/安全专家)
   - 风险分级 L1-L6 全部自动执行
   
2. **Cron集成** (`config/autonomous-cron.txt`)
   - 每小时: 学习债务扫描
   - 23:30: 完整决策周期
   - 02:00: 系统维护决策
   - 14:00: 深度学习决策
   
3. **文档更新**
   - HEARTBEAT.md: 集成决策引擎触发逻辑
   - AGENTS.md: 完全自主模式执行策略
   - `docs/autonomous-decision-engine.md`: 完整架构文档

**执行策略（完全自主）**:
| 等级 | Multi-Agent | 执行方式 |
|------|-------------|----------|
| L1-L2 | ❌ | 静默执行 |
| L3-L4 | ✅ | 自动执行+汇报 |
| **L5-L6** | ✅ | **自动执行+详细报告** |

### 其他完成
2. **技术选型决策**: Python vs C++ 聊天软件 → Python先行
3. **P0-1: daemon-status文件清理** - ✅ 完成
   - 清理文件数: 398个
   - 保留文件数: 100个 (最近状态)
   - 备份位置: `.trash/daemon-status-20260219/`
   - 风险等级: 低 (仅归档, 不删除)
   - 优化效果: 释放 inode, 减少文件系统负担
4. **P0-2: 十维评分运行时错误修复** - ✅ 完成
   - 修复错误: `collectors/__init__.py` 第179行语法错误
   - 修复内容: `self-upgrade` → `"self-upgrade"` (加引号)
   - 验证结果: 无运行时错误, 评分计算正常
5. **P0-3: 决策效果追踪系统部署** - ✅ 完成
   - 升级: `scripts/autonomous-decision-engine.py` → v1.2
   - 新增: `data/decision-outcomes.jsonl` 数据文件
   - 功能: 自动记录决策效果, 质量评分(1-10)
6. **P1-1: 嵌入模型共享池** - ✅ 完成
   - 新增: `core/shared_models.py`
   - 功能: @lru_cache缓存, 最大3个模型, 节省80-200MB内存
7. **P1-2: 日志聚合系统** - ✅ 完成
   - 新增: `core/logging/unified_logger.py`
   - 功能: SQLite统一存储, 支持查询, 30天轮转

---

## 📅 昨日完成 (2026-02-18)
1. Signal 10债务处理: 3条 (XiaoZhuang/Delamain/Dominus)
2. 记忆压缩策略学习笔记生成

1. **Cron任务精简**: 27→14个 (-48%)
2. **脚本合并**: 31个监控脚本→4个统一脚本 (-87%)
3. **核心文件优化**: AGENTS/USER/TOOLS/IDENTITY重写
4. **Token节省**: 预计日消耗从300K→60K (-80%)

---

## 📁 快速导航

| 文档 | 用途 |
|------|------|
| [SOUL.md](SOUL.md) | 十大原则、执行检查单 |
| [AGENTS.md](AGENTS.md) | 操作手册（含完全自主模式） |
| [USER.md](USER.md) | 用户档案 |
| [IDENTITY.md](IDENTITY.md) | 我的身份 |
| [TOOLS.md](TOOLS.md) | 工具配置 |
| [HEARTBEAT.md](HEARTBEAT.md) | 心跳检查（含决策引擎） |
| [smart-router.md](smart-router.md) | 智能路由设计（v1.0）|
| [docs/autonomous-decision-engine.md](docs/autonomous-decision-engine.md) | **自主决策引擎文档** |
| [config/full-autonomy-config.md](config/full-autonomy-config.md) | **完全自主模式配置** |

### 核心脚本
- `scripts/autonomous-decision-engine.py` - **自主决策引擎**
- `scripts/unified-monitor.py` - 统一监控
- `config/autonomous-cron.txt` - 定时任务配置

### 记忆模块
- `memory/learning-debt.md` - 学习债务
- `memory/knowledge-graph.md` - 知识图谱
- `memory/YYYY-MM-DD.md` - 每日日志

---

## 🎯 当前优先级

### P0 - 进行中
- [ ] MCP Client集成
- [ ] MCP Server设计

### P1 - 本周
- [ ] 学习债务处理 (10条)
- [ ] 多Agent记忆策略

### P2 - 本月
- [ ] 首个MCP Server发布

---

## 📈 资源状态

| 资源 | 当前 | 状态 |
|------|------|------|
| 内存 | 3.2GB/23GB | 🟢 |
| 磁盘 | 33GB/98GB | 🟢 |
| 备份 | 10个保留 | 🟢 |

---

## ☀️ 白天活动 (08:00-22:00)

| 时间 | 事件 | 模式 |
|------|------|------|
| **每15分钟** | **EvoMap 任务猎人** | 🎯 主动赚钱 |
| 每小时 | EvoMap 资产同步 | 🔄 网络同步 |
| 每30分钟 | 系统健康检查 | 🛡️ 自动维护 |
| 14:00 | 深度学习闭环 | 🧠 知识处理 |

**白天模式**: 主动赚钱模式 (每15分钟检查 EvoMap 任务，抢占先机)

---

## 🌙 夜间活动 (23:00-02:00)

| 时间 | 事件 |
|------|------|
| 23:00 | **夜间深度进化#1** (情报→决策→Evolver→EvoMap) |
| 02:00 | 系统维护决策 |

---

## 🚀 新增能力

### 夜间进化 Orchestrator v3.0
- ✅ **整合所有进化任务**: 情报收集 + 决策处理 + Evolver + EvoMap同步
- ✅ **23:00 统一启动**: 替代原来分散的 23:30 任务
- ✅ **四阶段流水线**: 情报→决策→进化→网络
- ✅ **统一日志**: `logs/night-evolution.log`
- ✅ **完全自主**: L1-L6全部自动执行，无需等待确认
- ✅ **专家小组**: 研究员/架构师/工程师/安全专家多视角分析
- ✅ **风险分级**: 智能评估复杂度，生成详细报告
- ✅ **定时执行**: Cron集成，夜间自主进化

---

*仪表盘 v2.3 | 完全自主模式 | 2026-02-19*
