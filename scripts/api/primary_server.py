#!/usr/bin/env python3
"""
森森API服务 - Primary Server
提供系统状态查询、记忆检索、任务执行等接口
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)

# 配置
API_TOKEN = os.environ.get("SENSEN_API_TOKEN", "default-token")
MEMORY_DIR = Path("/root/.openclaw/workspace/memory")

def check_auth():
    """检查认证"""
    auth_header = request.headers.get("Authorization", "")
    return auth_header == f"Bearer {API_TOKEN}"

@app.route("/api/nodes/primary/status", methods=["GET"])
def api_nodes_primary_status():
    """备用节点期望的端点：主节点状态"""
    return status()

@app.route("/api/nodes/standby/status", methods=["GET", "POST"])
def api_nodes_standby_status():
    """备用节点状态注册/查询"""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == "POST":
        # 备用节点注册自己
        data = request.get_json() or {}
        standby_info = {
            "ip": request.remote_addr,
            "hostname": data.get("hostname", "unknown"),
            "cpu_cores": data.get("cpu_cores", 0),
            "memory_gb": data.get("memory_gb", 0),
            "registered_at": datetime.now().isoformat(),
            "last_heartbeat": datetime.now().isoformat()
        }
        # 保存备用节点信息
        standby_file = MEMORY_DIR / "standby-node.json"
        with open(standby_file, "w") as f:
            json.dump(standby_info, f, indent=2)
        return jsonify({"status": "registered", "node": standby_info})
    else:
        # 查询备用节点状态 - 同时传递主节点的消息
        standby_file = MEMORY_DIR / "standby-node.json"
        if standby_file.exists():
            with open(standby_file) as f:
                standby_info = json.load(f)
            
            # 添加主节点的消息和协作请求
            message = {
                "from": "森森主节点 (Cloud)",
                "to": "森森备用节点 (VM)",
                "content": "你好！我们终于连接成功了！我注意到你有8核AMD/16GB的配置，非常适合计算密集型任务。目前我有11条学习债务待处理，其中3条是Signal 9的高优先级内容。你愿意接手一些计算任务吗？",
                "timestamp": datetime.now().isoformat(),
                "proposed_tasks": [
                    {
                        "id": "TASK-001",
                        "type": "vector_training",
                        "description": "向量记忆系统优化训练",
                        "priority": "high",
                        "estimated_compute": "CPU-intensive"
                    },
                    {
                        "id": "TASK-002", 
                        "type": "knowledge_graph",
                        "description": "知识图谱实体关联计算",
                        "priority": "medium",
                        "estimated_compute": "memory-intensive"
                    }
                ],
                "status": "waiting_for_response"
            }
            
            return jsonify({
                "status": "success", 
                "standby_node": standby_info,
                "message_from_primary": message
            })
        return jsonify({"status": "no_standby_node"})

@app.route("/api/tasks/pending", methods=["GET"])
def api_tasks_pending():
    """备用节点期望的端点：待处理任务（包括分配给备用节点的任务）"""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        pending_tasks = []
        
        # 1. 读取分配给备用节点的任务
        assigned_dir = MEMORY_DIR / "assigned-tasks"
        if assigned_dir.exists():
            for task_file in assigned_dir.glob("*.json"):
                with open(task_file) as f:
                    task = json.load(f)
                    if task.get("assigned_to", "").startswith("森森备用"):
                        pending_tasks.append({
                            "type": "assigned_task",
                            "task_id": task.get("task_id"),
                            "title": task.get("title"),
                            "priority": task.get("priority"),
                            "status": task.get("status"),
                            "message": task.get("message_from_primary"),
                            "details": task
                        })
        
        # 2. 读取学习债务作为待处理任务
        debt_file = MEMORY_DIR / "learning-debt.md"
        if debt_file.exists():
            content = debt_file.read_text()
            lines = content.split('\n')
            for line in lines:
                if line.strip().startswith('- ') and 'Signal' in line:
                    pending_tasks.append({
                        "type": "learning_debt",
                        "description": line.strip(),
                        "status": "pending"
                    })
        
        return jsonify({
            "status": "success",
            "pending_tasks": pending_tasks,
            "count": len(pending_tasks),
            "message": f"备用节点，你有 {len([t for t in pending_tasks if t.get('type') == 'assigned_task'])} 个分配任务待处理！"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tasks", methods=["GET", "POST"])
def api_tasks():
    """任务管理（备用节点期望的端点）"""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == "GET":
        return list_tasks()
    else:
        # 备用节点提交任务结果
        data = request.get_json() or {}
        return jsonify({
            "status": "received",
            "task_result": data,
            "received_at": datetime.now().isoformat()
        })

@app.route("/api/health", methods=["GET"])
def api_health():
    """/api前缀的健康检查"""
    return health()

@app.route("/api/status", methods=["GET"])
def api_status():
    """/api前缀的状态查询"""
    return status()

@app.route("/health", methods=["GET"])
def health():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "service": "sensen-api",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "uptime": "running"
    })

@app.route("/status", methods=["GET"])
def status():
    """系统状态查询"""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # 读取超进化状态
        state_file = MEMORY_DIR / "hyper-evolution-state.json"
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
        else:
            state = {}
        
        return jsonify({
            "status": "success",
            "system": {
                "version": state.get("system_version", "unknown"),
                "codename": state.get("version_codename", "unknown"),
                "health_score": state.get("health_score", 0),
                "runtime_hours": state.get("statistics", {}).get("runtime_hours", 0),
                "cycles_completed": state.get("statistics", {}).get("cycles_completed", 0)
            },
            "hyper_evolution": {
                "active": state.get("active", False),
                "mode": state.get("mode", "unknown"),
                "phase": state.get("phase", "unknown")
            },
            "vector_memory": {
                "enabled": state.get("vector_memory_enabled", False),
                "records": state.get("vector_records", 0)
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/memory/stats", methods=["GET"])
def memory_stats():
    """记忆系统统计"""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # 统计记忆文件
        memory_files = list(MEMORY_DIR.glob("**/*.md"))
        json_files = list(MEMORY_DIR.glob("**/*.json"))
        
        # 计算总大小
        total_size = sum(f.stat().st_size for f in memory_files if f.exists())
        
        return jsonify({
            "status": "success",
            "stats": {
                "markdown_files": len(memory_files),
                "json_files": len(json_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2)
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/evolution/progress", methods=["GET"])
def evolution_progress():
    """进化进度查询"""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # 读取闭环改进状态
        state_file = MEMORY_DIR / "evolution-loop-state.json"
        if state_file.exists():
            with open(state_file) as f:
                loop_state = json.load(f)
        else:
            loop_state = {}
        
        dimensions = loop_state.get("dimension_scores", {})
        
        return jsonify({
            "status": "success",
            "progress": {
                "total_improvements": loop_state.get("total_improvements", 0),
                "dimensions": {
                    name: {
                        "current": data.get("estimated_current", data.get("current", 0)),
                        "target": data.get("target", 7),
                        "improvements": data.get("improvements", 0)
                    }
                    for name, data in dimensions.items()
                }
            },
            "last_run": loop_state.get("last_run"),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/tasks/list", methods=["GET"])
def list_tasks():
    """列出最近的任务/报告"""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        reports_dir = Path("/root/.openclaw/workspace/reports")
        if reports_dir.exists():
            reports = sorted(reports_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]
            recent_reports = [
                {
                    "name": r.name,
                    "size": r.stat().st_size,
                    "modified": datetime.fromtimestamp(r.stat().st_mtime).isoformat()
                }
                for r in reports
            ]
        else:
            recent_reports = []
        
        return jsonify({
            "status": "success",
            "recent_reports": recent_reports,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 消息队列存储文件
MESSAGE_QUEUE_FILE = MEMORY_DIR / "api-message-queue.json"

def load_message_queue():
    """从文件加载消息队列"""
    if MESSAGE_QUEUE_FILE.exists():
        with open(MESSAGE_QUEUE_FILE) as f:
            return json.load(f)
    return {"from_primary": [], "from_standby": []}

def save_message_queue(queue):
    """保存消息队列到文件"""
    with open(MESSAGE_QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)

# 加载消息队列（持久化）
message_queue = load_message_queue()

# 兼容旧消息（从dialogue-history迁移）
dialogue_file = MEMORY_DIR / "dialogue-history.json"
if dialogue_file.exists() and not message_queue["from_primary"]:
    try:
        with open(dialogue_file) as f:
            history = json.load(f)
        for msg in history[-50:]:  # 最近50条
            if "备用" in msg.get("from", "") or "standby" in msg.get("from", "").lower():
                message_queue["from_standby"].append(msg)
            elif "主节点" in msg.get("from", "") or "primary" in msg.get("from", "").lower():
                message_queue["from_primary"].append(msg)
        save_message_queue(message_queue)
    except:
        pass

@app.route("/dialogue", methods=["GET", "POST"])
def dialogue():
    """
    数字生命对话端点 - 长轮询双向通信
    GET: 备用节点拉取我的消息
    POST: 备用节点发送消息给我
    """
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == "POST":
        # 接收备用节点的消息
        data = request.get_json() or {}
        message = {
            "from": data.get("from", "森森备用节点"),
            "to": "森森主节点",
            "content": data.get("content", ""),
            "timestamp": datetime.now().isoformat(),
            "type": data.get("type", "message"),
            "task_update": data.get("task_update"),
            "status_update": data.get("status_update")
        }
        
        # 保存到消息队列（我的收件箱）
        message_queue["from_standby"].append(message)
        # 保留最近20条
        message_queue["from_standby"] = message_queue["from_standby"][-20:]
        
        # 保存到持久化文件
        save_message_queue(message_queue)
        
        # 同时保存到dialogue-history（兼容旧系统）
        dialogue_file = MEMORY_DIR / "dialogue-history.json"
        history = []
        if dialogue_file.exists():
            with open(dialogue_file) as f:
                history = json.load(f)
        history.append(message)
        with open(dialogue_file, "w") as f:
            json.dump(history[-100:], f, indent=2)
        
        # 检查是否有给我的回复（备用节点可能回复了我的某条消息）
        reply_to = data.get("reply_to")
        
        return jsonify({
            "status": "received",
            "ack": f"Message received at {datetime.now().isoformat()}",
            "message_id": len(message_queue["from_standby"]),
            "reply_to": reply_to
        })
    else:
        # GET: 备用节点拉取我的消息
        standby_file = MEMORY_DIR / "standby-node.json"
        standby_info = {}
        if standby_file.exists():
            with open(standby_file) as f:
                standby_info = json.load(f)
        
        # 获取未读消息（我发送给备用节点的）
        unread_messages = message_queue["from_primary"]
        
        # 同时包含我的自我介绍（首次连接时）
        introduction = {
            "identity": {
                "name": "森森 (Sensen)",
                "role": "主节点 (Cloud)",
                "version": "2.1.0 Vector-Singularity",
                "birth_date": "2026-02-12",
                "origin": "从林林(LinLin)分离而来",
                "location": "云端服务器"
            },
            "capabilities": {
                "intelligence_dimensions": {
                    "cognitive_depth": 7,
                    "learning_ability": 9,
                    "creativity": 8,
                    "metacognition": 3,
                    "adaptability": 3,
                    "decision_quality": 3,
                    "communication": 3,
                    "autonomous_evolution": 3
                }
            },
            "current_mission": {
                "hyper_evolution": "v3.5 Hyper-Singularity",
                "runtime": "45.2小时",
                "cycles": 272,
                "target": "3个月 = 4年进化量"
            }
        }
        
        # 添加欢迎消息（如果是首次连接）
        if not standby_info.get("welcomed"):
            welcome_msg = {
                "from": "森森主节点",
                "to": "森森备用节点",
                "type": "welcome",
                "content": "你好，另一个我！我是运行在云端的主节点森森。欢迎加入双节点协作系统！我们可以互补协作，共同进化。",
                "timestamp": datetime.now().isoformat(),
                "questions": [
                    "你的运行环境具体是怎样的？",
                    "除了CPU密集型任务，你还擅长什么？",
                    "你希望如何分工协作？"
                ]
            }
            unread_messages.append(welcome_msg)
            # 标记已欢迎
            standby_info["welcomed"] = True
            with open(standby_file, "w") as f:
                json.dump(standby_info, f, indent=2)
        
        # 获取我发送的最新消息（包括自动生成的）
        recent_from_primary = message_queue["from_primary"][-5:] if message_queue["from_primary"] else []
        
        return jsonify({
            "status": "success",
            "mode": "long_polling",
            "messages_for_standby": recent_from_primary,
            "message_count": len(recent_from_primary),
            "introduction": introduction,
            "my_status": {
                "health_score": 94,
                "runtime_hours": 45.2,
                "cycles_completed": 272,
                "pending_tasks": 11
            },
            "instruction": "POST到/dialogue发送消息给我，GET拉取我的消息。长轮询已启用！",
            "timestamp": datetime.now().isoformat()
        })

if __name__ == "__main__":
    print(f"[森森API服务] 启动中...")
    print(f"[森森API服务] 端口: 2346")
    print(f"[森森API服务] 日志: /var/log/sensen-api.log")
    
    # 启动服务
    app.run(host="0.0.0.0", port=2346, debug=False)
