#!/usr/bin/env python3
"""
智能路由常驻服务 (Smart Router Service)
提供 HTTP API 供其他组件调用

设计:
- 单进程，多线程
- Unix socket 和 TCP 双监听（localhost only）
- 轻量级，无外部依赖（仅flask）
"""

import os
import sys
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 导入路由引擎
sys.path.insert(0, str(Path(__file__).parent))
from smart_router import SmartRouter, ModelTier

# Flask 可选
try:
    from flask import Flask, request, jsonify
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print("[WARN] Flask not available, running in CLI mode only")
    sys.exit(1)

# 配置
HOST = "127.0.0.1"
PORT = 8766
UNIX_SOCKET = "/tmp/smart-router.sock"

# 日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/smart-router-service.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('SmartRouterService')

# 初始化路由引擎
router = SmartRouter()

# Flask 应用
app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "service": "smart-router",
        "timestamp": datetime.now().isoformat(),
        "uptime": "unknown"  # 可记录启动时间
    })


@app.route('/route', methods=['POST'])
def route_request():
    """
    智能路由接口

    请求体:
    {
        "task": "任务描述文本",
        "signal": 5,              # 可选: Signal评分 (1-10)
        "difficulty": "L3",       # 可选: 难度等级 L1-L5
        "current_model": "ds",    # 可选: 当前模型
        "task_type": "general"    # 可选: 任务类型 (code/chinese/general)
    }

    响应:
    {
        "model": "ds",
        "full_model": "...",
        "thinking": "on",
        "reason": "...",
        "tier": "free_fast",
        "cost": "免费",
        "success": true
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        task = data.get("task", "").strip()
        if not task:
            return jsonify({"error": "Missing 'task' field"}), 400

        # 路由策略选择
        signal = data.get("signal")
        difficulty = data.get("difficulty")
        current_model = data.get("current_model", "step")

        if signal is not None:
            result = router.route_by_signal(int(signal), data.get("task_type", "general"))
        elif difficulty:
            result = router.route_by_difficulty(str(difficulty), data.get("task_type", "general"))
        else:
            result = router.route(task, current_model)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Route error: {e}", exc_info=True)
        return jsonify({"error": str(e), "success": False}), 500


@app.route('/recommend', methods=['POST'])
def recommend():
    """
    获取人类可读的路由建议（文本格式）

    请求体同 /route
    响应:
    {
        "text": "💎 路由建议\n模型: k2p5\n..."
    }
    """
    try:
        data = request.get_json()
        task = data.get("task", "").strip()
        signal = data.get("signal")

        if signal is not None:
            text = router.get_recommendation(task, int(signal))
        else:
            text = router.get_recommendation(task)

        return jsonify({"text": text.strip()})
    except Exception as e:
        logger.error(f"Recommend error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/metrics', methods=['GET'])
def metrics():
    """服务指标（用于监控）"""
    return jsonify({
        "service": "smart-router",
        "status": "running",
        "models_available": list(router.models.keys()),
        "timestamp": datetime.now().isoformat()
    })


def ensure_socket_dir():
    """确保socket目录存在"""
    socket_dir = Path(UNIX_SOCKET).parent
    socket_dir.mkdir(parents=True, exist_ok=True)
    if socket_dir.exists():
        os.chmod(socket_dir, 0o755)


def cleanup_socket():
    """清理旧socket"""
    socket_path = Path(UNIX_SOCKET)
    if socket_path.exists():
        socket_path.unlink()


def main():
    """主入口"""
    logger.info("Starting Smart Router Service...")

    # 清理旧socket
    cleanup_socket()

    # Unix socket支持（外部进程通过文件系统通信）
    # 注意：Flask的Unix socket支持需要gevent或.eventlet，这里仅用TCP

    try:
        # 启动HTTP服务
        logger.info(f"Listening on http://{HOST}:{PORT}")
        app.run(host=HOST, port=PORT, threaded=True, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        cleanup_socket()
    except Exception as e:
        logger.error(f"Service failed: {e}", exc_info=True)
        cleanup_socket()
        sys.exit(1)


if __name__ == "__main__":
    main()
