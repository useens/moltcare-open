#!/usr/bin/env python3
"""
Nanobot AI Agent - v3.0 自我进化版
添加自我修改能力
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
    """代码自我修改器 - 安全地修改代码"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.backup_dir = SELF_MODIFY_DIR / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.modifications_log = SELF_MODIFY_DIR / "modifications.jsonl"
    
    def _calculate_hash(self, content: str) -> str:
        """计算文件内容的hash"""
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    async def _backup_file(self, filepath: Path) -> str:
        """备份文件，返回备份路径"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{filepath.stem}_{timestamp}_{self.agent_id}.bak"
        backup_path = self.backup_dir / backup_name
        
        if filepath.exists():
            content = filepath.read_text(encoding='utf-8')
            backup_path.write_text(content, encoding='utf-8')
            log(f"已备份 {filepath.name} 到 {backup_name}")
            return str(backup_path)
        return ""
    
    async def read_code(self, filepath: str) -> Tuple[bool, str]:
        """读取代码文件"""
        try:
            path = Path(filepath)
            if not path.exists():
                return False, f"文件不存在: {filepath}"
            
            # 安全检查：只能读取特定目录下的文件
            allowed_dirs = [
                WORKSPACE_DIR / "projects/nanobot",
                WORKSPACE_DIR / "scripts"
            ]
            
            resolved_path = path.resolve()
            if not any(str(resolved_path).startswith(str(d)) for d in allowed_dirs):
                return False, f"无权访问该路径: {filepath}"
            
            content = path.read_text(encoding='utf-8')
            return True, content
            
        except Exception as e:
            return False, f"读取失败: {str(e)}"
    
    async def modify_code(self, filepath: str, description: str) -> str:
        """
        修改代码 - 安全流程：
        1. 读取原文件
        2. 备份
        3. 生成改进代码
        4. 写入
        5. 记录日志
        """
        try:
            path = Path(filepath)
            
            # 1. 读取原文件
            success, content = await self.read_code(filepath)
            if not success:
                return f"❌ {content}"
            
            original_hash = self._calculate_hash(content)
            log(f"准备修改 {filepath} (hash: {original_hash})")
            
            # 2. 备份
            backup_path = await self._backup_file(path)
            if not backup_path:
                return "❌ 备份失败"
            
            # 3. 调用LLM生成改进代码
            improved_content = await self._generate_improvement(content, description)
            
            if improved_content == content:
                return "⚠️ 生成的代码与原代码相同，无需修改"
            
            new_hash = self._calculate_hash(improved_content)
            
            # 4. 写入新代码
            path.write_text(improved_content, encoding='utf-8')
            log(f"已修改 {filepath} (新hash: {new_hash})")
            
            # 5. 记录修改日志
            mod_record = {
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "filepath": filepath,
                "original_hash": original_hash,
                "new_hash": new_hash,
                "backup_path": backup_path,
                "description": description
            }
            
            with open(self.modifications_log, "a") as f:
                f.write(json.dumps(mod_record) + "\n")
            
            return f"✅ 代码修改成功\n  文件: {filepath}\n  原hash: {original_hash}\n  新hash: {new_hash}\n  备份: {backup_path}\n  改进: {description[:50]}..."
            
        except Exception as e:
            return f"❌ 修改失败: {str(e)}"
    
    async def _generate_improvement(self, original_code: str, description: str) -> str:
        """调用LLM生成改进后的代码"""
        if not API_KEY:
            log("警告: 未配置API密钥，返回原代码")
            return original_code
        
        prompt = f"""你是一位专业的Python代码优化专家。

请根据以下描述优化代码：
{description}

原始代码：
```python
{original_code[:3000]}  # 限制长度避免token超限
```

要求：
1. 保持代码功能不变
2. 提高代码质量和可读性
3. 添加必要的注释
4. 修复潜在问题

请直接输出优化后的完整代码，不需要解释：
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
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.2
                }
                
                async with session.post(
                    f"{BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        improved = data["choices"][0]["message"].get("content", "")
                        # 提取代码块
                        if "```python" in improved:
                            improved = improved.split("```python")[1].split("```")[0]
                        elif "```" in improved:
                            improved = improved.split("```")[1].split("```")[0]
                        return improved.strip()
                    else:
                        log(f"LLM调用失败: {resp.status}")
                        return original_code
        except Exception as e:
            log(f"生成改进代码失败: {e}")
            return original_code
    
    async def rollback(self, filepath: str) -> str:
        """回滚到最近的备份"""
        try:
            # 查找最近的备份
            backups = sorted(self.backup_dir.glob(f"{Path(filepath).stem}_*_{self.agent_id}.bak"), reverse=True)
            if not backups:
                return f"❌ 未找到备份: {filepath}"
            
            latest_backup = backups[0]
            backup_content = latest_backup.read_text(encoding='utf-8')
            
            path = Path(filepath)
            path.write_text(backup_content, encoding='utf-8')
            
            return f"✅ 已回滚 {filepath} 到 {latest_backup.name}"
            
        except Exception as e:
            return f"❌ 回滚失败: {str(e)}"

class ToolExecutor:
    """工具执行器 - v3.0"""
    
    ALLOWED_COMMANDS = ["ls", "cat", "grep", "find", "wc", "head", "tail", "python3", "pip", "ps", "top", "df", "du", "free", "git", "curl", "wget", "crontab", "awk", "sort", "uniq", "basename", "stat", "xargs", "sed", "echo", "mkdir", "touch", "md5sum"]
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.workspace = WORKSPACE_DIR / f"projects/nanobot/workspaces/{agent_id}"
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.code_modifier = CodeModifier(agent_id)
    
    def validate_command(self, cmd: str) -> tuple:
        cmd_lower = cmd.lower().strip()
        dangerous = ["rm -rf /", "mkfs", "dd if=/dev/zero", "> /etc/passwd", "> /etc/shadow", "chmod -R 777 /"]
        for d in dangerous:
            if d in cmd_lower:
                return False, f"禁止执行危险命令: {d}"
        
        cmd_parts = cmd.split('|')[0].strip().split()
        if cmd_parts:
            base_cmd = cmd_parts[0]
            if base_cmd not in self.ALLOWED_COMMANDS:
                return False, f"命令 '{base_cmd}' 不在白名单中"
        return True, "OK"
    
    async def exec(self, command: str) -> str:
        """执行系统命令"""
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
        success, content = await self.code_modifier.read_code(filepath)
        if success:
            return f"📄 文件内容 ({len(content)} 字符):\n```\n{content[:3000]}\n```"
        return f"❌ {content}"
    
    async def write(self, filepath: str, content: str) -> str:
        """写入文件"""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            return f"✅ 文件已写入: {filepath} ({len(content)} 字符)"
        except Exception as e:
            return f"❌ 写入失败: {str(e)}"
    
    async def self_modify(self, filepath: str, description: str) -> str:
        """自我修改代码"""
        return await self.code_modifier.modify_code(filepath, description)
    
    async def rollback(self, filepath: str) -> str:
        """回滚代码修改"""
        return await self.code_modifier.rollback(filepath)

class NanobotAgent:
    """Nanobot Agent - v3.0 自我进化版"""
    
    def __init__(self):
        self.id = AGENT_ID
        self.name = IDENTITY.get("name", AGENT_ID)
        self.role = IDENTITY.get("role", "assistant")
        self.capabilities = IDENTITY.get("capabilities", [])
        self.system_prompt = IDENTITY.get("system_prompt", "")
        self.tools = ToolExecutor(AGENT_ID)
        self._running = False
    
    async def llm_chat(self, message: str) -> str:
        """调用LLM"""
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
    
    def parse_commands(self, description: str) -> List[Dict]:
        """从任务描述中解析命令"""
        commands = []
        import re
        
        # 标准命令模式
        patterns = [
            (r'(?:使用exec执行|执行)[:\s]+([^\n]+)', 'exec'),
            (r'(?:使用self_modify|自我修改|优化改进)[:\s]+([^\n]+)[,，]\s*([^\n]+)', 'self_modify'),
            (r'(?:读取|read)[:\s]+([^\n]+)', 'read'),
        ]
        
        for pattern, tool_type in patterns:
            if tool_type == 'self_modify':
                matches = re.findall(pattern, description, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        commands.append({'type': tool_type, 'filepath': match[0].strip(), 'description': match[1].strip()})
            else:
                matches = re.findall(pattern, description, re.IGNORECASE)
                for match in matches:
                    commands.append({'type': tool_type, 'command': match.strip()})
        
        return commands
    
    async def process_task(self, task_type: str, task_data: dict) -> dict:
        """处理任务"""
        log(f"开始处理任务: {task_type}")
        
        task_desc = task_data.get("description", f"执行 {task_type}")
        context = task_data.get("context", "general")
        
        results = []
        
        # 1. 解析命令
        commands = self.parse_commands(task_desc)
        
        if commands:
            log(f"解析到 {len(commands)} 个命令")
            for cmd in commands:
                tool_type = cmd['type']
                
                if tool_type == 'exec':
                    result = await self.tools.exec(cmd['command'])
                elif tool_type == 'read':
                    result = await self.tools.read(cmd['filepath'])
                elif tool_type == 'self_modify':
                    result = await self.tools.self_modify(cmd['filepath'], cmd['description'])
                else:
                    result = f"❌ 未知工具: {tool_type}"
                
                results.append(f"[{tool_type}]\n{result}")
        else:
            # 没有解析到命令，调用LLM
            log("未解析到命令，调用LLM")
            response = await self.llm_chat(task_desc)
            results.append(f"[LLM]\n{response}")
        
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
        log(f"🚀 {self.name} ({self.id}) 启动 - v3.0 自我进化版")
        log(f"   角色: {self.role}")
        log(f"   能力: {', '.join(self.capabilities)}")
        log(f"   新增: 自我代码修改能力")
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
            
            for line in reversed(lines):
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
