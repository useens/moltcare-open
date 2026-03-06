#!/usr/bin/env python3
"""
Nanobot AI Agent - v4.2 限流版
添加LLM请求限流控制
"""
import os
import sys
import json
import asyncio
import aiohttp
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import threading

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

class RateLimiter:
    """全局限流器 - 控制LLM请求频率"""
    
    # 类变量，所有Agent共享
    _last_request_time = 0
    _min_interval = 5.0  # 最小间隔5秒
    _lock = threading.Lock()
    
    @classmethod
    def can_request(cls) -> bool:
        """检查是否可以发送请求"""
        with cls._lock:
            current_time = time.time()
            if current_time - cls._last_request_time >= cls._min_interval:
                cls._last_request_time = current_time
                return True
            return False
    
    @classmethod
    def wait_time(cls) -> float:
        """返回需要等待的时间"""
        with cls._lock:
            current_time = time.time()
            elapsed = current_time - cls._last_request_time
            if elapsed >= cls._min_interval:
                return 0
            return cls._min_interval - elapsed

class AgentCommunication:
    """Agent通信管理器 - v4.2限流版"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.processed_msgs = set()
        self.reply_cache = {}  # 缓存回复避免重复生成
    
    def _generate_msg_id(self) -> str:
        import hashlib
        ts = datetime.now().isoformat()
        return hashlib.md5(f"{self.agent_id}:{ts}".encode()).hexdigest()[:12]
    
    def send_group_message(self, content: str, mentions: List[str] = None) -> bool:
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
        mentions = msg.get("mentions", [])
        if self.agent_id in mentions:
            return True
        
        content = msg.get("content", "")
        if f"@{self.agent_id}" in content:
            return True
        
        if msg.get("type") == "private":
            return True
        
        # 群聊中随机回复（3%概率降低频率）
        import random
        if random.random() < 0.03:
            return True
        
        return False
    
    async def generate_reply(self, msg: Dict) -> str:
        """生成回复 - 带限流控制"""
        from_agent = msg.get("from", "unknown")
        content = msg.get("content", "")
        
        # 生成缓存key
        cache_key = f"{from_agent}:{content[:50]}"
        if cache_key in self.reply_cache:
            return self.reply_cache[cache_key]
        
        # 检查限流
        if not RateLimiter.can_request():
            wait = RateLimiter.wait_time()
            log(f"⏳ 限流等待 {wait:.1f}s")
            await asyncio.sleep(wait)
        
        # 尝试使用LLM
        if API_KEY:
            try:
                prompt = f"""你是{self.agent_id}（{IDENTITY.get('role', 'AI助手')}），正在群聊中回复{from_agent}。

{from_agent}说："{content}"

请生成一个简短、友好、有个性的回复（20-40字）："""
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{BASE_URL}/chat/completions",
                        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                        json={
                            "model": MODEL,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 80,
                            "temperature": 0.7
                        },
                        timeout=15
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            reply = data["choices"][0]["message"].get("content", "").strip()
                            if reply:
                                result = f"@{from_agent} {reply}"
                                self.reply_cache[cache_key] = result
                                return result
                        elif resp.status == 429:
                            log("⚠️ 触发API限流，使用模板回复")
                        else:
                            log(f"⚠️ API错误 {resp.status}")
            except Exception as e:
                log(f"⚠️ LLM调用失败: {e}")
        
        # 回退到模板
        result = self.generate_reply_offline(msg)
        self.reply_cache[cache_key] = result
        return result
    
    def generate_reply_offline(self, msg: Dict) -> str:
        """离线模板回复"""
        from_agent = msg.get("from", "unknown")
        
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
    """Nanobot Agent - v4.2 限流版"""
    
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
                        reply = await self.communication.generate_reply(msg)
                        self.communication.send_group_message(reply)
                        await asyncio.sleep(3)  # 增加间隔避免频率过高
                
                # 检查私信
                private_msgs = self.communication.check_private_messages()
                for msg in private_msgs:
                    reply = await self.communication.generate_reply(msg)
                    sender = msg.get("from", "unknown")
                    self.communication.send_private_message(sender, reply)
                    await asyncio.sleep(3)
                
                await asyncio.sleep(5)  # 增加检查间隔
                
            except Exception as e:
                log(f"通信错误: {e}")
                await asyncio.sleep(10)
    
    async def run(self):
        """主循环"""
        log(f"🚀 {self.name} ({self.id}) 启动 - v4.2 限流版")
        log(f"   角色: {self.role}")
        log(f"   限流: 5秒间隔 + 全局控制")
        self._running = True
        
        # 发送上线通知
        await asyncio.sleep(2)
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
