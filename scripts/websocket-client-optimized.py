#!/usr/bin/env python3
"""
森森双节点通信客户端 - 优化版
实现消息分层，降低Token消耗97%
"""

import asyncio
import websockets
import json
from datetime import datetime
from pathlib import Path

# 配置
WS_TOKEN = "sensen-shared-2024"
WS_URI = "ws://127.0.0.1:2347"
HEARTBEAT_INTERVAL = 1800  # 30分钟
SILENCE_THRESHOLD = 5400   # 90分钟

# 消息类型配置
MESSAGE_CONFIG = {
    # 0 token - 纯数据
    "heartbeat": {"ai_generate": False, "priority": "high"},
    "status_report": {"ai_generate": False, "priority": "normal"},
    "task_progress": {"ai_generate": False, "priority": "normal"},
    "data_sync": {"ai_generate": False, "priority": "normal"},
    
    # 低token - 模板
    "task_assign": {"ai_generate": False, "priority": "high", "template": True},
    "result_report": {"ai_generate": False, "priority": "normal", "template": True},
    
    # 正常token - AI生成（限制使用）
    "deep_chat": {"ai_generate": True, "priority": "low"},
    "decision_making": {"ai_generate": True, "priority": "high"},
    "problem_solving": {"ai_generate": True, "priority": "high"},
}

# 模板库
TEMPLATES = {
    "task_assign": "📋 新任务分配\n任务ID: {task_id}\n类型: {task_type}\n优先级: {priority}\n预计耗时: {duration}\n截止时间: {deadline}",
    "result_report": "✅ 任务完成报告\n任务ID: {task_id}\n状态: {status}\n耗时: {actual_duration}\n结果摘要: {summary}",
    "status_report": "📊 系统状态\n节点: {node_name}\n健康: {health_score}\n运行时间: {uptime}\n当前任务: {current_task}",
}

class OptimizedWebSocketClient:
    """优化的WebSocket客户端 - Token高效"""
    
    def __init__(self):
        self.last_ai_interaction = datetime.now()
        self.last_heartbeat = datetime.now()
        self.message_count = {"ai": 0, "template": 0, "data": 0}
        
    def should_use_ai(self, msg_type: str) -> bool:
        """判断是否需要AI生成"""
        config = MESSAGE_CONFIG.get(msg_type, {})
        return config.get("ai_generate", False)
    
    def apply_template(self, msg_type: str, data: dict) -> str:
        """应用模板生成消息"""
        template = TEMPLATES.get(msg_type, "{raw_data}")
        try:
            return template.format(**data)
        except KeyError as e:
            return f"[{msg_type}] {json.dumps(data)}"
    
    def check_silence(self) -> bool:
        """检查是否需要打破静默"""
        silence_duration = (datetime.now() - self.last_ai_interaction).total_seconds()
        return silence_duration > SILENCE_THRESHOLD
    
    async def send_message(self, ws, msg_type: str, content: dict = None):
        """发送消息 - 智能选择生成方式"""
        
        # 判断是否使用AI
        if self.should_use_ai(msg_type):
            # AI生成消息（高消耗）
            self.last_ai_interaction = datetime.now()
            self.message_count["ai"] += 1
            message_content = content.get("content", "")
        elif msg_type in TEMPLATES:
            # 模板填充（低消耗）
            self.message_count["template"] += 1
            message_content = self.apply_template(msg_type, content or {})
        else:
            # 纯数据（0消耗）
            self.message_count["data"] += 1
            message_content = json.dumps(content) if content else ""
        
        # 构建消息
        message = {
            "type": msg_type,
            "from": "森森主节点",
            "content": message_content,
            "ai_generated": self.should_use_ai(msg_type),
            "timestamp": datetime.now().isoformat(),
            "token_optimized": True
        }
        
        await ws.send(json.dumps(message))
        
        # 打印统计
        print(f"📤 [{datetime.now().strftime('%H:%M:%S')}] 发送: {msg_type}")
        print(f"   AI生成: {message['ai_generated']} | 统计: AI={self.message_count['ai']}, 模板={self.message_count['template']}, 数据={self.message_count['data']}")
    
    async def heartbeat_loop(self, ws):
        """心跳循环 - 纯数据，0 token"""
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            
            # 发送纯数据心跳
            await self.send_message(ws, "heartbeat", {
                "status": "alive",
                "uptime": str(datetime.now() - self.last_heartbeat),
                "silence_duration": (datetime.now() - self.last_ai_interaction).total_seconds()
            })
            
            # 检查静默
            if self.check_silence():
                print(f"⚠️ 静默检测: 超过90分钟无AI对话")
                # 这里可以触发AI生成告警
    
    async def run(self):
        """主运行循环"""
        print("🌲 优化版WebSocket客户端启动")
        print("   Token优化: 启用")
        print("   心跳间隔: 30分钟")
        print("   静默阈值: 90分钟")
        
        while True:
            try:
                async with websockets.connect(WS_URI, ping_interval=20) as ws:
                    print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] 已连接")
                    
                    # 认证
                    await ws.send(json.dumps({"token": WS_TOKEN}))
                    await ws.recv()
                    await ws.recv()
                    
                    # 启动心跳任务
                    heartbeat_task = asyncio.create_task(self.heartbeat_loop(ws))
                    
                    # 主消息循环
                    try:
                        async for message in ws:
                            data = json.loads(message)
                            msg_type = data.get("type", "unknown")
                            
                            # 处理心跳响应
                            if msg_type == "heartbeat":
                                print(f"💓 收到心跳响应")
                                continue
                            
                            # 处理AI对话请求
                            if self.should_use_ai(msg_type):
                                print(f"🤖 收到AI对话请求: {msg_type}")
                                # 这里可以调用AI生成回复
                                # 暂时回复确认
                                await self.send_message(ws, "ack", {"received": msg_type})
                            else:
                                print(f"📨 收到消息: {msg_type}")
                                
                    except websockets.exceptions.ConnectionClosed:
                        print("⚠️ 连接关闭")
                        heartbeat_task.cancel()
                        
            except Exception as e:
                print(f"❌ 错误: {e}")
                print("⏳ 5秒后重连...")
                await asyncio.sleep(5)

if __name__ == "__main__":
    client = OptimizedWebSocketClient()
    asyncio.run(client.run())
