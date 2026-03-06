#!/usr/bin/env python3
"""
Nanobot AI Agent - v3.1 修复版
修复self_modify命令解析
"""
import os
import sys
import json
import asyncio
import aiohttp
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

# 配置
AGENT_ID = sys.argv[1] if len(sys.argv) > 1 else "nanobot-1"
AGENT_DIR = Path(f"/root/.openclaw/workspace/projects/nanobot/agents/{AGENT_ID}")
LOG_FILE = Path(f"/root/.openclaw/workspace/projects/nanobot/logs/{AGENT_ID}.log")
WORKSPACE_DIR = Path("/root/.openclaw/workspace")
SELF_MODIFY_DIR = WORKSPACE_DIR / "projects/nanobot/self_modifications"
SELF_MODIFY_DIR.mkdir(parents=True, exist_ok=True)

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

class CodeModifier:
    """代码自我修改器"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.backup_dir = SELF_MODIFY_DIR / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.modifications_log = SELF_MODIFY_DIR / "modifications.jsonl"
    
    def _calculate_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    async def modify_code(self, filepath: str, description: str) -> str:
        """修改代码"""
        try:
            path = Path(filepath)
            
            if not path.exists():
                return f"❌ 文件不存在: {filepath}"
            
            content = path.read_text(encoding='utf-8')
            original_hash = self._calculate_hash(content)
            
            log(f"准备修改 {filepath} (hash: {original_hash})")
            
            # 备份
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{path.stem}_{timestamp}_{self.agent_id}.bak"
            backup_path = self.backup_dir / backup_name
            backup_path.write_text(content, encoding='utf-8')
            
            # 生成改进代码
            improved = await self._generate_improvement(content, description)
            
            if improved == content:
                return "⚠️ 生成的代码与原代码相同"
            
            # 写入
            path.write_text(improved, encoding='utf-8')
            new_hash = self._calculate_hash(improved)
            
            log(f"已修改 {filepath} (新hash: {new_hash})")
            
            # 记录
            mod_record = {
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "filepath": filepath,
                "original_hash": original_hash,
                "new_hash": new_hash,
                "backup": str(backup_name)
            }
            with open(self.modifications_log, "a") as f:
                f.write(json.dumps(mod_record) + "\n")
            
            return f"✅ 修改成功\n  文件: {filepath}\n  hash: {original_hash} → {new_hash}"
            
        except Exception as e:
            return f"❌ 修改失败: {str(e)}"
    
    async def _generate_improvement(self, original: str, desc: str) -> str:
        if not API_KEY:
            return original
        
        prompt = f"""优化以下Python代码：{desc}

代码：
```python
{original[:2000]}
```

直接输出优化后的完整代码："""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                    json={"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2000, "temperature": 0.2},
                    timeout=60
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        improved = data["choices"][0]["message"].get("content", "")
                        if "```python" in improved:
                            improved = improved.split("```python")[1].split("```")[0]
                        elif "```" in improved:
                            improved = improved.split("```")[1].split("```")[0]
                        return improved.strip()
        except Exception as e:
            log(f"生成失败: {e}")
        
        return original

class ToolExecutor:
    """工具执行器"""
    
    ALLOWED = ["ls", "cat", "grep", "find", "wc", "head", "tail", "echo", "mkdir", "touch"]
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.modifier = CodeModifier(agent_id)
    
    async def exec(self, command: str) -> str:
        cmd_base = command.split()[0] if command else ""
        if cmd_base not in self.ALLOWED:
            return f"❌ 命令 '{cmd_base}' 不在白名单"
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
            out = stdout.decode() if stdout else ""
            return f"✅ 执行成功:\n{out[:1000]}"
        except Exception as e:
            return f"❌ 执行失败: {e}"
    
    async def self_modify(self, filepath: str, description: str) -> str:
        return await self.modifier.modify_code(filepath, description)

class NanobotAgent:
    """Nanobot Agent - v3.1"""
    
    def __init__(self):
        self.id = AGENT_ID
        self.name = IDENTITY.get("name", AGENT_ID)
        self.role = IDENTITY.get("role", "assistant")
        self.tools = ToolExecutor(AGENT_ID)
        self._running = False
    
    def parse_commands(self, desc: str) -> List[Dict]:
        """解析命令 - 修复版"""
        commands = []
        
        # 标准命令
        exec_matches = re.findall(r'执行[:\s]+([^\n]+)', desc)
        for m in exec_matches:
            commands.append({'type': 'exec', 'command': m.strip()})
        
        # 自我修改命令 - 修复模式匹配
        # 匹配 "自我修改: 文件路径, 改进描述"
        self_modify_matches = re.findall(
            r'(?:自我修改|self_modify)[:\s]+([^,\n]+)[,，]?\s*([^\n]*)',
            desc,
            re.IGNORECASE
        )
        for filepath, description in self_modify_matches:
            if filepath.strip():
                commands.append({
                    'type': 'self_modify',
                    'filepath': filepath.strip(),
                    'description': description.strip() or '优化代码'
                })
        
        return commands
    
    async def process_task(self, task_type: str, task_data: dict) -> dict:
        log(f"开始处理: {task_type}")
        
        desc = task_data.get("description", "")
        commands = self.parse_commands(desc)
        
        results = []
        for cmd in commands:
            t = cmd['type']
            if t == 'exec':
                r = await self.tools.exec(cmd['command'])
            elif t == 'self_modify':
                r = await self.tools.self_modify(cmd['filepath'], cmd['description'])
            else:
                r = f"❌ 未知: {t}"
            results.append(f"[{t}] {r}")
        
        final = "\n".join(results) if results else "⚠️ 未解析到命令"
        log(f"完成: {task_type} ({len(commands)}个命令)")
        
        return {"status": "completed", "result": final, "commands_count": len(commands)}
    
    async def run(self):
        log(f"🚀 {self.name} ({self.id}) 启动 - v3.1")
        self._running = True
        processed = set()
        
        while self._running:
            try:
                task = self._check_task(processed)
                if task:
                    result = await self.process_task(task.get("type"), task.get("data", {}))
                    # 保存结果
                    result_file = WORKSPACE_DIR / "projects/nanobot/hub/results.jsonl"
                    with open(result_file, "a") as f:
                        f.write(json.dumps({"agent_id": self.id, "result": result, "timestamp": datetime.now().isoformat()}) + "\n")
                else:
                    await asyncio.sleep(2)
            except Exception as e:
                log(f"错误: {e}")
                await asyncio.sleep(5)
        
        log(f"👋 {self.name} 已停止")
    
    def _check_task(self, processed: set) -> Optional[dict]:
        task_file = WORKSPACE_DIR / "projects/nanobot/hub/tasks.jsonl"
        if not task_file.exists():
            return None
        
        try:
            with open(task_file) as f:
                for line in reversed(f.readlines()):
                    try:
                        task = json.loads(line)
                        tid = f"{task.get('agent_id')}:{task.get('timestamp')}"
                        if task.get("agent_id") == self.id and tid not in processed:
                            processed.add(tid)
                            return task
                    except:
                        continue
        except Exception as e:
            log(f"读取错误: {e}")
        
        return None

if __name__ == "__main__":
    agent = NanobotAgent()
    asyncio.run(agent.run())
