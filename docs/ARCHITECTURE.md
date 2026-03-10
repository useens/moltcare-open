# MoltCare 技术架构设计文档

> 🦞 **版本**: Alpha-1.0  
> **状态**: 已定稿  
> **更新**: 2026-03-11  
> **决策记录**: [DESIGN_DECISIONS.md](./DESIGN_DECISIONS.md)

---

## 1. 架构概述

### 1.1 设计目标

| 目标 | 优先级 | 说明 | 验收标准 |
|------|--------|------|----------|
| 模块化 | P0 | 核心引擎、智能包、适配器完全解耦 | 单模块可独立测试 |
| 可扩展 | P0 | 支持第三方智能包开发 | 新包接入 < 30分钟 |
| 多语言 | P1 | 9语言i18n支持 | 覆盖率 100% |
| 性能 | P1 | 启动时间 < 2s | 冷启动基准测试 |
| 安全 | P0 | 沙箱执行、签名验证 | 恶意包隔离率 100% |

### 1.2 核心架构图

```
┌──────────────────────────────────────────────────────────────────────┐
│                        OpenClaw Agent                               │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    MoltCare Core Engine                     │    │
│  │                                                             │    │
│  │  ┌─────────────┐    ┌──────────────┐    ┌────────────────┐ │    │
│  │  │   Agent     │───→│   Multi-     │───→│ Intelligence   │ │    │
│  │  │ Bootstrap   │←───│   Expert     │←───│ Pack Manager   │ │    │
│  │  │   Module    │    │   Engine     │    │                │ │    │
│  │  └─────────────┘    └──────────────┘    └────────────────┘ │    │
│  │         │                   │                      │        │    │
│  │         └───────────────────┼──────────────────────┘        │    │
│  │                             ↓                               │    │
│  │                    ┌────────────────┐                       │    │
│  │                    │   Event Bus    │ (扩展点)               │    │
│  │                    └────────────────┘                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│           ┌──────────────────┼───────────────────┐                   │
│           ▼                  ▼                   ▼                   │
│  ┌─────────────┐     ┌──────────────┐     ┌────────────────┐       │
│  │  Foundation │     │ Professional │     │    Domain      │       │
│  │    Pack     │     │    Packs     │     │    Packs       │       │
│  │  (基础认知)  │     │   (工作流)   │     │   (领域专用)    │       │
│  └─────────────┘     └──────────────┘     └────────────────┘       │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                  OpenClaw Adapter                           │    │
│  │         (REST API / WebSocket / IPC)                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.3 模块职责

| 模块 | 职责 | 对外接口 |
|------|------|----------|
| Agent Bootstrap | Agent初始化、环境检测、配置生成 | `bootstrap()`, `detect_env()` |
| Multi-Expert | 决策触发、专家协调、结果聚合 | `should_trigger()`, `debate()` |
| Pack Manager | 包发现、加载、执行、卸载 | `load()`, `apply()`, `unload()` |
| Event Bus | 内部事件订阅发布 | `emit()`, `on()`, `off()` |
| OpenClaw Adapter | 与OpenClaw Gateway通信 | `sync_config()`, `send_event()` |

---

## 2. 核心引擎详解

### 2.1 Agent Bootstrap (初始化模块)

**职责**: 负责Agent首次启动时的环境感知与配置初始化

**执行流程**:
```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Detect  │───→│  Analyze │───→│ Generate │───→│ Recommend│───→│  Apply   │
│  Phase   │    │  Phase   │    │  Config  │    │   Packs  │    │  Phase   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
 • OS Type       • Profile      • Base.yaml    • Pack list    • Download
 • Shell         • Generation   • Mappings     • Priority     • Execute
 • OpenClaw      • Risk Level   • Preferences  • Dependencies • Validate
   Version       • Capability   • Constraints  • Conflicts    • Rollback
```

**环境检测清单**:
```yaml
detect_items:
  system:
    - os: [linux, macos, windows]
    - arch: [amd64, arm64]
    - shell: [bash, zsh, fish, powershell]
  openclaw:
    - gateway_version
    - agent_version
    - available_tools
    - existing_skills
  user:
    - primary_language
    - profession_hint
    - workflow_preference
```

### 2.2 Multi-Expert Engine (多专家引擎)

**核心算法**: 4层混合触发策略

```
Layer 1 (P0): 强制触发词
  └─ 关键词: "多专家讨论:", "DESIGN_DECISION"
  └─ 动作: 100%触发，跳过其他层

Layer 2 (P1): 关键词 + 上下文评分
  └─ 关键词库: [设计, 架构, 安全, 评估, 优化, ...]
  └─ 上下文权重: 代码变更量、文件影响范围
  └─ 阈值: match_score >= 0.8 → 触发

Layer 3 (P2): AI复杂度评估
  └─ 评估维度: 技术难度、影响范围、决策风险
  └─ 评估方式: LLM prompt 评分
  └─ 阈值: complexity >= 7.0 → 触发

Layer 4 (P3): 用户偏好学习
  └─ 历史数据: 用户过往决策模式
  └─ 个性化: 某类决策的自动触发率
```

**专家角色定义**:

| 角色 | ID | 职责 | 输出格式 |
|------|-----|------|----------|
| Researcher | `researcher` | 数据验证、技术调研 | 对比表格、数据来源 |
| Architect | `architect` | 系统设计、扩展性评估 | 架构图、风险分析 |
| Engineer | `engineer` | 实现评估、工期估算 | 工作量、依赖清单 |
| Captain | `captain` | 综合决策、资源协调 | 决策结论、执行方案 |

**执行流程**:
```
触发检测 → 并行4专家分析 → 结果聚合 → 队长决策 → 输出结论
```

### 2.3 Intelligence Pack Manager (智能包管理器)

**生命周期管理**:
```
Discovery ──→ Loading ──→ Validation ──→ Execution ──→ Unloading
    │            │             │              │             │
    ▼            ▼             ▼              ▼             ▼
 扫描目录    解析YAML      Schema验证    沙箱执行      资源释放
 远程索引    加载资源      签名验证      状态追踪      配置回滚
```

**沙箱安全模型**:
```
┌─────────────────────────────────────────┐
│           Pack Sandbox                  │
│  ┌─────────────────────────────────┐   │
│  │  Allowed Operations             │   │
│  │  • Read pack internal files     │   │
│  │  • Write to /tmp/moltcare/*     │   │
│  │  • Network: whitelist only      │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Forbidden Operations           │   │
│  │  • Write outside sandbox        │   │
│  │  • Execute system commands      │   │
│  │  • Access environment secrets   │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## 3. 智能包(Pack)规范

### 3.1 包结构

```
my-intelligence-pack/
├── pack.yaml              # 包元数据 (必选)
├── schema.json            # 自定义验证规则 (可选)
├── README.md              # 文档
├── icon.png               # 图标 (可选)
└── content/
    ├── prompts/           # 提示词模板
    │   ├── system.txt
    │   └── templates/
    ├── workflows/         # 工作流定义
    │   ├── onboarding.yaml
    │   └── maintenance.yaml
    ├── knowledge/         # 知识库
    │   ├── concepts.md
    │   └── best-practices/
    └── assets/            # 静态资源
        └── images/
```

### 3.2 pack.yaml 规范

```yaml
# pack.yaml 示例
moltcareVersion: "1.0.0"          # 兼容的MoltCare版本
pack:
  id: "foundation-python"         # 唯一标识符
  name:
    en: "Python Foundation"
    zh: "Python基础认知包"
    ja: "Python基礎パック"
  version: "1.0.0"
  description:
    en: "Essential Python knowledge and workflows"
    zh: "Python基础知识和工作流程"
  author: "MoltCare Team"
  license: "MIT"
  
  # 包分类
  category: "foundation"          # foundation | professional | domain
  domain: ["python", "backend"]   # 领域标签
  
  # 依赖管理
  requires:
    moltcare: ">=1.0.0"
    packs: []                     # 依赖的其他包
    tools: ["python", "pip"]      # 需要的系统工具
  
  # 兼容性
  compatibility:
    os: ["linux", "macos", "windows"]
    openclaw: ">=2.0.0"
  
  # 入口点
  entry:
    bootstrap: "content/workflows/onboarding.yaml"
    default: "content/prompts/system.txt"
  
  # 多专家触发配置
  triggers:
    keywords: ["python", "py", "pip"]
    auto_apply: false             # 是否自动应用
  
  # 资源声明
  resources:
    memory: "10MB"               # 预估内存占用
    disk: "5MB"                  # 磁盘占用

# 签名 (发布时添加)
signature: "-----BEGIN SIGNATURE-----\n..."
```

### 3.3 工作流规范

```yaml
# workflow.yaml
workflow:
  name: "onboarding"
  version: "1.0.0"
  description: "Agent初始化工作流"
  
  steps:
    - id: "detect_env"
      name: "环境检测"
      type: "builtin"
      action: "detect_environment"
      output: "env_info"
    
    - id: "generate_config"
      name: "配置生成"
      type: "template"
      template: "templates/config.j2"
      context:
        env: "{{ steps.detect_env.output }}"
      output: "agent_config"
    
    - id: "apply_config"
      name: "应用配置"
      type: "action"
      action: "sync_to_openclaw"
      input: "{{ steps.generate_config.output }}"
      
    - id: "verify"
      name: "验证"
      type: "condition"
      condition: "{{ steps.apply_config.success }}"
      on_true:
        - action: "log"
          message: "配置应用成功"
      on_false:
        - action: "rollback"
          target: "steps.apply_config"
```

---

## 4. OpenClaw 集成接口

### 4.1 集成架构

采用 **Hybrid模式**: Adapter优先，Plugin可选

```
┌─────────────────────────────────────────────────────────┐
│                    OpenClaw Agent                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │              MoltCare Adapter                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │   │
│  │  │  Python SDK │  │Node.js SDK  │  │  CLI     │ │   │
│  │  │  (官方推荐)  │  │  (轻量级)   │  │ (通用)   │ │   │
│  │  └─────────────┘  └─────────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │           MoltCare Core Engine                   │   │
│  │              (独立库/进程)                        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │   HTTP API  │    │  WebSocket  │    │  Files/IPC  │
    │  (Gateway)  │    │  (实时推送)  │    │  (本地通信)  │
    └─────────────┘    └─────────────┘    └─────────────┘
```

### 4.2 Adapter API

```typescript
// TypeScript SDK 接口
interface MoltCareAdapter {
  // 初始化
  initialize(config: AdapterConfig): Promise<void>;
  
  // 包管理
  listPacks(): Promise<PackInfo[]>;
  loadPack(packId: string): Promise<Pack>;
  applyPack(packId: string, options?: ApplyOptions): Promise<ApplyResult>;
  unloadPack(packId: string): Promise<void>;
  
  // 配置同步
  syncConfig(config: AgentConfig): Promise<SyncResult>;
  getCurrentConfig(): Promise<AgentConfig>;
  
  // 多专家决策
  shouldTriggerExpert(context: DecisionContext): Promise<TriggerResult>;
  runExpertDebate(topic: string, context: any): Promise<DebateResult>;
  
  // 事件订阅
  on(event: MoltCareEvent, handler: EventHandler): void;
  off(event: MoltCareEvent, handler: EventHandler): void;
}
```

### 4.3 Gateway Plugin (可选)

```python
# Gateway扩展 (FastAPI路由)
from fastapi import APIRouter

moltcare_router = APIRouter(prefix="/moltcare")

@moltcare_router.post("/packs/{pack_id}/apply")
async def apply_pack(pack_id: str, options: ApplyOptions):
    """应用智能包"""
    result = await moltcare_core.pack_manager.apply(pack_id, options)
    return result

@moltcare_router.get("/packs")
async def list_packs(category: str = None):
    """列出可用智能包"""
    packs = await moltcare_core.pack_manager.list(category=category)
    return {"packs": packs}

@moltcare_router.post("/expert/debate")
async def expert_debate(request: DebateRequest):
    """触发多专家讨论"""
    result = await moltcare_core.multi_expert.debate(
        topic=request.topic,
        context=request.context
    )
    return result
```

---

## 5. 事件系统

### 5.1 事件类型

```typescript
type MoltCareEvent =
  // 生命周期事件
  | 'pack:discovered'
  | 'pack:loaded'
  | 'pack:applied'
  | 'pack:failed'
  | 'pack:unloaded'
  
  // 配置事件
  | 'config:changed'
  | 'config:synced'
  | 'config:rollback'
  
  // 专家事件
  | 'expert:triggered'
  | 'expert:started'
  | 'expert:completed'
  | 'expert:failed'
  
  // 系统事件
  | 'system:error'
  | 'system:warning';
```

### 5.2 事件数据结构

```typescript
interface PackEvent {
  type: 'pack:loaded' | 'pack:applied' | 'pack:failed';
  packId: string;
  packVersion: string;
  timestamp: number;
  duration?: number;
  error?: ErrorInfo;
  metadata?: Record<string, any>;
}

interface ExpertEvent {
  type: 'expert:started' | 'expert:completed';
  debateId: string;
  topic: string;
  experts: ExpertRole[];
  timestamp: number;
  duration: number;
  result?: DebateResult;
}
```

---

## 6. 安全设计

### 6.1 包安全

| 安全措施 | 实现方式 | 优先级 |
|----------|----------|--------|
| 签名验证 | Ed25519签名 | P0 |
| 沙箱执行 | seccomp + namespace | P0 |
| 权限最小化 | 声明式权限清单 | P1 |
| 来源白名单 | 官方仓库 + 可信源 | P1 |
| 内容扫描 | 静态分析 + 模式匹配 | P2 |

### 6.2 运行时安全

```yaml
sandbox:
  filesystem:
    read: ["${PACK_DIR}/**"]
    write: ["/tmp/moltcare/${PACK_ID}/**"]
    forbidden: ["~/.ssh", "~/.env", "/etc/passwd"]
  
  network:
    mode: "whitelist"
    allowed_domains: ["github.com", "pypi.org"]
  
  process:
    max_memory: "100MB"
    max_cpu_percent: 50
    timeout: "30s"
    
  system_calls:
    mode: "allowlist"
    allowed: ["read", "write", "open", "close", ...]
```

---

## 7. 部署架构

### 7.1 单机部署

```
┌─────────────────────────────────────┐
│  User Machine                       │
│                                     │
│  ┌─────────────┐  ┌──────────────┐ │
│  │  OpenClaw   │  │  MoltCare    │ │
│  │  Gateway    │  │  Core        │ │
│  │  (Python)   │  │  (Python/TS) │ │
│  └──────┬──────┘  └──────┬───────┘ │
│         │                │         │
│         └──────┬─────────┘         │
│                │                    │
│         ┌──────┴──────┐            │
│         │  Local DB   │            │
│         │  (SQLite)   │            │
│         └─────────────┘            │
└─────────────────────────────────────┘
```

### 7.2 分布式部署 (企业版)

```
┌─────────────────────────────────────────────────────┐
│                 MoltCare Cloud                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Pack Repo   │  │ Analytics   │  │   Sync      │ │
│  │ (Registry)  │  │ (Telemetry) │  │  Service    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Agent #1   │  │  Agent #2   │  │  Agent #N   │
│ (User A)    │  │ (User B)    │  │ (User N)    │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## 8. 性能基准

### 8.1 目标指标

| 指标 | 目标值 | 测试方法 |
|------|--------|----------|
| 冷启动时间 | < 2s | 从import到ready |
| 包加载时间 | < 500ms | 标准foundation包 |
| 专家触发延迟 | < 100ms | 关键词匹配路径 |
| 内存占用 | < 50MB | 空闲状态 |
| 配置同步时间 | < 1s | 到OpenClaw Gateway |

### 8.2 优化策略

1. **懒加载**: 智能包按需加载，不预加载全部
2. **缓存**: 已解析的pack.yaml缓存，监听文件变更
3. **并行**: 专家并行执行，结果流式返回
4. **压缩**: 智能包分发使用zstd压缩

---

## 9. 路线图

| 版本 | 目标 | 时间 |
|------|------|------|
| Alpha | 核心引擎 + 2个基础包 + 中英双语 | 2026-03 |
| Beta | 7语言 + 5个专业包 + Plugin API | 2026-04 |
| v1.0 | 9语言 + 10个包 + 完整文档 | 2026-05 |
| v1.1 | 企业功能 + 云端同步 | 2026-06 |

---

## 10. 附录

### 10.1 术语表

| 术语 | 定义 |
|------|------|
| Pack | 智能包，包含知识、工作流、配置的模块化单元 |
| Expert | 专家角色，负责特定角度的决策分析 |
| Bootstrap | Agent初始化过程 |
| Trigger | 多专家讨论的触发条件 |
| Sandbox | 包执行的隔离环境 |

### 10.2 参考文档

- [DESIGN_DECISIONS.md](./DESIGN_DECISIONS.md) - 设计决策记录
- [types.ts](../src/types.ts) - 数据结构定义
- [API.md](./API.md) - API参考 (待补充)

---

*🦞 为每一只龙虾的智能蜕变而生*
