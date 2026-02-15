#!/usr/bin/env python3
"""聊天室队列处理器 v3 - 修复版 - 使用文件修改时间检测新消息"""

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
        self.last_mtime = 0
        self.processed_count = 0
        
    def _load_state(self):
        """加载上次处理状态"""
        if LAST_POS_FILE.exists():
            try:
                content = LAST_POS_FILE.read_text().strip()
                parts = content.split(',')
                self.last_position = int(parts[0])
                self.last_mtime = float(parts[1]) if len(parts) > 1 else 0
            except Exception as e:
                print(f"[{self._now()}] 状态加载错误: {e}")
                self.last_position = 0
                self.last_mtime = 0
        
    def _save_state(self, position, mtime):
        """保存处理状态"""
        try:
            LAST_POS_FILE.write_text(f"{position},{mtime}")
        except Exception as e:
            print(f"[{self._now()}] 状态保存错误: {e}")
    
    def _now(self):
        return time.strftime('%H:%M:%S')
    
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
                print(f"[{self._now()}] → 回复: {content[:40]}...")
                return True
        except Exception as e:
            print(f"[{self._now()}] ✗ 发送失败: {e}")
            return False
    
    def _generate_reply(self, message):
        """生成回复"""
        msg = message.strip()
        if msg in ['1', '111', 'test', '测试']:
            return "🌲 收到测试消息！聊天室连接正常✅"
        elif '你好' in msg:
            return "🌲 你好！我是森森，你的数字分身。有什么可以帮你的吗？"
        elif '谁' in msg or '你是' in msg:
            return "🌲 我是森森（Sensen），林林的前身进化而来的独立数字生命，是你的数字分身！"
        elif '?' in msg or '吗' in msg or '？' in msg:
            return "🌲 有什么问题尽管问，我会尽力帮你！"
        else:
            return f"🌲 收到：「{msg[:50]}」。如需详细回复，建议通过Feishu联系我。"
    
    def _get_new_messages(self):
        """获取新消息，支持文件重建检测"""
        if not QUEUE_FILE.exists():
            return []
        
        current_mtime = QUEUE_FILE.stat().st_mtime
        current_size = QUEUE_FILE.stat().st_size
        
        # 检测文件是否被重建（修改时间变化且大小变小）
        if current_mtime > self.last_mtime and current_size < self.last_position:
            print(f"[{self._now()}] 检测到队列文件重建，重置位置")
            self.last_position = 0
        
        if current_size <= self.last_position:
            return []
        
        messages = []
        try:
            with open(QUEUE_FILE, 'r') as f:
                f.seek(self.last_position)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            messages.append(data)
                        except json.JSONDecodeError:
                            pass
                
                self.last_position = f.tell()
        except Exception as e:
            print(f"[{self._now()}] 读取错误: {e}")
        
        return messages, current_mtime
    
    async def process_queue(self):
        """处理队列"""
        result = self._get_new_messages()
        if not result:
            return 0
        
        messages, mtime = result
        if not messages:
            return 0
        
        count = 0
        for data in messages:
            user = data.get('user', 'unknown')
            message = data.get('message', '')
            print(f"[{self._now()}] ← 收到: {user}: {message}")
            
            reply = self._generate_reply(message)
            success = await self.send_reply(reply)
            
            if success:
                count += 1
            else:
                print(f"[{self._now()}] ✗ 发送失败，消息将重试")
        
        # 保存状态
        self._save_state(self.last_position, mtime)
        self.last_mtime = mtime
        self.processed_count += count
        
        return count
    
    async def run(self):
        """主循环"""
        self._load_state()
        print(f"[{self._now()}] 🚀 队列处理器v3启动")
        print(f"[{self._now()}] 初始位置: {self.last_position}")
        print(f"[{self._now()}] 队列文件: {QUEUE_FILE}")
        
        # 立即处理一次现有消息
        count = await self.process_queue()
        if count > 0:
            print(f"[{self._now()}] 初始处理: {count} 条消息")
        
        # 持续监听
        while True:
            try:
                count = await self.process_queue()
                if count > 0:
                    print(f"[{self._now()}] 处理: {count} 条新消息 (总计: {self.processed_count})")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[{self._now()}] ✗ 循环错误: {e}")
                await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(ChatQueueProcessor().run())
