# Multi-Agent Canvas 实时可视化方案

## 目标

创建类似 Grok 4.20 右侧思考面板的实时可视化界面，展示：
- 4个专家的实时状态
- 每轮讨论的内容
- 专家之间的质疑和回应
- 最终共识形成过程

---

## 设计稿

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔮 Multi-Agent Real-time Discussion Panel              [Live]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │ 👑 Grok (队长)    │    │ 🔍 Harper         │                  │
│  │ Status: 裁决中    │    │ Status: ✅ Round 3│                  │
│  │                  │    │                  │                  │
│  │ 等待专家输入...   │    │ 【Round 1】       │                  │
│  │                  │    │ FastAPI性能...    │                  │
│  │                  │    │ 【Round 2】       │                  │
│  │                  │    │ @Benjamin: 质疑...│                  │
│  │                  │    │ 【Round 3】       │                  │
│  │                  │    │ 最终立场: ...     │                  │
│  └──────────────────┘    └──────────────────┘                  │
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │ 🧠 Benjamin       │    │ 💻 Lucas          │                  │
│  │ Status: 🔄 Round 2│    │ Status: 🔄 Round 2│                  │
│  │                  │    │                  │                  │
│  │ 【Round 1】       │    │ 【Round 1】       │                  │
│  │ 分层架构设计...   │    │ 实现规划...       │                  │
│  │                  │    │                  │                  │
│  │ 正在回应质疑...   │    │ 正在质疑中...     │                  │
│  │                  │    │                  │                  │
│  └──────────────────┘    └──────────────────┘                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 📊 辩论统计                                                      │
│ Round: 2/3  |  完成: 1/3  |  进行中: 2/3  |  已耗时: 3m 20s     │
├─────────────────────────────────────────────────────────────────┤
│ 💬 实时消息流                                                    │
│ [09:24:15] Harper质疑Benjamin: "分层是否过度设计?"             │
│ [09:24:23] Benjamin回应: "数据支持分层架构..."                  │
│ [09:24:31] Lucas质疑Harper: "工期评估过于乐观..."               │
│ ...                                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 技术方案

### 方案A: 文件系统 + Canvas (当前可行)
```python
# canvas_updater.py
import time
import json
from pathlib import Path

def update_canvas_from_files():
    """从文件系统读取并更新Canvas"""
    while True:
        # 读取所有专家的最新状态
        for agent in ['harper', 'benjamin', 'lucas']:
            for round_num in [1, 2, 3]:
                file_path = f"experiments/multi-agent-debate/shared/round-{round_num}/{agent}.md"
                if Path(file_path).exists():
                    content = read_file(file_path)
                    update_canvas_panel(agent, round_num, content)
        
        time.sleep(2)  # 每2秒刷新一次
```

### 方案B: Redis + Canvas (推荐)
```python
# canvas_redis.py
import redis
import json

r = redis.Redis()
pubsub = r.pubsub()
pubsub.subscribe("debate:updates")

def realtime_canvas_update():
    """Redis实时推送更新Canvas"""
    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            # 实时更新Canvas
            update_agent_panel(
                agent=data['agent'],
                round_num=data['round'],
                content=get_content_from_redis(data['round'], data['agent'])
            )
```

### 方案C: WebSocket + Web Canvas (长期)
```
OpenClaw Agent
    ↓ WebSocket
Node.js Server
    ↓ Broadcast
Browser Canvas (React/Vue)
```

---

## Canvas HTML 模板

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Multi-Agent Discussion Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0d1117;
            color: #e6edf3;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        /* 头部 */
        .header {
            background: #161b22;
            border-bottom: 1px solid #30363d;
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 16px; color: #58a6ff; }
        .live-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #3fb950;
            font-size: 12px;
        }
        .live-dot {
            width: 8px; height: 8px;
            background: #3fb950;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        
        /* 主面板 */
        .main-panel {
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            padding: 12px;
            overflow: hidden;
        }
        
        /* 专家卡片 */
        .agent-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .agent-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid #30363d;
        }
        .agent-avatar {
            width: 32px; height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
        }
        .grok { background: #58a6ff; color: #0d1117; }
        .harper { background: #a371f7; color: #0d1117; }
        .benjamin { background: #3fb950; color: #0d1117; }
        .lucas { background: #d29922; color: #0d1117; }
        
        .agent-info h3 { font-size: 13px; margin-bottom: 2px; }
        .agent-info .role { font-size: 11px; color: #8b949e; }
        .agent-status {
            margin-left: auto;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 12px;
        }
        .status-complete { background: #238636; }
        .status-debating { background: #9e6a03; }
        .status-waiting { background: #6e7681; }
        
        /* 内容区 */
        .agent-content {
            flex: 1;
            overflow-y: auto;
            font-size: 12px;
            line-height: 1.6;
            color: #c9d1d9;
        }
        .round-section {
            margin-bottom: 12px;
            padding: 8px;
            background: rgba(48, 54, 61, 0.5);
            border-radius: 6px;
        }
        .round-title {
            font-weight: 600;
            color: #58a6ff;
            margin-bottom: 6px;
        }
        
        /* 底部统计 */
        .stats-bar {
            background: #161b22;
            border-top: 1px solid #30363d;
            padding: 10px 20px;
            font-size: 12px;
            color: #8b949e;
            display: flex;
            gap: 24px;
        }
        .stat-item { display: flex; gap: 6px; }
        .stat-value { color: #e6edf3; font-weight: 600; }
        
        /* 消息流 */
        .message-stream {
            height: 120px;
            background: #0d1117;
            border-top: 1px solid #30363d;
            padding: 10px 20px;
            overflow-y: auto;
            font-size: 11px;
        }
        .message-item {
            padding: 4px 0;
            border-bottom: 1px solid #21262d;
        }
        .message-time { color: #6e7681; margin-right: 8px; }
        .message-agent { color: #58a6ff; margin-right: 6px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔮 Multi-Agent Real-time Discussion Panel</h1>
        <div class="live-indicator">
            <span>LIVE</span>
            <div class="live-dot"></div>
        </div>
    </div>
    
    <div class="main-panel" id="main-panel">
        <!-- 专家卡片将通过JS动态生成 -->
    </div>
    
    <div class="stats-bar">
        <div class="stat-item">
            <span>Round:</span>
            <span class="stat-value" id="current-round">2/3</span>
        </div>
        <div class="stat-item">
            <span>完成:</span>
            <span class="stat-value" id="completed">1/3</span>
        </div>
        <div class="stat-item">
            <span>已耗时:</span>
            <span class="stat-value" id="elapsed">3m 20s</span>
        </div>
    </div>
    
    <div class="message-stream" id="message-stream">
        <!-- 消息将通过JS动态添加 -->
    </div>

    <script>
        // 实时更新逻辑
        function updateAgentCard(agent, data) {
            // 更新或创建专家卡片
        }
        
        function addMessage(timestamp, agent, content) {
            const stream = document.getElementById('message-stream');
            const item = document.createElement('div');
            item.className = 'message-item';
            item.innerHTML = `
                <span class="message-time">[${timestamp}]</span>
                <span class="message-agent">${agent}:</span>
                <span>${content}</span>
            `;
            stream.insertBefore(item, stream.firstChild);
        }
        
        // 模拟实时更新
        setInterval(() => {
            // 从Redis或文件系统获取最新状态
            // updateAgentCard(...)
        }, 2000);
    </script>
</body>
</html>
```

---

## 集成方案

### 使用方式

```python
from openclaw import canvas
from multi_agent_debate import DebateMonitor

# 启动辩论
debate = MultiAgentDebate(topic="设计Web API")

# 启动Canvas面板
canvas.present(
    url="file:///skills/multi-agent-debate/canvas-panel.html",
    width=1200,
    height=800
)

# 启动实时监控
monitor = DebateMonitor(canvas_update_callback)
monitor.start()

# 开始辩论
result = debate.start()

# 关闭监控
monitor.stop()
```

---

## 待办清单

- [ ] 完善Canvas HTML模板
- [ ] 实现JavaScript实时更新逻辑
- [ ] 集成Redis读取
- [ ] 添加动画效果（打字机效果、状态切换）
- [ ] 测试Canvas与Agent的通信
- [ ] 优化移动端适配

---

*方案设计: 2026-02-19 | 状态: 原型阶段*
