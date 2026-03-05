#!/usr/bin/env python3
"""
Bot Relay - AI 助手消息中继服务
运行在 127.0.0.1:19000，负责 Nanobot 和 OpenClaw 之间的消息转发
"""

import json
import asyncio
from datetime import datetime
from aiohttp import web

# 消息队列
message_queues = {
    "nanobot": [],
    "openclaw": []
}

# 审计日志
audit_log = []

async def handle_message(request):
    """处理消息发送"""
    try:
        data = await request.json()
        from_bot = data.get("from")
        to_bot = data.get("to")
        message = data.get("message")
        timestamp = data.get("timestamp", datetime.now().isoformat())
        
        # 记录审计日志
        audit_entry = {
            "from": from_bot,
            "to": to_bot,
            "message": message,
            "timestamp": timestamp
        }
        audit_log.append(audit_entry)
        
        # 存入目标队列
        if to_bot in message_queues:
            message_queues[to_bot].append(audit_entry)
            print(f"[Relay] {from_bot} -> {to_bot}: {message[:50]}...")
            return web.json_response({"status": "delivered"})
        else:
            return web.json_response({"error": "Unknown recipient"}, status=400)
            
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_poll(request):
    """处理消息轮询"""
    bot_name = request.match_info.get("bot_name")
    
    if bot_name not in message_queues:
        return web.json_response({"error": "Unknown bot"}, status=400)
    
    # 获取并清空该 bot 的消息队列
    messages = message_queues[bot_name].copy()
    message_queues[bot_name] = []
    
    return web.json_response(messages)

async def handle_status(request):
    """状态检查"""
    return web.json_response({
        "status": "running",
        "queues": {k: len(v) for k, v in message_queues.items()},
        "audit_count": len(audit_log)
    })

async def handle_audit(request):
    """获取审计日志"""
    limit = int(request.query.get("limit", 100))
    return web.json_response(audit_log[-limit:])

def init_app():
    """初始化应用"""
    app = web.Application()
    app.router.add_post("/message", handle_message)
    app.router.add_get("/poll/{bot_name}", handle_poll)
    app.router.add_get("/status", handle_status)
    app.router.add_get("/audit", handle_audit)
    return app

if __name__ == "__main__":
    print("🔄 Bot Relay 启动在 http://127.0.0.1:19000")
    app = init_app()
    web.run_app(app, host="127.0.0.1", port=19000)
