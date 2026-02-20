#!/usr/bin/env python3
"""
EvoMap Periodic Sync - Cron 定时任务
每4小时同步一次 EvoMap 资产和任务
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
LOG_FILE = WORKSPACE / "logs" / "evomap-sync.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def main():
    log("=" * 50)
    log("EvoMap Periodic Sync Started")
    
    # 1. 同步资产
    result = subprocess.run([
        "python3", str(WORKSPACE / "scripts" / "evomap-integrate.py")
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        log("✅ Asset sync completed")
    else:
        log(f"⚠️ Asset sync failed: {result.stderr[:200]}")
    
    # 2. 检查已发布资产状态
    node_config = WORKSPACE / "config" / "evomap" / "node-config.json"
    if node_config.exists():
        with open(node_config) as f:
            config = json.load(f)
        
        published = config.get("published_assets", [])
        log(f"📦 Published assets: {len(published)} (checking status...)")
        
        # TODO: 查询资产状态（需要实现）
        for asset in published:
            log(f"  - {asset['type']}: {asset['asset_id'][:20]}... ({asset['status']})")
    
    # 3. 统计今日同步
    data_dir = WORKSPACE / "data" / "evomap"
    today_capsules = list(data_dir.glob("capsules-20260220.json"))
    log(f"📊 Today's capsule snapshots: {len(today_capsules)}")
    
    log("=" * 50)

if __name__ == "__main__":
    main()
