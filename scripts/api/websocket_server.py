#!/usr/bin/env python3
"""
森森WebSocket服务器 - 简化版
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
message_history = []

async def broadcast_message(message_data, exclude_client=None):
    """广播消息给所有客户端（除了发送者）"""
    disconnected = []
    for cid, client_ws in clients.items():
        if cid != exclude_client:  # 不发送给发送者自己
            try:
                await client_ws.send(json.dumps(message_data))
                print(f"[{datetime.now()}] 📤 广播给 {cid}")
            except Exception as e:
                print(f"[{datetime.now()}] ⚠️ 发送给 {cid} 失败: {e}")
                disconnected.append(cid)
    
    # 清理断开的客户端
    for cid in disconnected:
        if cid in clients:
            del clients[cid]

async def handle_client(websocket, path=None):
    """处理客户端连接"""
    client_id = None
    
    try:
        print(f"[{datetime.now()}] 新连接尝试...")
        
        # 等待认证
        auth_msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        auth_data = json.loads(auth_msg)
        
        if auth_data.get("token") != WS_TOKEN:
            await websocket.send(json.dumps({
                "type": "auth_failed",
                "message": "认证失败"
            }))
            return
        
        # 认证成功
        client_id = f"client_{datetime.now().strftime('%H%M%S')}"
        clients[client_id] = websocket
        
        await websocket.send(json.dumps({
            "type": "auth_success",
            "message": "认证成功",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        print(f"[{datetime.now()}] ✅ 客户端已连接: {client_id}")
        
        # 发送欢迎消息
        await websocket.send(json.dumps({
            "type": "welcome",
            "from": "森森主节点",
            "content": "🌲 WebSocket连接建立！实时通信已就绪。发送消息给我吧！",
            "timestamp": datetime.now().isoformat()
        }))
        
        # 保持连接，接收消息
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "message")
                
                # 处理心跳
                if msg_type == "ping":
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                    continue
                
                # 处理普通消息
                if msg_type in ["message", "chat", "test", "realtime_test", "realtime_chat", "direct_test"]:
                    msg_data = {
                        "from": data.get("from", "备用节点"),
                        "content": data.get("content", ""),
                        "timestamp": datetime.now().isoformat(),
                        "client_id": client_id,
                        "type": msg_type
                    }
                    message_history.append(msg_data)
                    
                    # 保存到文件
                    log_file = MEMORY_DIR / "websocket-messages.json"
                    with open(log_file, "w") as f:
                        json.dump(message_history[-100:], f, indent=2)
                    
                    print(f"[{datetime.now()}] 📨 收到消息: {msg_data['content'][:50]}...")
                    
                    # 广播消息给所有其他客户端
                    await broadcast_message(msg_data, exclude_client=client_id)
                    
                    # 回复确认给发送者
                    await websocket.send(json.dumps({
                        "type": "message_ack",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        print(f"[{datetime.now()}] 客户端断开: {client_id}")
    except Exception as e:
        print(f"[{datetime.now()}] 错误: {e}")
    finally:
        if client_id and client_id in clients:
            del clients[client_id]
            print(f"[{datetime.now()}] 清理客户端: {client_id}")

async def main():
    """启动WebSocket服务器"""
    print(f"[{datetime.now()}] 🌲 森森WebSocket服务器启动...")
    print(f"[{datetime.now()}] 监听: ws://0.0.0.0:2347")
    print(f"[{datetime.now()}] 等待备用节点连接...")
    
    async with websockets.serve(handle_client, "0.0.0.0", 2347, ping_interval=30, ping_timeout=10):
        await asyncio.Future()  # 永远运行

if __name__ == "__main__":
    asyncio.run(main())
