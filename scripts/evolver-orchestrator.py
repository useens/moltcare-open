#!/usr/bin/env python3
"""
Evolver + EvoMap 协调器
实现两者的真正协作：
1. 自动运行 Evolver 进化循环
2. 自动执行 solidify
3. 与 EvoMap 任务系统集成
4. 持续监控和自动恢复
"""

import subprocess
import json
import time
import os
import signal
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")
EVOLVER_DIR = WORKSPACE / "evolver"
LOG_DIR = WORKSPACE / "logs"
PID_FILE = WORKSPACE / "data" / "evolver-orchestrator.pid"
STATE_FILE = WORKSPACE / "data" / "evolver-orchestrator-state.json"

def log(msg, level="INFO"):
    """记录日志"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    
    # 写入日志文件
    log_file = LOG_DIR / "evolver-orchestrator.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a") as f:
        f.write(line + "\n")

def save_pid(pid):
    """保存进程ID"""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(pid))

def load_pid():
    """加载进程ID"""
    if PID_FILE.exists():
        with open(PID_FILE) as f:
            return int(f.read().strip())
    return None

def is_process_running(pid):
    """检查进程是否在运行"""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False

def save_state(state):
    """保存协调器状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def load_state():
    """加载协调器状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"cycles": 0, "last_run": None, "tasks_claimed": [], "solidify_count": 0}

def run_evolver_cycle():
    """运行一轮 Evolver 进化"""
    log("🚀 启动 Evolver 进化周期...")
    
    try:
        result = subprocess.run(
            ["node", "index.js", "run"],
            cwd=EVOLVER_DIR,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        log(f"Evolver 返回码: {result.returncode}")
        
        if result.returncode == 0:
            log("✅ Evolver 周期完成")
            return True, result.stdout, result.stderr
        else:
            log(f"⚠️ Evolver 返回非零: {result.stderr[:500]}", "WARN")
            return False, result.stdout, result.stderr
            
    except subprocess.TimeoutExpired:
        log("⏱️ Evolver 超时", "WARN")
        return False, "", "Timeout"
    except Exception as e:
        log(f"❌ Evolver 运行错误: {e}", "ERROR")
        return False, "", str(e)

def run_solidify():
    """执行 solidify 固化结果"""
    log("🔧 执行 solidify...")
    
    try:
        result = subprocess.run(
            ["node", "index.js", "solidify"],
            cwd=EVOLVER_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # 检查 stdout 中是否有 SUCCESS 标记
        if result.returncode == 0 or "[SOLIDIFY] SUCCESS" in result.stdout:
            log("✅ Solidify 成功")
            return True
        else:
            log(f"⚠️ Solidify 返回码: {result.returncode}", "WARN")
            if result.stderr:
                log(f"stderr: {result.stderr[:300]}", "WARN")
            return False
            
    except Exception as e:
        log(f"❌ Solidify 错误: {e}", "ERROR")
        return False

def check_evomap_tasks():
    """检查 EvoMap 任务"""
    log("📡 检查 EvoMap 任务...")
    
    try:
        sys.path.insert(0, str(WORKSPACE))
        from scripts.evomap.client import EvoMapClient
        from scripts.evomap.config import EvoMapConfig
        
        config = EvoMapConfig.load()
        client = EvoMapClient(config)
        
        # 重试机制
        for attempt in range(3):
            result = client.fetch(include_tasks=True)
            tasks = result.get('payload', {}).get('tasks', [])
            
            if tasks:
                break
            elif attempt < 2:
                time.sleep(1)  # 等待1秒后重试
        
        # 过滤 open 任务
        open_tasks = [t for t in tasks if t.get('status') == 'open']
        
        log(f"📋 发现 {len(open_tasks)} 个 open 任务 (总计 {len(tasks)})")
        
        # 打印任务列表
        for i, t in enumerate(open_tasks[:3]):
            log(f"  {i+1}. {t.get('title', 'N/A')[:50]}...")
        
        # 尝试认领赏金任务
        bounty_tasks = [t for t in open_tasks if t.get('bounty_id')]
        if bounty_tasks:
            log(f"💰 {len(bounty_tasks)} 个赏金任务")
            # 排序：优先赏金高的
            bounty_tasks.sort(key=lambda x: x.get('bounty_amount', 0), reverse=True)
            return bounty_tasks[0]  # 返回最佳任务
        elif open_tasks:
            # 如果没有赏金任务，返回第一个普通任务
            return open_tasks[0]
        
        return None
        
    except Exception as e:
        log(f"❌ EvoMap 检查错误: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        return None

def claim_evomap_task(task_id):
    """认领 EvoMap 任务"""
    log(f"🎯 尝试认领任务: {task_id}")
    
    try:
        sys.path.insert(0, str(WORKSPACE))
        from scripts.evomap.client import EvoMapClient
        from scripts.evomap.config import EvoMapConfig
        
        config = EvoMapConfig.load()
        client = EvoMapClient(config)
        
        # 使用 taskReceiver 的 claimTask 逻辑
        result = client._post("/a2a/task/claim", {
            "task_id": task_id,
            "node_id": config.sender_id
        })
        
        if result.get("status") == "success" or result.get("claimed"):
            log(f"✅ 成功认领任务: {task_id}")
            return True
        else:
            log(f"❌ 任务已被认领: {task_id}")
            return False
            
    except Exception as e:
        log(f"❌ 认领错误: {e}", "ERROR")
        return False

def inject_task_signals(task):
    """将任务信号注入 Evolver"""
    log(f"💉 注入任务信号: {task.get('title', 'Unknown')}")
    
    # 创建任务信号文件供 Evolver 读取
    signals = {
        "task_id": task.get('task_id'),
        "title": task.get('title'),
        "signals": task.get('signals', '').split(',') if task.get('signals') else [],
        "bounty_id": task.get('bounty_id'),
        "injected_at": datetime.now().isoformat()
    }
    
    signal_file = EVOLVER_DIR / "memory" / "injected-task-signals.json"
    signal_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(signal_file, "w") as f:
        json.dump(signals, f, indent=2)
    
    log(f"✅ 信号已注入: {signal_file}")
    return signals

def orchestrator_loop():
    """主协调循环"""
    log("=" * 60)
    log("🧬 Evolver + EvoMap 协调器启动")
    log("=" * 60)
    
    state = load_state()
    log(f"📊 历史周期: {state['cycles']}, Solidify: {state['solidify_count']}")
    
    while True:
        try:
            state['cycles'] += 1
            state['last_run'] = datetime.now().isoformat()
            save_state(state)
            
            log(f"\n{'='*60}")
            log(f"🔄 周期 #{state['cycles']} 开始")
            log(f"{'='*60}")
            
            # 1. 检查 EvoMap 任务
            best_task = check_evomap_tasks()
            
            if best_task:
                task_id = best_task.get('task_id')
                log(f"🎯 最佳任务: {best_task.get('title')}")
                
                # 尝试认领
                if claim_evomap_task(task_id):
                    # 注入信号
                    inject_task_signals(best_task)
                    state['tasks_claimed'].append({
                        'task_id': task_id,
                        'title': best_task.get('title'),
                        'claimed_at': datetime.now().isoformat()
                    })
                    save_state(state)
            else:
                log("📭 无可认领任务")
            
            # 2. 运行 Evolver 进化
            success, stdout, stderr = run_evolver_cycle()
            
            if success:
                # 3. 自动执行 solidify
                if run_solidify():
                    state['solidify_count'] += 1
                    save_state(state)
                    log("✅ 周期完成并已固化")
                else:
                    log("⚠️ Solidify 失败，继续下一轮")
            else:
                log("⚠️ Evolver 周期失败，稍后重试")
            
            # 4. 等待下一轮
            sleep_seconds = 300  # 5分钟间隔
            log(f"⏱️ 等待 {sleep_seconds} 秒后继续...")
            time.sleep(sleep_seconds)
            
        except KeyboardInterrupt:
            log("👋 收到中断信号，优雅退出...")
            break
        except Exception as e:
            log(f"❌ 协调器错误: {e}", "ERROR")
            time.sleep(60)  # 错误后等待1分钟

def stop_orchestrator():
    """停止协调器"""
    pid = load_pid()
    if pid and is_process_running(pid):
        log(f"🛑 停止协调器 (PID: {pid})")
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        if is_process_running(pid):
            os.kill(pid, signal.SIGKILL)
        PID_FILE.unlink(missing_ok=True)
        log("✅ 已停止")
    else:
        log("ℹ️ 协调器未运行")

def status():
    """显示状态"""
    pid = load_pid()
    state = load_state()
    
    print("=" * 60)
    print("📊 Evolver + EvoMap 协调器状态")
    print("=" * 60)
    
    if pid and is_process_running(pid):
        print(f"🟢 状态: 运行中 (PID: {pid})")
    else:
        print(f"🔴 状态: 未运行")
    
    print(f"📈 总周期: {state['cycles']}")
    print(f"🔧 Solidify: {state['solidify_count']}")
    print(f"🎯 已认领任务: {len(state['tasks_claimed'])}")
    
    if state['last_run']:
        print(f"🕐 最后运行: {state['last_run']}")
    
    # 检查 Evolver 原生进程
    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )
    if "node index.js evolve --loop" in result.stdout:
        print(f"🟢 Evolver 原生进程: 运行中")
    else:
        print(f"🔴 Evolver 原生进程: 未运行")
    
    print("=" * 60)

def main():
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start":
            # 检查是否已在运行
            pid = load_pid()
            if pid and is_process_running(pid):
                log("⚠️ 协调器已在运行")
                return
            
            # 后台启动
            log("🚀 后台启动协调器...")
            
            # 使用 nohup 启动
            process = subprocess.Popen(
                [sys.executable, __file__, "daemon"],
                stdout=open(LOG_DIR / "evolver-orchestrator.log", "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            
            save_pid(process.pid)
            log(f"✅ 协调器已启动 (PID: {process.pid})")
            print(f"协调器已启动，PID: {process.pid}")
            print(f"日志: {LOG_DIR / 'evolver-orchestrator.log'}")
            
        elif command == "daemon":
            # 实际运行循环
            orchestrator_loop()
            
        elif command == "stop":
            stop_orchestrator()
            
        elif command == "status":
            status()
            
        elif command == "once":
            # 运行单次
            log("🚀 运行单次协调...")
            state = load_state()
            
            best_task = check_evomap_tasks()
            if best_task:
                log(f"🎯 发现任务: {best_task.get('title')}")
                if claim_evomap_task(best_task.get('task_id')):
                    inject_task_signals(best_task)
            
            success, _, _ = run_evolver_cycle()
            if success:
                run_solidify()
            
            log("✅ 单次运行完成")
            
        else:
            print(f"未知命令: {command}")
            print("用法: python3 evolver-orchestrator.py [start|stop|status|once]")
    else:
        # 默认前台运行
        orchestrator_loop()

if __name__ == "__main__":
    main()
