#!/usr/bin/env python3
"""聊天室队列处理器 - 将用户消息转发到OpenClaw"""

import asyncio
import websockets
import json
import time
from pathlib import Path
import aiohttp

QUEUE_FILE = Path('/root/.openclaw/workspace/memory/chat-input.queue')
LAST_POS_FILE = Path('/root/.openclaw/workspace/memory/chat-queue.pos')
WS_URL = 'ws://localhost:8765'  # 连接到安全聊天服务器

class ChatQueueProcessor:
    def __init__(self):
        self.last_position = self._load_position()
        self.websocket = None
        
    def _load_position(self):
        if LAST_POS_FILE.exists():
            return int(LAST_POS_FILE.read_text())
        return 0
    
    def _save_position(self, pos):
        LAST_POS_FILE.write_text(str(pos))
    
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect(WS_URL)
            print(f"[{time.strftime('%H:%M:%S')}] 已连接到聊天服务器")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] 连接失败: {e}")
    
    async def send_assistant_message(self, content):
        """发送助手消息到聊天室"""
        if not self.websocket:
            await self.connect()
        
        try:
            message = {
                'type': 'assistant_message',
                'sender': '森森',
                'content': content
            }
            await self.websocket.send(json.dumps(message))
            print(f"[{time.strftime('%H:%M:%S')}] 回复: {content[:50]}...")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] 发送失败: {e}")
            self.websocket = None
    
    async def process_queue(self):
        """处理队列中的新消息"""
        if not QUEUE_FILE.exists():
            return
        
        current_size = QUEUE_FILE.stat().st_size
        if current_size <= self.last_position:
            return
        
        with open(QUEUE_FILE, 'r') as f:
            f.seek(self.last_position)
            new_lines = f.readlines()
            self.last_position = f.tell()
        
        self._save_position(self.last_position)
        
        for line in new_lines:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                user = data.get('user', 'unknown')
                message = data.get('message', '')
                print(f"[{time.strftime('%H:%M:%S')}] 收到: {user}: {message}")
                
                # 生成简单回复
                reply = self._generate_reply(message)
                await self.send_assistant_message(reply)
                
            except json.JSONDecodeError:
                continue
    
    def _generate_reply(self, message):
        """生成回复（简化版，实际应该调用OpenClaw API）"""
        msg_lower = message.lower().strip()
        
        if msg_lower in ['1', 'test', '测试']:
            return "🌲 收到！聊天室连接正常，我正在实时监听你的消息。"
        elif '你好' in message or 'hi' in msg_lower:
            return "🌲 你好！我是森森，有什么可以帮你的吗？"
        elif '?' in message or '吗' in message or '怎么' in message:
            return "🌲 这是一个好问题！请详细描述一下，我会尽力帮你解决。"
        else:
            return f"🌲 收到你的消息：「{message}」。由于我目前处于队列处理模式，详细回复请通过Feishu或其他渠道联系我。"
    
    async def run(self):
        """主循环"""
        print(f"[{time.strftime('%H:%M:%S')}] 队列处理器启动")
        await self.connect()
        
        while True:
            try:
                await self.process_queue()
                await asyncio.sleep(1)  # 每秒检查一次
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] 错误: {e}")
                await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(ChatQueueProcessor().run())
