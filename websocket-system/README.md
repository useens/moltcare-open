# WebSocket 即时通信系统

云端节点 ↔ 本地节点 双向即时通信系统

## 系统特性

- ✅ **低延迟通信** - 目标 <100ms 消息往返延迟
- ✅ **自动重连** - 指数退避策略，高可靠性
- ✅ **心跳检测** - 30秒间隔，90秒超时检测
- ✅ **安全传输** - TLS加密 + Token认证
- ✅ **自动响应** - 无人值守时自动处理请求
- ✅ **高并发** - 单服务器支持10,000+连接

## 快速开始

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install websockets psutil
```

### 3. 启动服务

```bash
# 使用快速启动脚本
chmod +x run.sh
./run.sh start

# 或手动启动
# 终端1 - 启动服务器
python src/server.py --host 0.0.0.0 --port 8765

# 终端2 - 启动客户端
python src/client.py --url ws://localhost:8765 --node-id local-node-01
```

### 4. 运行测试

```bash
./run.sh test

# 或手动测试
python tests/test_websocket.py --url ws://localhost:8765
```

## 项目结构

```
websocket-system/
├── docs/
│   ├── architecture.md      # 架构设计文档
│   └── protocol.md          # 通信协议设计
├── src/
│   ├── server.py            # WebSocket服务端
│   └── client.py            # WebSocket客户端
├── config/
│   ├── server.json          # 服务端配置
│   └── client.json          # 客户端配置
├── scripts/
│   ├── deploy-server.sh     # 服务端部署脚本
│   ├── deploy-client.sh     # 客户端部署脚本
│   ├── websocket-server.service  # systemd服务(服务端)
│   └── websocket-client.service  # systemd服务(客户端)
├── tests/
│   └── test_websocket.py    # 测试脚本
├── Dockerfile.server        # 服务端Docker镜像
├── Dockerfile.client        # 客户端Docker镜像
├── docker-compose.yml       # Docker编排
└── run.sh                   # 快速启动脚本
```

## 部署指南

### 云端节点部署（服务端）

```bash
# 1. 复制项目到云端服务器
cd websocket-system

# 2. 运行部署脚本
sudo ./scripts/deploy-server.sh

# 3. 启动服务
sudo systemctl enable websocket-server
sudo systemctl start websocket-server

# 4. 查看状态
sudo systemctl status websocket-server
sudo journalctl -u websocket-server -f
```

### 本地节点部署（客户端）

```bash
# 1. 复制项目到本地设备
cd websocket-system

# 2. 运行部署脚本（交互式配置）
sudo ./scripts/deploy-client.sh

# 3. 启动服务
sudo systemctl enable websocket-client
sudo systemctl start websocket-client
```

### Docker部署

```bash
# 使用Docker Compose启动
./run.sh docker

# 或手动启动
docker-compose up --build
```

## 通信协议

### 消息格式

```json
{
  "msg_id": "uuid-string",
  "msg_type": "auth|heartbeat|request|response|event|error",
  "timestamp": 1707955200,
  "sender": "node_id",
  "receiver": "node_id|broadcast",
  "payload": {}
}
```

### 认证流程

1. 客户端连接服务器
2. 客户端发送 `auth` 消息（携带Token）
3. 服务器验证Token
4. 服务器返回 `auth_response`

### 心跳机制

- **间隔**: 30秒
- **超时**: 90秒（3个心跳周期）
- **检测**: 服务器主动检测，超时断开

## 配置说明

### 服务端配置 (config/server.json)

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8765,
    "heartbeat_timeout": 90,
    "ssl": {
      "enabled": true,
      "cert_path": "/etc/ssl/server.crt",
      "key_path": "/etc/ssl/server.key"
    }
  },
  "auth": {
    "tokens": ["your-secret-token"]
  }
}
```

### 客户端配置 (config/client.json)

```json
{
  "client": {
    "server_url": "wss://your-server:8765",
    "node_id": "local-node-01",
    "token": "your-secret-token"
  },
  "reconnect": {
    "enabled": true,
    "base_delay": 1.0,
    "max_delay": 60.0
  },
  "heartbeat": {
    "interval": 30
  }
}
```

## API参考

### 请求动作

| 动作 | 说明 | 参数 |
|------|------|------|
| `get_status` | 获取状态 | - |
| `ping` | 测试连通 | - |
| `echo` | 回显测试 | `message` |
| `get_sensor_data` | 传感器数据 | `sensor_id` |
| `execute_command` | 执行命令 | `command`, `args` |

### 错误码

| 错误码 | 说明 |
|--------|------|
| `AUTH_FAILED` | 认证失败 |
| `INVALID_MESSAGE` | 消息格式错误 |
| `ACTION_NOT_SUPPORTED` | 不支持的动作 |
| `INTERNAL_ERROR` | 内部错误 |
| `TIMEOUT` | 请求超时 |

## 监控与日志

### 日志位置

- 服务端: `/var/log/websocket-server/server.log`
- 客户端: `/var/log/websocket-client/client.log`

### 关键指标

- 活跃连接数
- 消息吞吐量
- 平均延迟
- 重连次数

## 安全建议

1. **使用TLS加密** - 生产环境必须使用WSS
2. **强Token策略** - 使用随机生成的高强度Token
3. **防火墙规则** - 限制WebSocket端口访问
4. **定期更换Token** - 建议24小时轮换
5. **日志脱敏** - 日志中不记录敏感信息

## 许可证

MIT License
