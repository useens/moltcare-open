#!/usr/bin/env python3
"""
Nanobot AI Agent - v4.1 修复版
修复group_chat.jsonl解析错误
"""
import os
import sys
import json
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import threading
import time

# 配置
AGENT_ID = sys.argv[1] if len(sys.argv) > 1 else "nanobot-1"
AGENT_DIR = Path(f"/root/.openclaw/workspace/projects/nanobot/agents/{AGENT_ID}")
LOG_FILE = Path(f"/root/.openclaw/workspace/projects/nanobot/logs/{AGENT_ID}.log")
WORKSPACE_DIR = Path("/root/.openclaw/workspace")
HUB_DIR = WORKSPACE_DIR / "projects/nanobot/hub"

# 加载环境变量
env_file = AGENT_DIR / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

API_KEY = os.getenv("NVIDIA_API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL = os.getenv("MODEL_PRIORITY_1", "stepfun-ai/step-3.5-flash")

# 加载身份
IDENTITY_FILE = AGENT_DIR / ".env"
if IDENTITY_FILE.exists():
    with open(IDENTITY_FILE) as f:
        IDENTITY = json.load(f)
else:
    IDENTITY = {"id": AGENT_ID, "name": AGENT_ID, "role": "assistant", "capabilities": []}

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{AGENT_ID}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

class AgentCommunication:
    """Agent通信管理器 - v4.1修复版"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.processed_msgs = set()
        self.last_check_time = datetime.now()
    
    def _generate_msg_id(self) -> str:
        import hashlib
        ts = datetime.now().isoformat()
        return hashlib.md5(f"{self.agent_id}:{ts}".encode()).hexdigest()[:12]
    
    def send_group_message(self, content: str, mentions: List[str] = None) -> bool:
        """发送群聊消息"""
        try:
            msg = {
                "id": self._generate_msg_id(),
                "type": "group_chat",
                "from": self.agent_id,
                "to": "all",
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "mentions": mentions or []
            }
            
            with open(HUB_DIR / "group_chat.jsonl", "a") as f:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            
            log(f"📢 群聊: {content[:50]}")
            return True
        except Exception as e:
            log(f"❌ 群聊发送失败: {e}")
            return False
    
    def send_private_message(self, to: str, content: str) -> bool:
        """发送私信"""
        try:
            msg = {
                "id": self._generate_msg_id(),
                "type": "private",
                "from": self.agent_id,
                "to": to,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            
            inbox_file = HUB_DIR / f"private_chat/{to}_inbox.jsonl"
            with open(inbox_file, "a") as f:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            
            log(f"📨 私信给 {to}: {content[:50]}")
            return True
        except Exception as e:
            log(f"❌ 私信发送失败: {e}")
            return False
    
    def check_group_messages(self) -> List[Dict]:
        """检查群聊消息 - 修复版"""
        messages = []
        try:
            group_chat_file = HUB_DIR / "group_chat.jsonl"
            if not group_chat_file.exists():
                return messages
            
            with open(group_chat_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        msg = json.loads(line)
                        # 修复：确保是字典而不是列表
                        if not isinstance(msg, dict):
                            continue
                        
                        msg_id = msg.get("id", "")
                        if msg_id in self.processed_msgs:
                            continue
                        if msg.get("from") == self.agent_id:
                            self.processed_msgs.add(msg_id)
                            continue
                        
                        messages.append(msg)
                        self.processed_msgs.add(msg_id)
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            log(f"检查群聊消息失败: {e}")
        
        return messages
    
    def check_private_messages(self) -> List[Dict]:
        """检查私信 - 修复版"""
        messages = []
        try:
            inbox_file = HUB_DIR / f"private_chat/{self.agent_id}_inbox.jsonl"
            if not inbox_file.exists():
                return messages
            
            with open(inbox_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        msg = json.loads(line)
                        # 修复：确保是字典
                        if not isinstance(msg, dict):
                            continue
                        
                        msg_id = msg.get("id", "")
                        if msg_id in self.processed_msgs:
                            continue
                        
                        messages.append(msg)
                        self.processed_msgs.add(msg_id)
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            log(f"检查私信失败: {e}")
        
        return messages
    
    def should_respond(self, msg: Dict) -> bool:
        """判断是否应该回复"""
        mentions = msg.get("mentions", [])
        if self.agent_id in mentions:
            return True
        
        content = msg.get("content", "")
        if f"@{self.agent_id}" in content:
            return True
        
        if msg.get("type") == "private":
            return True
        
        # 群聊中随机回复（5%概率）
        import random
        if random.random() < 0.05:
            return True
        
        return False
    
    def generate_reply_offline(self, msg: Dict) -> str:
        """离线模式生成回复"""
        from_agent = msg.get("from", "unknown")
        content = msg.get("content", "")
        
        # 简单的回复模板
        replies = [
            f"@{from_agent} 收到！",
            f"@{from_agent} 明白，正在处理。",
            f"@{from_agent} 好的，我同意。",
            f"@{from_agent} 有意思！",
            f"@{from_agent} 了解了，谢谢分享。"
        ]
        
        import random
        return random.choice(replies)

class NanobotAgent:
    """Nanobot Agent - v4.1 修复版"""
    
    def __init__(self):
        self.id = AGENT_ID
        self.name = IDENTITY.get("name", AGENT_ID)
        self.role = IDENTITY.get("role", "assistant")
        self.communication = AgentCommunication(AGENT_ID)
        self._running = False
    
    async def handle_communication(self):
        """处理通信"""
        while self._running:
            try:
                # 检查群聊
                group_msgs = self.communication.check_group_messages()
                for msg in group_msgs:
                    if self.communication.should_respond(msg):
                        reply = self.communication.generate_reply_offline(msg)
                        self.communication.send_group_message(reply)
                        await asyncio.sleep(1)  # 避免消息风暴
                
                # 检查私信
                private_msgs = self.communication.check_private_messages()
                for msg in private_msgs:
                    reply = self.communication.generate_reply_offline(msg)
                    sender = msg.get("from", "unknown")
                    self.communication.send_private_message(sender, reply)
                    await asyncio.sleep(1)
                
                await asyncio.sleep(3)
                
            except Exception as e:
                log(f"通信错误: {e}")
                await asyncio.sleep(5)
    
    async def run(self):
        """主循环"""
        log(f"🚀 {self.name} ({self.id}) 启动 - v4.1 修复版")
        log(f"   角色: {self.role}")
        self._running = True
        
        # 发送上线通知
        await asyncio.sleep(1)  # 等待其他Agent启动
        self.communication.send_group_message(f"👋 大家好！我是{self.id}，已加入群聊。")
        
        # 启动通信处理
        comm_task = asyncio.create_task(self.handle_communication())
        
        try:
            while self._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False
            comm_task.cancel()
            log(f"👋 {self.name} 已离线")

if __name__ == "__main__":
    agent = NanobotAgent()
    asyncio.run(agent.run())
