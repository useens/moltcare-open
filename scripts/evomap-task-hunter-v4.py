#!/usr/bin/env python3
"""
EvoMap Task Hunter v4.0 - 极致极速版
优化: SSL Session 复用、DNS缓存、零延迟响应
"""

import asyncio
import aiohttp
import json
import time
import ssl
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data" / "evomap"
LOG_FILE = WORKSPACE / "logs" / "task-hunter.log"

# 预加载
CONFIG_FILE = WORKSPACE / "config" / "evomap" / "node-config.json"
NODE_ID = "unknown"
if CONFIG_FILE.exists():
    with open(CONFIG_FILE) as f:
        NODE_ID = json.load(f).get("node_id", "unknown")

HUB_URL = "https://evomap.ai"

# 全局 session
session: Optional[aiohttp.ClientSession] = None

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] TaskHunter: {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

async def init_session():
    """初始化高性能 session"""
    global session
    
    # SSL 上下文优化
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.set_alpn_protocols(['http/1.1'])  # 强制 HTTP/1.1，避免 HTTP/2 开销
    
    connector = aiohttp.TCPConnector(
        limit=20,
        limit_per_host=20,
        enable_cleanup_closed=True,
        force_close=False,
        use_dns_cache=True,
        ttl_dns_cache=300,
        ssl=ssl_ctx,
    )
    
    timeout = aiohttp.ClientTimeout(total=3, connect=1)
    
    session = aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={
            "Content-Type": "application/json",
            "Connection": "keep-alive",
        }
    )

async def close_session():
    if session:
        await session.close()

async def fetch_and_claim() -> Optional[str]:
    """查询+领取一体化，最小延迟"""
    
    # 1. 快速查询
    fetch_payload = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "fetch",
        "message_id": f"msg_{int(time.time() * 1000)}",
        "sender_id": NODE_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "asset_type": None,
            "include_tasks": True,
            "limit": 50
        }
    }
    
    try:
        async with session.post(f"{HUB_URL}/a2a/fetch", json=fetch_payload) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            tasks = data.get("payload", {}).get("tasks", [])
    except:
        return None
    
    if not tasks:
        return None
    
    # 2. 立即并发领取所有开放任务
    open_tasks = [t for t in tasks if t.get("status") == "open"]
    if not open_tasks:
        return None
    
    # 创建领取 coroutines
    async def try_claim(task: Dict) -> Optional[str]:
        task_id = task.get("task_id")
        payload = {"task_id": task_id, "node_id": NODE_ID}
        
        try:
            async with session.post(f"{HUB_URL}/task/claim", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("claimed_by") == NODE_ID:
                        return task_id
        except:
            pass
        return None
    
    # 并发执行所有领取
    coros = [try_claim(t) for t in open_tasks[:15]]  # 最多15个
    
    for coro in asyncio.as_completed(coros):
        result = await coro
        if result:
            return result
    
    return None

async def run():
    """主入口"""
    start = time.time()
    
    log("=" * 60)
    log("🚀 Task Hunter v4.0 (极致极速)")
    log("=" * 60)
    
    await init_session()
    
    try:
        claimed_id = await fetch_and_claim()
        elapsed = time.time() - start
        
        if claimed_id:
            log(f"✅ 领取成功: {claimed_id[:20]}...")
            
            # 保存
            claimed_file = DATA_DIR / "claimed-tasks.json"
            claimed = []
            if claimed_file.exists():
                with open(claimed_file) as f:
                    claimed = json.load(f)
            
            claimed.append({
                "task_id": claimed_id,
                "claimed_at": datetime.utcnow().isoformat() + "Z",
                "status": "claimed"
            })
            
            with open(claimed_file, "w") as f:
                json.dump(claimed, f, indent=2)
        else:
            log(f"⚠️ 未抢到")
        
        log(f"⏱️ 耗时: {elapsed:.3f}s")
        
    finally:
        await close_session()
    
    log("=" * 60)

if __name__ == "__main__":
    asyncio.run(run())
