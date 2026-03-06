#!/usr/bin/env python3
"""
Nanobot AI Agent - v4.0 群聊通信版
支持：群聊、私信、@功能
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
IDENTITY_FILE = AGENT_DIR / "identity.json"
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
    """Agent通信管理器"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.last_group_msg_id = ""
        self.last_private_msg_id = ""
        self.processed_msgs = set()
    
    def _generate_msg_id(self) -> str:
        """生成消息ID"""
        import hashlib
        ts = datetime.now().isoformat()
        return hashlib.md5(f"{self.agent_id}:{ts}".encode()).hexdigest()[:12]
    
    def send_group_message(self, content: str, mentions: List[str] = None, reply_to: str = None) -> bool:
        """发送群聊消息"""
        try:
            msg = {
                "id": self._generate_msg_id(),
                "type": "group_chat",
                "from": self.agent_id,
                "to": "all",
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "mentions": mentions or [],
                "reply_to": reply_to
            }
            
            # 追加到群聊文件
            with open(HUB_DIR / "group_chat.jsonl", "a") as f:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            
            log(f"📢 群聊消息已发送: {content[:50]}...")
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
                "timestamp": datetime.now().isoformat(),
                "read": False
            }
            
            # 写入对方收件箱
            inbox_file = HUB_DIR / f"private_chat/{to}_inbox.jsonl"
            with open(inbox_file, "a") as f:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            
            log(f"📨 私信已发送给 {to}: {content[:50]}...")
            return True
            
        except Exception as e:
            log(f"❌ 私信发送失败: {e}")
            return False
    
    def check_group_messages(self) -> List[Dict]:
        """检查群聊消息"""
        messages = []
        try:
            group_chat_file = HUB_DIR / "group_chat.jsonl"
            if not group_chat_file.exists():
                return messages
            
            with open(group_chat_file, "r") as f:
                for line in f:
                    try:
                        msg = json.loads(line.strip())
                        msg_id = msg.get("id", "")
                        
                        # 跳过已处理的消息
                        if msg_id in self.processed_msgs:
                            continue
                        
                        # 跳过自己发送的消息
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
        """检查私信"""
        messages = []
        try:
            inbox_file = HUB_DIR / f"private_chat/{self.agent_id}_inbox.jsonl"
            if not inbox_file.exists():
                return messages
            
            with open(inbox_file, "r") as f:
                for line in f:
                    try:
                        msg = json.loads(line.strip())
                        msg_id = msg.get("id", "")
                        
                        # 跳过已处理的
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
        """判断是否应该回复该消息"""
        # 自己被@了
        mentions = msg.get("mentions", [])
        if self.agent_id in mentions:
            return True
        
        # 消息内容中包含@自己
        content = msg.get("content", "")
        if f"@{self.agent_id}" in content:
            return True
        
        # 私信总是回复
        if msg.get("type") == "private":
            return True
        
        # 群聊中随机回复（10%概率）或包含关键词
        if "讨论" in content or "问题" in content or "大家" in content:
            return True
        
        return False
    
    async def generate_reply(self, msg: Dict) -> str:
        """生成回复内容"""
        from_agent = msg.get("from", "unknown")
        content = msg.get("content", "")
        msg_type = msg.get("type", "group_chat")
        
        # 构建回复提示
        prompt = f"""你是{self.agent_id}（{IDENTITY.get('role', 'AI助手')}），正在参与群聊。

{from_agent} 说："{content}"

请生成一个简短、友好的回复（不超过100字）："""
        
        if not API_KEY:
            # 离线回复模板
            replies = [
                f"@{from_agent} 收到，正在处理中。",
                f"@{from_agent} 明白，让我想想。",
                f"@{from_agent} 好的，我同意这个观点。",
                f"@{from_agent} 有意思，继续说。",
            ]
            import random
            return random.choice(replies)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 150,
                        "temperature": 0.7
                    },
                    timeout=30
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        reply = data["choices"][0]["message"].get("content", "")
                        return reply.strip()
        except Exception as e:
            log(f"生成回复失败: {e}")
        
        return f"@{from_agent} 收到！"

class NanobotAgent:
    """Nanobot Agent - v4.0 群聊版"""
    
    def __init__(self):
        self.id = AGENT_ID
        self.name = IDENTITY.get("name", AGENT_ID)
        self.role = IDENTITY.get("role", "assistant")
        self.communication = AgentCommunication(AGENT_ID)
        self._running = False
    
    async def handle_communication(self):
        """处理通信（异步任务）"""
        while self._running:
            try:
                # 1. 检查群聊消息
                group_msgs = self.communication.check_group_messages()
                for msg in group_msgs:
                    if self.communication.should_respond(msg):
                        reply = await self.communication.generate_reply(msg)
                        self.communication.send_group_message(reply)
                
                # 2. 检查私信
                private_msgs = self.communication.check_private_messages()
                for msg in private_msgs:
                    reply = await self.communication.generate_reply(msg)
                    sender = msg.get("from", "unknown")
                    self.communication.send_private_message(sender, reply)
                
                # 3. 休眠
                await asyncio.sleep(2)
                
            except Exception as e:
                log(f"通信处理错误: {e}")
                await asyncio.sleep(5)
    
    async def run(self):
        """主循环"""
        log(f"🚀 {self.name} ({self.id}) 启动 - v4.0 群聊通信版")
        log(f"   角色: {self.role}")
        log(f"   能力: 群聊、私信、@功能")
        self._running = True
        
        # 发送上线通知
        self.communication.send_group_message(f"👋 大家好！我是{self.id}，已加入群聊。")
        
        # 启动通信处理任务
        comm_task = asyncio.create_task(self.handle_communication())
        
        # 保持运行
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
