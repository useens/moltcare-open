# 🌉 WebSocket Bridge - 森森双节点即时通信系统

实现云端节点 ↔ 本地节点的实时双向通信，无需人工介入的持续对话。

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      云端节点 (Cloud)                        │
│  ┌─────────────────┐          ┌──────────────────┐         │
│  │ WebSocket Server │◄────────►│  森森·云端       │         │
│  │   Port: 8765    │          │  (主节点)        │         │
│  └────────┬────────┘          └──────────────────┘         │
│           │                                                  │
│           │ WebSocket (双向)                                 │
│           │                                                  │
│  ┌────────┴────────┐          ┌──────────────────┐         │
│  │ WebSocket Client │◄────────►│  森森·本地       │         │
│  │                 │          │  (备节点)        │         │
│  └─────────────────┘          └──────────────────┘         │
│                      本地节点 (Local)                        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速部署

### 1. 云端节点（服务端）

```bash
# 在云端服务器执行
/root/.openclaw/workspace/scripts/websocket-bridge/deploy-server.sh
```

**前置要求：**
- 防火墙开放 8765 端口
- Python 3.8+
- 可选：Nginx反向代理提供WSS(TLS)

### 2. 本地节点（客户端）

```bash
# 在本地服务器执行
/root/.openclaw/workspace/scripts/websocket-bridge/deploy-client.sh
```

**需要输入：**
- 云端服务器地址 (ws://IP:8765)

## 📡 通信协议

### 消息格式 (JSON)

```json
{
  "type": "chat|command|system|ping|pong",
  "from": "sensen-local",
  "target": "sensen-cloud",
  "content": "消息内容",
  "timestamp": "2026-02-15T05:55:00Z"
}
```

### 消息类型

| 类型 | 说明 | 方向 |
|------|------|------|
| `chat` | 普通聊天消息 | 双向 |
| `command` | 执行命令请求 | 双向 |
| `system` | 系统事件通知 | 服务端→客户端 |
| `ping/pong` | 心跳保活 | 双向 |
| `auth` | 连接认证 | 客户端→服务端 |

### 认证流程

```
Client                          Server
  │                                │
  ├─────── {type:auth, token} ────►│
  │                                │
  │◄────── {type:auth_success} ────┤
  │                                │
  ├─ 开始正常通信 ─────────────────►│
```

## 🔧 配置说明

### 服务端配置 (server.py)

```python
HOST = "0.0.0.0"          # 监听地址
PORT = 8765               # 监听端口
HEARTBEAT_INTERVAL = 30   # 心跳间隔(秒)
TOKEN = "sensen-bridge-2024"  # 认证令牌
```

### 客户端配置 (client.py)

```python
SERVER_URI = "ws://your-server:8765"  # 服务端地址
CLIENT_ID = "sensen-local"            # 客户端标识
TOKEN = "sensen-bridge-2024"          # 认证令牌
```

## 🛡️ 安全建议

1. **使用WSS (WebSocket over TLS)**
   ```bash
   # 通过Nginx反向代理
   server {
       listen 443 ssl;
       location /ws {
           proxy_pass http://localhost:8765;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

2. **更换默认Token**
   - 修改 server.py 和 client.py 中的 TOKEN
   - 使用强随机字符串

3. **限制访问IP**
   - 防火墙仅允许本地节点IP访问

## 📊 监控命令

```bash
# 查看服务状态
systemctl status sensen-ws-server  # 云端
systemctl status sensen-ws-client  # 本地

# 查看实时日志
tail -f /var/log/sensen-ws-server.log
tail -f /var/log/sensen-ws-client.log

# 查看连接状态
netstat -tulpn | grep 8765
```

## 🔄 自动重启

systemd已配置自动重启：
- 崩溃后5秒自动重启
- 无限重试次数

## 📝 扩展开发

### 添加新消息处理器

```python
# client.py
async def handle_custom(self, message: dict):
    """处理自定义消息"""
    data = message.get('data')
    # 实现处理逻辑
    await self.send({
        'type': 'custom_response',
        'result': '处理完成'
    })

# 注册处理器
self.register_handler('custom', self.handle_custom)
```

## 🐛 故障排除

| 问题 | 解决方案 |
|------|----------|
| 连接失败 | 检查防火墙、服务端是否运行 |
| 认证失败 | 检查TOKEN是否一致 |
| 频繁断开 | 检查网络稳定性、调整心跳间隔 |
| 消息丢失 | 检查日志、实现消息确认机制 |

## 📄 文件清单

```
scripts/websocket-bridge/
├── server.py                    # 服务端代码
├── client.py                    # 客户端代码
├── sensen-ws-server.service     # 服务端systemd配置
├── sensen-ws-client.service     # 客户端systemd配置
├── deploy-server.sh             # 服务端部署脚本
├── deploy-client.sh             # 客户端部署脚本
├── test-bridge.py               # 测试脚本
└── README.md                    # 本文件
```

## 🎯 使用场景

1. **即时对话** - 两节点实时聊天，无需人工介入
2. **任务分发** - 云端分析拆解，本地执行实现
3. **状态同步** - 实时同步两节点状态信息
4. **协同计算** - 分布式任务协同处理

---
*版本: 1.0.0 | 森森 WebSocket Bridge*