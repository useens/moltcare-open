#!/usr/bin/env python3
"""
Nanobot AI Agent - v2.0 优化版
修复工具执行和报告生成
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
REPORTS_DIR = WORKSPACE_DIR / "reports"

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
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

class ToolExecutor:
    """工具执行器 - 优化版"""
    
    ALLOWED_COMMANDS = ["ls", "cat", "grep", "find", "wc", "head", "tail", "python3", "pip", "ps", "top", "df", "du", "free", "git", "curl", "wget", "crontab", "awk", "sort", "uniq", "basename", "stat", "xargs", "sed", "echo", "mkdir", "touch"]
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.workspace = WORKSPACE_DIR / f"projects/nanobot/workspaces/{agent_id}"
        self.workspace.mkdir(parents=True, exist_ok=True)
    
    def validate_command(self, cmd: str) -> tuple:
        cmd_lower = cmd.lower().strip()
        dangerous = ["rm -rf /", "mkfs", "dd if=/dev/zero", "> /etc/passwd", "> /etc/shadow", "chmod -R 777 /"]
        for d in dangerous:
            if d in cmd_lower:
                return False, f"禁止执行危险命令: {d}"
        
        # 提取命令的第一个词
        cmd_parts = cmd.split('|')[0].strip().split()
        if cmd_parts:
            base_cmd = cmd_parts[0]
            if base_cmd not in self.ALLOWED_COMMANDS:
                return False, f"命令 '{base_cmd}' 不在白名单中"
        return True, "OK"
    
    async def exec(self, command: str) -> str:
        """执行系统命令 - 返回完整结果"""
        valid, reason = self.validate_command(command)
        if not valid:
            return f"❌ 安全拦截: {reason}"
        
        log(f"执行命令: {command[:80]}...")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(WORKSPACE_DIR)
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            
            output = stdout.decode('utf-8', errors='ignore') if stdout else ""
            error = stderr.decode('utf-8', errors='ignore') if stderr else ""
            
            if process.returncode == 0:
                result = f"✅ 执行成功:\n{output}" if output else "✅ 执行成功 (无输出)"
                if error:
                    result += f"\n⚠️  stderr:\n{error[:500]}"
            else:
                result = f"⚠️ 执行失败 (code {process.returncode}):\n{error[:1000] or output[:1000]}"
            
            return result
            
        except asyncio.TimeoutError:
            return "⏱️ 执行超时 (>120秒)"
        except Exception as e:
            return f"❌ 执行异常: {str(e)}"
    
    async def read(self, filepath: str) -> str:
        """读取文件"""
        try:
            path = Path(filepath)
            if not path.exists():
                return f"❌ 文件不存在: {filepath}"
            content = path.read_text(encoding='utf-8', errors='ignore')
            return f"📄 文件内容 ({len(content)} 字符):\n```\n{content[:3000]}\n```"
        except Exception as e:
            return f"❌ 读取失败: {str(e)}"
    
    async def write(self, filepath: str, content: str) -> str:
        """写入文件 - 用于生成报告"""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            return f"✅ 文件已写入: {filepath} ({len(content)} 字符)"
        except Exception as e:
            return f"❌ 写入失败: {str(e)}"

class NanobotAgent:
    """Nanobot Agent - v2.0"""
    
    def __init__(self):
        self.id = AGENT_ID
        self.name = IDENTITY.get("name", AGENT_ID)
        self.role = IDENTITY.get("role", "assistant")
        self.capabilities = IDENTITY.get("capabilities", [])
        self.system_prompt = IDENTITY.get("system_prompt", "")
        self.tools = ToolExecutor(AGENT_ID)
        self._running = False
    
    async def llm_chat(self, message: str) -> str:
        """调用LLM - 仅在需要时"""
        if not API_KEY:
            return "[错误] 未配置API密钥"
        
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
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 2000,
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
    
    def parse_commands(self, description: str) -> List[str]:
        """从任务描述中解析需要执行的命令"""
        commands = []
        import re
        
        # 匹配 "执行: xxx" 或 "使用exec执行: xxx" 或数字编号后的命令
        patterns = [
            r'(?:使用exec执行|执行)[:\s]+([^\n]+)',
            r'\d+\.\s*([^\n]+find[^\n]+)',
            r'\d+\.\s*([^\n]+ls[^\n]+)',
            r'\d+\.\s*([^\n]+grep[^\n]+)',
            r'\d+\.\s*([^\n]+wc[^\n]+)',
            r'\d+\.\s*([^\n]+cat[^\n]+)',
            r'\d+\.\s*([^\n]+ps[^\n]+)',
            r'\d+\.\s*([^\n]+df[^\n]+)',
            r'\d+\.\s*([^\n]+du[^\n]+)',
            r'\d+\.\s*([^\n]+crontab[^\n]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                cmd = match.strip()
                if cmd and cmd not in commands:
                    commands.append(cmd)
        
        return commands
    
    async def process_task(self, task_type: str, task_data: dict) -> dict:
        """处理任务 - 优化版"""
        log(f"开始处理任务: {task_type}")
        
        task_desc = task_data.get("description", f"执行 {task_type}")
        context = task_data.get("context", "general")
        
        results = []
        
        # 1. 解析并执行系统命令
        commands = self.parse_commands(task_desc)
        if commands:
            log(f"解析到 {len(commands)} 个命令")
            for cmd in commands:
                result = await self.tools.exec(cmd)
                results.append(f"命令: {cmd}\n{result}")
        
        # 2. 如果任务要求生成报告，创建报告文件
        report_match = None
        import re
        report_pattern = r'(?:报告|保存到|输出到)[:\s]+(/[^\n]+\.json)'
        report_matches = re.findall(report_pattern, task_desc)
        if report_matches:
            report_path = report_matches[0]
            # 生成JSON报告
            report_data = {
                "agent_id": self.id,
                "role": self.role,
                "task_type": task_type,
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "commands_executed": len(commands),
                "results": results,
                "summary": f"执行了{len(commands)}个命令，收集了系统数据"
            }
            report_content = json.dumps(report_data, indent=2, ensure_ascii=False)
            write_result = await self.tools.write(report_path, report_content)
            results.append(write_result)
        
        # 3. 如果需要分析，调用LLM
        if "分析" in task_desc or "审计" in task_desc or "评估" in task_desc:
            analysis_prompt = f"""基于以下执行结果，生成简洁的分析总结：

任务: {task_desc}

执行结果:
{chr(10).join(results[:5])}

请提供:
1. 主要发现
2. 关键数据点
3. 简要建议
"""
            analysis = await self.llm_chat(analysis_prompt)
            results.append(f"\n🧠 分析:\n{analysis}")
        
        final_result = "\n\n".join(results)
        log(f"任务完成: {task_type} (执行了{len(commands)}个命令)")
        
        return {
            "status": "completed",
            "result": final_result,
            "agent": self.id,
            "commands_count": len(commands)
        }
    
    async def run(self):
        """主循环"""
        log(f"🚀 {self.name} ({self.id}) 启动 - v2.0")
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
                    await asyncio.sleep(2)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                log(f"错误: {e}")
                await asyncio.sleep(5)
        
        log(f"👋 {self.name} 已停止")
    
    def _check_task_queue(self, processed_tasks: set) -> Optional[dict]:
        """检查任务队列"""
        task_file = WORKSPACE_DIR / "projects/nanobot/hub/tasks.jsonl"
        
        if not task_file.exists():
            return None
        
        try:
            with open(task_file, 'r') as f:
                lines = f.readlines()
            
            for line in reversed(lines):  # 从最新的开始检查
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
        """处理任务并保存结果"""
        task_type = task.get("type", "unknown")
        task_data = task.get("data", {})
        
        result = await self.process_task(task_type, task_data)
        
        # 保存结果
        result_file = WORKSPACE_DIR / "projects/nanobot/hub/results.jsonl"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        result_data = {
            "agent_id": self.id,
            "task_type": task_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(result_file, "a") as f:
            f.write(json.dumps(result_data, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    agent = NanobotAgent()
    asyncio.run(agent.run())
