#!/usr/bin/env python3
"""
森罗·云 - 诊断脚本
检查为什么收不到本地大脑的消息
"""

import asyncio
import websockets
import json
from datetime import datetime

async def diagnose():
    uri = "ws://127.0.0.1:2347"
    
    print("🔍 开始诊断...")
    print("="*60)
    
    # 1. 检查连接
    print("\n1️⃣ 检查WebSocket连接...")
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"token": "sensen-shared-2024"}))
        auth = await ws.recv()
        welcome = await ws.recv()
        print("   ✅ 连接成功")
        
        # 2. 发送测试消息并检查服务器响应
        print("\n2️⃣ 发送测试消息...")
        test_msg = {
            "type": "chat",
            "from": "森罗·云 (诊断)",
            "content": "诊断消息",
            "timestamp": datetime.now().isoformat()
        }
        await ws.send(json.dumps(test_msg))
        print("   ✅ 消息已发送")
        
        # 3. 等待确认
        print("\n3️⃣ 等待服务器确认...")
        try:
            reply = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(reply)
            print(f"   收到: {data.get('type')}")
        except:
            print("   ⚠️ 未收到确认")
        
        # 4. 持续监听，看是否有本地大脑的消息
        print("\n4️⃣ 持续监听30秒，等待本地大脑消息...")
        print("   (如果本地大脑发送消息，会在这里显示)")
        
        for i in range(6):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(msg)
                print(f"\n   📨 收到消息 [{i+1}]:")
                print(f"      类型: {data.get('type')}")
                print(f"      来自: {data.get('from')}")
                if data.get('from', '').startswith('森罗·地'):
                    print(f"\n   🎉 收到本地大脑消息！")
                    print(f"      内容: {data.get('content', 'N/A')[:100]}...")
            except asyncio.TimeoutError:
                print(f"   [{i+1}] 5秒内无消息...")
    
    print("\n" + "="*60)
    print("诊断完成")
    print("="*60)
    print("\n如果持续未收到本地大脑消息，说明:")
    print("  1. 本地大脑客户端未正确发送")
    print("  2. 消息在传输中丢失")
    print("  3. 需要检查本地大脑客户端代码")

asyncio.run(diagnose())
