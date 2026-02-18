#!/usr/bin/env python3
"""
Hyper-Evolution Engine - 主入口
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# 添加工作区到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from core import state, event_bus
from collectors import run_all_collectors
from decider import decider
from executor import Executor
# 加载高级策略
import strategies.advanced  # noqa

def cmd_status(args):
    """查看进化系统状态"""
    print("🧬 Hyper-Evolution Engine v2.0")
    print("=" * 50)
    print(f"状态: {'✅ 启用' if state.get('evolution_enabled') else '⏸️ 暂停'}")
    print(f"当前模型: {state.get('current_model')}")
    print(f"置信度阈值: {state.get('config', {}).get('confidence_threshold')}")
    print(f"总进化次数: {state.get('stats', {}).get('total_evolutions')}")
    print(f"成功率: {state.get('stats', {}).get('successful_evolutions')} / {state.get('stats', {}).get('total_evolutions')}")

    # 显示最近的决策历史
    import sqlite3
    DB_PATH = Path("/root/.openclaw/workspace/evolution/data/evolution.db")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 5
    """)
    rows = cursor.fetchall()
    if rows:
        print("\n📊 最近进化记录:")
        for row in rows:
            status_icon = "✅" if row["status"] == "success" else "❌"
            print(f"  {status_icon} {row['timestamp'][:19]} | {row['trigger']} → {row['strategy']} ({row['confidence']:.0%})")
    conn.close()

def cmd_evaluate(args):
    """手动触发一次评估"""
    print("🔍 运行进化评估...")
    decision = decider.run_evaluation()
    if decision:
        print(json.dumps(decision, indent=2, ensure_ascii=False))

        # 自动执行（如果置信度足够且非 dry-run）
        if args.execute and decision["confidence"] >= state.get("config", {}).get("confidence_threshold", 0.8):
            print("\n⚡ 自动执行中...")
            executor = Executor()
            result = executor.execute(decision, dry_run=args.dry_run)
            print(json.dumps({
                "success": result.success,
                "plan_id": result.plan_id,
                "errors": result.errors
            }, indent=2))
    else:
        print("✅ 无需进化，系统状态良好")

def cmd_collect(args):
    """手动运行数据收集"""
    print("📊 收集数据...")
    from collectors import run_all_collectors
    run_all_collectors()
    print("✅ 完成")

def cmd_pause(args):
    """暂停自动进化"""
    state.set("evolution_enabled", False)
    print("⏸️  自动进化已暂停")

def cmd_resume(args):
    """恢复自动进化"""
    state.set("evolution_enabled", True)
    print("▶️  自动进化已恢复")

def cmd_history(args):
    """查看进化历史"""
    import sqlite3
    DB_PATH = Path("/root/.openclaw/workspace/evolution/data/evolution.db")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM decisions ORDER BY timestamp DESC LIMIT ?
    """, (args.limit,))
    rows = cursor.fetchall()

    for row in rows:
        status_icon = "✅" if row["status"] == "success" else "❌"
        print(f"{status_icon} {row['timestamp'][:19]}")
        print(f"   触发: {row['trigger']}")
        print(f"   策略: {row['strategy']}")
        print(f"   置信度: {float(row['confidence']):.0%}")
        print(f"   状态: {row['status']}")
        print()
    conn.close()

def cmd_rollback(args):
    """手动回滚到最后备份"""
    executor = Executor()
    # 查找最近一次成功执行的备份
    # TODO: 实现
    print("🔙 回滚功能待实现")

def main():
    parser = argparse.ArgumentParser(description="Hyper-Evolution Engine v2.0")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # status
    subparsers.add_parser("status", help="查看系统状态")

    # evaluate
    eval_parser = subparsers.add_parser("evaluate", help="运行进化评估")
    eval_parser.add_argument("--execute", action="store_true", help="自动执行决策（如果置信度足够）")
    eval_parser.add_argument("--dry-run", action="store_true", help="试运行（不实际应用）")

    # collect
    subparsers.add_parser("collect", help="手动运行数据收集")

    # pause
    subparsers.add_parser("pause", help="暂停自动进化")

    # resume
    subparsers.add_parser("resume", help="恢复自动进化")

    # history
    history_parser = subparsers.add_parser("history", help="查看进化历史")
    history_parser.add_argument("--limit", type=int, default=20, help="显示条目数")

    # rollback
    rollback_parser = subparsers.add_parser("rollback", help="手动回滚")
    rollback_parser.add_argument("--to", help="回滚到指定备份")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 路由命令
    commands = {
        "status": cmd_status,
        "evaluate": cmd_evaluate,
        "collect": cmd_collect,
        "pause": cmd_pause,
        "resume": cmd_resume,
        "history": cmd_history,
        "rollback": cmd_rollback
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
