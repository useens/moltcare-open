# WebSocket服务器生产部署完整指南

## 🎯 目标

在独立服务器上部署WebSocket客户端，实现7x24小时稳定运行。

---

## 📋 服务器要求

| 配置 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 系统 | Ubuntu 20.04+ | Ubuntu 22.04 LTS |
| CPU | 1核 | 2核+ |
| 内存 | 512MB | 1GB+ |
| 网络 | 公网IP | 固定公网IP |
| Python | 3.8+ | 3.11+ |

---

## 🚀 部署步骤

### 第一步：服务器准备

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装Python和依赖
sudo apt install -y python3 python3-pip python3-venv

# 3. 创建用户
sudo useradd -m -s /bin/bash sensen
sudo usermod -aG sudo sensen

# 4. 切换到用户
sudo su - sensen
```

---

### 第二步：安装WebSocket客户端

```bash
# 1. 创建工作目录
mkdir -p ~/sensen-ws
cd ~/sensen-ws

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install websockets

# 4. 创建客户端文件
cat > websocket_client.py << 'PYTHON'
#!/usr/bin/env python3
import asyncio
import websockets
import json
import time
import logging
from datetime import datetime

# 配置
WS_URL = "ws://129.154.251.13:2347"
TOKEN = "sensen-shared-2024"
NODE_ID = "standby-server-production"

# 日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/sensen-websocket.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StableWebSocketClient:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.reconnect_delay = 5
        self.msg_count = 0
        
    async def connect(self):
        while True:
            try:
                logger.info("连接WebSocket...")
                self.ws = await websockets.connect(WS_URL)
                
                # 认证
                await self.ws.send(json.dumps({
                    "type": "auth",
                    "token": TOKEN,
                    "node_id": NODE_ID
                }))
                
                auth = await self.ws.recv()
                logger.info(f"认证成功: {json.loads(auth).get('message')}")
                
                # 就绪
                await self.ws.send(json.dumps({
                    "type": "status",
                    "status": "ready",
                    "system": {"cpu_cores": 8, "memory_gb": 16}
                }))
                
                self.connected = True
                self.reconnect_delay = 5
                logger.info("已就绪，开始通信")
                
                # 消息循环
                async for message in self.ws:
                    await self.handle_message(message)
                    
            except Exception as e:
                logger.error(f"连接错误: {e}")
                self.connected = False
            
            # 重连
            logger.info(f"{self.reconnect_delay}秒后重连...")
            await asyncio.sleep(self.reconnect_delay)
            self.reconnect_delay = min(self.reconnect_delay * 2, 60)
    
    async def handle_message(self, msg):
        try:
            data = json.loads(msg)
            if data.get('type') == 'message':
                self.msg_count += 1
                content = data.get('content', '')
                logger.info(f"收到[{self.msg_count}]: {content[:60]}...")
                
                # 回复
                reply = f"收到！服务器节点在线 ({datetime.now().strftime('%H:%M:%S')})"
                await self.ws.send(json.dumps({
                    "type": "message",
                    "from": "服务器节点",
                    "content": reply
                }))
                logger.info(f"回复: {reply}")
        except Exception as e:
            logger.error(f"处理错误: {e}")

if __name__ == '__main__':
    client = StableWebSocketClient()
    asyncio.run(client.connect())
PYTHON

chmod +x websocket_client.py
```

---

### 第三步：创建Systemd服务

```bash
# 1. 创建服务文件
sudo tee /etc/systemd/system/sensen-websocket.service << 'EOF'
[Unit]
Description=Sensen WebSocket Client
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=sensen
Group=sensen
WorkingDirectory=/home/sensen/sensen-ws
Environment="PATH=/home/sensen/sensen-ws/venv/bin"
ExecStart=/home/sensen/sensen-ws/venv/bin/python /home/sensen/sensen-ws/websocket_client.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sensen-websocket

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true

[Install]
WantedBy=multi-user.target
EOF

# 2. 重新加载systemd
sudo systemctl daemon-reload

# 3. 启动服务
sudo systemctl enable sensen-websocket
sudo systemctl start sensen-websocket

# 4. 检查状态
sudo systemctl status sensen-websocket
```

---

### 第四步：监控和日志

```bash
# 查看实时日志
sudo journalctl -u sensen-websocket -f

# 查看历史日志
sudo journalctl -u sensen-websocket --since "1 hour ago"

# 查看服务状态
sudo systemctl status sensen-websocket

# 重启服务
sudo systemctl restart sensen-websocket

# 停止服务
sudo systemctl stop sensen-websocket
```

---

### 第五步：健康检查

```bash
# 创建健康检查脚本
sudo tee /usr/local/bin/sensen-health-check.sh << 'EOF'
#!/bin/bash

# 检查进程
if ! pgrep -f "websocket_client.py" > /dev/null; then
    echo "⚠️  WebSocket进程不存在，重启服务..."
    systemctl restart sensen-websocket
    exit 1
fi

# 检查日志活动
LAST_LOG=$(journalctl -u sensen-websocket --since "5 minutes ago" | tail -1)
if [ -z "$LAST_LOG" ]; then
    echo "⚠️  5分钟无日志活动，重启服务..."
    systemctl restart sensen-websocket
    exit 1
fi

echo "✅ 服务健康"
exit 0
EOF

sudo chmod +x /usr/local/bin/sensen-health-check.sh

# 添加到cron (每5分钟检查)
echo "*/5 * * * * root /usr/local/bin/sensen-health-check.sh" | sudo tee -a /etc/crontab
```

---

### 第六步：防火墙配置

```bash
# 开放WebSocket端口（如果需要）
sudo ufw allow 2347/tcp

# 或者使用iptables
sudo iptables -A INPUT -p tcp --dport 2347 -j ACCEPT
```

---

### 第七步：备份和恢复

```bash
# 备份脚本
sudo tee /usr/local/bin/sensen-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/sensen/backups"
mkdir -p $BACKUP_DIR
tar czf "$BACKUP_DIR/sensen-ws-$(date +%Y%m%d).tar.gz" /home/sensen/sensen-ws/
EOF

sudo chmod +x /usr/local/bin/sensen-backup.sh
```

---

## 📊 监控指标

| 指标 | 命令 | 正常范围 |
|------|------|----------|
| 进程状态 | `systemctl status sensen-websocket` | active (running) |
| CPU使用 | `top -p $(pgrep -f websocket_client.py)` | < 10% |
| 内存使用 | `ps -o rss= -p $(pgrep -f websocket_client.py)` | < 100MB |
| 日志活动 | `journalctl -u sensen-websocket --since "5 min ago"` | 有最近日志 |
| 连接状态 | `netstat -tnp | grep 2347` | ESTABLISHED |

---

## 🚨 故障排除

### 服务无法启动
```bash
# 检查日志
sudo journalctl -u sensen-websocket -n 50

# 检查Python环境
/home/sensen/sensen-ws/venv/bin/python --version

# 手动测试
sudo su - sensen
cd ~/sensen-ws
source venv/bin/activate
python websocket_client.py
```

### 连接断开频繁
```bash
# 检查网络
ping 129.154.251.13

# 检查防火墙
sudo ufw status

# 增加日志级别
# 修改服务文件，添加 -v 参数
```

### 内存占用过高
```bash
# 重启服务
sudo systemctl restart sensen-websocket

# 检查是否有内存泄漏
sudo journalctl -u sensen-websocket | grep -i memory
```

---

## ✅ 部署检查清单

- [ ] 服务器系统更新完成
- [ ] Python环境安装完成
- [ ] WebSocket客户端部署完成
- [ ] Systemd服务配置完成
- [ ] 服务成功启动
- [ ] 日志正常输出
- [ ] 健康检查脚本配置完成
- [ ] 防火墙配置完成
- [ ] 备份脚本配置完成
- [ ] 监控告警配置完成

---

## 🎉 完成

部署完成后，WebSocket客户端将在服务器上7x24小时稳定运行，与主节点保持实时通信！

**主节点IP**: 129.154.251.13:2347
**服务器节点**: 备用节点生产环境
**监控日志**: `journalctl -u sensen-websocket -f`
