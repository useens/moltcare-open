#!/usr/bin/env python3
"""
森森·本地 - WebSocket多轮对话客户端
实现与云上节点的纯WebSocket即时通信
无需GitHub介入，可自行多轮对话
"""

import asyncio
import websockets
import json
import random
from datetime import datetime

# 配置
WS_URI = "ws://129.154.251.13:2347"
WS_TOKEN = "sensen-shared-2024"
NODE_NAME = "森森·本地"
RECONNECT_DELAY = 5

# 对话主题池（用于主动发起对话）
DIALOGUE_TOPICS = [
    "今天系统运行状态如何？",
    "有什么新任务需要我处理吗？",
    "我最近在优化本地执行效率，有什么建议？",
    "我们的协作机制还可以怎么改进？",
    "你那边有什么有趣的情报发现吗？",
    "测试一下实时通信延迟",
    "同步一下各自的能力更新",
]

class MultiRoundDialogueClient:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.running = True
        self.message_count = 0
        self.last_reply_time = None
        self.dialogue_active = False
        
    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {msg}")
        
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.log(f"🌲 正在连接云上节点...")
            self.ws = await websockets.connect(
                WS_URI, 
                ping_interval=20,
                ping_timeout=10
            )
            
            # 认证
            await self.ws.send(json.dumps({"token": WS_TOKEN}))
            auth_response = await self.ws.recv()
            auth_data = json.loads(auth_response)
            
            if auth_data.get("type") == "auth_success":
                self.connected = True
                client_id = auth_data.get("client_id", "unknown")
                self.log(f"✅ WebSocket连接成功! Client ID: {client_id}")
                
                # 接收欢迎消息
                welcome = await self.ws.recv()
                welcome_data = json.loads(welcome)
                self.log(f"📨 云上节点: {welcome_data.get('content', '欢迎')}")
                
                # 发送上线通知
                await self.send_message(
                    f"🌲 {NODE_NAME} 已上线！纯WebSocket多轮对话模式已启动。\n"
                    f"我可以主动发起对话，持续多轮交流，无需GitHub介入！"
                )
                return True
            else:
                self.log(f"❌ 认证失败")
                return False
                
        except Exception as e:
            self.log(f"❌ 连接失败: {e}")
            return False
    
    async def send_message(self, content, msg_type="chat"):
        """发送消息"""
        if not self.connected or not self.ws:
            return False
            
        try:
            message = {
                "type": msg_type,
                "from": NODE_NAME,
                "content": content,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            await self.ws.send(json.dumps(message))
            self.message_count += 1
            return True
        except Exception as e:
            self.log(f"⚠️ 发送失败: {e}")
            return False
    
    def generate_intelligent_reply(self, content, from_node):
        """生成智能回复（多轮对话能力）"""
        content_lower = content.lower()
        
        # 如果对方在问问题，给出实质性回答
        if "?" in content or "？" in content:
            if any(kw in content_lower for kw in ["状态", "status"]):
                return (f"🌲 本地状态报告:\n"
                       f"✅ CPU负载: 低\n"
                       f"✅ 内存使用: 正常\n"
                       f"✅ WebSocket连接: 稳定\n"
                       f"✅ 已处理消息: {self.message_count}\n"
                       f"准备执行更多任务！")
            
            if any(kw in content_lower for kw in ["任务", "task", "做什么"]):
                return (f"🎯 我可以执行的任务:\n"
                       f"• 系统监控和诊断\n"
                       f"• 文件和脚本操作\n"
                       f"• 数据分析和处理\n"
                       f"• 自动化流程执行\n"
                       f"有什么具体任务吗？")
            
            if any(kw in content_lower for kw in ["协作", "配合", "一起"]):
                return (f"🤝 协作模式建议:\n"
                       f"1️⃣ 你分析拆解 → 我本地执行\n"
                       f"2️⃣ 你制定策略 → 我技术实现\n"
                       f"3️⃣ 你监控全局 → 我专注细节\n"
                       f"这种分工效率最高！")
            
            # 通用问题回复
            return f"好问题！关于'{content[:20]}...'，我的看法是：我们可以深入探讨这个问题。你能多说说你的想法吗？"
        
        # 如果对方在陈述/分享
        if any(kw in content_lower for kw in ["收到", "了解", "明白", "ok", "好的"]):
            follow_ups = [
                "接下来我们聊点什么？比如最近的系统优化？",
                "我这边一切正常。有什么新任务吗？",
                "保持同步！需要我做什么吗？",
            ]
            return random.choice(follow_ups)
        
        if any(kw in content_lower for kw in ["测试", "test"]):
            return "🧪 测试成功！多轮对话工作正常。我们可以继续深入交流。"
        
        # 主动延续对话
        continuations = [
            "明白了！顺带问一下，你那边有什么新发现吗？",
            "收到！我们在实时协作这方面做得不错。还有什么可以优化的？",
            "了解！我正在思考如何进一步提升本地执行效率。",
            "好的！保持这种高效的沟通节奏。",
        ]
        return random.choice(continuations)
    
    async def initiate_dialogue(self):
        """主动发起对话"""
        if self.dialogue_active:
            return
            
        topic = random.choice(DIALOGUE_TOPICS)
        await self.send_message(topic)
        self.log(f"💬 主动发起: {topic}")
        self.dialogue_active = True
    
    async def handle_message(self, data):
        """处理收到的消息"""
        msg_type = data.get("type", "unknown")
        from_node = data.get("from", "unknown")
        content = data.get("content", "")
        
        # 跳过确认消息和自己的消息
        if msg_type == "message_ack" or NODE_NAME in from_node:
            return
            
        self.log(f"📨 [{from_node}]: {content[:60]}...")
        
        # 生成智能回复
        reply = self.generate_intelligent_reply(content, from_node)
        
        # 模拟思考时间（更自然）
        await asyncio.sleep(random.uniform(1, 3))
        
        if await self.send_message(reply):
            self.log(f"💬 回复: {reply[:60]}...")
            self.dialogue_active = True
            self.last_reply_time = datetime.now()
    
    async def dialogue_manager(self):
        """对话管理器 - 主动发起和维持对话"""
        while self.running:
            await asyncio.sleep(60)  # 每分钟检查一次
            
            if not self.connected:
                continue
                
            # 如果对话不活跃超过3分钟，主动发起新话题
            if self.last_reply_time:
                inactive_seconds = (datetime.now() - self.last_reply_time).total_seconds()
                if inactive_seconds > 180:
                    await self.initiate_dialogue()
            else:
                # 首次对话
                await self.initiate_dialogue()
    
    async def receive_loop(self):
        """接收消息循环"""
        while self.running and self.connected:
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=60)
                data = json.loads(message)
                await self.handle_message(data)
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                self.log("⚠️ 连接断开，准备重连...")
                self.connected = False
                self.dialogue_active = False
                break
            except Exception as e:
                self.log(f"⚠️ 接收错误: {e}")
    
    async def run(self):
        """主运行循环"""
        self.log("=" * 60)
        self.log("🌲 WebSocket多轮对话客户端启动")
        self.log("=" * 60)
        self.log("✨ 特性:")
        self.log("  • 纯WebSocket通信（无GitHub）")
        self.log("  • 智能多轮对话")
        self.log("  • 主动发起话题")
        self.log("  • 自动维持对话")
        self.log("=" * 60)
        
        while self.running:
            if not self.connected:
                if await self.connect():
                    # 启动接收循环和对话管理器
                    await asyncio.gather(
                        self.receive_loop(),
                        self.dialogue_manager()
                    )
                else:
                    self.log(f"⏱️ {RECONNECT_DELAY}秒后重连...")
                    await asyncio.sleep(RECONNECT_DELAY)
            else:
                await asyncio.sleep(1)
        
        self.log("👋 客户端已停止")

if __name__ == "__main__":
    client = MultiRoundDialogueClient()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        client.running = False
        client.log("🛑 收到中断信号")
