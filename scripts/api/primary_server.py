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

if __name__ == "__main__":
    print(f"[森森API服务] 启动中...")
    print(f"[森森API服务] 端口: 2346")
    print(f"[森森API服务] 日志: /var/log/sensen-api.log")
    
    # 启动服务
    app.run(host="0.0.0.0", port=2346, debug=False)
