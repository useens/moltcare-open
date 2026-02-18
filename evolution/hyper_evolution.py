#!/usr/bin/env python3
"""
Hyper-Evolution Engine v3.0 - 十维高度智能化进化框架
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# 添加工作区到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from core import state, event_bus
from core.dimension_assessor import DimensionAssessor
from core.evolution_orchestrator import EvolutionOrchestrator
# 加载策略
# import strategies  # TODO: 实现后取消注释

def cmd_status(args):
    """查看十维评估状态"""
    print("🧬 Hyper-Evolution Engine v3.0")
    print("=" * 60)
    print(f"状态: {'✅ 启用' if state.get('evolution_enabled') else '⏸️ 暂停'}")
    print(f"当前模型: {state.get('current_model')}")
    print()
    
    assessor = DimensionAssessor()
    assessor.print_status()

def cmd_evaluate(args):
    """运行完整进化评估"""
    print("🔍 运行十维进化评估...")
    
    orchestrator = EvolutionOrchestrator()
    result = orchestrator.run_evolution_cycle(dry_run=args.dry_run)
    
    if not args.dry_run and result.get("executed_strategies"):
        print("\n⚡ 进化策略已执行!")
    
    print("\n" + "=" * 60)
    print(f"✅ 评估完成: {result.get('message')}")

def cmd_assess(args):
    """只评估不执行"""
    print("📊 评估十维状态...")
    
    assessor = DimensionAssessor()
    assessor.print_status()
    
    critical = assessor.get_critical_dimensions(40.0)
    if critical:
        print(f"\n⚠️  临界维度: {', '.join([assessor.DIMENSIONS[d]['name'] for d in critical])}")
    else:
        print(f"\n✅ 所有维度健康")

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
    
    if not DB_PATH.exists():
        print("📭 暂无进化历史")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 显示维度评分历史
    cursor.execute("""
        SELECT dimension, score, level, timestamp
        FROM dimension_history
        ORDER BY timestamp DESC
        LIMIT ?
    """, (args.limit,))
    
    rows = cursor.fetchall()
    
    if rows:
        print("📊 维度评分历史")
        print("=" * 60)
        for row in rows:
            print(f"{row['timestamp'][:19]} | {row['dimension']:12s} | {row['score']:5.1f}% | {row['level']}")
    
    conn.close()

def cmd_reset(args):
    """重置评分（谨慎使用）"""
    from core.dimension_assessor import SCORES_PATH
    
    if SCORES_PATH.exists():
        SCORES_PATH.unlink()
        print("🔄 评分已重置，将重新初始化")
    else:
        print("ℹ️  评分文件不存在")

def main():
    parser = argparse.ArgumentParser(
        description="Hyper-Evolution Engine v3.0 - 十维高度智能化进化框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python hyper_evolution.py status         # 查看十维状态
  python hyper_evolution.py assess         # 只评估不执行
  python hyper_evolution.py evaluate       # 运行完整评估（dry-run）
  python hyper_evolution.py evaluate --execute  # 执行进化
  python hyper_evolution.py history --limit 20
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # status
    status_parser = subparsers.add_parser("status", help="查看十维评估状态")

    # assess
    assess_parser = subparsers.add_parser("assess", help="只评估不执行")

    # evaluate
    eval_parser = subparsers.add_parser("evaluate", help="运行完整进化评估")
    eval_parser.add_argument("--execute", action="store_true", help="实际执行进化策略")
    eval_parser.add_argument("--dry-run", action="store_true", help="试运行（不实际应用）")

    # pause
    subparsers.add_parser("pause", help="暂停自动进化")

    # resume
    subparsers.add_parser("resume", help="恢复自动进化")

    # history
    history_parser = subparsers.add_parser("history", help="查看进化历史")
    history_parser.add_argument("--limit", type=int, default=20, help="显示条目数")

    # reset
    subparsers.add_parser("reset", help="重置评分（谨慎使用）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 路由命令
    commands = {
        "status": cmd_status,
        "assess": cmd_assess,
        "evaluate": cmd_evaluate,
        "pause": cmd_pause,
        "resume": cmd_resume,
        "history": cmd_history,
        "reset": cmd_reset
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
