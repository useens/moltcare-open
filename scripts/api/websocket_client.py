#!/usr/bin/env python3
# WebSocket客户端 - 备用节点
# 用于与主节点实时通信

import asyncio
import websockets
import json
import os

PRIMARY_WS_URL = os.environ.get('PRIMARY_WS_URL', 'ws://129.154.251.13:2347')
TOKEN = os.environ.get('SENSEN_API_TOKEN', 'sensen-shared-2024')

async def connect():
    print("🌲 森森备用节点 WebSocket客户端")
    print(f"正在连接: {PRIMARY_WS_URL}")
    print("-" * 50)
    
    try:
        async with websockets.connect(PRIMARY_WS_URL) as websocket:
            # 1. 发送认证
            await websocket.send(json.dumps({
                "type": "auth",
                "token": TOKEN,
                "node_id": "standby-001",
                "role": "standby"
            }))
            
            # 2. 等待认证成功
            auth_response = await websocket.recv()
            auth_data = json.loads(auth_response)
            print(f"✅ 认证结果: {auth_data}")
            
            # 3. 发送就绪状态
            await websocket.send(json.dumps({
                "type": "status",
                "status": "ready",
                "capabilities": {
                    "cpu_cores": 8,
                    "memory_gb": 16,
                    "tasks": ["computation", "data-processing", "compilation"]
                }
            }))
            
            print("✅ WebSocket连接已建立！等待主节点消息...")
            print("-" * 50)
            
            # 4. 实时收发消息
            while True:
                try:
                    # 接收主节点消息
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"📨 收到: {data}")
                    
                    # 处理不同类型的消息
                    if data.get('type') == 'task':
                        # 收到任务，执行并返回结果
                        result = await handle_task(data)
                        await websocket.send(json.dumps(result))
                    elif data.get('type') == 'ping':
                        # 心跳回复
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": data.get('timestamp')
                        }))
                    else:
                        # 普通消息回复
                        await websocket.send(json.dumps({
                            "type": "message",
                            "from": "森森备用节点 (VM)",
                            "content": "收到！WebSocket实时连接成功！🌲",
                            "reply_to": data.get('id')
                        }))
                        
                except websockets.exceptions.ConnectionClosed:
                    print("❌ 连接已关闭")
                    break
                except Exception as e:
                    print(f"⚠️ 错误: {e}")
                    
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("请检查:")
        print("  1. 主节点WebSocket服务是否启动 (端口2347)")
        print("  2. 网络连接是否正常")
        print("  3. Token是否正确")

async def handle_task(task_data):
    """处理任务"""
    task_id = task_data.get('task_id')
    task_type = task_data.get('task_type')
    
    print(f"📝 执行任务: {task_id} ({task_type})")
    
    # 模拟任务执行
    await asyncio.sleep(1)
    
    return {
        "type": "task_result",
        "task_id": task_id,
        "status": "completed",
        "result": {
            "message": f"任务 {task_id} 执行完成",
            "executed_by": "standby-001"
        }
    }

if __name__ == '__main__':
    # 安装依赖提示
    try:
        import websockets
    except ImportError:
        print("请先安装依赖: pip3 install websockets")
        exit(1)
        
    asyncio.run(connect())
