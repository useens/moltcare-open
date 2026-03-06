#!/usr/bin/env python3
"""
Nanobot AI Agent - 真正的AI代理
项目: nanobot
"""
import os
import sys
import json
import asyncio
import aiohttp
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

# 配置
AGENT_ID = sys.argv[1] if len(sys.argv) > 1 else "nanobot-1"
AGENT_DIR = Path(f"/root/.openclaw/workspace/projects/nanobot/agents/{AGENT_ID}")
LOG_FILE = Path(f"/root/.openclaw/workspace/projects/nanobot/logs/{AGENT_ID}.log")
WORKSPACE_DIR = Path("/root/.openclaw/workspace")

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
    IDENTITY = {
        "id": AGENT_ID,
        "name": AGENT_ID,
        "role": "assistant",
        "capabilities": [],
        "system_prompt": "你是一个AI助手。"
    }

def log(msg: str):
    """记录日志"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{AGENT_ID}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

class ToolExecutor:
    """工具执行器 - 赋予Agent实际能力"""
    
    ALLOWED_COMMANDS = [
        "ls", "cat", "grep", "find", "wc", "head", "tail",
        "python3", "pip", "ps", "top", "df", "du", "free",
        "git", "curl", "wget"
    ]
    
    FORBIDDEN_PATTERNS = [
        "rm -rf /", "mkfs", "dd if=/dev/zero",
        "> /etc/passwd", "> /etc/shadow"
    ]
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.workspace = WORKSPACE_DIR / f"projects/nanobot/workspaces/{agent_id}"
        self.workspace.mkdir(parents=True, exist_ok=True)
    
    def validate_command(self, cmd: str) -> tuple:
        """验证命令安全性"""
        cmd_lower = cmd.lower().strip()
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in cmd_lower:
                return False, f"禁止执行危险命令: {pattern}"
        
        cmd_parts = cmd.split()
        if cmd_parts and cmd_parts[0] not in self.ALLOWED_COMMANDS:
            return False, f"命令 '{cmd_parts[0]}' 不在白名单中"
        
        return True, "OK"
    
    async def exec(self, command: str) -> str:
        """执行系统命令"""
        valid, reason = self.validate_command(command)
        if not valid:
            return f"❌ 安全拦截: {reason}"
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace)
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            
            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""
            
            if process.returncode == 0:
                return f"✅ 执行成功:\n{output[:1000]}"
            else:
                return f"⚠️ 执行失败:\n{error[:500] or output[:500]}"
        except asyncio.TimeoutError:
            return "⏱️ 执行超时 (>60秒)"
        except Exception as e:
            return f"❌ 执行异常: {str(e)}"
    
    async def read(self, filepath: str) -> str:
        """读取文件"""
        try:
            path = Path(filepath)
            if not path.exists():
                return f"❌ 文件不存在: {filepath}"
            content = path.read_text()
            return f"📄 文件内容 ({len(content)} 字符):\n```\n{content[:2000]}\n```"
        except Exception as e:
            return f"❌ 读取失败: {str(e)}"
    
    async def write(self, filepath: str, content: str) -> str:
        """写入文件"""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return f"✅ 文件已写入: {filepath}"
        except Exception as e:
            return f"❌ 写入失败: {str(e)}"
    
    async def web_fetch(self, url: str) -> str:
        """获取网页"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        return f"🌐 获取成功 ({len(text)} 字符):\n{text[:1500]}"
                    else:
                        return f"⚠️ HTTP {resp.status}"
        except Exception as e:
            return f"❌ 获取失败: {str(e)}"

class NanobotAgent:
    """真正的AI Agent"""
    
    def __init__(self):
        self.id = AGENT_ID
        self.name = IDENTITY.get("name", AGENT_ID)
        self.role = IDENTITY.get("role", "assistant")
        self.capabilities = IDENTITY.get("capabilities", [])
        self.system_prompt = IDENTITY.get("system_prompt", "")
        self.tools = ToolExecutor(AGENT_ID)
        self._running = False
        self.message_queue = asyncio.Queue()
        
    async def llm_chat(self, message: str, tools_available: bool = True) -> str:
        """调用LLM"""
        if not API_KEY:
            return "[错误] 未配置API密钥"
        
        tool_descriptions = """
你可以使用以下工具来完成任务：
1. exec: 执行系统命令 (ls, cat, grep, python3等)
   使用格式: {"tool": "exec", "params": {"command": "命令"}}
   
2. read: 读取文件
   使用格式: {"tool": "read", "params": {"path": "/path/to/file"}}
   
3. write: 写入文件
   使用格式: {"tool": "write", "params": {"path": "/path/to/file", "content": "内容"}}
   
4. web_fetch: 获取网页内容
   使用格式: {"tool": "web_fetch", "params": {"url": "https://example.com"}}

如果需要使用工具，请在回复中包含JSON格式的工具调用。
如果不需要工具，直接回答即可。
""" if tools_available else ""
        
        prompt = f"""{self.system_prompt}

{tool_descriptions}

当前任务: {message}

请根据你的角色和能力处理这个任务。
角色: {self.role}
能力: {', '.join(self.capabilities)}

注意:
- 直接回答，不要使用"好的"、"我来帮你"等客套话
- 如果需要执行操作，使用工具调用JSON格式
- 保持简洁，只输出必要内容
"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    json={
                        "model": MODEL,
                        "messages": [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.3
                    },
                    timeout=60
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        error = await resp.text()
                        return f"[API错误] {resp.status}: {error[:200]}"
        except Exception as e:
            return f"[错误] {str(e)}"
    
    async def process_task(self, task_type: str, task_data: dict) -> dict:
        """处理任务"""
        log(f"开始处理任务: {task_type}")
        
        # 构建任务描述
        task_desc = task_data.get("description", f"执行 {task_type}")
        
        # 调用LLM
        response = await self.llm_chat(task_desc)
        
        # 检测是否需要工具
        result = await self._handle_tool_calls(response)
        
        log(f"任务完成: {task_type}")
        return {
            "status": "completed",
            "result": result,
            "agent": self.id
        }
    
    async def _handle_tool_calls(self, response: str) -> str:
        """处理工具调用"""
        import re
        
        # 查找JSON工具调用
        json_pattern = r'\{[^{}]*"tool"[^{}]*\}'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        if not matches:
            return response
        
        results = []
        for match in matches:
            try:
                tool_call = json.loads(match)
                tool_name = tool_call.get("tool")
                params = tool_call.get("params", {})
                
                log(f"执行工具: {tool_name}")
                
                if tool_name == "exec":
                    result = await self.tools.exec(params.get("command", ""))
                elif tool_name == "read":
                    result = await self.tools.read(params.get("path", ""))
                elif tool_name == "write":
                    result = await self.tools.write(params.get("path", ""), params.get("content", ""))
                elif tool_name == "web_fetch":
                    result = await self.tools.web_fetch(params.get("url", ""))
                else:
                    result = f"❌ 未知工具: {tool_name}"
                
                results.append(f"[工具:{tool_name}]\n{result}")
                
            except json.JSONDecodeError:
                continue
        
        if results:
            return response + "\n\n" + "\n\n".join(results)
        
        return response
    
    async def run(self):
        """主循环"""
        log(f"🚀 {self.name} ({self.id}) 启动")
        log(f"   角色: {self.role}")
        log(f"   能力: {', '.join(self.capabilities)}")
        self._running = True
        
        # 注册到神经中枢
        await self._register_to_hub()
        
        # 已处理的任务ID记录
        processed_tasks = set()
        
        while self._running:
            try:
                # 检查文件队列中的新任务
                task = self._check_task_queue(processed_tasks)
                if task:
                    await self._handle_task(task)
                else:
                    # 没有新任务，等待一下
                    await asyncio.sleep(3)
                    
                # 定期心跳
                await self._heartbeat()
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                log(f"错误: {e}")
                await asyncio.sleep(5)
        
        log(f"👋 {self.name} 已停止")
    
    def _check_task_queue(self, processed_tasks: set) -> dict:
        """检查文件队列中的任务"""
        task_file = WORKSPACE_DIR / "projects/nanobot/hub/tasks.jsonl"
        
        if not task_file.exists():
            return None
        
        try:
            with open(task_file) as f:
                lines = f.readlines()
            
            for line in lines:
                try:
                    task = json.loads(line)
                    task_id = f"{task.get('agent_id')}:{task.get('timestamp')}"
                    
                    # 检查是否是给自己的任务且未处理
                    if (task.get("agent_id") == self.id and 
                        task_id not in processed_tasks):
                        processed_tasks.add(task_id)
                        return task
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            log(f"读取任务队列错误: {e}")
        
        return None
    
    async def _register_to_hub(self):
        """注册到神经中枢"""
        # 通过文件或Redis注册
        reg_file = WORKSPACE_DIR / "projects/nanobot/hub/registrations.jsonl"
        reg_file.parent.mkdir(parents=True, exist_ok=True)
        
        reg_data = {
            "type": "register",
            "agent_id": self.id,
            "name": self.name,
            "role": self.role,
            "capabilities": self.capabilities,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(reg_file, "a") as f:
            f.write(json.dumps(reg_data) + "\n")
        
        log("已注册到神经中枢")
    
    async def _heartbeat(self):
        """心跳"""
        hb_file = WORKSPACE_DIR / "projects/nanobot/hub/heartbeat.jsonl"
        hb_file.parent.mkdir(parents=True, exist_ok=True)
        
        hb_data = {
            "agent_id": self.id,
            "status": "alive",
            "timestamp": datetime.now().isoformat()
        }
        
        with open(hb_file, "a") as f:
            f.write(json.dumps(hb_data) + "\n")
    
    async def _handle_task(self, task: dict):
        """处理任务"""
        task_type = task.get("type")
        task_data = task.get("data", {})
        
        result = await self.process_task(task_type, task_data)
        
        # 报告结果
        result_file = WORKSPACE_DIR / "projects/nanobot/hub/results.jsonl"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        result_data = {
            "agent_id": self.id,
            "task_type": task_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(result_file, "a") as f:
            f.write(json.dumps(result_data) + "\n")
    
    def stop(self):
        """停止Agent"""
        self._running = False

if __name__ == "__main__":
    agent = NanobotAgent()
    
    # 信号处理
    import signal
    def signal_handler(sig, frame):
        agent.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    asyncio.run(agent.run())
