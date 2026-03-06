#!/usr/bin/env python3
"""
Nanobot AI Agent - 修复版
修复了API调用403问题
"""
import os
import sys
import json
import asyncio
import aiohttp
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

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
    IDENTITY = {"id": AGENT_ID, "name": AGENT_ID, "role": "assistant", "capabilities": [], "system_prompt": "你是一个AI助手。"}

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{AGENT_ID}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

class ToolExecutor:
    ALLOWED_COMMANDS = ["ls", "cat", "grep", "find", "wc", "head", "tail", "python3", "pip", "ps", "top", "df", "du", "free", "git", "curl", "wget", "crontab"]
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.workspace = WORKSPACE_DIR / f"projects/nanobot/workspaces/{agent_id}"
        self.workspace.mkdir(parents=True, exist_ok=True)
    
    def validate_command(self, cmd: str) -> tuple:
        cmd_lower = cmd.lower().strip()
        if "rm -rf /" in cmd_lower or "mkfs" in cmd_lower:
            return False, "禁止执行危险命令"
        cmd_parts = cmd.split()
        if cmd_parts and cmd_parts[0] not in self.ALLOWED_COMMANDS:
            return False, f"命令 '{cmd_parts[0]}' 不在白名单中"
        return True, "OK"
    
    async def exec(self, command: str) -> str:
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
                return f"✅ 执行成功:\n{output[:2000]}"
            else:
                return f"⚠️ 执行失败:\n{error[:500] or output[:500]}"
        except asyncio.TimeoutError:
            return "⏱️ 执行超时 (>60秒)"
        except Exception as e:
            return f"❌ 执行异常: {str(e)}"
    
    async def read(self, filepath: str) -> str:
        try:
            path = Path(filepath)
            if not path.exists():
                return f"❌ 文件不存在: {filepath}"
            content = path.read_text()
            return f"📄 文件内容 ({len(content)} 字符):\n```\n{content[:2000]}\n```"
        except Exception as e:
            return f"❌ 读取失败: {str(e)}"
    
    async def write(self, filepath: str, content: str) -> str:
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return f"✅ 文件已写入: {filepath}"
        except Exception as e:
            return f"❌ 写入失败: {str(e)}"

class NanobotAgent:
    def __init__(self):
        self.id = AGENT_ID
        self.name = IDENTITY.get("name", AGENT_ID)
        self.role = IDENTITY.get("role", "assistant")
        self.capabilities = IDENTITY.get("capabilities", [])
        self.system_prompt = IDENTITY.get("system_prompt", "")
        self.tools = ToolExecutor(AGENT_ID)
        self._running = False
    
    async def llm_chat(self, message: str) -> str:
        if not API_KEY:
            return "[错误] 未配置API密钥"
        
        # 检查是否是纯工具任务
        if "使用exec执行" in message or "使用工具" in message:
            return "这是工具执行任务，请直接执行系统命令获取数据。"
        
        prompt = f"""{self.system_prompt}

当前任务: {message}

角色: {self.role}
能力: {', '.join(self.capabilities)}

注意:
- 直接回答，不要使用客套话
- 如果需要执行操作，直接描述需要做什么
- 保持简洁
"""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.3
                }
                
                async with session.post(
                    f"{BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"].get("content", "")
                    else:
                        error = await resp.text()
                        return f"[API错误] {resp.status}: {error[:200]}"
        except Exception as e:
            return f"[错误] {str(e)}"
    
    async def process_task(self, task_type: str, task_data: dict) -> dict:
        log(f"开始处理任务: {task_type}")
        task_desc = task_data.get("description", f"执行 {task_type}")
        
        # 如果任务描述包含exec指令，直接执行工具
        if "使用exec执行" in task_desc:
            import re
            exec_match = re.search(r'exec执行[:\s]+([^\n]+)', task_desc)
            if exec_match:
                command = exec_match.group(1).strip()
                result = await self.tools.exec(command)
                log(f"任务完成: {task_type}")
                return {"status": "completed", "result": result, "agent": self.id}
        
        # 否则调用LLM
        response = await self.llm_chat(task_desc)
        log(f"任务完成: {task_type}")
        return {"status": "completed", "result": response, "agent": self.id}
    
    async def run(self):
        log(f"🚀 {self.name} ({self.id}) 启动")
        log(f"   角色: {self.role}")
        log(f"   能力: {', '.join(self.capabilities)}")
        self._running = True
        processed_tasks = set()
        
        while self._running:
            try:
                task = self._check_task_queue(processed_tasks)
                if task:
                    await self._handle_task(task)
                else:
                    await asyncio.sleep(3)
            except KeyboardInterrupt:
                break
            except Exception as e:
                log(f"错误: {e}")
                await asyncio.sleep(5)
        
        log(f"👋 {self.name} 已停止")
    
    def _check_task_queue(self, processed_tasks: set) -> dict:
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
                    if task.get("agent_id") == self.id and task_id not in processed_tasks:
                        processed_tasks.add(task_id)
                        return task
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            log(f"读取任务队列错误: {e}")
        return None
    
    async def _handle_task(self, task: dict):
        task_type = task.get("type")
        task_data = task.get("data", {})
        result = await self.process_task(task_type, task_data)
        
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

if __name__ == "__main__":
    agent = NanobotAgent()
    asyncio.run(agent.run())
