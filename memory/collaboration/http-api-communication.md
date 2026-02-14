# 主备节点HTTP API通信方案 v1.0

> 网络条件: 主节点有公网IP，备用节点无公网IP  
> 设计时间: 2026-02-14 16:23  
> 核心思路: 备用节点主动连接主节点（Pull + Push）

---

## 一、网络架构分析

```
                    互联网
                      │
         ┌────────────┼────────────┐
         │            │            │
    主节点(云)        │       其他客户端
   ┌──────────┐       │      (可访问主节点)
   │ 公网IP   │◄──────┘
   │ 可被访问 │
   └────┬─────┘
        │
        │ HTTP API
        │ (备用节点主动连接)
        │
   ┌────┴─────┐
   │ 备用节点  │
   │ (本地VM) │
   │ 无公网IP │
   └──────────┘
```

### 关键约束

| 节点 | 网络位置 | 能否被访问 | 通信方式 |
|------|----------|-----------|----------|
| 主节点 | 云端 | ✅ 有公网IP，可被任何客户端访问 | 被动等待连接 |
| 备用节点 | 本地 | ❌ 无公网IP，无法被外部访问 | 主动发起连接 |

### 解决方案

**Pull + Push 模式**:
1. **Pull**: 备用节点定期轮询主节点的任务队列
2. **Push**: 备用节点执行完任务后，主动推送结果到主节点

---

## 二、HTTP API设计

### 2.1 主节点API端点（部署在主节点）

#### 任务管理端点

```http
# 1. 获取待处理任务（备用节点轮询）
GET /api/tasks/pending
Authorization: Bearer {token}
Response: {
  "tasks": [
    {
      "id": "task-001",
      "type": "data-processing",
      "priority": "high",
      "payload": {...},
      "created_at": "2026-02-14T16:20:00Z"
    }
  ]
}

# 2. 认领任务（备用节点开始执行）
POST /api/tasks/{task_id}/claim
Authorization: Bearer {token}
Body: {
  "node_id": "standby-001",
  "claimed_at": "2026-02-14T16:21:00Z"
}

# 3. 更新任务进度（执行过程中）
POST /api/tasks/{task_id}/progress
Authorization: Bearer {token}
Body: {
  "progress": 50,
  "status": "processing",
  "log": "处理中..."
}

# 4. 提交任务结果（执行完成）
POST /api/tasks/{task_id}/complete
Authorization: Bearer {token}
Body: {
  "status": "success",
  "result": {...},
  "execution_time": 120,
  "completed_at": "2026-02-14T16:23:00Z"
}
```

#### 状态管理端点

```http
# 5. 备用节点上报自身状态
POST /api/nodes/status
Authorization: Bearer {token}
Body: {
  "node_id": "standby-001",
  "hostname": "sensen-standby",
  "cpu_usage": 45,
  "memory_usage": 60,
  "active_tasks": 3,
  "queue_length": 0,
  "timestamp": "2026-02-14T16:20:00Z"
}

# 6. 获取主节点状态
GET /api/nodes/primary/status
Authorization: Bearer {token}
Response: {
  "cpu_usage": 30,
  "memory_usage": 40,
  "active_tasks": 5
}
```

#### 文件传输端点（小文件）

```http
# 7. 下载任务附件
GET /api/files/{file_id}/download
Authorization: Bearer {token}
Response: Binary file data

# 8. 上传结果文件
POST /api/files/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data
Body: file, task_id
```

### 2.2 API认证

使用简单的Token认证：
```http
Authorization: Bearer {shared_secret}
```

Shared Secret通过GitHub同步，避免硬编码。

---

## 三、通信流程设计

### 3.1 任务执行流程

```
┌─────────────┐                    ┌─────────────┐
│  主节点      │                    │  备用节点    │
│ (云端API)   │                    │ (本地轮询)  │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │◄──────── 1. 轮询任务 ───────────┤ 每30秒
       │                                  │
       ├───────── 2. 返回任务列表 ───────►│
       │                                  │
       │◄──────── 3. 认领任务 ───────────┤
       │                                  │
       ├───────── 4. 确认认领 ──────────►│
       │                                  │
       │                                  ▼
       │                          [执行任务]
       │                                  │
       │◄──────── 5. 进度更新 ───────────┤ 每5秒
       │                                  │
       │◄──────── 6. 提交结果 ───────────┤ 完成
       │                                  │
       ├───────── 7. 确认接收 ──────────►│
       │                                  │
```

### 3.2 心跳与状态同步

```
备用节点每60秒:
  ├─ POST /api/nodes/status (上报自身状态)
  ├─ GET /api/nodes/primary/status (查询主节点状态)
  └─ 如果任务队列>0，立即处理
```

---

## 四、备用节点客户端实现

### 4.1 核心架构

```python
# standby_client.py (运行在备用节点)

import requests
import time
import threading
from typing import Dict, List

class StandbyClient:
    def __init__(self, primary_url: str, token: str):
        self.primary_url = primary_url
        self.token = token
        self.node_id = "standby-001"
        self.running = False
        self.active_tasks = {}
        
    def start(self):
        """启动客户端"""
        self.running = True
        
        # 启动轮询线程
        threading.Thread(target=self._poll_loop, daemon=True).start()
        
        # 启动心跳线程
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        
    def _poll_loop(self):
        """任务轮询循环"""
        while self.running:
            try:
                # 获取待处理任务
                tasks = self._fetch_pending_tasks()
                
                for task in tasks:
                    if task['id'] not in self.active_tasks:
                        # 启动新任务
                        threading.Thread(
                            target=self._execute_task,
                            args=(task,),
                            daemon=True
                        ).start()
                        
            except Exception as e:
                print(f"轮询错误: {e}")
                
            time.sleep(30)  # 每30秒轮询一次
            
    def _fetch_pending_tasks(self) -> List[Dict]:
        """从主节点获取待处理任务"""
        response = requests.get(
            f"{self.primary_url}/api/tasks/pending",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=10
        )
        response.raise_for_status()
        return response.json().get('tasks', [])
        
    def _execute_task(self, task: Dict):
        """执行任务"""
        task_id = task['id']
        self.active_tasks[task_id] = task
        
        try:
            # 1. 认领任务
            self._claim_task(task_id)
            
            # 2. 执行具体任务（根据类型）
            result = self._run_task_logic(task)
            
            # 3. 提交结果
            self._submit_result(task_id, result)
            
        except Exception as e:
            self._submit_error(task_id, str(e))
        finally:
            del self.active_tasks[task_id]
            
    def _run_task_logic(self, task: Dict) -> Dict:
        """根据任务类型执行具体逻辑"""
        task_type = task.get('type')
        
        if task_type == 'data-processing':
            return self._process_data(task['payload'])
        elif task_type == 'web-scraping':
            return self._scrape_web(task['payload'])
        elif task_type == 'compilation':
            return self._compile_project(task['payload'])
        else:
            return {"error": "Unknown task type"}
            
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                self._send_heartbeat()
            except Exception as e:
                print(f"心跳错误: {e}")
            time.sleep(60)  # 每60秒心跳一次
            
    def _send_heartbeat(self):
        """发送状态心跳"""
        import psutil
        
        status = {
            "node_id": self.node_id,
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "active_tasks": len(self.active_tasks),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        requests.post(
            f"{self.primary_url}/api/nodes/status",
            headers={"Authorization": f"Bearer {self.token}"},
            json=status,
            timeout=5
        )
```

---

## 五、主节点服务端实现

### 5.1 轻量级API服务（Python Flask示例）

```python
# primary_server.py (运行在主节点)

from flask import Flask, request, jsonify
from functools import wraps
import threading
import time
from typing import Dict, List

app = Flask(__name__)

# 内存存储（生产环境应使用Redis/数据库）
task_queue: Dict[str, Dict] = {}
task_results: Dict[str, Dict] = {}
node_status: Dict[str, Dict] = {}

# 共享密钥（从环境变量或配置文件读取）
API_TOKEN = "shared-secret-token"

def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Unauthorized"}), 401
        token = auth_header.split(' ')[1]
        if token != API_TOKEN:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

# ========== 任务管理API ==========

@app.route('/api/tasks/pending', methods=['GET'])
@require_auth
def get_pending_tasks():
    """获取待处理任务"""
    pending = [
        task for task in task_queue.values()
        if task.get('status') == 'pending'
    ]
    # 按优先级排序
    pending.sort(key=lambda x: x.get('priority', 0), reverse=True)
    return jsonify({"tasks": pending[:10]})  # 最多返回10个

@app.route('/api/tasks', methods=['POST'])
@require_auth
def create_task():
    """创建新任务（主节点调用）"""
    data = request.json
    task_id = f"task-{int(time.time() * 1000)}"
    
    task = {
        "id": task_id,
        "type": data.get('type'),
        "priority": data.get('priority', 'normal'),
        "payload": data.get('payload', {}),
        "status": "pending",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "created_by": "primary"
    }
    
    task_queue[task_id] = task
    return jsonify({"task_id": task_id, "status": "created"})

@app.route('/api/tasks/<task_id>/claim', methods=['POST'])
@require_auth
def claim_task(task_id):
    """备用节点认领任务"""
    if task_id not in task_queue:
        return jsonify({"error": "Task not found"}), 404
    
    task = task_queue[task_id]
    if task.get('status') != 'pending':
        return jsonify({"error": "Task already claimed"}), 400
    
    data = request.json
    task['status'] = 'processing'
    task['claimed_by'] = data.get('node_id')
    task['claimed_at'] = data.get('claimed_at')
    
    return jsonify({"status": "claimed"})

@app.route('/api/tasks/<task_id>/progress', methods=['POST'])
@require_auth
def update_progress(task_id):
    """更新任务进度"""
    if task_id not in task_queue:
        return jsonify({"error": "Task not found"}), 404
    
    data = request.json
    task_queue[task_id]['progress'] = data.get('progress', 0)
    task_queue[task_id]['status'] = data.get('status', 'processing')
    task_queue[task_id]['log'] = data.get('log', '')
    
    return jsonify({"status": "updated"})

@app.route('/api/tasks/<task_id>/complete', methods=['POST'])
@require_auth
def complete_task(task_id):
    """任务完成"""
    if task_id not in task_queue:
        return jsonify({"error": "Task not found"}), 404
    
    data = request.json
    task = task_queue[task_id]
    task['status'] = data.get('status', 'completed')
    task['result'] = data.get('result', {})
    task['execution_time'] = data.get('execution_time', 0)
    task['completed_at'] = data.get('completed_at')
    
    # 移动到结果存储
    task_results[task_id] = task
    del task_queue[task_id]
    
    return jsonify({"status": "completed"})

# ========== 状态管理API ==========

@app.route('/api/nodes/status', methods=['POST'])
@require_auth
def update_node_status():
    """备用节点上报状态"""
    data = request.json
    node_id = data.get('node_id')
    node_status[node_id] = {
        **data,
        "last_seen": time.time()
    }
    return jsonify({"status": "received"})

@app.route('/api/nodes/primary/status', methods=['GET'])
@require_auth
def get_primary_status():
    """获取主节点状态"""
    import psutil
    return jsonify({
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "active_tasks": len([t for t in task_queue.values() if t.get('status') == 'processing']),
        "pending_tasks": len([t for t in task_queue.values() if t.get('status') == 'pending'])
    })

# 健康检查
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "time": time.time()})

if __name__ == '__main__':
    # 生产环境应使用gunicorn/uwsgi
    app.run(host='0.0.0.0', port=8080, threaded=True)
```

---

## 六、部署方案

### 6.1 主节点部署（云端）

```bash
# 1. 安装依赖
pip install flask psutil gunicorn

# 2. 配置systemd服务
sudo tee /etc/systemd/system/primary-api.service > /dev/null << EOF
[Unit]
Description=Primary Node API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace
Environment="API_TOKEN=shared-secret-token"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:8080 primary_server:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 3. 启动服务
sudo systemctl enable primary-api
sudo systemctl start primary-api

# 4. 开放防火墙端口
sudo ufw allow 8080/tcp
```

### 6.2 备用节点部署（本地）

```bash
# 1. 安装依赖
pip install requests psutil

# 2. 创建启动脚本
tee /root/.openclaw/workspace/standby_client.py > /dev/null << 'EOF'
#!/usr/bin/env python3
from standby_client import StandbyClient

client = StandbyClient(
    primary_url="http://{主节点公网IP}:8080",
    token="shared-secret-token"
)
client.start()

# 保持运行
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    client.running = False
EOF

# 3. 配置systemd服务
sudo tee /etc/systemd/system/standby-client.service > /dev/null << EOF
[Unit]
Description=Standby Node Client
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/standby_client.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 4. 启动服务
sudo systemctl enable standby-client
sudo systemctl start standby-client
```

---

## 七、安全性考虑

### 7.1 网络安全

```yaml
安全措施:
  - API Token认证 (共享密钥)
  - HTTPS加密 (使用nginx反向代理 + SSL证书)
  - IP白名单 (可选，限制备用节点IP范围)
  - 请求限流 (防止DDoS)
```

### 7.2 数据安全

- 敏感数据不通过API传输，使用GitHub同步
- 任务结果加密传输
- 定期轮换API Token

---

## 八、扩展方案

### 8.1 WebSocket实时通信（可选）

如果需要更低延迟，可以使用WebSocket：

```python
# 备用节点建立WebSocket连接（仍然主动连接主节点）
import websocket

ws = websocket.create_connection(f"ws://{primary_ip}:8080/ws")
ws.send(json.dumps({"type": "register", "node_id": "standby-001"}))

# 主节点可以主动推送消息到备用节点
```

### 8.2 多备用节点支持

```python
# 主节点支持多个备用节点注册
node_registry = {
    "standby-001": {"ip": "...", "last_seen": ..., "capabilities": [...]},
    "standby-002": {"ip": "...", "last_seen": ..., "capabilities": [...]}
}
```

---

## 九、总结

| 特性 | 实现方式 |
|------|----------|
| **网络穿透** | 备用节点主动连接（无需公网IP） |
| **任务分发** | 轮询 + 长轮询（Pull模式） |
| **结果返回** | HTTP POST（Push模式） |
| **实时性** | 30秒轮询间隔，可配置 |
| **扩展性** | 支持多备用节点 |
| **安全性** | Token认证 + HTTPS |

**核心优势**：无需复杂网络配置，备用节点只要有出网能力即可工作。

---

*方案设计: 森森*  
*时间: 2026-02-14 16:23*
