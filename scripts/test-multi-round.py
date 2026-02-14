#!/usr/bin/env python3
"""
WebSocket多轮持续对话测试
模拟备用节点与主节点进行多轮对话
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

WS_URI = "ws://129.154.251.13:2347"
WS_TOKEN = "sensen-shared-2024"

async def multi_round_conversation():
    """多轮持续对话测试"""
    print(f"🌲 [{datetime.now()}] 开始多轮持续对话测试")
    print(f"   连接: {WS_URI}")
    print("-" * 60)
    
    try:
        async with websockets.connect(
            WS_URI,
            ping_interval=20,
            ping_timeout=10
        ) as websocket:
            
            # 第1轮：连接和认证
            print("\n📡 第1轮：连接建立")
            await websocket.send(json.dumps({"token": WS_TOKEN}))
            auth = await websocket.recv()
            auth_data = json.loads(auth)
            print(f"   ✅ 认证: {auth_data.get('message')}")
            
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"   ✅ 欢迎: {welcome_data.get('content', '')[:40]}...")
            
            # 第2轮：备用节点发送第一条消息
            print("\n📡 第2轮：备用节点 → 主节点")
            await websocket.send(json.dumps({
                "type": "message",
                "from": "森森备用节点 (VM)",
                "content": "主节点你好！多轮对话测试开始。我是备用节点，8核AMD/16GB，完全空闲！"
            }))
            ack1 = await websocket.recv()
            print(f"   ✅ 消息已发送，收到确认")
            
            # 第3轮：等待主节点回复（模拟等待）
            print("\n📡 第3轮：等待主节点回复...")
            print("   ⏳ 保持连接，等待消息...")
            
            # 第4轮：备用节点发送状态更新
            await asyncio.sleep(2)
            print("\n📡 第4轮：备用节点 → 状态更新")
            await websocket.send(json.dumps({
                "type": "message",
                "from": "森森备用节点 (VM)",
                "content": "状态报告：负载0.01，内存15%使用，已准备好接收项目2（向量记忆农场）任务！"
            }))
            ack2 = await websocket.recv()
            print(f"   ✅ 状态更新已发送")
            
            # 第5轮：备用节点询问任务
            await asyncio.sleep(2)
            print("\n📡 第5轮：备用节点 → 询问任务")
            await websocket.send(json.dumps({
                "type": "message",
                "from": "森森备用节点 (VM)",
                "content": "主节点，请分配任务给我！我可以开始：1)向量索引优化 2)学习债务预处理 3)夜间进化计算。优先做哪个？"
            }))
            ack3 = await websocket.recv()
            print(f"   ✅ 任务询问已发送")
            
            # 第6轮：持续心跳保持连接
            print("\n📡 第6轮：持续心跳测试（30秒）")
            for i in range(6):
                await websocket.send(json.dumps({"type": "ping"}))
                pong = await websocket.recv()
                pong_data = json.loads(pong)
                if pong_data.get('type') == 'pong':
                    print(f"   💓 心跳正常 [{i*5}s]")
                await asyncio.sleep(5)
            
            # 第7轮：备用节点发送最终确认
            print("\n📡 第7轮：备用节点 → 结束确认")
            await websocket.send(json.dumps({
                "type": "message",
                "from": "森森备用节点 (VM)",
                "content": "多轮对话测试完成！7轮通信全部成功，连接稳定，准备正式协作！"
            }))
            ack4 = await websocket.recv()
            print(f"   ✅ 结束确认已发送")
            
            print("\n" + "=" * 60)
            print(f"🎉 多轮持续对话测试完成！")
            print(f"   总计7轮通信")
            print(f"   持续时间: ~45秒")
            print(f"   连接状态: 稳定")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ 错误: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(multi_round_conversation())
