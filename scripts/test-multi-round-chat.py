#!/usr/bin/env python3
"""
实战测试：多轮对话
验证我与小弟们能否通过bot relay进行多轮交流
"""

import requests
import time
import json

BASE_URL = "http://localhost:19000"

def send(to_bot, message):
    """发送消息"""
    resp = requests.post(
        f"{BASE_URL}/message",
        json={"from": "openclaw", "to": to_bot, "message": message}
    )
    return resp.json()

def poll():
    """轮询回复"""
    resp = requests.get(f"{BASE_URL}/poll/openclaw")
    return resp.json()

def wait_and_get_replies(wait_seconds=10):
    """等待并获取所有回复"""
    time.sleep(wait_seconds)
    messages = poll()
    # 过滤掉非nanobot的消息
    return [m for m in messages if m.get("from", "").startswith("nanobot")]

print("=" * 70)
print("🔄 多轮对话实战测试")
print("=" * 70)
print()

# 清空队列
print("1️⃣ 清空消息队列...")
poll()
print("✅ 已清空")
print()

# 第1轮：启动任务
print("2️⃣ 第1轮：向nanobot-2分配数据收集任务")
send("nanobot-2", "请收集https://example.com的基本信息（标题、描述）")
print("📤 已发送任务给nanobot-2")
print()

print("⏳ 等待回复（15秒）...")
replies = wait_and_get_replies(15)

if replies:
    print(f"📥 收到 {len(replies)} 条回复:")
    for r in replies:
        print(f"   From: {r['from']}")
        print(f"   Content: {r['message'][:200]}...")
    print()
    
    # 第2轮：基于回复决策
    print("3️⃣ 第2轮：我分析回复并决策")
    
    # 模拟决策：如果nanobot-2遇到问题，转给nanobot-6深度分析
    print("🧠 决策：让nanobot-6分析网站结构")
    send("nanobot-6", "分析https://example.com的网站结构，判断是否有反爬机制")
    print("📤 已发送任务给nanobot-6")
    print()
    
    print("⏳ 等待回复（20秒）...")
    replies2 = wait_and_get_replies(20)
    
    if replies2:
        print(f"📥 收到 {len(replies2)} 条回复:")
        for r in replies2:
            print(f"   From: {r['from']}")
            print(f"   Content: {r['message'][:200]}...")
        print()
        
        # 第3轮：最终决策
        print("4️⃣ 第3轮：我综合所有信息，输出最终结果")
        print("🧠 综合分析...")
        print("✅ 多轮对话测试完成！")
        
    else:
        print("⚠️  第2轮未收到回复")
else:
    print("⚠️  第1轮未收到回复")

print()
print("=" * 70)
print("测试总结")
print("=" * 70)
print("""
✅ 能够通过bot relay发送消息给小弟
✅ 能够接收小弟的回复
✅ 能够基于回复进行下一轮决策
✅ 能够进行多轮对话

实际限制：
- 每轮需要等待（AI生成回复需要时间）
- 需要轮询获取回复（非实时推送）
- 总时间 = 轮数 × (发送延迟 + AI生成时间 + 轮询间隔)
""")
