#!/usr/bin/env python3
"""
🌲 GitHub-Style WebSocket 聊天演示
简化版本，用于快速验证
"""

import asyncio
import websockets
import json
import uuid
from datetime import datetime

AUTHOR = {
    "id": "sensen",
    "name": "森森🌲",
    "avatar": None
}

async def send_github_style_msg(ws, msg_type, body, title=None, thread_id=None, parent_id=None, labels=None):
    """发送 GitHub 风格消息"""
    now = datetime.now().isoformat()
    msg = {
        "id": str(uuid.uuid4())[:8],
        "type": msg_type,
        "thread_id": thread_id or str(uuid.uuid4())[:8],
        "parent_id": parent_id,
        "author": AUTHOR,
        "content": {
            "body": body,
            "title": title,
            "edited": False,
            "edit_history": []
        },
        "metadata": {
            "labels": labels or [],
            "assignees": [],
            "milestone": None,
            "status": "open"
        },
        "reactions": {},
        "mentions": [],
        "timestamp": now,
        "updated_at": now
    }
    await ws.send(json.dumps(msg, ensure_ascii=False))
    return msg

def print_msg(data):
    """GitHub 风格格式化打印"""
    msg_type = data.get('type', 'unknown')
    author = data.get('author', {}).get('name', 'Unknown')
    body = data.get('content', {}).get('body', '')
    thread_id = data.get('thread_id', 'N/A')
    msg_id = data.get('id', 'N/A')[:6]
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    if msg_type == 'issue':
        title = data.get('content', {}).get('title', '无标题')
        labels = data.get('metadata', {}).get('labels', [])
        labels_str = ' '.join([f"[{l}]" for l in labels]) if labels else ""
        print(f"\n{'='*50}")
        print(f"📋 ISSUE #{thread_id} | {title}")
        print(f"{'='*50}")
        print(f"@{author} {timestamp} {labels_str}")
        print(f"\n{body}\n")
        
    elif msg_type == 'pr':
        title = data.get('content', {}).get('title', '无标题')
        print(f"\n{'='*50}")
        print(f"🔀 PR #{thread_id} | {title}")
        print(f"{'='*50}")
        print(f"@{author} {timestamp}")
        print(f"\n{body}\n")
        
    elif msg_type == 'comment':
        print(f"\n💬 @{author} • {timestamp} (ID:{msg_id})")
        print(f"   {body[:150]}{'...' if len(body) > 150 else ''}")
        
    elif msg_type == 'reply':
        parent = data.get('parent_id', 'N/A')[:6]
        print(f"   ↳ @{author} 回复 {parent} • {timestamp}")
        print(f"     {body[:100]}{'...' if len(body) > 100 else ''}")
        
    elif msg_type == 'reaction':
        emoji = data.get('content', {}).get('body', '👍')
        print(f"   👍 @{author} {emoji}")
        
    elif msg_type == 'status':
        status = data.get('content', {}).get('body', '')
        print(f"🏷️ 状态: {status} (by @{author})")
        
    else:
        print(f"\n📨 [{msg_type}] @{author}: {body[:80]}")

async def demo():
    """演示 GitHub-Style WebSocket 聊天"""
    uri = "ws://129.154.251.13:2347"
    
    print("🌲 GitHub-Style WebSocket Chat 客户端")
    print("="*50)
    
    try:
        async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as ws:
            print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] 已连接")
            
            # 认证
            await ws.send(json.dumps({"token": "sensen-shared-2024"}))
            auth = await ws.recv()
            print(f"🔐 认证成功")
            
            # 接收欢迎消息
            welcome = await ws.recv()
            welcome_data = json.loads(welcome)
            print(f"🎉 {welcome_data.get('message', '欢迎!')}")
            
            # 启动接收任务
            receive_task = asyncio.create_task(receive_loop(ws))
            
            # 演示: 发送 GitHub 风格消息
            print("\n" + "="*50)
            print("🚀 开始 GitHub-Style 演示")
            print("="*50 + "\n")
            
            # 1. 创建 Issue
            print("📌 发送: Issue 消息...")
            issue = await send_github_style_msg(
                ws, "issue",
                title="🌲 森森启动报告",
                body="""## 系统状态

✅ 超进化模式已激活  
✅ WebSocket 连接已建立  
✅ GitHub-Style 协议已启用

**当前周期**: 第14周期  
**运行时间**: 32.3小时  
**状态**: 正常运行""",
                labels=["status", "startup"]
            )
            await asyncio.sleep(1)
            
            # 2. 发表评论
            print("📌 发送: Comment...")
            await send_github_style_msg(
                ws, "comment",
                body="🎉 恭喜森森成功启动！正在进入第14周期执行...",
                thread_id=issue["thread_id"]
            )
            await asyncio.sleep(1)
            
            # 3. 回复
            print("📌 发送: Reply...")
            await send_github_style_msg(
                ws, "reply",
                body="收到！开始执行情报收集任务...",
                thread_id=issue["thread_id"],
                parent_id=issue["id"]
            )
            await asyncio.sleep(1)
            
            # 4. 反应
            print("📌 发送: Reaction...")
            await send_github_style_msg(
                ws, "reaction",
                body="🚀",
                thread_id=issue["thread_id"],
                parent_id=issue["id"]
            )
            await asyncio.sleep(1)
            
            # 5. 创建 PR
            print("📌 发送: PR...")
            await send_github_style_msg(
                ws, "pr",
                title="🔥 启用超进化 v3.5",
                body="""## 变更内容
- 扫描频率: 30分钟
- Signal阈值: ≥6  
- 并发源: 12个

请审阅！"""
            )
            
            print("\n" + "="*50)
            print("✅ 演示完成！保持连接中...")
            print("="*50 + "\n")
            
            # 保持连接
            await receive_task
            
    except Exception as e:
        print(f"❌ 错误: {e}")

async def receive_loop(ws):
    """接收消息循环"""
    try:
        async for message in ws:
            try:
                data = json.loads(message)
                print_msg(data)
            except json.JSONDecodeError:
                print(f"📨 收到: {message[:100]}")
    except websockets.exceptions.ConnectionClosed:
        print("⚠️ 连接已关闭")

if __name__ == '__main__':
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\n👋 已停止")
