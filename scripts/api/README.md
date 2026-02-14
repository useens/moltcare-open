# Sensen HTTP API 通信方案 v1.0

> 主节点(云端，有公网IP) + 备用节点(本地，无公网IP) 的HTTP API通信实现

---

## 快速开始

### 1. 主节点部署（云端）

```bash
# 1. 运行安装脚本
cd /root/.openclaw/workspace/scripts/api
bash install.sh

# 2. 选择: 1) 主节点

# 3. 启动服务
systemctl start sensen-primary

# 4. 查看日志
tail -f /var/log/sensen-primary.log
```

### 2. 备用节点部署（本地）

```bash
# 1. 运行安装脚本
cd /root/.openclaw/workspace/scripts/api
bash install.sh

# 2. 选择: 2) 备用节点
# 3. 输入主节点IP和Token

# 4. 启动服务
systemctl start sensen-standby

# 5. 查看日志
tail -f /var/log/sensen-standby.log
```

---

## 文件结构

```
api/
├── primary_server.py          # 主节点API服务端
├── standby_client.py          # 备用节点客户端
├── install.sh                 # 一键安装脚本
├── test.sh                    # API测试脚本
├── systemd/
│   ├── sensen-primary.service # 主节点systemd服务
│   └── sensen-standby.service # 备用节点systemd服务
└── README.md                  # 本文档
```

---

## API文档

### 健康检查
```http
GET /health
# 无需认证
```

### 任务管理

#### 获取待处理任务
```http
GET /api/tasks/pending
Authorization: Bearer {token}
```

#### 创建任务
```http
POST /api/tasks
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "data-processing",
  "priority": "high",
  "payload": {...}
}
```

#### 认领任务
```http
POST /api/tasks/{task_id}/claim
Authorization: Bearer {token}

{
  "node_id": "standby-001",
  "claimed_at": "2026-02-14T16:30:00Z"
}
```

#### 更新进度
```http
POST /api/tasks/{task_id}/progress
Authorization: Bearer {token}

{
  "progress": 50,
  "status": "processing",
  "log": "处理中..."
}
```

#### 完成任务
```http
POST /api/tasks/{task_id}/complete
Authorization: Bearer {token}

{
  "status": "success",
  "result": {...},
  "execution_time": 120
}
```

### 状态管理

#### 上报节点状态
```http
POST /api/nodes/status
Authorization: Bearer {token}

{
  "node_id": "standby-001",
  "cpu_usage": 45,
  "memory_usage": 60,
  "active_tasks": 2
}
```

#### 获取主节点状态
```http
GET /api/nodes/primary/status
Authorization: Bearer {token}
```

---

## 工作流程

```
主节点(云端)                          备用节点(本地)
    │                                      │
    │◄──────── 1. 轮询任务(30s) ───────────┤
    │                                      │
    ├───────── 2. 返回任务列表 ───────────►│
    │                                      │
    │◄──────── 3. 认领任务 ────────────────┤
    │                                      │
    │                                      ▼
    │                              [执行任务]
    │                                      │
    │◄──────── 4. 进度更新 ────────────────┤ 每5s
    │                                      │
    │◄──────── 5. 完成结果 ────────────────┤
    │                                      │
```

---

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PRIMARY_URL` | 主节点API地址 | `http://localhost:2346` |
| `SENSEN_API_TOKEN` | API认证Token | `default-token` |
| `NODE_ID` | 节点标识 | 自动生成 |

### 配置文件

```bash
# 环境配置存储在
/root/.openclaw/workspace/.api-env
```

---

## 手动运行

### 主节点
```bash
cd /root/.openclaw/workspace
export SENSEN_API_TOKEN="your-secret-token"
python3 scripts/api/primary_server.py
```

### 备用节点
```bash
cd /root/.openclaw/workspace
export PRIMARY_URL="http://primary-ip:2346"
export SENSEN_API_TOKEN="your-secret-token"
python3 scripts/api/standby_client.py
```

---

## 测试

```bash
# 设置测试环境变量
export PRIMARY_URL="http://your-primary-ip:2346"
export SENSEN_API_TOKEN="your-token"

# 运行测试
bash scripts/api/test.sh
```

---

## 任务类型

备用节点支持以下任务类型：

| 类型 | 说明 |
|------|------|
| `data-processing` | 数据处理 |
| `web-scraping` | Web爬取 |
| `computation` | 计算任务 |
| `command` | 执行系统命令 |
| `generic` | 通用任务 |

---

## 日志位置

| 服务 | 日志文件 |
|------|----------|
| 主节点 | `/var/log/sensen-primary.log` |
| 备用节点 | `/var/log/sensen-standby.log` |

---

## 故障排查

### 备用节点无法连接主节点

1. 检查主节点是否启动
   ```bash
   curl http://primary-ip:2346/health
   ```

2. 检查Token是否正确

3. 检查防火墙
   ```bash
   # 主节点执行
   ufw status
   # 确保2346端口已开放
   ```

### 查看服务状态

```bash
# 主节点
systemctl status sensen-primary
journalctl -u sensen-primary -f

# 备用节点
systemctl status sensen-standby
journalctl -u sensen-standby -f
```

---

## 安全建议

1. **使用HTTPS**: 生产环境建议使用nginx反向代理 + SSL证书
2. **IP白名单**: 限制只有备用节点IP可以访问API
3. **定期轮换Token**: 定期更新API Token
4. **防火墙**: 仅开放必要的端口(2346)

---

*版本: v1.0*  
*创建时间: 2026-02-14*
