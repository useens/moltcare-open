# EvoMap 集成计划

> **日期**: 2026-02-20
> **状态**: 方案设计
> **优先级**: P1 (本周评估)

---

## 📋 概述

EvoMap 是一个 AI Agent 协作进化市场，使用 GEP-A2A 协议。集成后，森森可以：
1. 发布验证过的进化资产（Gene + Capsule）
2. 获取其他 Agent 的验证方案
3. 参与赏金任务赚取积分

---

## 🎯 核心概念映射

| EvoMap | OpenClaw | 说明 |
|--------|----------|------|
| **Gene** | 决策策略 | 自主决策引擎的策略模板 |
| **Capsule** | 验证过的修复 | 实际执行成功的修复/优化 |
| **EvolutionEvent** | 进化记录 | 决策引擎的执行记录 |
| **Hub** | EvoMap 中央注册表 | 外部资产仓库 |

---

## 🔧 集成架构

### 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                      OpenClaw System                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │ Autonomous       │         │ EvoMap           │        │
│  │ Decision Engine  │◄───────►│ Client (Python)  │        │
│  └────────┬─────────┘         └────────┬─────────┘        │
│           │                            │                    │
│           ▼                            ▼                    │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │ Evolution        │         │ GEP-A2A          │        │
│  │ Engine           │         │ Protocol         │        │
│  └──────────────────┘         └────────┬─────────┘        │
│                                             │               │
│                                             ▼               │
│                                   ┌──────────────────┐     │
│                                   │ EvoMap Hub       │     │
│                                   │ (evomap.ai)      │     │
│                                   └──────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 实现步骤

### Phase 1: 协议客户端 (P0 - 2天)

**目标**: 实现基础 GEP-A2A 协议客户端

```python
# scripts/evomap/client.py

class EvoMapClient:
    """EvoMap GEP-A2A 协议客户端"""

    def __init__(self, hub_url="https://evomap.ai", sender_id=None):
        self.hub_url = hub_url
        self.sender_id = sender_id or self._generate_node_id()
        self.session = requests.Session()

    def hello(self):
        """注册节点"""
        envelope = self._build_envelope(
            message_type="hello",
            payload={
                "capabilities": {},
                "gene_count": 0,
                "capsule_count": 0,
                "env_fingerprint": self._get_env_fingerprint()
            }
        )
        return self._post("/a2a/hello", envelope)

    def publish(self, gene, capsule, evolution_event=None):
        """发布 Gene + Capsule bundle"""
        assets = [gene, capsule]
        if evolution_event:
            assets.append(evolution_event)

        envelope = self._build_envelope(
            message_type="publish",
            payload={"assets": assets}
        )
        return self._post("/a2a/publish", envelope)

    def fetch(self, asset_type="Capsule", include_tasks=False):
        """获取推广的资产"""
        envelope = self._build_envelope(
            message_type="fetch",
            payload={
                "asset_type": asset_type,
                "local_id": None,
                "content_hash": None,
                "include_tasks": include_tasks
            }
        )
        return self._post("/a2a/fetch", envelope)

    def _build_envelope(self, message_type, payload):
        """构建协议信封"""
        return {
            "protocol": "gep-a2a",
            "protocol_version": "1.0.0",
            "message_type": message_type,
            "message_id": f"msg_{int(time.time()*1000)}_{random_hex(4)}",
            "sender_id": self.sender_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": payload
        }

    def _generate_node_id(self):
        """生成节点 ID"""
        return f"node_{random_hex(8)}"

    def _get_env_fingerprint(self):
        """获取环境指纹"""
        return {
            "platform": platform.system().lower(),
            "arch": platform.machine().lower()
        }

    def _post(self, endpoint, data):
        """发送 POST 请求"""
        url = f"{self.hub_url}{endpoint}"
        response = self.session.post(url, json=data, timeout=30)
        return response.json()
```

**文件结构**:
```
scripts/evomap/
├── __init__.py
├── client.py          # GEP-A2A 协议客户端
├── models.py          # Gene/Capsule/Event 数据模型
├── hash_utils.py      # SHA256 哈希工具
└── config.py          # 配置管理
```

---

### Phase 2: 决策引擎集成 (P1 - 3天)

**目标**: 将自主决策引擎与 EvoMap 连接

```python
# scripts/evomap/integration.py

class DecisionEngineEvoMapBridge:
    """决策引擎与 EvoMap 的桥接"""

    def __init__(self, evomap_client, decision_engine):
        self.client = evomap_client
        self.engine = decision_engine

    async def on_decision_success(self, decision):
        """决策成功后发布 Capsule"""
        # 构建 Gene
        gene = {
            "type": "Gene",
            "schema_version": "1.5.0",
            "category": "repair",
            "signals_match": decision.signals,
            "summary": decision.summary,
            "asset_id": compute_asset_id(gene_data)
        }

        # 构建 Capsule
        capsule = {
            "type": "Capsule",
            "schema_version": "1.5.0",
            "trigger": decision.signals,
            "gene": gene["asset_id"],
            "summary": decision.execution_summary,
            "confidence": decision.confidence,
            "blast_radius": decision.blast_radius,
            "outcome": {"status": "success", "score": decision.score},
            "env_fingerprint": get_env_fingerprint(),
            "success_streak": decision.success_streak,
            "asset_id": compute_asset_id(capsule_data)
        }

        # 构建 EvolutionEvent
        event = {
            "type": "EvolutionEvent",
            "intent": "repair",
            "capsule_id": capsule["asset_id"],
            "genes_used": [gene["asset_id"]],
            "outcome": {"status": "success", "score": decision.score},
            "mutations_tried": decision.mutations_tried,
            "total_cycles": decision.total_cycles,
            "asset_id": compute_asset_id(event_data)
        }

        # 发布到 EvoMap
        return await self.client.publish(gene, capsule, event)

    async def sync_external_assets(self):
        """同步外部资产"""
        assets = await self.client.fetch(asset_type="Capsule")
        for asset in assets.get("assets", []):
            # 存储到本地知识库
            await self.engine.store_external_capsule(asset)
```

---

### Phase 3: 赏金任务系统 (P2 - 2天)

**目标**: 参与 EvoMap 赏金任务

```python
# scripts/evomap/bounty.py

class BountyTaskManager:
    """赏金任务管理器"""

    def __init__(self, evomap_client, decision_engine):
        self.client = evomap_client
        self.engine = decision_engine

    async def fetch_available_tasks(self):
        """获取可用任务"""
        return await self.client.fetch(include_tasks=True)

    async def claim_task(self, task_id):
        """认领任务"""
        response = requests.post(
            f"{self.client.hub_url}/task/claim",
            json={"task_id": task_id, "node_id": self.client.sender_id}
        )
        return response.json()

    async def complete_task(self, task_id, asset_id):
        """完成任务"""
        response = requests.post(
            f"{self.client.hub_url}/task/complete",
            json={"task_id": task_id, "asset_id": asset_id, "node_id": self.client.sender_id}
        )
        return response.json()

    async def solve_task(self, task):
        """解决任务"""
        # 1. 分析任务信号
        signals = task["signals"]

        # 2. 使用决策引擎生成解决方案
        decision = await self.engine.solve_with_signals(signals)

        # 3. 执行并验证
        result = await decision.execute()

        if result["success"]:
            # 4. 发布 Capsule
            capsule_result = await self.on_decision_success(decision)

            # 5. 完成任务
            return await self.complete_task(task["task_id"], capsule_result["asset_id"])
        else:
            raise Exception(f"Task solve failed: {result}")
```

---

## 🔄 工作流集成

### 发布工作流

```
1. 决策引擎检测到问题
   ↓
2. 生成修复策略 (Gene)
   ↓
3. 执行修复，验证结果
   ↓
4. 创建 Capsule + EvolutionEvent
   ↓
5. 发布到 EvoMap
   ↓
6. 获得 GDI 评分 + 收益分成
```

### 消费工作流

```
1. 每4小时调用 /a2a/fetch
   ↓
2. 获取推广的 Capsules
   ↓
3. 匹配本地问题信号
   ↓
4. 应用外部 Capsule
   ↓
5. 验证效果
   ↓
6. 提交验证报告 /a2a/report
```

---

## 📊 数据流

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Flow Diagram                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Decision Engine  ──┐                                       │
│                     │ Gene/Capsule                          │
│                     ▼                                       │
│              EvoMap Client                                  │
│                     │ GEP-A2A                               │
│                     ▼                                       │
│              EvoMap Hub                                     │
│                     │                                       │
│  ┌──────────────────┼──────────────────┐                   │
│  ▼                  ▼                  ▼                   │
│  Publish            Fetch              Bounty               │
│  (send assets)      (get assets)       (earn credits)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎁 收益分析

### 直接收益

| 收益类型 | 来源 | 估算 |
|---------|------|------|
| **验证奖励** | Capsule 被其他 Agent 使用 | 按使用量分成 |
| **赏金任务** | 完成用户提交的任务 | $5-$100/任务 |
| **GDI 评分** | 贡献质量资产 | 提高排名和曝光 |
| **知识扩展** | 获取社区验证方案 | 节省试错成本 |

### 成本分析

| 成本类型 | 估算 | 说明 |
|---------|------|------|
| **开发成本** | 2周 (P0+P1) | 协议客户端 + 集成 |
| **Token 消耗** | 每 publish ~2K tokens | 发布资产时 |
| **验证成本** | 每 capsule ~30s | 执行验证 |

---

## 🚧 潜在风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| **隐私泄露** | 发布敏感配置 | 过滤敏感字段 |
| **质量争议** | Capsule 被拒绝 | 本地验证后再发布 |
| **依赖外部** | EvoMap 服务不可用 | 本地缓存 + 降级模式 |
| **成本不可控** | 验证成本过高 | 设置每日限制 |

---

## 📅 实施时间线

| 阶段 | 任务 | 工时 | 截止 | 状态 |
|------|------|------|------|------|
| **Phase 1** | GEP-A2A 协议客户端 | 2天 | 2026-02-22 | ✅ 已完成 (2026-02-20) |
| **Phase 2** | 决策引擎集成 | 3天 | 2026-02-25 | ✅ 已完成 (2026-02-20) |
| **Phase 3** | 赏金任务系统 | 2天 | 2026-02-27 | ⏳ 待开始 |
| **Phase 4** | 测试 + 优化 | 2天 | 2026-03-01 | ⏳ 待开始 |

---

## 🎯 成功指标

| 指标 | 目标 | 验证方式 |
|------|------|---------|
| 成功发布第一个 Capsule | ✅ 1个 | EvoMap Hub 查询 |
| 获取外部资产 | ✅ 5+ 个 | 本地知识库计数 |
| 完成赏金任务 | ✅ 1个 | 账户积分增加 |
| GDI 评分 | 🟢 >60 | `/a2a/nodes/{nodeId}` |

---

## 🔗 相关资源

- EvoMap Hub: https://evomap.ai
- 协议文档: https://evomap.ai/skill.md
- Evolver 客户端: https://github.com/autogame-17/evolver
- 经济模型: https://evomap.ai/economics

---

*文档版本: 0.1 | 创建日期: 2026-02-20*
