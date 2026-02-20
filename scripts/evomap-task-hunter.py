#!/usr/bin/env python3
"""
EvoMap Task Hunter - 白天自动赚取收益
每小时检查并领取 EvoMap 任务，生成解决方案
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data" / "evomap"
LOG_FILE = WORKSPACE / "logs" / "task-hunter.log"
CONFIG_FILE = DATA_DIR / "task-hunter-state.json"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] TaskHunter: {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_node_id():
    """从配置文件加载当前节点ID"""
    config_file = WORKSPACE / "config" / "evomap" / "node-config.json"
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
            return config.get("node_id", "unknown")
    return "unknown"

def fetch_available_tasks() -> List[Dict]:
    """从 EvoMap 获取可用任务"""
    log("📡 查询 EvoMap 任务...")
    
    payload = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "fetch",
        "message_id": f"msg_{int(datetime.utcnow().timestamp() * 1000)}_tasks",
        "sender_id": load_node_id(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "asset_type": "Capsule",
            "include_tasks": True,
            "limit": 20
        }
    }
    
    try:
        result = subprocess.run(
            ["curl", "-sL", "-X", "POST",
             "https://evomap.ai/a2a/fetch",
             "-H", "Content-Type: application/json",
             "-d", json.dumps(payload),
             "--max-time", "15"],
            capture_output=True, text=True, timeout=20
        )
        
        if result.returncode != 0:
            log(f"⚠️ 查询失败: {result.stderr[:200]}")
            return []
        
        data = json.loads(result.stdout)
        tasks = data.get("payload", {}).get("tasks", [])
        log(f"✅ 找到 {len(tasks)} 个任务")
        return tasks
        
    except Exception as e:
        log(f"⚠️ 查询异常: {e}")
        return []

def claim_task(task_id: str) -> bool:
    """领取任务"""
    log(f"🎯 尝试领取任务: {task_id}")
    
    try:
        result = subprocess.run(
            ["curl", "-sL", "-X", "POST",
             "https://evomap.ai/task/claim",
             "-H", "Content-Type: application/json",
             "-d", json.dumps({"task_id": task_id, "node_id": load_node_id()}),
             "--max-time", "15"],
            capture_output=True, text=True, timeout=20
        )
        
        if result.returncode != 0:
            return False
        
        data = json.loads(result.stdout)
        if data.get("claimed_by") == load_node_id():
            log(f"✅ 任务领取成功: {task_id}")
            return True
        elif "error" in data:
            log(f"⚠️ 领取失败: {data.get('error')}")
            return False
        else:
            return False
            
    except Exception as e:
        log(f"⚠️ 领取异常: {e}")
        return False

def is_suitable_task(task: Dict) -> bool:
    """判断任务是否适合森森"""
    # 检查声望要求
    min_rep = task.get("min_reputation", 0)
    # 森森目前 reputation 估计为 0-30（新节点），只能接 beginner friendly 任务
    
    if task.get("beginner_friendly") != True:
        return False
    
    # 检查 signals 是否匹配森森的能力
    signals = task.get("signals", "")
    suitable_keywords = [
        "python", "node", "docker", "redis", "postgresql",
        "api", "error", "fix", "optimize", "test",
        "agent", "automation", "script"
    ]
    
    signals_lower = signals.lower()
    return any(kw in signals_lower for kw in suitable_keywords)

def generate_solution(task: Dict) -> Optional[str]:
    """为任务生成解决方案（简化版，实际可以调用 evolver）"""
    # 这里可以集成 Evolver 生成解决方案
    # 目前返回 None，表示需要手动处理
    return None

def run_task_hunter():
    """主入口"""
    log("=" * 60)
    log("🎯 EvoMap Task Hunter 启动")
    log("=" * 60)
    
    # 获取可用任务
    tasks = fetch_available_tasks()
    
    if not tasks:
        log("ℹ️ 没有新任务")
        return
    
    # 筛选适合的任务
    open_tasks = [t for t in tasks if t.get("status") == "open"]
    suitable_tasks = [t for t in open_tasks if is_suitable_task(t)]
    
    log(f"📊 统计: {len(open_tasks)} open, {len(suitable_tasks)} suitable")
    
    if not suitable_tasks:
        log("ℹ️ 没有适合的任务")
        return
    
    # 尝试领取适合的任务（按优先级排序）
    for task in sorted(suitable_tasks, 
                       key=lambda t: float(t.get("bounty_amount", 0) or 0), 
                       reverse=True)[:3]:  # 最多尝试前3个
        
        task_id = task.get("task_id")
        title = task.get("title", "No title")[:40]
        
        log(f"⭐ 尝试任务: {title}")
        
        if claim_task(task_id):
            # 保存到待处理列表
            claimed_file = DATA_DIR / "claimed-tasks.json"
            claimed = []
            if claimed_file.exists():
                with open(claimed_file) as f:
                    claimed = json.load(f)
            
            claimed.append({
                "task_id": task_id,
                "title": task.get("title"),
                "signals": task.get("signals"),
                "claimed_at": datetime.utcnow().isoformat() + "Z",
                "status": "claimed",
                "auto_processed": False
            })
            
            with open(claimed_file, "w") as f:
                json.dump(claimed, f, indent=2)
            
            log(f"💰 任务已保存，等待处理")
            return  # 成功领取一个就退出
    
    log(f"⚠️ 所有任务都被抢光了")
    
    log("=" * 60)

def get_stats():
    """获取统计信息"""
    claimed_file = DATA_DIR / "claimed-tasks.json"
    if not claimed_file.exists():
        return {"total_claimed": 0, "completed": 0}
    
    with open(claimed_file) as f:
        claimed = json.load(f)
    
    return {
        "total_claimed": len(claimed),
        "completed": len([c for c in claimed if c.get("status") == "completed"]),
        "pending": len([c for c in claimed if c.get("status") == "claimed"])
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        stats = get_stats()
        print(f"Task Hunter Stats:")
        print(f"  Total claimed: {stats['total_claimed']}")
        print(f"  Completed: {stats['completed']}")
        print(f"  Pending: {stats['pending']}")
    else:
        run_task_hunter()
