"""
Multi-Agent Canvas - Phase 2 实时可视化服务器
使用 Flask + Server-Sent Events (SSE) 实现实时推送
"""
from flask import Flask, render_template_string, jsonify
import redis
import json
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Redis连接
redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)

# HTML模板
CANVAS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔮 Multi-Agent Real-time Discussion Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #e6edf3;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: #161b22;
            border-bottom: 1px solid #30363d;
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 18px; color: #58a6ff; }
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
        .main-panel {
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            padding: 12px;
        }
        .agent-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            min-height: 300px;
        }
        .agent-card.active { border-color: #58a6ff; }
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
            display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 14px;
        }
        .grok { background: #58a6ff; color: #0d1117; }
        .harper { background: #a371f7; color: #0d1117; }
        .benjamin { background: #3fb950; color: #0d1117; }
        .lucas { background: #d29922; color: #0d1117; }
        .agent-info h3 { font-size: 14px; margin-bottom: 2px; }
        .agent-info .role { font-size: 11px; color: #8b949e; }
        .agent-status {
            margin-left: auto;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 12px;
            background: #21262d;
        }
        .status-thinking { background: #9e6a03; color: #fff; }
        .status-complete { background: #238636; color: #fff; }
        .status-debating { background: #1f6feb; color: #fff; }
        .agent-content {
            flex: 1;
            overflow-y: auto;
            font-size: 12px;
            line-height: 1.6;
            color: #c9d1d9;
            white-space: pre-wrap;
            max-height: 200px;
        }
        .round-section {
            margin-bottom: 8px;
            padding: 8px;
            background: rgba(48, 54, 61, 0.5);
            border-radius: 6px;
            border-left: 3px solid #58a6ff;
        }
        .round-title {
            font-weight: 600;
            color: #58a6ff;
            margin-bottom: 4px;
            font-size: 11px;
        }
        .stats-bar {
            background: #161b22;
            border-top: 1px solid #30363d;
            padding: 12px 20px;
            font-size: 12px;
            display: flex;
            gap: 24px;
        }
        .stat-item { display: flex; gap: 6px; }
        .stat-label { color: #8b949e; }
        .stat-value { color: #e6edf3; font-weight: 600; }
        .message-stream {
            height: 150px;
            background: #0d1117;
            border-top: 1px solid #30363d;
            padding: 10px 20px;
            overflow-y: auto;
            font-size: 11px;
        }
        .message-item {
            padding: 4px 0;
            border-bottom: 1px solid #21262d;
            display: flex;
            gap: 8px;
        }
        .message-time { color: #6e7681; min-width: 70px; }
        .message-agent { color: #58a6ff; min-width: 80px; }
        .message-content { color: #c9d1d9; }
        .typing::after {
            content: '▋';
            animation: blink 1s infinite;
        }
        @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }
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
    
    <div class="main-panel">
        <div class="agent-card" id="card-grok">
            <div class="agent-header">
                <div class="agent-avatar grok">G</div>
                <div class="agent-info">
                    <h3>Grok</h3>
                    <div class="role">队长 · 整合裁决</div>
                </div>
                <div class="agent-status" id="status-grok">等待中</div>
            </div>
            <div class="agent-content" id="content-grok">
                <div class="round-section">
                    <div class="round-title">系统就绪</div>
                    等待专家输入...
                </div>
            </div>
        </div>
        
        <div class="agent-card" id="card-harper">
            <div class="agent-header">
                <div class="agent-avatar harper">H</div>
                <div class="agent-info">
                    <h3>Harper</h3>
                    <div class="role">研究 · 验证专家</div>
                </div>
                <div class="agent-status" id="status-harper">等待中</div>
            </div>
            <div class="agent-content" id="content-harper">
                <div class="round-section">
                    <div class="round-title">等待开始</div>
                    等待辩论开始...
                </div>
            </div>
        </div>
        
        <div class="agent-card" id="card-benjamin">
            <div class="agent-header">
                <div class="agent-avatar benjamin">B</div>
                <div class="agent-info">
                    <h3>Benjamin</h3>
                    <div class="role">架构 · 逻辑专家</div>
                </div>
                <div class="agent-status" id="status-benjamin">等待中</div>
            </div>
            <div class="agent-content" id="content-benjamin">
                <div class="round-section">
                    <div class="round-title">等待开始</div>
                    等待辩论开始...
                </div>
            </div>
        </div>
        
        <div class="agent-card" id="card-lucas">
            <div class="agent-header">
                <div class="agent-avatar lucas">L</div>
                <div class="agent-info">
                    <h3>Lucas</h3>
                    <div class="role">工具 · 执行专家</div>
                </div>
                <div class="agent-status" id="status-lucas">等待中</div>
            </div>
            <div class="agent-content" id="content-lucas">
                <div class="round-section">
                    <div class="round-title">等待开始</div>
                    等待辩论开始...
                </div>
            </div>
        </div>
    </div>
    
    <div class="stats-bar">
        <div class="stat-item">
            <span class="stat-label">辩论ID:</span>
            <span class="stat-value" id="debate-id">-</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">当前轮次:</span>
            <span class="stat-value" id="current-round">-</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">完成进度:</span>
            <span class="stat-value" id="progress">-</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">运行时间:</span>
            <span class="stat-value" id="elapsed">00:00</span>
        </div>
    </div>
    
    <div class="message-stream" id="message-stream">
        <div class="message-item">
            <span class="message-time">--:--:--</span>
            <span class="message-agent">System</span>
            <span class="message-content">Canvas面板已启动，等待辩论开始...</span>
        </div>
    </div>

    <script>
        const debateId = new URLSearchParams(window.location.search).get('debate') || 'demo';
        let startTime = Date.now();
        let messageCount = 0;
        
        // 更新统计
        function updateStats() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const mins = Math.floor(elapsed / 60).toString().padStart(2, '0');
            const secs = (elapsed % 60).toString().padStart(2, '0');
            document.getElementById('elapsed').textContent = `${mins}:${secs}`;
        }
        setInterval(updateStats, 1000);
        
        // 添加消息
        function addMessage(agent, content, type='info') {
            const now = new Date();
            const time = now.toTimeString().slice(0, 8);
            const stream = document.getElementById('message-stream');
            const item = document.createElement('div');
            item.className = 'message-item';
            
            const agentColors = {
                'Harper': '#a371f7',
                'Benjamin': '#3fb950',
                'Lucas': '#d29922',
                'Grok': '#58a6ff',
                'System': '#8b949e'
            };
            
            item.innerHTML = `
                <span class="message-time">${time}</span>
                <span class="message-agent" style="color: ${agentColors[agent] || '#8b949e'}">${agent}</span>
                <span class="message-content">${content}</span>
            `;
            stream.insertBefore(item, stream.firstChild);
            messageCount++;
        }
        
        // 更新专家状态
        function updateAgent(agent, data) {
            const statusEl = document.getElementById(`status-${agent}`);
            const contentEl = document.getElementById(`content-${agent}`);
            const cardEl = document.getElementById(`card-${agent}`);
            
            if (data.status) {
                statusEl.textContent = data.status;
                statusEl.className = 'agent-status';
                if (data.status.includes('思考')) statusEl.classList.add('status-thinking');
                if (data.status.includes('完成')) statusEl.classList.add('status-complete');
                if (data.status.includes('回应')) statusEl.classList.add('status-debating');
            }
            
            if (data.content) {
                const roundNum = data.round || 1;
                contentEl.innerHTML += `
                    <div class="round-section">
                        <div class="round-title">Round ${roundNum}</div>
                        ${data.content}
                    </div>
                `;
            }
            
            // 高亮活跃卡片
            if (data.active) {
                cardEl.classList.add('active');
                setTimeout(() => cardEl.classList.remove('active'), 1000);
            }
        }
        
        // 长轮询获取更新
        async function pollUpdates() {
            try {
                const response = await fetch(`/api/updates/${debateId}?last=${messageCount}`);
                const data = await response.json();
                
                document.getElementById('debate-id').textContent = debateId;
                document.getElementById('current-round').textContent = data.round || '-';
                document.getElementById('progress').textContent = 
                    `${data.completed || 0}/${data.total || 3}`;
                
                // 处理更新
                data.updates.forEach(update => {
                    if (update.agent) {
                        updateAgent(update.agent.toLowerCase(), update);
                        addMessage(update.agent, update.message || update.status, update.type);
                    }
                });
                
            } catch (err) {
                console.error('Poll error:', err);
            }
            
            setTimeout(pollUpdates, 500); // 500ms轮询
        }
        
        // 开始轮询
        pollUpdates();
        addMessage('System', 'Canvas面板已连接，开始接收实时更新...', 'system');
    </script>
</body>
</html>
'''

# 存储更新历史
updates_history = {}

def get_updates(debate_id, last_count=0):
    """获取更新"""
    key = f"debate:{debate_id}:updates:history"
    updates = redis_client.lrange(key, last_count, -1)
    return [json.loads(u) for u in updates] if updates else []

@app.route('/')
def index():
    """主页"""
    return render_template_string(CANVAS_TEMPLATE)

@app.route('/api/updates/<debate_id>')
def api_updates(debate_id):
    """API: 获取更新"""
    last = int(request.args.get('last', 0))
    
    # 获取状态
    status = redis_client.get(f"debate:{debate_id}:status") or 'unknown'
    progress = redis_client.keys(f"debate:{debate_id}:progress:*")
    
    # 获取更新
    updates = get_updates(debate_id, last)
    
    return jsonify({
        'status': status,
        'round': redis_client.hget(f"debate:{debate_id}:meta", "current_round"),
        'completed': len(progress),
        'total': 3,
        'updates': updates
    })

@app.route('/api/stats/<debate_id>')
def api_stats(debate_id):
    """API: 获取统计"""
    thoughts_r1 = redis_client.hgetall(f"debate:{debate_id}:round:1")
    thoughts_r2 = redis_client.hgetall(f"debate:{debate_id}:round:2")
    thoughts_r3 = redis_client.hgetall(f"debate:{debate_id}:round:3")
    
    return jsonify({
        'round1': thoughts_r1,
        'round2': thoughts_r2,
        'round3': thoughts_r3,
        'progress': redis_client.keys(f"debate:{debate_id}:progress:*")
    })

def store_update(debate_id, update_data):
    """存储更新到历史"""
    key = f"debate:{debate_id}:updates:history"
    redis_client.rpush(key, json.dumps(update_data))
    redis_client.expire(key, 3600)  # 1小时过期

if __name__ == '__main__':
    print("🚀 Canvas服务器启动中...")
    print("📍 访问地址: http://localhost:5000")
    print("\n🔧 功能:")
    print("   - 实时展示4个专家状态")
    print("   - 500ms轮询更新")
    print("   - 消息流显示")
    print("\n⚠️  按 Ctrl+C 停止服务器\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
