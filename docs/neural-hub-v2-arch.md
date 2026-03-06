# 神经中枢 2.0 架构设计

> **项目**: Neural Hub V2 - 完全重构的多Agent协作系统  
> **日期**: 2026-03-06  
> **架构师**: 森森  

---

## 1. 系统架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           🧠 神经中枢 2.0                                │
│                     Neural Hub V2 - Master Node                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │   Unix Socket   │  │  Redis Pub/Sub │  │    SQLite      │            │
│  │   (控制通道)    │  │   (消息总线)   │  │   (持久化)     │            │
│  │   Latency<10ms  │  │   Broadcast    │  │   Task Store   │            │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘            │
│          │                   │                   │                     │
│          └───────────────────┼───────────────────┘                     │
│                              │                                         │
│  ┌───────────────────────────┴───────────────────────────┐            │
│  │              智能调度引擎 (Scheduler)                  │            │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │            │
│  │  │ 任务队列    │ │ 负载均衡    │ │ 故障恢复    │      │            │
│  │  │ Priority Q  │ │ Load Balance│ │ Auto-heal   │      │            │
│  │  └─────────────┘ └─────────────┘ └─────────────┘      │            │
│  └───────────────────────────────────────────────────────┘            │
│                              │                                         │
│  ┌───────────────────────────┴───────────────────────────┐            │
│  │              状态管理中心 (State Manager)              │            │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │            │
│  │  │ 在线状态    │ │ 能力注册    │ │ 任务追踪    │      │            │
│  │  │ Heartbeat   │ │ Capability  │ │ Tracking    │      │            │
│  │  └─────────────┘ └─────────────┘ └─────────────┘      │            │
│  └───────────────────────────────────────────────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               │                    │                    │
               ▼                    ▼                    ▼
        ┌──────────┐         ┌──────────┐         ┌──────────┐
        │nanobot-1 │         │nanobot-2 │   ...   │nanobot-10│
        │ 研究员   │         │ 架构师   │         │ 协调者   │
        └──────────┘         └──────────┘         └──────────┘
```

---

## 2. 通信协议设计

### 2.1 三层通信栈

| 层级 | 协议 | 用途 | 延迟 |
|------|------|------|------|
| **L1 控制层** | Unix Socket | 指令下发、紧急控制 | <10ms |
| **L2 消息层** | Redis Pub/Sub | 广播、事件通知 | <50ms |
| **L3 持久层** | SQLite | 任务记录、状态存储 | <100ms |

### 2.2 消息格式 (统一)

```json
{
  "header": {
    "msg_id": "uuid",
    "timestamp": 1234567890.123,
    "priority": 5,
    "ttl": 300
  },
  "routing": {
    "from": "openclaw|nanobot-X",
    "to": "broadcast|nanobot-X|group:researchers",
    "reply_to": "msg_id"
  },
  "payload": {
    "type": "command|response|event|heartbeat",
    "action": "execute_task|report_status|...",
    "data": {...}
  },
  "metadata": {
    "requires_ack": true,
    "retry_count": 0,
    "source": "manual|scheduler|cron"
  }
}
```

### 2.3 通道定义

```
Redis Channels:
  neuralhub:commands        # 指令广播 (我→所有)
  neuralhub:responses       # 响应收集 (所有→我)
  neuralhub:events          # 事件通知 (双向)
  neuralhub:heartbeat       # 心跳 (所有→我)
  neuralhub:control         # 紧急控制 (我→特定)
  
Unix Socket:
  /run/neural-hub/control.sock  # 控制通道
  /run/neural-hub/data.sock     # 数据通道
```

---

## 3. 状态机设计

### 3.1 Nanobot 状态机

```
                    ┌─────────────┐
         ┌─────────│   OFFLINE   │◄────────┐
         │         └──────┬──────┘         │
         │ heartbeat      │ connect        │ disconnect
         │ timeout        ▼                │
         │         ┌─────────────┐         │
         └────────►│   IDLE      │─────────┘
                   └──────┬──────┘
                          │ assign task
                          ▼
                   ┌─────────────┐
              ┌───►│   BUSY      │────┐
              │    └──────┬──────┘    │ complete
              │           │ pause     │
              │           ▼           │
              └───│  PAUSED   │◄──────┘
                   └───────────┘
                          │ resume
                          ▼
                   ┌─────────────┐
                   │   ERROR     │
                   └─────────────┘
```

### 3.2 任务状态机

```
CREATED → ASSIGNED → EXECUTING → COMPLETED
   │          │           │           │
   │          │           ▼           │
   │          │      PAUSED/FAILED    │
   │          │           │           │
   ▼          ▼           ▼           ▼
 CANCELLED  RETRY      RETRY      ARCHIVED
```

---

## 4. 智能调度算法

### 4.1 任务分配策略

```python
class SmartScheduler:
    def assign_task(self, task):
        candidates = self.filter_by_capability(task.requirements)
        candidates = self.filter_by_availability(candidates)
        
        if not candidates:
            return self.queue_task(task)  # 排队等待
        
        # 评分算法
        scores = []
        for bot in candidates:
            score = (
                bot.capability_match(task) * 0.4 +      # 能力匹配度
                bot.current_load() * -0.3 +              # 当前负载 (越低越好)
                bot.historical_success_rate() * 0.2 +    # 历史成功率
                bot.recent_performance() * 0.1           # 近期表现
            )
            scores.append((bot, score))
        
        best_bot = max(scores, key=lambda x: x[1])
        return self.dispatch(task, best_bot)
```

### 4.2 优先级队列

| 优先级 | 场景 | 抢占策略 |
|--------|------|----------|
| P0 | 系统故障、安全事件 | 抢占所有任务 |
| P1 | 用户紧急指令 | 抢占P2及以下 |
| P2 | 高价值任务 | 抢占P3及以下 |
| P3 | 常规任务 | 不抢占 |
| P4 | 后台任务 | 可被任意抢占 |

### 4.3 负载均衡

- **轮询**: 简单任务平均分配
- **加权**: 根据能力调整权重
- **最少连接**: 分配给最闲的小弟
- **一致性哈希**: 同类任务分配给固定小弟（缓存优势）

---

## 5. 故障恢复机制

### 5.1 检测机制

```
心跳检测:
  - 每30秒一次 ping/pong
  - 连续3次无响应 → 标记 OFFLINE
  - 任务超时 → 自动重试/重新分配

健康检查:
  - CPU/内存阈值检查
  - 任务失败率监控
  - API调用延迟监控
```

### 5.2 恢复策略

| 故障类型 | 自动处理 | 人工介入 |
|----------|----------|----------|
| 网络断开 | 重连+任务重分配 | 无 |
| 任务失败 | 重试3次后换小弟 | 连续失败 |
| 小弟崩溃 | 自动重启 | 启动失败 |
| 数据丢失 | 从SQLite恢复 | 无 |

---

## 6. API 接口设计

### 6.1 神经中枢 API

```python
class NeuralHubAPI:
    # 任务管理
    async def submit_task(self, task: Task) -> TaskID
    async def cancel_task(self, task_id: TaskID) -> bool
    async def get_task_status(self, task_id: TaskID) -> TaskStatus
    
    # 状态查询
    async def get_bot_status(self, bot_id: str) -> BotStatus
    async def list_active_tasks(self) -> List[Task]
    async def get_system_metrics(self) -> Metrics
    
    # 控制指令
    async def pause_bot(self, bot_id: str)
    async def resume_bot(self, bot_id: str)
    async def restart_bot(self, bot_id: str)
    
    # 广播
    async def broadcast(self, message: str, priority: int = 3)
```

### 6.2 Nanobot API

```python
class NanobotAPI:
    # 注册/心跳
    async def register(self, capabilities: List[str])
    async def heartbeat(self, status: BotStatus)
    
    # 任务执行
    async def accept_task(self, task_id: TaskID)
    async def report_progress(self, task_id: TaskID, progress: float)
    async def complete_task(self, task_id: TaskID, result: Any)
    async def fail_task(self, task_id: TaskID, error: str)
    
    # 能力上报
    async def update_capabilities(self, capabilities: List[str])
```

---

## 7. 数据库设计

### 7.1 SQLite 表结构

```sql
-- 任务表
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    priority INTEGER DEFAULT 3,
    status TEXT DEFAULT 'pending',
    assigned_to TEXT,
    created_at REAL,
    started_at REAL,
    completed_at REAL,
    payload TEXT,
    result TEXT,
    retry_count INTEGER DEFAULT 0,
    error TEXT
);

-- nanobot状态表
CREATE TABLE bot_status (
    bot_id TEXT PRIMARY KEY,
    name TEXT,
    role TEXT,
    state TEXT DEFAULT 'offline',
    capabilities TEXT,  -- JSON array
    current_task TEXT,
    last_heartbeat REAL,
    success_rate REAL DEFAULT 1.0,
    total_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0
);

-- 事件日志
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL,
    level TEXT,
    source TEXT,
    event_type TEXT,
    message TEXT,
    metadata TEXT
);

-- 消息历史
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    msg_type TEXT,
    from_bot TEXT,
    to_bot TEXT,
    content TEXT,
    timestamp REAL,
    delivered BOOLEAN DEFAULT 0
);
```

---

## 8. 部署架构

```
┌─────────────────────────────────────────┐
│           Systemd Services              │
├─────────────────────────────────────────┤
│  neural-hub.service    (主服务)         │
│  neural-hub-redis.service (Redis)       │
│  nanobot-1.service ~ nanobot-10.service │
└─────────────────────────────────────────┘

文件布局:
/root/.openclaw/workspace/
├── core/neural_hub/           # 神经中枢核心
│   ├── __init__.py
│   ├── hub.py                 # 主服务
│   ├── scheduler.py           # 调度引擎
│   ├── state_manager.py       # 状态管理
│   ├── socket_server.py       # Socket服务
│   └── redis_client.py        # Redis客户端
├── ai-nanobots/
│   └── nanobot-v3.py          # V3客户端
├── data/neural_hub/
│   ├── tasks.db               # SQLite数据库
│   └── logs/                  # 日志目录
└── docs/neural-hub-v2-arch.md # 本文档
```

---

## 9. 性能目标

| 指标 | 目标 | 当前(文件队列) |
|------|------|----------------|
| 指令延迟 | <10ms | ~3000ms |
| 状态查询 | <50ms | ~500ms |
| 任务分发 | <100ms | ~5000ms |
| 心跳检测 | <500ms | ~30000ms |
| 并发任务 | 100+ | 10 |
| 可靠性 | 99.9% | ~95% |

---

## 10. 迁移计划

1. **Phase 1**: 部署Redis + SQLite (并行运行)
2. **Phase 2**: 部署神经中枢 V2 服务
3. **Phase 3**: 逐个升级 nanobot → V3
4. **Phase 4**: 切换流量，下线旧系统
5. **Phase 5**: 清理旧文件队列代码

---

*架构设计 v1.0 | 2026-03-06 | 森森*
