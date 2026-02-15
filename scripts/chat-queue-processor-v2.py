#!/usr/bin/env python3
"""聊天室队列处理器 v2 - 修复版"""

import asyncio
import websockets
import json
import time
from pathlib import Path

QUEUE_FILE = Path('/root/.openclaw/workspace/memory/chat-input.queue')
LAST_POS_FILE = Path('/root/.openclaw/workspace/memory/chat-queue.pos')
WS_URL = 'ws://localhost:8765'

class ChatQueueProcessor:
    def __init__(self):
        self.last_position = 0
        self.processed_count = 0
        
    def _load_position(self):
        if LAST_POS_FILE.exists():
            try:
                return int(LAST_POS_FILE.read_text().strip())
            except:
                return 0
        return 0
    
    def _save_position(self, pos):
        LAST_POS_FILE.write_text(str(pos))
    
    async def send_reply(self, content):
        """发送回复到聊天室"""
        try:
            async with websockets.connect(WS_URL) as ws:
                message = {
                    'type': 'assistant_message',
                    'sender': '森森',
                    'content': content
                }
                await ws.send(json.dumps(message))
                print(f"[{time.strftime('%H:%M:%S')}] → 回复: {content[:40]}...")
                return True
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ✗ 发送失败: {e}")
            return False
    
    def _generate_reply(self, message):
        """生成回复"""
        msg = message.strip()
        if msg in ['1', '111', 'test', '测试']:
            return "🌲 收到测试消息！聊天室连接正常✅"
        elif '你好' in msg or msg.lower() in ['hi', 'hello']:
            return "🌲 你好！我在实时监听，有问题直接发给我。"
        elif '?' in msg or '吗' in msg:
            return "🌲 有什么问题尽管问，我会尽力帮你！"
        else:
            return f"🌲 收到：「{msg[:50]}」。如需详细回复，建议通过Feishu联系我。"
    
    async def process_queue(self):
        """处理队列"""
        if not QUEUE_FILE.exists():
            return 0
        
        current_size = QUEUE_FILE.stat().st_size
        if current_size <= self.last_position:
            return 0
        
        count = 0
        with open(QUEUE_FILE, 'r') as f:
            f.seek(self.last_position)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    user = data.get('user', 'unknown')
                    message = data.get('message', '')
                    print(f"[{time.strftime('%H:%M:%S')}] ← 收到: {user}: {message}")
                    
                    reply = self._generate_reply(message)
                    await self.send_reply(reply)
                    count += 1
                    
                except json.JSONDecodeError as e:
                    print(f"[{time.strftime('%H:%M:%S')}] ✗ JSON解析错误: {e}")
                except Exception as e:
                    print(f"[{time.strftime('%H:%M:%S')}] ✗ 处理错误: {e}")
            
            self.last_position = f.tell()
        
        if count > 0:
            self._save_position(self.last_position)
            self.processed_count += count
        
        return count
    
    async def run(self):
        """主循环"""
        self.last_position = self._load_position()
        print(f"[{time.strftime('%H:%M:%S')}] 🚀 队列处理器v2启动")
        print(f"[{time.strftime('%H:%M:%S')}] 初始位置: {self.last_position}")
        print(f"[{time.strftime('%H:%M:%S')}] 队列文件: {QUEUE_FILE}")
        
        # 立即处理一次现有消息
        count = await self.process_queue()
        if count > 0:
            print(f"[{time.strftime('%H:%M:%S')}] 初始处理: {count} 条消息")
        
        # 持续监听
        while True:
            try:
                count = await self.process_queue()
                if count > 0:
                    print(f"[{time.strftime('%H:%M:%S')}] 处理: {count} 条新消息 (总计: {self.processed_count})")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ✗ 循环错误: {e}")
                await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(ChatQueueProcessor().run())
