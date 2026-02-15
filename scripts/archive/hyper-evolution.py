#!/usr/bin/env python3
"""
超进化模式控制器
Hyper-Evolution Mode Controller

使用方法:
  python3 hyper_evolution.py start              # 开始超进化，直到用户说结束
  python3 hyper_evolution.py start --duration 48 # 开始超进化，持续48小时
  python3 hyper_evolution.py start --milestone "version-release" # 直到发布新版本
  python3 hyper_evolution.py stop               # 停止超进化
  python3 hyper_evolution.py status             # 查看当前状态
"""

import argparse
import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import yaml

# 状态文件路径
STATE_FILE = Path("memory/hyper-evolution-state.json")
CONFIG_FILE = Path("config/hyper-evolution.yaml")
LOCK_FILE = Path("memory/.hyper-evolution.lock")

def load_config():
    """加载超进化配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def load_state():
    """加载当前状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "active": False,
        "start_time": None,
        "mode": "normal",
        "duration_hours": None,
        "milestone": None,
        "tasks_completed": 0,
        "deep_learning_count": 0,
        "knowledge_updates": 0
    }

def save_state(state):
    """保存状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def start_hyper_evolution(duration=None, milestone=None):
    """启动超进化模式"""
    config = load_config()
    state = load_state()
    
    if state.get("active"):
        print("⚠️ 超进化模式已在运行中")
        print(f"   开始时间: {state.get('start_time')}")
        print(f"   已运行: {calculate_runtime(state.get('start_time'))}")
        return False
    
    # 创建锁文件
    LOCK_FILE.touch()
    
    # 更新状态
    now = datetime.now().isoformat()
    state = {
        "active": True,
        "start_time": now,
        "mode": "hyper-evolution",
        "version": config.get("version", "1.0.0"),
        "codename": config.get("codename", "Hyperion"),
        "duration_hours": duration,
        "milestone": milestone,
        "scheduled_end": (datetime.now() + timedelta(hours=duration)).isoformat() if duration else None,
        "tasks_completed": 0,
        "deep_learning_count": 0,
        "knowledge_updates": 0,
        "sources_processed": [],
        "high_signal_items": [],
        "learning_debt_cleared": 0
    }
    
    save_state(state)
    
    # 记录到进化日志
    log_evolution_start(state)
    
    # 更新MEMORY.md状态
    update_memory_status(state)
    
    print(f"\n{'='*60}")
    print(f"🚀 超进化模式启动")
    print(f"{'='*60}")
    print(f"版本: {state['version']} ({state['codename']})")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if duration:
        end_time = datetime.now() + timedelta(hours=duration)
        print(f"预计结束: {end_time.strftime('%Y-%m-%d %H:%M:%S')} ({duration}小时)")
    elif milestone:
        print(f"结束条件: 达成里程碑 '{milestone}'")
    else:
        print(f"结束条件: 等待用户指令")
    
    print(f"\n配置摘要:")
    dl_config = config.get("deep_learning", {})
    print(f"  • 扫描间隔: {dl_config.get('scan_interval_minutes', 30)}分钟")
    print(f"  • Signal阈值: {dl_config.get('extraction', {}).get('signal_threshold', 6)}")
    print(f"  • 每轮深度提取: 最多{dl_config.get('extraction', {}).get('max_deep_extract_per_source', 10)}条")
    print(f"  • 活跃源数量: {len(dl_config.get('sources', {}).get('enabled', []))}个")
    
    print(f"\n{'='*60}\n")
    
    # 启动后台任务调度
    setup_cron_tasks()
    
    return True

def stop_hyper_evolution(reason="user_command"):
    """停止超进化模式"""
    state = load_state()
    
    if not state.get("active"):
        print("超进化模式未在运行")
        return False
    
    # 计算运行统计
    runtime = calculate_runtime(state.get("start_time"))
    
    # 生成结束报告
    report = generate_evolution_report(state, runtime)
    
    # 更新状态
    state["active"] = False
    state["end_time"] = datetime.now().isoformat()
    state["runtime_hours"] = runtime
    state["stop_reason"] = reason
    save_state(state)
    
    # 删除锁文件
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
    
    # 清理cron任务
    cleanup_cron_tasks()
    
    # 记录到进化日志
    log_evolution_end(state, report)
    
    # 更新MEMORY.md状态
    update_memory_status(state, ended=True)
    
    print(f"\n{'='*60}")
    print(f"🏁 超进化模式结束")
    print(f"{'='*60}")
    print(f"运行时长: {runtime:.2f}小时")
    print(f"停止原因: {reason}")
    print(f"\n运行统计:")
    print(f"  • 深度学习次数: {state.get('deep_learning_count', 0)}")
    print(f"  • 知识更新次数: {state.get('knowledge_updates', 0)}")
    print(f"  • 高Signal发现: {len(state.get('high_signal_items', []))}条")
    print(f"  • 学习债务清理: {state.get('learning_debt_cleared', 0)}条")
    print(f"\n{'='*60}\n")
    
    return True

def check_status():
    """检查当前状态"""
    state = load_state()
    config = load_config()
    
    print(f"\n{'='*60}")
    print(f"📊 超进化模式状态")
    print(f"{'='*60}")
    
    if not state.get("active"):
        print("状态: 未运行 (正常模式)")
        if state.get("end_time"):
            print(f"上次运行: {state.get('start_time')} ~ {state.get('end_time')}")
            print(f"运行时长: {state.get('runtime_hours', 0):.2f}小时")
    else:
        print("状态: 🟢 超进化模式运行中")
        print(f"版本: {state.get('version')} ({state.get('codename')})")
        runtime = calculate_runtime(state.get("start_time"))
        print(f"已运行: {runtime:.2f}小时")
        
        if state.get("scheduled_end"):
            end = datetime.fromisoformat(state["scheduled_end"])
            remaining = (end - datetime.now()).total_seconds() / 3600
            print(f"剩余时间: {remaining:.2f}小时")
        elif state.get("milestone"):
            print(f"目标里程碑: {state['milestone']}")
        else:
            print(f"结束条件: 等待用户指令")
        
        print(f"\n实时统计:")
        print(f"  • 深度学习次数: {state.get('deep_learning_count', 0)}")
        print(f"  • 知识更新: {state.get('knowledge_updates', 0)}次")
        print(f"  • 处理源: {len(state.get('sources_processed', []))}个")
        print(f"  • 高Signal内容: {len(state.get('high_signal_items', []))}条")
    
    print(f"\n{'='*60}\n")
    return state.get("active")

def calculate_runtime(start_time_str):
    """计算运行时长（小时）"""
    if not start_time_str:
        return 0
    start = datetime.fromisoformat(start_time_str)
    return (datetime.now() - start).total_seconds() / 3600

def log_evolution_start(state):
    """记录进化开始"""
    log_file = Path("memory/evolution-log.md")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} - 超进化启动\n\n")
        f.write(f"**版本**: {state['version']} ({state['codename']})\n")
        f.write(f"**模式**: {state['mode']}\n")
        if state['duration_hours']:
            f.write(f"**持续时间**: {state['duration_hours']}小时\n")
        if state['milestone']:
            f.write(f"**目标里程碑**: {state['milestone']}\n")
        f.write(f"\n### 初始配置\n")
        f.write(f"- 扫描间隔: 30分钟\n")
        f.write(f"- Signal阈值: 6\n")
        f.write(f"- 活跃信息源: Moltbook, HN, GitHub, Reddit, arXiv...\n")
        f.write(f"\n---\n")

def log_evolution_end(state, report):
    """记录进化结束"""
    log_file = Path("memory/evolution-log.md")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n### {datetime.now().strftime('%Y-%m-%d %H:%M')} - 超进化结束\n\n")
        f.write(f"**运行时长**: {state.get('runtime_hours', 0):.2f}小时\n")
        f.write(f"**停止原因**: {state.get('stop_reason', 'unknown')}\n\n")
        f.write(f"**成果统计**:\n")
        f.write(f"- 深度学习: {state.get('deep_learning_count', 0)}次\n")
        f.write(f"- 知识更新: {state.get('knowledge_updates', 0)}次\n")
        f.write(f"- 高Signal发现: {len(state.get('high_signal_items', []))}条\n")
        f.write(f"\n---\n")

def update_memory_status(state, ended=False):
    """更新MEMORY.md中的状态"""
    memory_file = Path("MEMORY.md")
    if not memory_file.exists():
        return
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新今日状态部分
    status_line = f"**当前模式**: {'🟢 超进化模式' if not ended else '⚪ 正常模式'}"
    
    if "**当前模式**:" in content:
        # 更新现有行
        import re
        content = re.sub(r'\*\*当前模式\*\*:.*', status_line, content)
    else:
        # 添加新行
        content = content.replace("## 今日核心状态", f"## 今日核心状态\n\n{status_line}")
    
    with open(memory_file, 'w', encoding='utf-8') as f:
        f.write(content)

def generate_evolution_report(state, runtime):
    """生成进化报告"""
    report = {
        "start_time": state.get("start_time"),
        "end_time": datetime.now().isoformat(),
        "runtime_hours": runtime,
        "statistics": {
            "deep_learning_count": state.get("deep_learning_count", 0),
            "knowledge_updates": state.get("knowledge_updates", 0),
            "high_signal_items": len(state.get("high_signal_items", [])),
            "learning_debt_cleared": state.get("learning_debt_cleared", 0)
        },
        "sources_processed": state.get("sources_processed", []),
        "stop_reason": state.get("stop_reason", "user_command")
    }
    
    report_file = Path(f"memory/reports/evolution-report-{datetime.now().strftime('%Y%m%d-%H%M')}.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report

def setup_cron_tasks():
    """设置cron任务"""
    # 这里会设置定时任务来执行深度学习循环
    # 实际实现会调用cron工具
    print("  📅 已设置定时任务")

def cleanup_cron_tasks():
    """清理cron任务"""
    print("  📅 已清理定时任务")

def main():
    parser = argparse.ArgumentParser(description="超进化模式控制器")
    parser.add_argument("action", choices=["start", "stop", "status"], help="操作")
    parser.add_argument("--duration", type=int, help="持续时间（小时）")
    parser.add_argument("--milestone", type=str, help="目标里程碑")
    
    args = parser.parse_args()
    
    if args.action == "start":
        start_hyper_evolution(args.duration, args.milestone)
    elif args.action == "stop":
        stop_hyper_evolution()
    elif args.action == "status":
        check_status()

if __name__ == "__main__":
    main()
