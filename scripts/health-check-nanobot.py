#!/usr/bin/env python3
"""Nanobot健康检查 - 由NB05执行"""
import requests
import json
from datetime import datetime

NODES = [
    ("NB01", 18801), ("NB02", 18802), ("NB03", 18803),
    ("NB04", 18804), ("NB05", 18805), ("NB06", 18806),
    ("NB07", 18807), ("NB08", 18808), ("NB09", 18809), ("NB10", 18810)
]

def check_node(node_id, port):
    try:
        resp = requests.get(f"http://127.0.0.1:{port}/status", timeout=5)
        return resp.status_code == 200
    except:
        return False

results = {}
for node_id, port in NODES:
    results[node_id] = check_node(node_id, port)

# 记录结果
log_file = "/root/.openclaw/workspace/nanobots/nb05/logs/health-check.log"
with open(log_file, "a") as f:
    f.write(f"[{datetime.now().isoformat()}] Health check: {json.dumps(results)}\n")

# 如果有离线节点，通知指挥中心
offline = [n for n, status in results.items() if not status]
if offline:
    import subprocess
    subprocess.run([
        "python3", "/root/.openclaw/workspace/scripts/feishu-sync.py",
        "high", "health.monitor",
        f"节点离线: {', '.join(offline)}"
    ])
    print(f"⚠️  发现离线节点: {offline}")
else:
    print("✅ 所有节点在线")
