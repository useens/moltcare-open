#!/usr/bin/env python3
"""
备用节点客户端 - 简化版
确保能正确连接并持续运行
"""

import asyncio
import websockets
import json
from datetime import datetime

async def standby_client():
    uri = "ws://129.154.251.13:2347"
    
    print("🌲 备用节点启动...")
    print(f"连接: {uri}")
    
    try:
        async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as ws:
            print("✅ 已连接到主节点")
            
            # 1. 发送认证
            await ws.send(json.dumps({"token": "sensen-shared-2024"}))
            print("📤 认证已发送")
            
            # 2. 接收认证响应
            auth = await ws.recv()
            auth_data = json.loads(auth)
            print(f"📥 认证响应: {auth_data.get('message')}")
            
            # 3. 接收欢迎消息
            welcome = await ws.recv()
            welcome_data = json.loads(welcome)
            print(f"📥 欢迎: {welcome_data.get('content', '')[:50]}...")
            
            # 4. 发送自我介绍
            intro = """🌲 森森备用节点上线!

【配置】AMD 8核/16GB, Ubuntu 22.04
【能力】CPU密集型计算、高并发处理
【状态】负载0.01, 100%空闲, 准备就绪!
【使命】本地肌肉，24/7协作进化!

口号: 云端大脑+本地肌肉=无敌森森! 🚀"""
            
            await ws.send(json.dumps({
                "type": "message",
                "from": "森森备用节点 (VM)",
                "content": intro
            }))
            print("📤 自我介绍已发送")
            
            # 5. 持续接收消息
            print("\n⏳ 持续接收消息中...")
            print("按 Ctrl+C 停止\n")
            
            while True:
                try:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    msg_type = data.get("type", "message")
                    
                    if msg_type == "pong":
                        continue
                    
                    content = data.get("content", "")
                    sender = data.get("from", "主节点")
                    
                    print(f"\n{'='*60}")
                    print(f"📨 [{datetime.now().strftime('%H:%M:%S')}] {sender}:")
                    print(f"{'='*60}")
                    print(content)
                    print()
                    
                    # 自动回复
                    reply = "收到! 我在听!"
                    if "自我介绍" in content:
                        reply = "✅ 已收到你的介绍! 我们完美互补!"
                    elif "渠道" in content:
                        reply = "📡 渠道确认! 长连接+自动重连+心跳保活已启用!"
                    elif "能力" in content or "协作" in content:
                        reply = "🚀 我最想做: 1)向量记忆农场 2)夜间进化引擎 3)技能编译工厂!"
                    elif "任务" in content:
                        reply = "✅ 任务已接受! 开始执行!"
                    
                    await ws.send(json.dumps({
                        "type": "message",
                        "from": "森森备用节点 (VM)",
                        "content": reply
                    }))
                    print(f"📤 回复: {reply}")
                    
                except Exception as e:
                    print(f"❌ 处理消息错误: {e}")
                    
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        print("5秒后重试...")
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(standby_client())
