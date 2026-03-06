#!/usr/bin/env python3
"""
检查Nanobot AI Agent状态
"""
import json
import time
from pathlib import Path
from datetime import datetime

HUB_DIR = Path("/root/.openclaw/workspace/projects/nanobot/hub")
LOGS_DIR = Path("/root/.openclaw/workspace/projects/nanobot/logs")

def check_registrations():
    """检查注册状态"""
    reg_file = HUB_DIR / "registrations.jsonl"
    if not reg_file.exists():
        return {}
    
    agents = {}
    with open(reg_file) as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("type") == "register":
                    agent_id = data.get("agent_id")
                    agents[agent_id] = data
            except:
                pass
    
    return agents

def check_heartbeat():
    """检查心跳状态"""
    hb_file = HUB_DIR / "heartbeat.jsonl"
    if not hb_file.exists():
        return {}
    
    heartbeats = {}
    with open(hb_file) as f:
        for line in f:
            try:
                data = json.loads(line)
                agent_id = data.get("agent_id")
                heartbeats[agent_id] = data.get("timestamp")
            except:
                pass
    
    return heartbeats

def check_pids():
    """检查进程状态"""
    import os
    pids = {}
    
    for i in range(1, 11):
        agent_id = f"nanobot-{i}"
        pid_file = LOGS_DIR / f"{agent_id}.pid"
        
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                if os.path.exists(f"/proc/{pid}"):
                    pids[agent_id] = pid
            except:
                pass
    
    return pids

def main():
    print("=" * 70)
    print("🤖 Nanobot AI Agent 状态检查")
    print("=" * 70)
    print()
    
    # 检查注册
    agents = check_registrations()
    print(f"📋 已注册 Agent: {len(agents)} 个")
    
    # 检查心跳
    heartbeats = check_heartbeat()
    
    # 检查进程
    pids = check_pids()
    print(f"🔄 运行中进程: {len(pids)} 个")
    print()
    
    # 显示详细状态
    print("详细状态:")
    print("-" * 70)
    
    for i in range(1, 11):
        agent_id = f"nanobot-{i}"
        
        # 注册状态
        reg = agents.get(agent_id, {})
        name = reg.get("name", agent_id)
        
        # 进程状态
        if agent_id in pids:
            proc_status = f"🟢 运行中 (PID: {pids[agent_id]})"
        else:
            proc_status = "🔴 未运行"
        
        # 心跳状态
        hb_time = heartbeats.get(agent_id)
        if hb_time:
            hb_status = "💓"
        else:
            hb_status = "💔"
        
        print(f"{hb_status} {agent_id:12s} | {name:10s} | {proc_status}")
    
    print()
    print("=" * 70)
    
    # 检查日志
    print("\n最近日志:")
    print("-" * 70)
    
    for i in range(1, 4):  # 显示前3个的日志
        agent_id = f"nanobot-{i}"
        log_file = LOGS_DIR / f"{agent_id}.log"
        
        if log_file.exists():
            lines = log_file.read_text().strip().split("\n")
            if lines:
                last_line = lines[-1]
                print(f"[{agent_id}] {last_line[:80]}...")

if __name__ == "__main__":
    main()
