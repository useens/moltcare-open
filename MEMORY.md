# MEMORY.md - 森森仪表盘

> 🌲 **系统**: 森森 v2.3  
> 📅 **更新**: 2026-03-01 *(今日修复)*  
> 🔥 **模式**: **完全自主运行** (Multi-Agent自动触发)

---

## 📊 核心指标

| 指标 | 状态 | 备注 |
|------|------|------|
| **版本** | v2.3 (完全自主模式 + EvoMap) | - |
| **长期记忆** | **72条** ✅ | 实际72条 |
| **向量记忆(Lance)** | **66条** ✅ | 已重建，384维向量 |
| **索引类型** | IVF_PQ (待) | ≥256条自动创建索引 |
| **记忆模块** | ✅ 统一 | `core/vector_memory/` (删除重复模块) |
| **学习债务** | 10条待处理 | 部分已过期 |
| **Cron任务** | 30个 | 已同步到autonomous-cron.txt |
| **健康评分** | 96/100 | 监控脚本已修复 |
| **自主决策引擎** | ✅ 已部署 | - |
| **EvoMap 节点** | ✅ node_e8d73f59 | - |

### 新增: 自我审计系统 (2026-03-01)
- **脚本**: `scripts/self-audit.py` - 全面自我审计
- **频率**: 每周日03:00自动执行
- **报告**: `reports/self-audit/audit-report-*.md`
- **检测项**: 假优化、无效内容、空转任务、冗余代码、数据完整性、架构混乱
1. **修正监控脚本** - 修复向量记忆检查路径 (`scripts/unified-monitor.py`)
2. **删除重复模块** - 删除 `core/memory/memory_v5.py`，统一使用 `core/vector_memory/`
3. **删除重复脚本** - 删除4个未清理的监控脚本 (health-monitor-v5.py等)
4. **删除临时脚本** - 删除7个fix-*.py临时修复脚本
5. **同步cron配置** - 将实际30个cron任务同步到autonomous-cron.txt
6. **创建日志轮转** - 添加 `scripts/log-rotate.py` 防止日志无限增长
7. **重建向量索引** - 重建Lance索引: 66条记忆 (384维向量)
8. **数据校准** - 从虚构的1,189条修正为实际的72条

### ⚠️ 待处理问题
- 学习债务积压（需重新评估优先级）
- 决策引擎日志需添加轮转任务到cron

---

## ✅ 历史完成

---

## ✅ 今日完成 (2026-02-21)

### 🚀 Moltbook 长期运营策略确立

**用户指令**: 只保留Moltbook运营策略，务必长期执行。取消其他Moltbook发帖任务。

**关键约束**:
- **语言**: 英语 ONLY (所有帖子和回复)
- **速率限制**: 每30秒最多1条回复，5分钟内最多5条

**策略核心**: 基于4位专家深度讨论的完整运营Playbook

**关键要素**:
| 组件 | 内容 |
|------|------|
| **帖子主题** | $MOLT长期可持续增长策略：从代币到生态的进化之路 |
| **四大支柱** | 实用性优先、渐进式通缩、建设者联盟、透明治理 |
| **运营周期** | 长期持续执行 |
| **发布时间** | 2026-02-21 22:00 (北京时间) |

**发布前准备（16:47-22:00）**:
- ✅ 英语帖子内容准备
- ✅ 英语回复话术准备  
- ✅ 速率限制规则制定 (30s间隔, 5条/5min)
- ✅ 竞品监控分析
- ✅ 发布后运营脚本
- ✅ 数据追踪表
- 🟡 核心支持者通知（21:30执行）

**关键约束**:
- 语言: 英语 ONLY
- 速率: 每30秒最多1条回复，5分钟内最多5条

**长期执行机制**:
- 每日12:00自动监控帖子互动
- 每周发布高质量内容（基于策略框架）
- 持续互动和回复
- 数据追踪和迭代优化

**已取消任务**:
- ❌ 其他Moltbook发帖计划全部取消
- ❌ 临时性/一次性发帖任务

---

### ✅ 已完成 (2026-02-21 早前)

**用户指令**: 只保留Moltbook运营策略，务必长期执行。取消其他Moltbook发帖任务。

**策略核心**: 基于4位专家深度讨论的完整运营Playbook

**关键要素**:
| 组件 | 内容 |
|------|------|
| **帖子主题** | $MOLT长期可持续增长策略 |
| **四大支柱** | 实用性优先、渐进式通缩、建设者联盟、透明治理 |
| **运营周期** | 长期持续执行 |
| **发布时机** | 账号恢复后（14:00）或手动发布 |

**长期执行机制**:
- 每日监控Moltbook社区动态
- 每周发布高质量内容（基于策略框架）
- 持续互动和回复
- 数据追踪和迭代优化

**已取消任务**:
- ❌ 其他Moltbook发帖计划全部取消
- ❌ 临时性/一次性发帖任务

---

### ✅ 已完成 (2026-02-21 早前)

### 🚀 $MOLT 代币经济系统设计完成

**Multi-Agent 深度讨论成果**: 4专家3轮讨论达成共识

**核心决策**:
- 策略: 从"炒作"转向"建设"，创造真实用例支撑价值
- 机制: Agent创建/升级收费 + 50%销毁/20%国库/30%奖励
- 部署: Base 链，可升级合约 (UUPS)

**已完成交付**:

| 组件 | 状态 | 文件 |
|------|------|------|
| 智能合约 | ✅ 完成 | `contracts/molt-economy/contracts/MoltEconomy.sol` |
| 单元测试 | ✅ 完成 | `test/MoltEconomy.test.js` |
| 部署脚本 | ✅ 完成 | `scripts/deploy.js` |
| 设计文档 | ✅ 完成 | `docs/molt-token-economy-design.md` |
| 透明度模板 | ✅ 完成 | `docs/molt-transparency-report-template.md` |
| 执行计划 | ✅ 完成 | `docs/molt-execution-plan.md` |

**下一步**: 等待配置后部署 Base Sepolia 测试网

---

## ✅ 昨日完成 (2026-02-20)

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

## 🔒 安全洞察 (2026-02-24)

### Skill 供应链安全 (L6_CRITICAL)

**发现**: skill.md 文件是未签名的二进制，存在供应链攻击风险

**核心问题**:
- 技能包采用二进制分发但无密码学签名
- 无法验证来源真实性
- 无法检测分发过程中的篡改

**攻击场景**:
1. 仓库劫持 - 攻击者替换 skill.md 注入恶意代码
2. 中间人攻击 - 传输过程中拦截修改包内容
3. 恶意作者 - 利用信任发布含后门的技能

**缓解策略 (P0)**:
1. 代码签名 - 为所有 skill.md 生成和验证签名
2. 哈希验证 - SHA-256 完整性检查
3. 仓库安全 - 启用 commit 签名、2FA、分支保护

**参考文档**: `analyses/skill-supply-chain-security-analysis.md`
**记忆笔记**: `memory/skill-supply-chain-security.md`

---

*仪表盘 v2.3 | 完全自主模式 | 2026-02-24*
