# Multi-Agent Redis 实时同步方案

## 当前问题

**文件系统方案的缺点**：
- ❌ 轮询延迟：5-10秒检查一次文件
- ❌ I/O开销：频繁读写磁盘
- ❌ 并发问题：多个Agent同时写可能冲突
- ❌ 没有Pub/Sub：无法实时推送更新

---

## Redis 优化方案

### 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    主Agent (Grok)                        │
│                    订阅Redis频道                         │
│                         │                               │
│                         ▼                               │
│              ┌─────────────────────┐                    │
│              │   Redis Pub/Sub     │                    │
│              │  ┌─────────────┐    │                    │
│              │  │ round:1     │    │                    │
│              │  │ round:2     │    │                    │
│              │  │ round:3     │    │                    │
│              │  └─────────────┘    │                    │
│              └─────────────────────┘                    │
│                         │                               │
│         ┌───────────────┼───────────────┐               │
│         ▼               ▼               ▼               │
│    ┌─────────┐    ┌─────────┐    ┌─────────┐           │
│    │ Harper  │    │Benjamin │    │  Lucas  │           │
│    │ 发布    │    │ 发布    │    │ 发布    │           │
│    └─────────┘    └─────────┘    └─────────┘           │
└─────────────────────────────────────────────────────────┘
```

---

## 数据结构

### 1. 状态存储 (Hash)
```redis
HSET debate:round:1 harper "..." benjamin "..." lucas "..."
HSET debate:round:2 harper "..." benjamin "..." lucas "..."
HSET debate:round:3 harper "..." benjamin "..." lucas "..."
```

### 2. 实时通知 (Pub/Sub)
```redis
# 专家发布更新
PUBLISH debate:updates "{\"round\":2,\"agent\":\"harper\",\"status\":\"complete\"}"

# 主Agent订阅
SUBSCRIBE debate:updates
```

### 3. 进度追踪 (String)
```redis
SET debate:progress "round:2:harper:complete"
SET debate:status "debating"  # debating | consensus | completed
```

### 4. 超时控制 (TTL)
```redis
# 每轮2分钟超时
EXPIRE debate:round:1 120
EXPIRE debate:round:2 120
EXPIRE debate:round:3 120
```

---

## 实现代码

### 专家Agent端 (Python)
```python
import redis
import json
import time

r = redis.Redis(host='localhost', port=6379, db=0)

def publish_thought(round_num, agent_name, content):
    """发布思考内容"""
    # 存储内容
    r.hset(f"debate:round:{round_num}", agent_name, content)
    
    # 发布通知
    r.publish("debate:updates", json.dumps({
        "round": round_num,
        "agent": agent_name,
        "status": "updated",
        "timestamp": time.time()
    }))
    
    # 更新进度
    r.set(f"debate:progress:{agent_name}", f"round:{round_num}:complete")

def get_other_agents_thoughts(round_num, my_name):
    """获取其他专家的观点"""
    all_thoughts = r.hgetall(f"debate:round:{round_num}")
    return {k.decode(): v.decode() for k, v in all_thoughts.items() if k.decode() != my_name}
```

### 主Agent端 (Python)
```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0)

# 订阅实时更新
pubsub = r.pubsub()
pubsub.subscribe("debate:updates")

def listen_updates():
    """监听实时更新"""
    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            update_panel(data)  # 更新Canvas/面板
            
def update_panel(data):
    """更新可视化面板"""
    agent = data['agent']
    round_num = data['round']
    status = data['status']
    
    # 获取最新内容
    content = r.hget(f"debate:round:{round_num}", agent)
    
    # 更新UI (Canvas/终端)
    print(f"[Round {round_num}] {agent}: {status}")
    # 或更新Canvas...
```

---

## 优势对比

| 特性 | 文件系统 | Redis |
|------|----------|-------|
| 延迟 | 5-10秒轮询 | **毫秒级** |
| 并发 | 可能冲突 | **原子操作** |
| 实时性 | 低 | **Pub/Sub实时推送** |
| 扩展性 | 单机 | **支持集群** |
| 可靠性 | 磁盘持久化 | **AOF/RDB持久化** |
| 复杂度 | 低 | 中等 |

---

## 部署步骤

1. **安装Redis**
```bash
apt-get install redis-server
systemctl enable redis
systemctl start redis
```

2. **Python依赖**
```bash
pip install redis
```

3. **配置**
```python
# config.py
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'decode_responses': True
}

# 每轮超时时间（秒）
ROUND_TIMEOUT = 120
```

4. **启动辩论**
```python
from debate import MultiAgentDebate

debate = MultiAgentDebate(
    topic="设计高性能Python Web API",
    agents=['harper', 'benjamin', 'lucas'],
    use_redis=True
)

result = debate.start()
```

---

## 监控命令

```bash
# 查看当前辩论状态
redis-cli HGETALL debate:round:2

# 查看实时更新流
redis-cli SUBSCRIBE debate:updates

# 查看进度
redis-cli KEYS debate:progress:*

# 清空辩论数据
redis-cli FLUSHDB
```

---

## 下一步实现

待办：
- [ ] 搭建Redis环境
- [ ] 编写redis_debate.py模块
- [ ] 集成到现有cron任务
- [ ] 性能测试（对比文件系统）

---

*方案设计: 2026-02-19 | 状态: 待实施*
