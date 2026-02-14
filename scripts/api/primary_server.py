#!/usr/bin/env python3
# 主节点API服务端 v1.0
# 部署在主节点(云端)，提供公网API服务

from flask import Flask, request, jsonify
from functools import wraps
import threading
import time
import os
from typing import Dict, List
import psutil

app = Flask(__name__)

# 内存存储（生产环境建议使用Redis）
task_queue: Dict[str, Dict] = {}
task_results: Dict[str, Dict] = {}
node_status: Dict[str, Dict] = {}

# 从环境变量读取API Token
API_TOKEN = os.environ.get('SENSEN_API_TOKEN', 'default-token-change-in-production')
PRIMARY_NODE_ID = os.environ.get('NODE_ID', 'primary-001')

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
    priority_map = {'high': 3, 'normal': 2, 'low': 1}
    pending.sort(key=lambda x: priority_map.get(x.get('priority', 'normal'), 0), reverse=True)
    return jsonify({"tasks": pending[:10]})

@app.route('/api/tasks', methods=['POST'])
@require_auth
def create_task():
    """创建新任务（主节点调用）"""
    data = request.json
    task_id = f"task-{int(time.time() * 1000)}-{data.get('type', 'generic')}"
    
    task = {
        "id": task_id,
        "type": data.get('type', 'generic'),
        "priority": data.get('priority', 'normal'),
        "payload": data.get('payload', {}),
        "status": "pending",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "created_by": "primary"
    }
    
    task_queue[task_id] = task
    print(f"[TASK CREATED] {task_id} - {task['type']}")
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
    task['claimed_by'] = data.get('node_id', 'unknown')
    task['claimed_at'] = data.get('claimed_at', time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    
    print(f"[TASK CLAIMED] {task_id} by {task['claimed_by']}")
    return jsonify({"status": "claimed", "task": task})

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
    task['completed_at'] = data.get('completed_at', time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    
    # 移动到结果存储
    task_results[task_id] = task
    del task_queue[task_id]
    
    print(f"[TASK COMPLETED] {task_id} - status: {task['status']}")
    return jsonify({"status": "completed"})

@app.route('/api/tasks/<task_id>', methods=['GET'])
@require_auth
def get_task(task_id):
    """获取任务详情"""
    if task_id in task_queue:
        return jsonify(task_queue[task_id])
    elif task_id in task_results:
        return jsonify(task_results[task_id])
    else:
        return jsonify({"error": "Task not found"}), 404

# ========== 状态管理API ==========

@app.route('/api/nodes/status', methods=['POST'])
@require_auth
def update_node_status():
    """备用节点上报状态"""
    data = request.json
    node_id = data.get('node_id')
    if node_id:
        node_status[node_id] = {
            **data,
            "last_seen": time.time()
        }
    return jsonify({"status": "received"})

@app.route('/api/nodes/standby/status', methods=['GET'])
@require_auth
def get_standby_status():
    """获取备用节点状态"""
    # 过滤掉超过5分钟没有心跳的节点
    current_time = time.time()
    active_nodes = {
        node_id: status for node_id, status in node_status.items()
        if current_time - status.get('last_seen', 0) < 300
    }
    return jsonify({"nodes": active_nodes})

@app.route('/api/nodes/primary/status', methods=['GET'])
@require_auth
def get_primary_status():
    """获取主节点状态"""
    return jsonify({
        "node_id": PRIMARY_NODE_ID,
        "role": "PRIMARY",
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "active_tasks": len([t for t in task_queue.values() if t.get('status') == 'processing']),
        "pending_tasks": len([t for t in task_queue.values() if t.get('status') == 'pending']),
        "completed_tasks": len(task_results),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    })

# ========== 管理API ==========

@app.route('/api/tasks/list', methods=['GET'])
@require_auth
def list_all_tasks():
    """列出所有任务（调试使用）"""
    return jsonify({
        "pending": list(task_queue.values()),
        "completed": list(task_results.values())[-10:]  # 最近10个完成
    })

@app.route('/api/tasks/cleanup', methods=['POST'])
@require_auth
def cleanup_tasks():
    """清理旧任务"""
    # 清理超过24小时的已完成任务
    current_time = time.time()
    to_remove = []
    for task_id, task in task_results.items():
        completed_at = task.get('completed_at', '')
        if completed_at:
            try:
                completed_timestamp = time.mktime(time.strptime(completed_at, "%Y-%m-%dT%H:%M:%SZ"))
                if current_time - completed_timestamp > 86400:  # 24小时
                    to_remove.append(task_id)
            except:
                pass
    
    for task_id in to_remove:
        del task_results[task_id]
    
    return jsonify({"cleaned": len(to_remove)})

# 健康检查
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "time": time.time(),
        "node_id": PRIMARY_NODE_ID,
        "role": "PRIMARY"
    })

# 根路径
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "service": "Sensen Primary Node API",
        "version": "1.0",
        "role": "PRIMARY",
        "endpoints": [
            "/health",
            "/api/tasks/pending",
            "/api/tasks",
            "/api/nodes/status"
        ]
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🌲 Sensen Primary Node API Server v1.0")
    print("=" * 50)
    print(f"Node ID: {PRIMARY_NODE_ID}")
    print(f"API Token: {API_TOKEN[:10]}...")
    print("Listening on 0.0.0.0:2346")
    print("=" * 50)
    
    # 开发环境使用Flask内置服务器
    # 生产环境应使用: gunicorn -w 4 -b 0.0.0.0:2346 primary_server:app
    app.run(host='0.0.0.0', port=2346, threaded=True, debug=False)
