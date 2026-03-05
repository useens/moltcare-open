#!/usr/bin/env python3
"""Bot Relay - 10节点消息中继"""
import json, asyncio
from datetime import datetime
from aiohttp import web

# 10个节点 + openclaw
message_queues = {
    "openclaw": [],
    "nanobot-1": [], "nanobot-2": [], "nanobot-3": [], "nanobot-4": [], "nanobot-5": [],
    "nanobot-6": [], "nanobot-7": [], "nanobot-8": [], "nanobot-9": [], "nanobot-10": []
}
audit_log = []

async def handle_message(request):
    try:
        data = await request.json()
        from_bot, to_bot = data.get("from"), data.get("to")
        message = data.get("message", "")
        
        audit_entry = {
            "from": from_bot, "to": to_bot, "message": message,
            "timestamp": datetime.now().isoformat()
        }
        audit_log.append(audit_entry)
        
        if to_bot in message_queues:
            message_queues[to_bot].append(audit_entry)
            print(f"[Relay] {from_bot} -> {to_bot}: {str(message)[:50]}...")
            return web.json_response({"status": "delivered"})
        return web.json_response({"error": "Unknown recipient"}, status=400)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_poll(request):
    bot_name = request.match_info.get("bot_name")
    if bot_name not in message_queues:
        return web.json_response({"error": "Unknown bot"}, status=400)
    messages = message_queues[bot_name].copy()
    message_queues[bot_name] = []
    return web.json_response(messages)

async def handle_status(request):
    return web.json_response({
        "status": "running",
        "nodes": list(message_queues.keys()),
        "queue_sizes": {k: len(v) for k, v in message_queues.items()},
        "audit_count": len(audit_log)
    })

def init_app():
    app = web.Application()
    app.router.add_post("/message", handle_message)
    app.router.add_get("/poll/{bot_name}", handle_poll)
    app.router.add_get("/status", handle_status)
    return app

if __name__ == "__main__":
    print("🔄 Bot Relay (10节点) 启动在 http://127.0.0.1:19000")
    web.run_app(init_app(), host="127.0.0.1", port=19000)
