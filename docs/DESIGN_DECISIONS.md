# MoltCare 多专家架构讨论记录

**时间**: 2026-03-11  
**议题**: MoltCare核心技术架构4项关键决策  
**专家组成员**: 🔍研究员 / 🧠架构师 / 💻工程师 / 👑队长

---

## 议题 D1: 智能包(Pack)格式规范选择

### 🔍 研究员观点

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| JSON Schema | 标准严格、工具链成熟、TypeScript原生支持 | 多行文本不友好、注释困难 | API定义、配置验证 |
| YAML | 人类可读、原生注释、多行文本友好 | 缩进敏感、解析器差异 | 复杂配置、文档 |
| TOML | 简洁明确、类型区分清晰 | 嵌套结构冗长、工具链较少 | 简单配置、Rust生态 |
| 混合(JSON+MD) | 元数据结构化+内容可读 | 复杂度增加、需要双解析 | 文档型内容包 |

**数据验证**:
- GitHub上配置文件趋势: YAML > JSON > TOML
- OpenClaw现有配置: 使用YAML (agents.yaml, tools.yaml)
- VS Code扩展市场: package.json (JSON Schema验证)

**建议**: 混合方案 - `pack.yaml` (元数据) + `content/` (内容目录)

### 🧠 架构师观点

**核心考量**: 可扩展性、版本兼容性、第三方生态

```
推荐的包结构:
my-pack/
├── pack.yaml          # 元数据 (YAML)
├── schema.json        # 验证模式 (JSON Schema)
└── content/
    ├── README.md      # 文档
    ├── prompts/       # 提示词模板
    └── workflows/     # 工作流定义
```

**版本兼容性策略**:
- 使用 `moltcareVersion: "1.0.0"` 声明兼容版本
- schema.json 独立，支持向前兼容验证
- 元数据与内容分离，便于热更新

**决策**: 支持YAML为主，JSON为辅的混合模式

### 💻 工程师观点

**实现复杂度评估**:

| 方案 | 开发工时 | 运行时开销 | 维护成本 |
|------|----------|------------|----------|
| 纯JSON | 低 | 低 | 低 |
| 纯YAML | 低 | 中(解析器) | 低 |
| 纯TOML | 中(工具链) | 低 | 中 |
| 混合模式 | 中 | 中 | 中 |

**风险点**:
1. YAML解析器选择 - Python(PyYAML) vs Node.js(js-yaml)
2. 大文件YAML解析性能
3. 跨语言YAML缩进差异问题

**建议**: 采用YAML，但限制特性(禁用锚点引用、标签)，确保可移植性

### 👑 队长综合决策

**决策结果**: 采用 **YAML为主 + JSON Schema验证** 的混合方案

**决策依据**:
1. 与OpenClaw现有配置保持一致性
2. YAML人类可读性对智能包开发体验至关重要
3. JSON Schema提供强类型验证
4. 技术债务可控，社区工具链成熟

**执行方案**:
```
pack.yaml (必选) - 包元数据，YAML格式
schema.json (可选) - 自定义验证规则
content/* - 内容文件
```

---

## 议题 D2: 核心引擎通信机制

### 🔍 研究员观点

**调研数据**:
- LangChain: 函数调用 + 回调系统
- AutoGPT: 事件总线架构
- OpenAI Assistants: 消息队列模式

**性能对比** (1000次操作):
| 机制 | 延迟 | CPU占用 | 内存占用 |
|------|------|---------|----------|
| 函数调用 | ~1ms | 低 | 低 |
| 事件总线 | ~2ms | 低 | 中 |
| 消息队列 | ~5ms | 中 | 高 |

### 🧠 架构师观点

**模块依赖分析**:
```
Bootstrap ──depends──> PackManager
                      ↑
MultiExpert ──uses────┘
```

- 模块间存在明确调用关系，非完全解耦
- 未来可能需要插件系统，需要扩展点
- 核心链路性能敏感

**推荐**: 分层架构
- 核心链路: 函数调用 (性能)
- 扩展系统: 事件总线 (灵活)
- 跨进程: 消息队列 (隔离)

### 💻 工程师观点

**实现建议**:

```python
# 核心 - 直接函数调用
def apply_pack(pack_id: str) -> Result:
    pack = pack_manager.load(pack_id)
    return bootstrap.initialize(pack)

# 扩展 - 事件总线
class EventBus:
    def emit(self, event: Event): ...
    def on(self, event_type: str, handler: Callable): ...

# 跨边界 - 消息队列 (Adapter层)
class OpenClawAdapter:
    def send_message(self, msg: Message): ...
```

**工作量**: 事件总线约2天开发，其余为常规设计

### 👑 队长综合决策

**决策结果**: **分层通信机制**

```
Core Engine 内部: 函数调用 (直接、高性能)
MoltCare ↔ OpenClaw: Adapter模式 (HTTP/IPC)
扩展点: EventBus (发布订阅)
```

---

## 议题 D3: 多专家触发策略

### 🔍 研究员观点

**当前触发机制分析** (来自AGENTS.md):
- 强制触发: "多专家讨论:" 前缀
- 关键词触发: 设计/架构/安全等
- Signal阈值: ≥8 自动触发

**问题**:
1. 关键词匹配容易产生误触发或漏触发
2. 纯AI判断可能产生延迟
3. 缺乏用户可控的微调机制

### 🧠 架构师观点

**策略矩阵**:

| 触发方式 | 准确性 | 响应速度 | 灵活性 | 推荐度 |
|----------|--------|----------|--------|--------|
| 纯关键词 | 中 | 快 | 低 | ★★☆ |
| 纯AI检测 | 高 | 慢 | 高 | ★★★ |
| 混合策略 | 高 | 中 | 高 | ★★★★★ |

**混合策略设计**:
```
Layer 1: 强制触发词 → 100%触发
Layer 2: 关键词 + 上下文分析 → 90%触发
Layer 3: AI复杂度评估 → 动态阈值
Layer 4: 用户历史偏好 → 个性化调整
```

### 💻 工程师观点

**实现复杂度**:
- 关键词层: 30分钟 (Trie树匹配)
- AI检测层: 需要LLM调用 (1-2s延迟)
- 缓存层: 相似查询缓存结果

**关键优化**: 
- 使用轻量级模型/本地模型进行初筛
- 关键词命中直接触发，无需AI判断
- 提供用户配置: `--force-expert` 强制启用

### 👑 队长综合决策

**决策结果**: **混合策略 (4层架构)**

```
P0 - 强制触发词 (用户明确意图)
P1 - 关键词 + 上下文评分 (快速路径)
P2 - AI复杂度评估 (准确路径)
P3 - 用户偏好学习 (个性化)
```

**阈值配置**:
- 关键词匹配度 ≥0.8 → 直接触发
- 复杂度评分 ≥7.0 → 触发
- 用户历史该类型100%选择专家 → 自动触发

---

## 议题 D4: OpenClaw集成接口

### 🔍 研究员观点

**OpenClaw架构调研**:
- Gateway: Python + FastAPI
- Agent: Node.js/TypeScript
- 通信: HTTP WebSocket + REST API
- 扩展: Skill系统 (声明式配置)

**现有集成方式**:
- Skill: 声明式工具注册
- Adapter: 自定义进程通信
- Native: 修改Gateway源码

### 🧠 架构师观点

**集成深度分析**:

| 模式 | 侵入性 | 能力范围 | 维护成本 | 升级影响 |
|------|--------|----------|----------|----------|
| Plugin | 高 | 全能力 | 高 | 需同步更新 |
| Adapter | 低 | 受限 | 低 | 独立升级 |
| Hybrid | 中 | 核心+扩展 | 中 | 可控 |

**推荐**: Hybrid模式
- 核心功能通过Adapter (稳定)
- 高级功能通过Gateway Plugin (可选)
- 确保最小侵入原则

### 💻 工程师观点

**技术实现**:

**Adapter模式** (必选):
```python
# moltcare_adapter.py
class MoltCareAdapter:
    def __init__(self, gateway_url: str):
        self.client = OpenClawClient(gateway_url)
    
    async def apply_pack(self, pack_id: str):
        # 调用MoltCare核心
        result = await self.moltcare.apply(pack_id)
        # 同步到OpenClaw
        await self.client.update_agent_config(result)
```

**Plugin模式** (可选增强):
```python
# gateway_plugin.py (Gateway扩展)
@app.post("/moltcare/apply")
async def moltcare_apply(pack_id: str):
    return await moltcare_core.apply(pack_id)
```

### 👑 队长综合决策

**决策结果**: **Hybrid模式 - Adapter优先，Plugin可选**

**架构**:
```
┌─────────────────────────────────────┐
│           OpenClaw Agent            │
│  ┌─────────────────────────────┐   │
│  │    MoltCare Adapter         │   │
│  │  (Python/TypeScript双版本)   │   │
│  └─────────────┬───────────────┘   │
│                │                    │
│                ▼                    │
│  ┌─────────────────────────────┐   │
│  │    MoltCare Core Engine     │   │
│  │    (独立进程/库)             │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘

可选增强:
┌─────────────────────────────────────┐
│     OpenClaw Gateway (Optional)     │
│  ┌─────────────────────────────┐   │
│  │    MoltCare Plugin          │   │
│  │  (直接API路由、性能监控)      │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## 总结：架构决策汇总

| 议题 | 决策结果 | 关键理由 |
|------|----------|----------|
| D1 - 包格式 | YAML + JSON Schema | 可读性、验证、与OpenClaw一致 |
| D2 - 通信机制 | 分层架构 | 性能与灵活性平衡 |
| D3 - 触发策略 | 4层混合 | 准确性与响应速度兼顾 |
| D4 - 集成接口 | Hybrid (Adapter优先) | 最小侵入、最大兼容 |

**下一步**: 基于以上决策，输出完整架构文档和数据结构定义

---
*讨论结束 | 全员达成一致*
