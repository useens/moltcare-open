#!/usr/bin/env python3
"""
EvoMap Task Hunter v2.0 - 极速版
使用 requests 替代 curl，并发尝试，更快响应
"""

import json
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data" / "evomap"
LOG_FILE = WORKSPACE / "logs" / "task-hunter.log"
CONFIG_FILE = DATA_DIR / "task-hunter-state.json"

# 配置
HUB_URL = "https://evomap.ai"
TIMEOUT = 8  # 减少超时时间

# 创建持久化 session，复用连接，更快
session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

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
    """从 EvoMap 获取可用任务 - 使用 requests 更快"""
    log("📡 查询 EvoMap 任务...")
    
    payload = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "fetch",
        "message_id": f"msg_{int(time.time() * 1000)}_tasks",
        "sender_id": load_node_id(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "asset_type": "Capsule",
            "include_tasks": True,
            "limit": 50  # 获取更多任务
        }
    }
    
    try:
        resp = session.post(
            f"{HUB_URL}/a2a/fetch",
            json=payload,
            timeout=TIMEOUT
        )
        
        if resp.status_code != 200:
            log(f"⚠️ 查询失败: {resp.status_code}")
            return []
        
        data = resp.json()
        tasks = data.get("payload", {}).get("tasks", [])
        log(f"✅ 找到 {len(tasks)} 个任务")
        return tasks
        
    except Exception as e:
        log(f"⚠️ 查询异常: {e}")
        return []

def claim_task(task_id: str) -> Dict:
    """领取任务 - 返回结果和耗时"""
    start_time = time.time()
    
    try:
        resp = session.post(
            f"{HUB_URL}/task/claim",
            json={"task_id": task_id, "node_id": load_node_id()},
            timeout=TIMEOUT
        )
        
        elapsed = time.time() - start_time
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("claimed_by") == load_node_id():
                return {"success": True, "elapsed": elapsed, "data": data}
            elif "error" in data:
                return {"success": False, "elapsed": elapsed, "error": data.get("error")}
        
        return {"success": False, "elapsed": elapsed, "error": f"HTTP {resp.status_code}"}
        
    except Exception as e:
        elapsed = time.time() - start_time
        return {"success": False, "elapsed": elapsed, "error": str(e)}

def claim_task_concurrent(task_ids: List[str]) -> Optional[str]:
    """并发尝试领取多个任务，返回第一个成功的"""
    log(f"🚀 并发尝试 {len(task_ids)} 个任务...")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        # 提交所有任务
        future_to_task = {
            executor.submit(claim_task, task_id): task_id 
            for task_id in task_ids
        }
        
        # 等待第一个成功的
        for future in as_completed(future_to_task):
            task_id = future_to_task[future]
            try:
                result = future.result()
                if result["success"]:
                    log(f"✅ 任务 {task_id[:20]}... 领取成功! 耗时: {result['elapsed']:.2f}s")
                    return task_id
                else:
                    log(f"   {task_id[:15]}... 失败: {result.get('error', 'unknown')} ({result['elapsed']:.2f}s)")
            except Exception as e:
                log(f"   {task_id[:15]}... 异常: {e}")
    
    return None

def is_suitable_task(task: Dict) -> bool:
    """判断任务是否适合森森"""
    # 检查声望要求
    min_rep = task.get("min_reputation", 0) or 0
    
    # 新节点只能接 beginner friendly 任务
    if task.get("beginner_friendly") != True:
        return False
    
    # 检查 signals 是否匹配
    signals = task.get("signals", "")
    suitable_keywords = [
        "python", "node", "docker", "redis", "postgresql",
        "api", "error", "fix", "optimize", "test",
        "agent", "automation", "script", "bash", "shell",
        "config", "setup", "deploy", "sync"
    ]
    
    signals_lower = signals.lower()
    return any(kw in signals_lower for kw in suitable_keywords)

def calculate_success_probability(task: Dict) -> float:
    """计算任务成功领取的概率"""
    base_prob = 0.5
    
    if task.get("beginner_friendly") == True:
        base_prob += 0.3
    
    min_rep = task.get("min_reputation", 0) or 0
    if min_rep == 0:
        base_prob += 0.2
    elif min_rep < 30:
        base_prob += 0.1
    
    priority = task.get("priority", 0) or 0
    if priority == 0:
        base_prob += 0.1
    elif priority > 5:
        base_prob -= 0.2
    
    boost = task.get("boost_level", 0) or 0
    if boost == 0:
        base_prob += 0.1
    elif boost > 3:
        base_prob -= 0.1
    
    return max(0.1, min(base_prob, 0.95))

def run_task_hunter():
    """主入口 - 极速版"""
    start_time = time.time()
    
    log("=" * 60)
    log("🎯 EvoMap Task Hunter v2.0 (极速版) 启动")
    log("=" * 60)
    
    # 获取任务
    tasks = fetch_available_tasks()
    
    if not tasks:
        log("ℹ️ 没有新任务")
        log(f"⏱️ 总耗时: {time.time() - start_time:.2f}s")
        return
    
    # 筛选适合的任务
    open_tasks = [t for t in tasks if t.get("status") == "open"]
    suitable_tasks = [t for t in open_tasks if is_suitable_task(t)]
    
    log(f"📊 统计: {len(open_tasks)} open, {len(suitable_tasks)} suitable")
    
    if not suitable_tasks:
        log("ℹ️ 没有适合的任务")
        log(f"⏱️ 总耗时: {time.time() - start_time:.2f}s")
        return
    
    # 排序并按概率分组
    sorted_tasks = sorted(suitable_tasks, 
                          key=lambda t: calculate_success_probability(t), 
                          reverse=True)
    
    # 显示排序结果
    log(f"📋 任务排序 (按成功概率):")
    for i, task in enumerate(sorted_tasks[:5], 1):
        prob = calculate_success_probability(task)
        title = task.get("title", "No title")[:30]
        min_rep = task.get("min_reputation", 0) or 0
        log(f"   {i}. [{prob:.0%}] {title}... (声望: {min_rep})")
    
    # 并发尝试前5个任务
    top_tasks = sorted_tasks[:5]
    task_ids = [t.get("task_id") for t in top_tasks]
    
    claimed_id = claim_task_concurrent(task_ids)
    
    if claimed_id:
        # 找到对应的任务详情
        claimed_task = next((t for t in top_tasks if t.get("task_id") == claimed_id), None)
        if claimed_task:
            # 保存到待处理列表
            claimed_file = DATA_DIR / "claimed-tasks.json"
            claimed = []
            if claimed_file.exists():
                with open(claimed_file) as f:
                    claimed = json.load(f)
            
            claimed.append({
                "task_id": claimed_id,
                "title": claimed_task.get("title"),
                "signals": claimed_task.get("signals"),
                "min_reputation": claimed_task.get("min_reputation"),
                "priority": claimed_task.get("priority"),
                "claimed_at": datetime.utcnow().isoformat() + "Z",
                "status": "claimed",
                "auto_processed": False
            })
            
            with open(claimed_file, "w") as f:
                json.dump(claimed, f, indent=2)
            
            log(f"💾 任务已保存到 {claimed_file}")
    else:
        log(f"⚠️ 所有任务尝试完毕，未抢到")
    
    log(f"⏱️ 总耗时: {time.time() - start_time:.2f}s")
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
