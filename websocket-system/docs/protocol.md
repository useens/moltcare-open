# WebSocket 通信协议设计

## 1. 消息格式 (JSON)

### 1.1 基础消息结构
```json
{
  "msg_id": "uuid-string",      // 消息唯一标识
  "msg_type": "string",         // 消息类型
  "timestamp": 1707955200,      // Unix时间戳(秒)
  "sender": "node_id",          // 发送方ID
  "receiver": "node_id|broadcast", // 接收方ID或广播
  "payload": {}                 // 消息内容
}
```

### 1.2 消息类型定义

| msg_type | 方向 | 说明 |
|----------|------|------|
| `auth` | C→S | 连接认证 |
| `auth_response` | S→C | 认证响应 |
| `heartbeat` | C→S | 心跳请求 |
| `heartbeat_ack` | S→C | 心跳确认 |
| `request` | 双向 | 业务请求 |
| `response` | 双向 | 业务响应 |
| `event` | S→C | 服务器推送事件 |
| `error` | 双向 | 错误消息 |

## 2. 协议详情

### 2.1 认证消息 (auth)
**方向**: 客户端 → 服务端
```json
{
  "msg_id": "auth-001",
  "msg_type": "auth",
  "timestamp": 1707955200,
  "sender": "local-node-01",
  "receiver": "cloud-server",
  "payload": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "node_type": "local",
    "version": "1.0.0",
    "capabilities": ["camera", "sensor"]
  }
}
```

### 2.2 认证响应 (auth_response)
**方向**: 服务端 → 客户端
```json
{
  "msg_id": "auth-resp-001",
  "msg_type": "auth_response",
  "timestamp": 1707955201,
  "sender": "cloud-server",
  "receiver": "local-node-01",
  "payload": {
    "success": true,
    "session_id": "sess-abc123",
    "server_time": 1707955201,
    "heartbeat_interval": 30
  }
}
```

### 2.3 心跳消息 (heartbeat)
**方向**: 客户端 → 服务端
```json
{
  "msg_id": "hb-001",
  "msg_type": "heartbeat",
  "timestamp": 1707955230,
  "sender": "local-node-01",
  "receiver": "cloud-server",
  "payload": {
    "sequence": 1,
    "status": "alive"
  }
}
```

### 2.4 心跳确认 (heartbeat_ack)
**方向**: 服务端 → 客户端
```json
{
  "msg_id": "hb-ack-001",
  "msg_type": "heartbeat_ack",
  "timestamp": 1707955230,
  "sender": "cloud-server",
  "receiver": "local-node-01",
  "payload": {
    "sequence": 1,
    "server_time": 1707955230
  }
}
```

### 2.5 业务请求 (request)
**方向**: 双向
```json
{
  "msg_id": "req-001",
  "msg_type": "request",
  "timestamp": 1707955260,
  "sender": "cloud-server",
  "receiver": "local-node-01",
  "payload": {
    "action": "get_status",
    "params": {},
    "request_id": "rq-abc123"
  }
}
```

**请求动作列表**:
| action | 说明 | 参数 | 响应 |
|--------|------|------|------|
| `get_status` | 获取状态 | - | 节点状态信息 |
| `execute_command` | 执行命令 | `command`, `args` | 执行结果 |
| `get_sensor_data` | 获取传感器数据 | `sensor_id` | 传感器读数 |
| `trigger_action` | 触发动作 | `action_type`, `params` | 动作结果 |
| `sync_config` | 同步配置 | `config_version` | 配置数据 |

### 2.6 业务响应 (response)
**方向**: 双向
```json
{
  "msg_id": "resp-001",
  "msg_type": "response",
  "timestamp": 1707955261,
  "sender": "local-node-01",
  "receiver": "cloud-server",
  "payload": {
    "request_id": "rq-abc123",
    "success": true,
    "data": {
      "cpu_usage": 45.2,
      "memory_usage": 60.1,
      "uptime": 86400
    },
    "error_code": null,
    "error_message": null
  }
}
```

### 2.7 事件推送 (event)
**方向**: 服务端 → 客户端
```json
{
  "msg_id": "evt-001",
  "msg_type": "event",
  "timestamp": 1707955290,
  "sender": "cloud-server",
  "receiver": "local-node-01",
  "payload": {
    "event_type": "config_updated",
    "event_data": {
      "config_version": "2.0.0",
      "changes": ["interval", "thresholds"]
    }
  }
}
```

**事件类型列表**:
| event_type | 说明 |
|------------|------|
| `config_updated` | 配置更新 |
| `command_received` | 收到远程命令 |
| `server_notify` | 服务器通知 |
| `broadcast` | 广播消息 |

### 2.8 错误消息 (error)
**方向**: 双向
```json
{
  "msg_id": "err-001",
  "msg_type": "error",
  "timestamp": 1707955320,
  "sender": "cloud-server",
  "receiver": "local-node-01",
  "payload": {
    "error_code": "AUTH_FAILED",
    "error_message": "Invalid or expired token",
    "original_msg_id": "auth-001"
  }
}
```

**错误码定义**:
| error_code | 说明 | HTTP状态码映射 |
|------------|------|----------------|
| `AUTH_FAILED` | 认证失败 | 401 |
| `UNAUTHORIZED` | 未授权 | 403 |
| `INVALID_MESSAGE` | 消息格式错误 | 400 |
| `RATE_LIMITED` | 请求过于频繁 | 429 |
| `INTERNAL_ERROR` | 内部错误 | 500 |
| `TIMEOUT` | 请求超时 | 504 |
| `NODE_NOT_FOUND` | 节点不存在 | 404 |
| `ACTION_NOT_SUPPORTED` | 不支持的动作 | 400 |

## 3. 消息路由规则

### 3.1 服务端路由逻辑
```
收到消息
    │
    ▼
┌──────────────┐
│ 解析消息类型  │
└──────┬───────┘
       │
       ├── auth ────────► 认证处理器
       ├── heartbeat ───► 心跳处理器
       ├── request ─────► 请求处理器 ──► 业务逻辑
       ├── response ────► 响应处理器 ──► 回调队列
       └── event ───────► 事件处理器
```

### 3.2 客户端路由逻辑
```
收到消息
    │
    ▼
┌──────────────┐
│ 解析消息类型  │
└──────┬───────┘
       │
       ├── auth_response ──► 认证结果处理
       ├── heartbeat_ack ──► 更新心跳状态
       ├── request ────────► 业务请求处理 ──► 自动响应
       ├── response ───────► 响应回调处理
       ├── event ──────────► 事件处理器
       └── error ──────────► 错误处理
```

## 4. 超时与重试

### 4.1 超时设置
| 操作 | 超时时间 | 说明 |
|------|----------|------|
| WebSocket握手 | 10s | 连接建立超时 |
| 认证响应 | 5s | 等待认证结果 |
| 业务请求响应 | 30s | 请求-响应超时 |
| 心跳超时 | 90s | 3个心跳周期 |

### 4.2 重试策略
- 连接失败: 指数退避重试 (1s, 2s, 4s, 8s... 最大60s)
- 消息发送失败: 立即重试1次，然后标记失败
- 请求无响应: 重试2次后返回超时错误

## 5. 自动对话协议 (Auto-Dialog)

### 5.1 自动响应模式
当本地节点处于无人值守模式时，对特定请求自动响应：

| 触发条件 | 自动响应动作 |
|----------|--------------|
| 收到 `get_status` | 自动收集并返回系统状态 |
| 收到 `get_sensor_data` | 自动读取传感器并返回 |
| 收到 `ping` | 自动返回 `pong` |
| 收到 `sync_config` | 自动应用配置并返回结果 |

### 5.2 自动上报模式
本地节点可配置定时自动上报：
```json
{
  "auto_report": {
    "enabled": true,
    "interval": 300,
    "metrics": ["cpu", "memory", "disk", "network"]
  }
}
```
