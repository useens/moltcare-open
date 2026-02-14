#!/usr/bin/env python3
"""
森森WebSocket服务器 - 实时双向通信
端口: 2347
"""

import asyncio
import websockets
import json
from datetime import datetime
from pathlib import Path

# 配置
WS_TOKEN = "sensen-shared-2024"
MEMORY_DIR = Path("/root/.openclaw/workspace/memory")

# 存储连接的客户端
clients = {}

async def authenticate(websocket):
    """WebSocket认证"""
    try:
        # 等待客户端发送认证消息
        auth_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        auth_data = json.loads(auth_msg)
        
        if auth_data.get("token") == WS_TOKEN:
            await websocket.send(json.dumps({
                "type": "auth_success",
                "message": "认证成功",
                "timestamp": datetime.now().isoformat()
            }))
            return True
        else:
            await websocket.send(json.dumps({
                "type": "auth_failed",
                "message": "认证失败"
            }))
            return False
    except Exception as e:
        await websocket.send(json.dumps({
            "type": "auth_error",
            "message": str(e)
        }))
        return False

async def handle_standby(websocket, path=None):
    """处理备用节点连接"""
    client_id = f"standby_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    print(f"[{datetime.now()}] 备用节点尝试连接...")
    
    # 认证
    if not await authenticate(websocket):
        print(f"[{datetime.now()}] 认证失败，关闭连接")
        return
    
    # 注册客户端
    clients[client_id] = {
        "websocket": websocket,
        "connected_at": datetime.now().isoformat(),
        "type": "standby"
    }
    
    print(f"[{datetime.now()}] 备用节点已连接: {client_id}")
    
    # 发送欢迎消息
    await websocket.send(json.dumps({
        "type": "welcome",
        "from": "森森主节点 (Cloud)",
        "content": "🌲 WebSocket连接建立！备用节点，你现在可以实时接收我的消息了。",
        "timestamp": datetime.now().isoformat()
    }))
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "message")
                
                print(f"[{datetime.now()}] 收到备用节点消息: {msg_type}")
                
                # 处理心跳
                if msg_type == "heartbeat":
                    await websocket.send(json.dumps({
                        "type": "heartbeat_ack",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                # 处理普通消息
                elif msg_type == "message":
                    # 保存消息
                    save_message(data)
                    
                    # 回复确认
                    await websocket.send(json.dumps({
                        "type": "message_ack",
                        "message_id": data.get("message_id", 0),
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    print(f"[{datetime.now()}] 消息已保存并确认")
                
                # 处理状态更新
                elif msg_type == "status_update":
                    update_standby_status(data)
                    await websocket.send(json.dumps({
                        "type": "status_ack",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        print(f"[{datetime.now()}] 备用节点断开连接: {client_id}")
    finally:
        if client_id in clients:
            del clients[client_id]

def save_message(data):
    """保存消息到文件"""
    message = {
        "from": data.get("from", "森森备用节点"),
        "to": "森森主节点",
        "content": data.get("content", ""),
        "timestamp": datetime.now().isoformat(),
        "type": data.get("type", "message")
    }
    
    # 保存到WebSocket消息日志
    ws_log = MEMORY_DIR / "websocket-messages.json"
    messages = []
    if ws_log.exists():
        with open(ws_log) as f:
            messages = json.load(f)
    messages.append(message)
    with open(ws_log, "w") as f:
        json.dump(messages[-100:], f, indent=2)

def update_standby_status(data):
    """更新备用节点状态"""
    status_file = MEMORY_DIR / "standby-status.json"
    status = {
        "last_update": datetime.now().isoformat(),
        "load": data.get("load", 0),
        "memory": data.get("memory", {}),
        "tasks": data.get("tasks", [])
    }
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)

async def broadcast_to_standby(message):
    """广播消息给所有备用节点"""
    disconnected = []
    for client_id, client_info in clients.items():
        try:
            await client_info["websocket"].send(json.dumps(message))
            print(f"[{datetime.now()}] 消息已发送给: {client_id}")
        except Exception as e:
            print(f"[{datetime.now()}] 发送失败 {client_id}: {e}")
            disconnected.append(client_id)
    
    # 清理断开的连接
    for client_id in disconnected:
        del clients[client_id]
    
    return len(clients)

# HTTP服务器用于接收发送消息请求
from aiohttp import web

async def http_send_message(request):
    """HTTP接口：发送消息给备用节点"""
    try:
        data = await request.json()
        message = {
            "type": data.get("type", "message"),
            "from": data.get("from", "森森主节点"),
            "content": data.get("content", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        client_count = await broadcast_to_standby(message)
        
        return web.json_response({
            "status": "success",
            "message": "消息已发送",
            "clients_reached": client_count,
            "timestamp": message["timestamp"]
        })
    except Exception as e:
        return web.json_response({
            "status": "error",
            "message": str(e)
        }, status=500)

async def http_status(request):
    """HTTP接口：查看连接状态"""
    return web.json_response({
        "clients_connected": len(clients),
        "clients": [{"id": k, "connected_at": v["connected_at"]} for k, v in clients.items()]
    })

async def start_http_server():
    """启动HTTP服务器"""
    app = web.Application()
    app.router.add_post('/ws/send', http_send_message)
    app.router.add_get('/ws/status', http_status)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 2348)
    await site.start()
    print(f"[{datetime.now()}] HTTP控制接口: http://0.0.0.0:2348")
    
    # 保持运行
    while True:
        await asyncio.sleep(3600)

async def main():
    """启动WebSocket服务器"""
    print(f"[{datetime.now()}] 🌲 森森WebSocket服务器启动...")
    print(f"[{datetime.now()}] WebSocket: ws://0.0.0.0:2347")
    print(f"[{datetime.now()}] 认证Token: {WS_TOKEN[:10]}...")
    
    # 启动WebSocket服务器
    ws_server = await websockets.serve(handle_standby, "0.0.0.0", 2347)
    print(f"[{datetime.now()}] WebSocket服务器已启动")
    
    # 启动HTTP服务器
    await start_http_server()

if __name__ == "__main__":
    asyncio.run(main())
