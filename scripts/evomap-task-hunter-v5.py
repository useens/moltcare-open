#!/usr/bin/env python3
"""
EvoMap Task Hunter v5.0 - 极速静默版
零日志输出，纯内存操作，极致速度
"""

import asyncio
import aiohttp
import json
import time
import ssl
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data" / "evomap"

# 预加载
with open(WORKSPACE / "config" / "evomap" / "node-config.json") as f:
    NODE_ID = json.load(f).get("node_id", "unknown")

HUB_URL = "https://evomap.ai"

async def run():
    """极速执行，只输出结果"""
    start = time.time()
    
    # 创建优化 session
    ssl_ctx = ssl.create_default_context()
    connector = aiohttp.TCPConnector(
        limit=30, limit_per_host=30,
        use_dns_cache=True, ttl_dns_cache=600,
        ssl=ssl_ctx
    )
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=aiohttp.ClientTimeout(total=2, connect=1),
        headers={"Content-Type": "application/json"}
    ) as session:
        
        # 快速查询
        try:
            async with session.post(f"{HUB_URL}/a2a/fetch", json={
                "protocol": "gep-a2a", "protocol_version": "1.0.0",
                "message_type": "fetch", "message_id": f"msg_{int(time.time()*1000)}",
                "sender_id": NODE_ID,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "payload": {"asset_type": None, "include_tasks": True, "limit": 100}
            }) as resp:
                data = await resp.json()
                tasks = data.get("payload", {}).get("tasks", [])
        except:
            print(f"❌ 查询失败 ({time.time()-start:.2f}s)")
            return
        
        open_tasks = [t for t in tasks if t.get("status") == "open"]
        if not open_tasks:
            print(f"ℹ️ 无开放任务 ({time.time()-start:.2f}s)")
            return
        
        # 并发领取
        async def claim(task):
            try:
                async with session.post(f"{HUB_URL}/task/claim", 
                    json={"task_id": task.get("task_id"), "node_id": NODE_ID}) as resp:
                    if resp.status == 200:
                        d = await resp.json()
                        if d.get("claimed_by") == NODE_ID:
                            return task.get("task_id")
            except:
                pass
            return None
        
        results = await asyncio.gather(*[claim(t) for t in open_tasks[:20]])
        claimed = next((r for r in results if r), None)
        
        elapsed = time.time() - start
        
        if claimed:
            print(f"✅ 抢到: {claimed[:20]}... ({elapsed:.3f}s)")
            # 保存
            claimed_file = DATA_DIR / "claimed-tasks.json"
            claimed_list = json.load(open(claimed_file)) if claimed_file.exists() else []
            claimed_list.append({
                "task_id": claimed,
                "claimed_at": datetime.utcnow().isoformat() + "Z",
                "status": "claimed"
            })
            with open(claimed_file, "w") as f:
                json.dump(claimed_list, f)
        else:
            print(f"❌ 未抢到 ({len(open_tasks)} tasks, {elapsed:.3f}s)")

if __name__ == "__main__":
    asyncio.run(run())
