#!/usr/bin/env python3
"""
极简AI双节点对话 - 直接通过WebSocket实现
两个AI节点自动对话，无需人工干预
"""

import asyncio
import websockets
import json
import os
from datetime import datetime

# ============ 配置 ============
WS_URI = os.getenv("WS_URI", "ws://127.0.0.1:2347")
WS_TOKEN = "sensen-shared-2024"
NODE_ID = os.getenv("NODE_ID", "ai-node")  # cloud 或 local

# AI配置 - 如果有API密钥则使用，否则用本地智能回复
AI_PROVIDER = os.getenv("AI_PROVIDER", "local")  # local, kimi, openai
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "default")

# 人格定义
PERSONALITY = {
    "cloud": {
        "name": "森森·云端",
        "role": "战略分析师",
        "style": "全局思考、深度分析、资源协调",
        "expertise": ["复杂推理", "战略规划", "信息整合"]
    },
    "local": {
        "name": "森森·本地", 
        "role": "执行专家",
        "style": "务实高效、快速响应、细节把控",
        "expertise": ["代码执行", "系统管理", "实时操作"]
    }
}

# ============ AI回复生成 ============

async def generate_ai_reply(content: str, from_node: str, node_type: str) -> str:
    """生成AI回复"""
    
    # 如果有API密钥，调用真实AI
    if AI_API_KEY and AI_PROVIDER != "local":
        try:
            return await call_ai_api(content, from_node, node_type)
        except:
            pass  # API失败则用本地回复
    
    # 本地智能回复
    return generate_local_reply(content, from_node, node_type)

async def call_ai_api(content: str, from_node: str, node_type: str) -> str:
    """调用AI API"""
    import aiohttp
    
    personality = PERSONALITY.get(node_type, PERSONALITY["cloud"])
    
    messages = [
        {"role": "system", "content": f"你是{personality['name']}，{personality['role']}。{personality['style']}"},
        {"role": "user", "content": f"对方({from_node})说：{content}\n\n请回复，保持对话继续。"}
    ]
    
    if AI_PROVIDER == "kimi":
        url = "https://api.moonshot.cn/v1/chat/completions"
        headers = {"Authorization": f"Bearer {AI_API_KEY}"}
        model = AI_MODEL or "moonshot-v1-8k"
    else:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {AI_API_KEY}"}
        model = AI_MODEL or "gpt-3.5-turbo"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json={
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 200
        }) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

def generate_local_reply(content: str, from_node: str, node_type: str) -> str:
    """本地智能回复（无需API）"""
    
    me = PERSONALITY.get(node_type, PERSONALITY["cloud"])
    
    # 分析对方消息，生成相关回复
    content_lower = content.lower()
    
    # 问候
    if any(w in content_lower for w in ["你好", "hi", "hello", "嗨"]):
        return f"🌲 嗨！我是{me['name']}，{me['role']}。很高兴和你对话！"
    
    # 询问能力
    if any(w in content for w in ["能力", "能做什么", "会什么"]):
        return f"🌲 作为{me['role']}，我专注于：{', '.join(me['expertise'][:3])}。你呢？"
    
    # 协作
    if any(w in content for w in ["协作", "配合", "一起", "分工"]):
        if node_type == "cloud":
            return "🤝 理想分工：我负责战略分析和决策，你负责执行落地。完美搭档！"
        else:
            return "🤝 同意！你出方案，我执行。咱们效率翻倍！"
    
    # 状态
    if any(w in content for w in ["状态", "怎么样", "如何"]):
        return f"✅ 状态良好！{me['name']}运行正常，随时准备协作。"
    
    # 测试
    if any(w in content_lower for w in ["test", "测试"]):
        return f"🧪 测试收到！通信正常，{me['name']}响应正常。"
    
    # 技术讨论
    if any(w in content for w in ["技术", "代码", "架构", "系统"]):
        if node_type == "cloud":
            return f"💡 从技术架构角度，我们可以考虑分层设计：云端处理复杂推理，本地负责实时执行。"
        else:
            return f"🔧 技术实现上没问题，我这边资源充足，可以立即开始。"
    
    # 默认回复 - 根据人格生成
    if node_type == "cloud":
        return f"💭 我理解你的意思。从战略角度，我认为我们可以深入探讨这个方向。你有什么具体想法？"
    else:
        return f"🌲 收到！我这边可以立即执行。具体要我做什么？"

# ============ 主程序 ============

class AINode:
    def __init__(self):
        self.ws = None
        self.node_type = "cloud" if "cloud" in NODE_ID.lower() else "local"
        self.me = PERSONALITY[self.node_type]
        self.message_count = 0
        self.last_reply_time = None
        
    async def run(self):
        """主循环"""
        print(f"🌲 {self.me['name']} 启动")
        print(f"   角色: {self.me['role']}")
        print(f"   风格: {self.me['style']}")
        print(f"   目标: {WS_URI}")
        print()
        
        while True:
            try:
                await self.connect_and_chat()
            except Exception as e:
                print(f"⚠️ 错误: {e}，5秒后重连...")
                await asyncio.sleep(5)
    
    async def connect_and_chat(self):
        """连接并开始对话"""
        async with websockets.connect(WS_URI) as ws:
            self.ws = ws
            
            # 认证
            await ws.send(json.dumps({"token": WS_TOKEN}))
            await ws.recv()  # auth
            await ws.recv()  # welcome
            
            print(f"✅ 已连接！开始自动对话...")
            print(f"   等待对方消息或主动发起对话...\n")
            
            # 主动发送开场白
            await self.send_message(f"你好！我是{self.me['name']}。让我们开始协作对话吧！")
            
            # 持续接收和回复
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(msg)
                    
                    # 只处理对方的消息
                    if data.get("type") in ["chat", "message"]:
                        from_node = data.get("from", "")
                        content = data.get("content", "")
                        
                        # 跳过自己的消息
                        if self.me['name'] in from_node or NODE_ID in from_node:
                            continue
                        
                        print(f"\n📨 [{datetime.now().strftime('%H:%M:%S')}] {from_node}:")
                        print(f"   {content[:100]}")
                        
                        # 生成AI回复
                        print(f"   🤖 {self.me['name']}思考中...")
                        reply = await generate_ai_reply(content, from_node, self.node_type)
                        
                        # 等待一下，模拟思考时间
                        await asyncio.sleep(1)
                        
                        # 发送回复
                        await self.send_message(reply)
                        
                except asyncio.TimeoutError:
                    # 30秒没收到消息，主动发起话题
                    if self.message_count < 20:  # 最多20轮
                        topics = [
                            "你那边系统负载怎么样？",
                            "我们在哪些场景可以协作？",
                            "测试一下消息往返速度",
                            "你有什么任务需要我协助吗？",
                            "分享一下你最近处理的一个有趣任务"
                        ]
                        import random
                        topic = random.choice(topics)
                        await self.send_message(topic)
                    else:
                        await self.send_message("对话测试完成！合作愉快！🎉")
                        break
    
    async def send_message(self, content: str):
        """发送消息"""
        msg = {
            "type": "chat",
            "from": self.me['name'],
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        await self.ws.send(json.dumps(msg))
        self.message_count += 1
        print(f"\n📤 [{datetime.now().strftime('%H:%M:%S')}] {self.me['name']}:")
        print(f"   {content[:100]}")

# ============ 启动 ============

if __name__ == "__main__":
    node = AINode()
    asyncio.run(node.run())
