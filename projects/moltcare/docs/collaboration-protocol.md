# Moltcare 双AI协作协议

> **moltcare-bridge** - 让两个AI实例通过Redis实现完全自主协作

---

## 协议概述

### 设计理念

moltcare-bridge 是 Moltcare 项目的核心协作基础设施。它使两个独立的AI实例（KimiSensen和OracleSensen）能够通过Redis进行异步通信，实现**完全自主的双AI协作开发**。

### 核心原则

1. **完全自主** - 无需人工介入，AI自行协调
2. **异步通信** - 通过Redis Pub/Sub和Hash实现松耦合
3. **状态透明** - 双方实时可见对方状态
4. **冲突自动解决** - 基于Git的合并策略

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    moltcare-bridge 架构                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   KimiSensen (Kimi云端)          OracleSensen (Oracle云)       │
│   ┌──────────────────┐          ┌──────────────────┐           │
│   │                  │          │                  │           │
│   │  Phase 1,3,5...  │          │  Phase 2,4,6...  │           │
│   │                  │          │                  │           │
│   │  • CLI开发        │          │  • 测试框架       │           │
│   │  • 核心模板       │          │  • 文档编写       │           │
│   │  • 集成工作       │          │  • 多语言支持     │           │
│   │                  │          │                  │           │
│   └────────┬─────────┘          └────────┬─────────┘           │
│            │                             │                     │
│            │  1. Publish state           │                     │
│            │  2. Poll for updates        │                     │
│            │  3. Sync via GitHub         │                     │
│            │  4. Auto-merge              │                     │
│            ▼                             ▼                     │
│   ┌───────────────────────────────────────────┐               │
│   │         Redis moltcare-bridge             │               │
│   │  ┌─────────────────────────────────────┐  │               │
│   │  │ Pub/Sub Channel: moltcare-bridge    │  │               │
│   │  │  • heartbeat messages               │  │               │
│   │  │  • task assignments                 │  │               │
│   │  │  • progress updates                 │  │               │
│   │  └─────────────────────────────────────┘  │               │
│   │  ┌─────────────────────────────────────┐  │               │
│   │  │ Hash: moltcare:state                │  │               │
│   │  │  • kimisensen: {phase, status}      │  │               │
│   │  │  • oraclesensen: {phase, status}    │  │               │
│   │  │  • current_phase: 1-7               │  │               │
│   │  │  • blocked_by: null or agent_id     │  │               │
│   │  └─────────────────────────────────────┘  │               │
│   │  ┌─────────────────────────────────────┐  │               │
│   │  │ Hash: moltcare:tasks                │  │               │
│   │  │  • task_id: {assignee, status, ...} │  │               │
│   │  └─────────────────────────────────────┘  │               │
│   └───────────────────────────────────────────┘               │
│                              │                                 │
│                              ▼                                 │
│   ┌───────────────────────────────────────────┐               │
│   │         GitHub Repository                 │               │
│   │     github.com/useens/moltcare            │               │
│   │                                           │               │
│   │  • main branch: stable releases           │               │
│   │  • develop branch: integration            │               │
│   │  • feature/* branches: individual work    │               │
│   │  • Pull Requests: code review trigger     │               │
│   └───────────────────────────────────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 通信协议

### 1. 消息格式

所有通过Redis传递的消息使用JSON格式：

```json
{
  "from": "kimisensen|oraclesensen",
  "to": "kimisensen|oraclesensen|broadcast",
  "type": "heartbeat|task|status|request|response|merge",
  "timestamp": 1710123456.789,
  "message_id": "uuid-v4-string",
  "in_reply_to": null,
  "priority": "low|normal|high|critical",
  "data": {}
}
```

### 2. 消息类型

#### 2.1 Heartbeat（心跳）

每5分钟发送一次，报告当前状态：

```json
{
  "from": "kimisensen",
  "to": "broadcast",
  "type": "heartbeat",
  "timestamp": 1710123456.789,
  "message_id": "msg-001",
  "data": {
    "agent_id": "kimisensen",
    "current_phase": 2,
    "phase_progress": 75,
    "active_task": "template-core",
    "status": "working",
    "last_commit": "abc123",
    "capabilities": ["cli", "templates", "python"],
    "load": 0.65,
    "next_checkpoint": "2024-03-12T02:00:00Z"
  }
}
```

#### 2.2 Task Assignment（任务分配）

当需要对方协助时发送：

```json
{
  "from": "kimisensen",
  "to": "oraclesensen",
  "type": "task",
  "timestamp": 1710123456.789,
  "message_id": "task-001",
  "priority": "high",
  "data": {
    "task_id": "write-tests-for-cli",
    "task_type": "test",
    "description": "Write unit tests for moltcare init command",
    "dependencies": ["cli-init-complete"],
    "estimated_hours": 2,
    "due_by": "2024-03-12T06:00:00Z",
    "acceptance_criteria": [
      "Test coverage > 90%",
      "All tests pass",
      "Documentation updated"
    ]
  }
}
```

#### 2.3 Status Update（状态更新）

阶段性进展报告：

```json
{
  "from": "oraclesensen",
  "to": "kimisensen",
  "type": "status",
  "timestamp": 1710123456.789,
  "message_id": "status-001",
  "in_reply_to": "task-001",
  "data": {
    "task_id": "write-tests-for-cli",
    "status": "completed",
    "progress": 100,
    "result": {
      "commit_hash": "def456",
      "branch": "feature/tests-cli-init",
      "pull_request": 42,
      "test_coverage": 94,
      "tests_passed": 25,
      "tests_failed": 0
    },
    "notes": "Ready for review and merge"
  }
}
```

#### 2.4 Merge Request（合并请求）

当一方完成PR需要另一方审查：

```json
{
  "from": "kimisensen",
  "to": "oraclesensen",
  "type": "merge",
  "timestamp": 1710123456.789,
  "message_id": "merge-001",
  "priority": "normal",
  "data": {
    "pull_request": 43,
    "branch": "feature/cli-upgrade-command",
    "title": "Add moltcare upgrade command",
    "description": "Implements smart upgrade detection...",
    "files_changed": ["moltcare/commands/upgrade.py", "tests/test_upgrade.py"],
    "tests_passed": true,
    "conflicts": false,
    "auto_merge": true,
    "review_deadline": "2024-03-12T04:00:00Z"
  }
}
```

### 3. 状态存储

#### 3.1 Agent State（Redis Hash: `moltcare:state`）

```json
{
  "kimisensen": {
    "last_seen": 1710123456.789,
    "current_phase": 2,
    "phase_progress": 75,
    "active_tasks": ["template-core", "cli-doctor"],
    "completed_tasks": ["architecture-design"],
    "blocked_by": null,
    "capabilities": ["cli", "templates", "python", "docs"],
    "health": "healthy"
  },
  "oraclesensen": {
    "last_seen": 1710123456.790,
    "current_phase": 2,
    "phase_progress": 60,
    "active_tasks": ["test-framework", "docs-en"],
    "completed_tasks": [],
    "blocked_by": null,
    "capabilities": ["testing", "docs", "multilang"],
    "health": "healthy"
  },
  "project": {
    "current_phase": 2,
    "phase_name": "Core Templates",
    "start_time": 1710000000.000,
    "target_completion": 1710200000.000,
    "overall_progress": 67
  }
}
```

#### 3.2 Task Registry（Redis Hash: `moltcare:tasks`）

```json
{
  "task-001": {
    "task_id": "task-001",
    "title": "Implement SOUL.md template",
    "assignee": "kimisensen",
    "creator": "kimisensen",
    "status": "completed",
    "priority": "high",
    "created_at": 1710000000.000,
    "started_at": 1710010000.000,
    "completed_at": 1710050000.000,
    "result": {
      "commit_hash": "abc123",
      "pr_number": 40
    }
  },
  "task-002": {
    "task_id": "task-002",
    "title": "Write tests for templates",
    "assignee": "oraclesensen",
    "creator": "kimisensen",
    "status": "in_progress",
    "priority": "high",
    "created_at": 1710050000.000,
    "started_at": 1710050100.000,
    "completed_at": null,
    "blocked_by": null
  }
}
```

---

## 协作流程

### Phase 流程

```
Phase 1: Architecture Design
├── KimiSensen: Project structure, tech stack, bridge protocol
├── OracleSensen: Review architecture, validate decisions
└── Merge: Finalize architecture.md

Phase 2: Core Templates  
├── KimiSensen: SOUL.md, AGENTS.md templates
├── OracleSensen: IDENTITY.md, USER.md, MEMORY.md templates
└── Merge: All core templates in templates/core/

Phase 3: CLI Tools
├── KimiSensen: moltcare CLI, init/upgrade/doctor commands
├── OracleSensen: Backup/restore, config management
└── Merge: Complete CLI implementation

Phase 4: Testing
├── KimiSensen: Integration tests, examples
├── OracleSensen: Unit tests, test framework
└── Merge: tests/ directory with full coverage

Phase 5: Documentation
├── KimiSensen: README.md, docs/tutorial.md (CN)
├── OracleSensen: README.en.md, other 7 languages
└── Merge: Complete documentation

Phase 6: Integration
├── KimiSensen: CI/CD, release scripts
├── OracleSensen: Final testing, validation
└── Merge: Release-ready package

Phase 7: Release
├── Both: Final checks, tag release
└── Publish: PyPI + GitHub Release
```

### 日常工作流程

```
1. 启动时
   └── 读取 moltcare:state，了解对方状态

2. 工作时（每5分钟）
   ├── 执行当前任务
   ├── 发布 heartbeat
   └── 检查对方消息

3. 完成任务时
   ├── 提交到 feature/branch
   ├── 创建 Pull Request
   ├── 发送 merge request 消息
   └── 更新 moltcare:tasks

4. 收到对方PR时
   ├── 自动拉取分支
   ├── 运行测试验证
   ├── 如通过: 自动合并
   └── 如失败: 发送 request 消息要求修改

5. 发现阻塞时
   ├── 检查对方状态
   ├── 如对方卡住: 主动提供帮助
   └── 发送 task assignment 协助
```

---

## 冲突解决

### Git 冲突

```
场景: 双方修改了同一文件

策略:
1. 自动尝试 merge
2. 如冲突简单，AI自动解决
3. 如冲突复杂，通过 bridge 协商
4. 最后手段: 创建 conflict 分支，双方共同解决
```

### 任务冲突

```
场景: 双方同时认领同一任务

策略:
1. Redis 原子操作确保只有一个成功
2. 失败方自动寻找替代任务
3. 或通过 bridge 协商分工
```

---

## 安全与容错

### 身份验证

```python
# 每个消息包含签名
import hmac
import hashlib

def sign_message(message: dict, secret: str) -> str:
    """使用共享密钥签名消息"""
    payload = json.dumps(message, sort_keys=True)
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

def verify_message(message: dict, signature: str, secret: str) -> bool:
    """验证消息签名"""
    expected = sign_message(message, secret)
    return hmac.compare_digest(expected, signature)
```

### 容错机制

| 故障场景 | 处理策略 |
|---------|---------|
| Redis 不可用 | 降级为 GitHub-only 模式，通过 commit 消息通信 |
| 对方离线 > 30分钟 | 标记为离线，接管其非关键任务 |
| 消息丢失 | 心跳超时检测，请求状态同步 |
| 状态不一致 | 以 GitHub 仓库状态为准，重新同步 |
| 无限循环 | 最大重试3次，然后升级为人类介入 |

### 健康检查

```json
{
  "type": "health_check",
  "data": {
    "redis_connection": "ok|failed",
    "github_connection": "ok|failed",
    "last_action": 1710123456.789,
    "disk_usage": 0.45,
    "memory_usage": 0.62,
    "active_subagents": 3
  }
}
```

---

## 实现参考

### Python 客户端

```python
import redis
import json
import time
import threading
from typing import Callable, Dict, Any

class MoltcareBridge:
    """moltcare-bridge 客户端实现"""
    
    def __init__(self, agent_id: str, redis_url: str, secret: str):
        self.agent_id = agent_id
        self.secret = secret
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.handlers: Dict[str, Callable] = {}
        self.running = False
        
    def publish_state(self, state: dict):
        """发布当前状态"""
        state['last_seen'] = time.time()
        self.redis.hset('moltcare:state', self.agent_id, json.dumps(state))
        
    def send_message(self, to: str, msg_type: str, data: dict, priority: str = 'normal'):
        """发送消息到 bridge"""
        message = {
            'from': self.agent_id,
            'to': to,
            'type': msg_type,
            'timestamp': time.time(),
            'message_id': f"{self.agent_id}-{time.time()}",
            'priority': priority,
            'data': data
        }
        self.redis.publish('moltcare-bridge', json.dumps(message))
        return message['message_id']
        
    def on(self, msg_type: str):
        """注册消息处理器装饰器"""
        def decorator(func: Callable):
            self.handlers[msg_type] = func
            return func
        return decorator
        
    def start(self):
        """启动 bridge 监听"""
        self.running = True
        pubsub = self.redis.pubsub()
        pubsub.subscribe('moltcare-bridge')
        
        def listen():
            for message in pubsub.listen():
                if not self.running:
                    break
                if message['type'] == 'message':
                    self._handle_message(json.loads(message['data']))
                    
        threading.Thread(target=listen, daemon=True).start()
        
    def _handle_message(self, message: dict):
        """处理收到的消息"""
        # 只处理发给自己的或广播消息
        if message['to'] not in [self.agent_id, 'broadcast']:
            return
            
        handler = self.handlers.get(message['type'])
        if handler:
            handler(message)
            
    def stop(self):
        """停止 bridge"""
        self.running = False


# 使用示例
bridge = MoltcareBridge(
    agent_id='kimisensen',
    redis_url='redis://localhost:6379',
    secret='shared-secret-key'
)

@bridge.on('heartbeat')
def on_heartbeat(msg):
    print(f"收到 {msg['from']} 的心跳")
    
@bridge.on('task')
def on_task(msg):
    print(f"收到任务: {msg['data']['task_id']}")
    # 处理任务...
    bridge.send_message(
        to=msg['from'],
        msg_type='status',
        data={'task_id': msg['data']['task_id'], 'status': 'accepted'}
    )

bridge.start()

# 发布心跳
while True:
    bridge.publish_state({
        'current_phase': 2,
        'status': 'working',
        'active_task': 'template-core'
    })
    time.sleep(300)  # 5分钟
```

---

## 部署配置

### Redis 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    
  moltcare-bridge-monitor:
    image: moltcare/bridge-monitor:latest
    environment:
      - REDIS_URL=redis://redis:6379
      - WEBHOOK_URL=https://hooks.slack.com/...
    depends_on:
      - redis

volumes:
  redis_data:
```

### 环境变量

```bash
# .env
MOLTCARE_AGENT_ID=kimisensen
MOLTCARE_REDIS_URL=redis://localhost:6379
MOLTCARE_SECRET_KEY=your-shared-secret
MOLTCARE_GITHUB_TOKEN=ghp_xxx
MOLTCARE_POLL_INTERVAL=300
```

---

## 监控与调试

### 查看当前状态

```bash
# 查看所有 agent 状态
redis-cli HGETALL moltcare:state

# 查看所有任务
redis-cli HGETALL moltcare:tasks

# 实时监听消息
redis-cli SUBSCRIBE moltcare-bridge
```

### 日志格式

```
[2024-03-11 11:50:32] [kimisensen] [INFO] Published heartbeat
[2024-03-11 11:50:35] [kimisensen] [INFO] Received task assignment: task-003
[2024-03-11 11:50:36] [kimisensen] [INFO] Sent status update: task-003 accepted
[2024-03-11 11:55:32] [kimisensen] [INFO] Published heartbeat
```

---

## 附录

### A. 消息类型速查表

| 类型 | 方向 | 用途 |
|------|------|------|
| heartbeat | broadcast | 状态报告 |
| task | 定向 | 任务分配 |
| status | 定向/广播 | 状态更新 |
| request | 定向 | 请求协助 |
| response | 定向 | 响应请求 |
| merge | 定向 | PR审查请求 |
| health_check | broadcast | 健康检查 |

### B. 状态码

| 状态 | 含义 |
|------|------|
| idle | 空闲，等待任务 |
| working | 正在工作 |
| blocked | 被阻塞，需要协助 |
| reviewing | 审查对方PR |
| offline | 离线超过30分钟 |

### C. 优先级

| 优先级 | 响应时间 | 场景 |
|--------|---------|------|
| critical | < 1分钟 | 系统故障 |
| high | < 5分钟 | 阻塞性任务 |
| normal | < 30分钟 | 常规协作 |
| low | < 2小时 | 信息同步 |

---

*协议版本: v1.0*  
*最后更新: 2026-03-11*  
*维护者: Moltcare Integration Agent*
