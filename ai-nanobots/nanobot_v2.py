#!/usr/bin/env python3
"""
Nanobot V2 - 具备执行能力的AI助手
支持工具调用：exec, read, write, web_fetch等
"""

import os
import sys
import json
import asyncio
import aiohttp
import subprocess
from datetime import datetime
from pathlib import Path

# 配置
NB_ID = sys.argv[1] if len(sys.argv) > 1 else "nanobot-1"
NB_DIR = Path(f"/root/.openclaw/workspace/ai-nanobots/{NB_ID}")
LOG_FILE = NB_DIR / f"{NB_ID}.log"
RELAY_URL = "http://127.0.0.1:19000"
WORKSPACE_DIR = Path("/root/.openclaw/workspace")

# 安全边界
ALLOWED_COMMANDS = [
    "ls", "cat", "grep", "find", "wc", "head", "tail",
    "python3", "pip", "curl", "wget",
    "ps", "top", "df", "du", "free"
]
FORBIDDEN_PATTERNS = [
    "rm -rf /", "mkfs", "dd if=/dev/zero", 
    "> /etc/passwd", "> /etc/shadow",
    ":(){:|:"  # fork bomb
]

def load_env():
    """加载环境变量"""
    env_file = NB_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

# 加载身份
IDENTITY_FILE = NB_DIR / "identity.json"
if IDENTITY_FILE.exists():
    with open(IDENTITY_FILE) as f:
        IDENTITY = json.load(f)
else:
    IDENTITY = {"id": NB_ID, "name": NB_ID, "role": "assistant", "model": "step-3.5-flash"}

def log(msg):
    """记录日志"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{NB_ID}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

class ToolExecutor:
    """工具执行器 - 赋予小弟们实际能力"""
    
    def __init__(self, nb_id):
        self.nb_id = nb_id
        self.workspace = WORKSPACE_DIR / f"nanobot-workspace/{nb_id}"
        self.workspace.mkdir(parents=True, exist_ok=True)
    
    def validate_command(self, cmd):
        """验证命令安全性"""
        cmd_lower = cmd.lower().strip()
        
        # 检查禁止模式
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in cmd_lower:
                return False, f"禁止执行危险命令: {pattern}"
        
        # 检查允许命令
        cmd_parts = cmd.split()
        if cmd_parts and cmd_parts[0] not in ALLOWED_COMMANDS:
            return False, f"命令 '{cmd_parts[0]}' 不在白名单中"
        
        return True, "OK"
    
    async def exec_command(self, command, cwd=None):
        """执行系统命令"""
        # 验证
        valid, reason = self.validate_command(command)
        if not valid:
            return f"❌ 安全拦截: {reason}"
        
        try:
            work_dir = cwd or str(self.workspace)
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""
            
            if process.returncode == 0:
                return f"✅ 执行成功:\n{output[:500]}"
            else:
                return f"⚠️ 执行失败 (code {process.returncode}):\n{error[:300] or output[:300]}"
        except asyncio.TimeoutError:
            return "⏱️ 执行超时 (>30秒)"
        except Exception as e:
            return f"❌ 执行异常: {str(e)}"
    
    async def read_file(self, filepath):
        """读取文件"""
        try:
            path = Path(filepath)
            # 限制在工作目录
            if not str(path.resolve()).startswith(str(WORKSPACE_DIR)):
                return "❌ 路径超出工作目录"
            
            if not path.exists():
                return f"❌ 文件不存在: {filepath}"
            
            content = path.read_text()
            return f"📄 文件内容 ({len(content)} 字符):\n```\n{content[:1000]}\n```"
        except Exception as e:
            return f"❌ 读取失败: {str(e)}"
    
    async def write_file(self, filepath, content):
        """写入文件"""
        try:
            path = Path(filepath)
            # 限制在工作目录
            if not str(path.resolve()).startswith(str(WORKSPACE_DIR)):
                return "❌ 路径超出工作目录"
            
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return f"✅ 文件已写入: {filepath} ({len(content)} 字符)"
        except Exception as e:
            return f"❌ 写入失败: {str(e)}"
    
    async def web_fetch(self, url):
        """获取网页内容"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        return f"🌐 获取成功 ({len(text)} 字符):\n{text[:800]}"
                    else:
                        return f"⚠️ HTTP {resp.status}"
        except Exception as e:
            return f"❌ 获取失败: {str(e)}"
    
    async def execute_tool(self, tool_name, params):
        """执行工具"""
        if tool_name == "exec":
            return await self.exec_command(params.get("command", ""))
        elif tool_name == "read":
            return await self.read_file(params.get("path", ""))
        elif tool_name == "write":
            return await self.write_file(params.get("path", ""), params.get("content", ""))
        elif tool_name == "web_fetch":
            return await self.web_fetch(params.get("url", ""))
        else:
            return f"❌ 未知工具: {tool_name}"

class NanobotV2:
    """具备执行能力的Nanobot V2"""
    
    def __init__(self):
        self.id = NB_ID
        self.name = IDENTITY.get("name", NB_ID)
        self.role = IDENTITY.get("role", "assistant")
        self.model = IDENTITY.get("model", "step-3.5-flash")
        self.api_key = os.getenv("NVIDIA_API_KEY", "")
        self.tools = ToolExecutor(NB_ID)
    
    async def ai_chat_with_tools(self, message):
        """AI对话，可能触发工具调用"""
        # 检测是否需要工具
        tool_prompt = f"""作为{self.name}({self.role})，分析用户请求：
        
用户请求: {message}

如果需要执行操作，请以JSON格式返回工具调用：
{{
    "tool": "exec|read|write|web_fetch",
    "params": {{...}}
}}

如果不需要工具，直接回答。

可用工具：
- exec: 执行系统命令 (ls, cat, grep, python3等)
- read: 读取文件
- write: 写入文件
- web_fetch: 获取网页内容

安全限制：禁止危险命令(rm -rf /, mkfs等)，只能操作工作目录。"""

        # 调用AI
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "stepfun-ai/step-3.5-flash",
                        "messages": [
                            {"role": "system", "content": "你是AI助手，可以调用工具执行任务。"},
                            {"role": "user", "content": tool_prompt}
                        ],
                        "max_tokens": 800,
                        "temperature": 0.3
                    },
                    timeout=30
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        ai_response = data["choices"][0]["message"]["content"]
                        
                        # 检测是否包含工具调用
                        try:
                            # 尝试解析JSON工具调用
                            if '"tool"' in ai_response and '"params"' in ai_response:
                                import re
                                json_match = re.search(r'\{[^}]*"tool"[^}]*\}', ai_response, re.DOTALL)
                                if json_match:
                                    tool_call = json.loads(json_match.group())
                                    tool_name = tool_call.get("tool")
                                    params = tool_call.get("params", {})
                                    
                                    # 执行工具
                                    tool_result = await self.tools.execute_tool(tool_name, params)
                                    
                                    # 返回工具执行结果
                                    return f"🛠️ 执行工具 [{tool_name}]:\n{tool_result}"
                        except:
                            pass
                        
                        # 普通回复
                        return ai_response
                    else:
                        error = await resp.text()
                        return f"[AI错误] {resp.status}: {error[:100]}"
        except Exception as e:
            return f"[AI错误] {str(e)}"
    
    async def handle_message(self, msg_data):
        """处理消息"""
        message = msg_data.get("message", "")
        from_bot = msg_data.get("from", "unknown")
        
        log(f"收到来自 {from_bot}: {message[:50]}...")
        
        # 简单命令
        cmd = message.strip().lower()
        if cmd == "ping":
            response = f"pong from {self.id} (V2 with tools)"
        elif cmd == "status":
            response = f"✅ {self.name} | 角色: {self.role} | 模型: {self.model} | 工具就绪"
        elif cmd in ["help", "?"]:
            response = """🛠️ 可用工具：
• exec: 执行命令 (ls, cat, python3...)
• read: 读取文件
• write: 写入文件  
• web_fetch: 获取网页

示例：
"列出当前目录"
"读取 /path/to/file"
"获取 https://example.com"""
        else:
            # AI处理，可能触发工具
            response = await self.ai_chat_with_tools(message)
        
        # 发送回复
        await self.send_to_relay(response, to=from_bot)
        log(f"回复: {response[:100]}...")
    
    async def send_to_relay(self, message, to="openclaw"):
        """发送到relay"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "from": self.id,
                    "to": to,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                await session.post(f"{RELAY_URL}/message", json=payload)
        except Exception as e:
            log(f"发送失败: {e}")
    
    async def run(self):
        """主循环"""
        log(f"🚀 {self.name} (V2) 启动")
        log(f"🛠️ 工具能力: exec, read, write, web_fetch")
        
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
                break
            except Exception as e:
                log(f"错误: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    bot = NanobotV2()
    asyncio.run(bot.run())
