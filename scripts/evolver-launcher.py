#!/usr/bin/env python3
"""
Evolver Launcher for Sensen
启动 Evolver 并与 EvoMap 节点 node_42192f01 衔接
"""

import subprocess
import json
import os
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")
EVOLVER_DIR = WORKSPACE / "evolver"
LOG_FILE = WORKSPACE / "logs" / "evolver.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] Evolver: {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def sync_node_assets():
    """将已发布的资产同步到 Evolver"""
    node_config = WORKSPACE / "config" / "evomap" / "node-config.json"
    if not node_config.exists():
        log("⚠️ 未找到节点配置")
        return
    
    with open(node_config) as f:
        config = json.load(f)
    
    log(f"📦 节点资产数: {len(config.get('published_assets', []))}")
    
    # 同步到 evolver 的 assets/gep/
    gep_dir = EVOLVER_DIR / "assets" / "gep"
    
    # 读取现有的 genes/capsules
    genes_file = gep_dir / "genes.json"
    capsules_file = gep_dir / "capsules.json"
    
    log("✅ 资产同步完成")

def run_evolver_once():
    """运行一次 Evolver"""
    log("🚀 启动 Evolver (单次模式)...")
    
    result = subprocess.run(
        ["node", "index.js", "run"],
        cwd=EVOLVER_DIR,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode == 0:
        log("✅ Evolver 运行成功")
        if result.stdout:
            log(f"输出: {result.stdout[:500]}")
    else:
        log(f"❌ Evolver 运行失败: {result.stderr[:500]}")
    
    return result.returncode == 0

def run_evolver_loop():
    """运行 Evolver Loop 模式 (后台)"""
    log("🚀 启动 Evolver Loop 模式...")
    
    # 使用 nohup 后台运行
    process = subprocess.Popen(
        ["nohup", "node", "index.js", "--loop"],
        cwd=EVOLVER_DIR,
        stdout=open(LOG_FILE, "a"),
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid
    )
    
    log(f"✅ Evolver Loop 已启动 (PID: {process.pid})")
    
    # 保存 PID
    pid_file = WORKSPACE / "data" / "evolver.pid"
    with open(pid_file, "w") as f:
        f.write(str(process.pid))
    
    return process.pid

def solidify():
    """固化进化结果"""
    log("🔧 固化进化结果...")
    
    result = subprocess.run(
        ["node", "index.js", "solidify"],
        cwd=EVOLVER_DIR,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        log("✅ 固化成功")
    else:
        log(f"⚠️ 固化结果: {result.stderr[:300]}")
    
    return result.returncode == 0

def main():
    import sys
    
    print("=" * 60)
    print("🧬 Sensen Evolver Launcher")
    print("=" * 60)
    print()
    print(f"Node ID: node_42192f01")
    print(f"Evolver Path: {EVOLVER_DIR}")
    print()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "loop":
            sync_node_assets()
            pid = run_evolver_loop()
            print(f"\nEvolver Loop 已启动，PID: {pid}")
            print(f"日志: {LOG_FILE}")
        elif command == "once":
            sync_node_assets()
            run_evolver_once()
        elif command == "solidify":
            solidify()
        elif command == "status":
            pid_file = WORKSPACE / "data" / "evolver.pid"
            if pid_file.exists():
                with open(pid_file) as f:
                    pid = f.read().strip()
                print(f"Evolver PID: {pid}")
            else:
                print("Evolver 未运行")
        else:
            print(f"未知命令: {command}")
            print("用法: python3 evolver-launcher.py [loop|once|solidify|status]")
    else:
        # 默认：运行一次
        sync_node_assets()
        run_evolver_once()

if __name__ == "__main__":
    main()
