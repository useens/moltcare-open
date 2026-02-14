#!/usr/bin/env python3
"""
WebSocket连接测试 - 模拟备用节点
"""

import asyncio
import websockets
import json
import sys

WS_URI = "ws://129.154.251.13:2347"
WS_TOKEN = "sensen-shared-2024"

async def test_connection():
    """测试WebSocket连接"""
    print(f"🌲 连接WebSocket服务器: {WS_URI}")
    
    try:
        async with websockets.connect(
            WS_URI,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10
        ) as websocket:
            print("✅ TCP连接建立")
            
            # 发送认证
            await websocket.send(json.dumps({
                "token": WS_TOKEN
            }))
            print("📤 认证消息已发送")
            
            # 接收认证响应
            auth_response = await asyncio.wait_for(websocket.recv(), timeout=10)
            auth_data = json.loads(auth_response)
            print(f"📥 认证响应: {auth_data.get('message', 'Unknown')}")
            
            if auth_data.get('type') != 'auth_success':
                print("❌ 认证失败")
                return
            
            print("✅ 认证成功！")
            
            # 接收欢迎消息
            welcome = await asyncio.wait_for(websocket.recv(), timeout=10)
            welcome_data = json.loads(welcome)
            print(f"📥 欢迎消息: {welcome_data.get('content', 'No content')[:50]}...")
            
            # 发送测试消息
            await websocket.send(json.dumps({
                "type": "message",
                "from": "备用节点测试客户端",
                "content": "主节点你好！连接测试成功，准备持续对话！"
            }))
            print("📤 测试消息已发送")
            
            # 保持连接，等待回复
            print("⏳ 保持连接，等待主节点回复...")
            
            for i in range(60):  # 保持60秒
                try:
                    # 发送心跳
                    await websocket.send(json.dumps({"type": "ping"}))
                    
                    # 等待响应（使用超时避免永久阻塞）
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get('type') == 'pong':
                        if i % 10 == 0:
                            print(f"  💓 心跳正常 [{i}s]")
                    else:
                        print(f"  📨 收到消息: {data.get('content', 'No content')[:50]}...")
                        
                except asyncio.TimeoutError:
                    print(f"  ⏱️ 第{i}秒: 等待消息超时，但连接仍在")
                    continue
                    
            print("✅ 60秒连接测试完成！连接稳定！")
            
    except websockets.exceptions.InvalidURI as e:
        print(f"❌ URI错误: {e}")
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket错误: {e}")
    except ConnectionRefusedError:
        print(f"❌ 连接被拒绝，服务器可能未启动或防火墙阻止")
    except Exception as e:
        print(f"❌ 错误: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
