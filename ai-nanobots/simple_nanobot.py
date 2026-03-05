#!/usr/bin/env python3
"""
简化版AI Nanobot - 专注于relay通信
基于Step 3.5 Flash或DeepSeek V3.2
"""

import os
import sys
import json
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path

# 配置
NB_ID = sys.argv[1] if len(sys.argv) > 1 else "nanobot-1"
NB_DIR = Path(f"/root/.openclaw/workspace/ai-nanobots/{NB_ID}")
LOG_FILE = NB_DIR / f"{NB_ID}.log"
RELAY_URL = "http://127.0.0.1:19000"

# 加载.env文件
def load_env():
    """手动加载.env文件"""
    env_file = NB_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

# 加载身份配置
IDENTITY_FILE = NB_DIR / "identity.json"
if IDENTITY_FILE.exists():
    with open(IDENTITY_FILE) as f:
        IDENTITY = json.load(f)
else:
    IDENTITY = {
        "id": NB_ID,
        "name": NB_ID,
        "role": "assistant",
        "model": "step-3.5-flash",
        "description": "AI assistant"
    }

def log(msg):
    """记录日志"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{NB_ID}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

class SimpleNanobot:
    """简化版Nanobot"""
    
    def __init__(self):
        self.id = NB_ID
        self.name = IDENTITY.get("name", NB_ID)
        self.role = IDENTITY.get("role", "assistant")
        self.model = IDENTITY.get("model", "step-3.5-flash")
        self.api_key = os.getenv("NVIDIA_API_KEY", "")
        
    async def ai_chat(self, message: str) -> str:
        """调用AI模型生成回复"""
        try:
            # 根据模型选择不同的API
            if "deepseek" in self.model.lower():
                # DeepSeek API
                base_url = "https://api.deepseek.com/v1"
                model_id = "deepseek-chat"
            else:
                # NVIDIA/Step API
                base_url = "https://integrate.api.nvidia.com/v1"
                model_id = "stepfun-ai/step-3.5-flash"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": model_id,
                        "messages": [
                            {"role": "system", "content": f"你是{self.name}，角色是{self.role}。请简洁回答。"},
                            {"role": "user", "content": message}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=30
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        error_text = await resp.text()
                        return f"[AI错误] 状态码: {resp.status}, 错误: {error_text[:100]}"
        except Exception as e:
            return f"[AI错误] {str(e)}"
    
    async def handle_message(self, msg_data: dict):
        """处理收到的消息"""
        message = msg_data.get("message", "")
        from_bot = msg_data.get("from", "unknown")
        
        log(f"收到来自 {from_bot} 的消息: {message[:50]}...")
        
        # 本地命令处理
        cmd_lower = message.strip().lower()
        
        if cmd_lower in ["status", "状态"]:
            response = f"📊 {self.name} 状态:\n模型: {self.model}\n角色: {self.role}\n状态: 运行中"
        elif cmd_lower in ["help", "帮助", "?"]:
            response = f"🤖 {self.name} 命令:\n• status - 查看状态\n• ping - 测试连通\n• help - 显示帮助\n其他消息将使用AI回复"
        elif cmd_lower == "ping":
            response = f"pong from {self.id}"
        else:
            # 使用AI生成回复
            log("调用AI生成回复...")
            response = await self.ai_chat(message)
        
        # 发送回复到relay
        await self.send_to_relay(response, to=from_bot)
        log(f"回复: {response[:100]}...")
    
    async def send_to_relay(self, message: str, to: str = "openclaw"):
        """发送消息到relay"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "from": self.id,
                    "to": to,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                async with session.post(f"{RELAY_URL}/message", json=payload) as resp:
                    return resp.status == 200
        except Exception as e:
            log(f"发送失败: {e}")
            return False
    
    async def run(self):
        """主运行循环"""
        log(f"🚀 {self.name} ({self.id}) 启动")
        log(f"🧠 模型: {self.model}")
        log(f"🎯 角色: {self.role}")
        log("进入消息轮询模式...")
        
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{RELAY_URL}/poll/{self.id}") as resp:
                        if resp.status == 200:
                            messages = await resp.json()
                            for msg in messages:
                                await self.handle_message(msg)
                                
                await asyncio.sleep(3)
                
            except KeyboardInterrupt:
                log("收到中断信号，退出...")
                break
            except Exception as e:
                log(f"轮询错误: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    bot = SimpleNanobot()
    asyncio.run(bot.run())
