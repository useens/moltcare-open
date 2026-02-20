#!/usr/bin/env python3
"""
EvoMap Task Hunter v3.0 - 极致极速版
使用 asyncio + aiohttp 实现真正异步，零延迟领取
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data" / "evomap"
LOG_FILE = WORKSPACE / "logs" / "task-hunter.log"

# 预加载配置，避免运行时读取
CONFIG_FILE = WORKSPACE / "config" / "evomap" / "node-config.json"
NODE_ID = "unknown"
if CONFIG_FILE.exists():
    with open(CONFIG_FILE) as f:
        NODE_ID = json.load(f).get("node_id", "unknown")

HUB_URL = "https://evomap.ai"
TIMEOUT = aiohttp.ClientTimeout(total=5, connect=2)

# 全局 session，复用连接
session: Optional[aiohttp.ClientSession] = None

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] TaskHunter: {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

async def init_session():
    """初始化全局 session"""
    global session
    connector = aiohttp.TCPConnector(
        limit=10,
        limit_per_host=10,
        enable_cleanup_closed=True,
        force_close=False,
    )
    session = aiohttp.ClientSession(
        connector=connector,
        timeout=TIMEOUT,
        headers={"Content-Type": "application/json"}
    )

async def close_session():
    """关闭 session"""
    if session:
        await session.close()

async def fetch_tasks_raw() -> List[Dict]:
    """原始获取任务，不做任何处理"""
    payload = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "fetch",
        "message_id": f"msg_{int(time.time() * 1000)}",
        "sender_id": NODE_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "asset_type": None,  # 获取所有类型
            "include_tasks": True,
            "limit": 100  # 获取更多
        }
    }
    
    try:
        async with session.post(f"{HUB_URL}/a2a/fetch", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("payload", {}).get("tasks", [])
    except Exception as e:
        pass
    return []

async def claim_task_raw(task_id: str) -> tuple:
    """原始领取任务，返回 (success, task_id, error)"""
    payload = {"task_id": task_id, "node_id": NODE_ID}
    
    try:
        async with session.post(f"{HUB_URL}/task/claim", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("claimed_by") == NODE_ID:
                    return (True, task_id, None)
                elif "error" in data:
                    return (False, task_id, data.get("error"))
                return (False, task_id, f"status_{resp.status}")
            return (False, task_id, f"http_{resp.status}")
    except Exception as e:
        return (False, task_id, str(e)[:50])

async def claim_all_concurrent(tasks: List[Dict]) -> Optional[str]:
    """并发领取所有任务，第一个成功即返回"""
    if not tasks:
        return None
    
    # 只取前 10 个，避免过多请求
    task_ids = [t.get("task_id") for t in tasks[:10] if t.get("status") == "open"]
    
    if not task_ids:
        return None
    
    log(f"🚀 并发领取 {len(task_ids)} 个任务...")
    
    # 创建所有领取任务
    claim_tasks = [claim_task_raw(tid) for tid in task_ids]
    
    # 等待第一个成功的
    for coro in asyncio.as_completed(claim_tasks):
        success, task_id, error = await coro
        if success:
            return task_id
        # 静默记录失败，不输出日志（减少IO延迟）
    
    return None

async def run_hunter():
    """主入口 - 极致极速版"""
    start = time.time()
    
    log("=" * 60)
    log("🎯 Task Hunter v3.0 (极致极速版)")
    log("=" * 60)
    
    # 初始化 session
    await init_session()
    
    try:
        # 1. 快速获取任务
        log("📡 查询任务...")
        tasks = await fetch_tasks_raw()
        
        if not tasks:
            log("ℹ️ 无任务")
            return
        
        open_tasks = [t for t in tasks if t.get("status") == "open"]
        log(f"✅ 找到 {len(open_tasks)} 个开放任务")
        
        if not open_tasks:
            log("ℹ️ 无开放任务")
            return
        
        # 2. 立即并发领取所有（不做筛选，先抢到再说）
        claimed_id = await claim_all_concurrent(open_tasks)
        
        elapsed = time.time() - start
        
        if claimed_id:
            # 找到任务详情
            task = next((t for t in open_tasks if t.get("task_id") == claimed_id), None)
            
            log(f"✅ 领取成功! {claimed_id[:20]}...")
            
            if task:
                # 保存
                claimed_file = DATA_DIR / "claimed-tasks.json"
                claimed = []
                if claimed_file.exists():
                    with open(claimed_file) as f:
                        claimed = json.load(f)
                
                claimed.append({
                    "task_id": claimed_id,
                    "title": task.get("title"),
                    "claimed_at": datetime.utcnow().isoformat() + "Z",
                    "status": "claimed"
                })
                
                with open(claimed_file, "w") as f:
                    json.dump(claimed, f, indent=2)
        else:
            log(f"⚠️ 未抢到 (尝试 {len(open_tasks)} 个)")
        
        log(f"⏱️ 总耗时: {elapsed:.3f}s")
        
    finally:
        await close_session()
    
    log("=" * 60)

def main():
    """同步入口"""
    asyncio.run(run_hunter())

if __name__ == "__main__":
    main()