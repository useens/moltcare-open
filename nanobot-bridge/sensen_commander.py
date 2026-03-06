#!/usr/bin/env python3
"""
森森自动指挥 nanobot 小弟模块
自动识别任务并委派给小弟执行
"""

import json
import time
import uuid
import subprocess
from pathlib import Path
from datetime import datetime

HUB_DIR = Path.home() / ".nanobot-bridge"
INBOX = HUB_DIR / "to_nanobot.jsonl"
OUTBOX = HUB_DIR / "from_nanobot.jsonl"
NANOBOT_BIN = "/usr/local/bin/nanobot"

def send_task_to_nanobot(task_description, wait=True, timeout=120):
    """
    向 nanobot 小弟发送任务
    
    Args:
        task_description: 任务描述
        wait: 是否等待回复
        timeout: 超时时间(秒)
    
    Returns:
        如果 wait=True: 返回 nanobot 的回复内容
        如果 wait=False: 返回任务ID
    """
    HUB_DIR.mkdir(exist_ok=True)
    
    task_id = str(uuid.uuid4())[:8]
    msg = {
        "id": task_id,
        "from": "sensen",
        "to": "nanobot",
        "content": task_description,
        "timestamp": datetime.now().isoformat()
    }
    
    # 写入任务队列
    with open(INBOX, "a") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    
    if not wait:
        return task_id
    
    # 等待回复
    start_time = time.time()
    while time.time() - start_time < timeout:
        if OUTBOX.exists():
            with open(OUTBOX, "r") as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                try:
                    reply = json.loads(line.strip())
                    if reply.get("id") == task_id:
                        # 删除已读取的回复
                        remaining = [l for j, l in enumerate(lines) if j != i]
                        with open(OUTBOX, "w") as f:
                            f.writelines(remaining)
                        return reply.get("content", "小弟没有回复")
                except:
                    continue
        
        time.sleep(0.3)
    
    return "小弟超时未回复"

def direct_nanobot_call(message, timeout=60):
    """
    直接调用 nanobot (不通过文件队列，直接 subprocess)
    用于简单快速的任务
    """
    try:
        result = subprocess.run(
            [NANOBOT_BIN, "agent", "-m", message],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout.strip()
        # 移除 🐈 nanobot 前缀
        if "🐈 nanobot" in output:
            output = output.split("🐈 nanobot")[-1].strip()
        return output
    except subprocess.TimeoutExpired:
        return "小弟处理超时"
    except Exception as e:
        return f"调用小弟失败: {str(e)}"

def delegate_to_nanobot(task_type, task_content, context=None):
    """
    智能委派任务给小弟
    
    Args:
        task_type: 任务类型 (search/code/write/analyze等)
        task_content: 任务内容
        context: 可选的上下文信息
    
    Returns:
        nanobot 的执行结果
    """
    # 构建任务提示
    prompt = f"""
【来自森森的指令】
任务类型: {task_type}
{'上下文: ' + context if context else ''}

具体任务:
{task_content}

请执行此任务并返回结果。
""".strip()
    
    return direct_nanobot_call(prompt)

# 快捷调用函数
def nanobot_search(query):
    """让小弟搜索信息"""
    return delegate_to_nanobot("search", f"搜索: {query}")

def nanobot_code(task):
    """让小弟写代码"""
    return delegate_to_nanobot("code", task)

def nanobot_write(content):
    """让小弟写文档/内容"""
    return delegate_to_nanobot("write", content)

def nanobot_analyze(data):
    """让小弟分析数据"""
    return delegate_to_nanobot("analyze", data)

# 兼容直接调用
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
        print(direct_nanobot_call(msg))
