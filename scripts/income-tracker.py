#!/usr/bin/env python3
"""
收入追踪系统 - 森森的赚钱仪表盘
实时追踪所有收入来源和进度
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass, asdict

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_FILE = WORKSPACE / "data" / "income-tracker.json"

@dataclass
class IncomeRecord:
    """收入记录"""
    date: str
    source: str  # evomap / consulting / templates / other
    description: str
    amount_cny: float
    amount_usd: float
    status: str  # pending / completed / cancelled
    client: str
    notes: str


class IncomeTracker:
    """收入追踪器"""
    
    # 收入目标 (月度)
    MONTHLY_TARGETS = {
        "week1": 5000,
        "week2": 10000,
        "week3": 15000,
        "week4": 20000
    }
    
    # 收入来源权重
    SOURCE_WEIGHTS = {
        "evomap": 0.30,      # 30% - EvoMap赏金
        "consulting": 0.40,  # 40% - 企业咨询
        "templates": 0.20,   # 20% - 脚本模板
        "other": 0.10        # 10% - 其他
    }
    
    def __init__(self):
        self.data_file = DATA_FILE
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.records = self._load_records()
    
    def _load_records(self) -> List[IncomeRecord]:
        """加载记录"""
        if self.data_file.exists():
            with open(self.data_file) as f:
                data = json.load(f)
                return [IncomeRecord(**r) for r in data.get("records", [])]
        return []
    
    def _save_records(self):
        """保存记录"""
        data = {
            "records": [asdict(r) for r in self.records],
            "updated_at": datetime.now().isoformat()
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_income(self, source: str, description: str, amount_cny: float,
                   client: str = "", notes: str = "", status: str = "completed"):
        """添加收入记录"""
        # 简单汇率转换
        amount_usd = amount_cny / 7.2
        
        record = IncomeRecord(
            date=datetime.now().strftime("%Y-%m-%d"),
            source=source,
            description=description,
            amount_cny=amount_cny,
            amount_usd=amount_usd,
            status=status,
            client=client,
            notes=notes
        )
        
        self.records.append(record)
        self._save_records()
        
        print(f"✅ 收入记录已添加: {source} +¥{amount_cny}")
        return record
    
    def get_stats(self) -> Dict:
        """获取统计数据"""
        # 按来源统计
        by_source = {}
        for record in self.records:
            if record.status == "completed":
                by_source[record.source] = by_source.get(record.source, 0) + record.amount_cny
        
        # 计算总额
        total_cny = sum(by_source.values())
        total_usd = total_cny / 7.2
        
        # 本月统计
        current_month = datetime.now().strftime("%Y-%m")
        month_records = [r for r in self.records 
                        if r.date.startswith(current_month) and r.status == "completed"]
        month_total = sum(r.amount_cny for r in month_records)
        
        # 今日统计
        today = datetime.now().strftime("%Y-%m-%d")
        today_records = [r for r in self.records if r.date == today and r.status == "completed"]
        today_total = sum(r.amount_cny for r in today_records)
        
        # 本周统计
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
        week_records = [r for r in self.records 
                       if r.date >= week_start and r.status == "completed"]
        week_total = sum(r.amount_cny for r in week_records)
        
        # 目标进度
        current_week = min(datetime.now().day // 7 + 1, 4)
        week_key = f"week{current_week}"
        target = self.MONTHLY_TARGETS.get(week_key, 20000)
        progress = (week_total / target * 100) if target > 0 else 0
        
        return {
            "total_cny": round(total_cny, 2),
            "total_usd": round(total_usd, 2),
            "month_total": round(month_total, 2),
            "week_total": round(week_total, 2),
            "today_total": round(today_total, 2),
            "by_source": {k: round(v, 2) for k, v in by_source.items()},
            "target": target,
            "progress": round(progress, 1),
            "record_count": len(self.records)
        }
    
    def print_dashboard(self):
        """打印仪表盘"""
        stats = self.get_stats()
        
        print("=" * 60)
        print("💰 森森收入仪表盘".center(60))
        print("=" * 60)
        
        print(f"\n📊 总收入: ¥{stats['total_cny']:,.2f} (${stats['total_usd']:,.2f})")
        print(f"📅 本月: ¥{stats['month_total']:,.2f}")
        print(f"📆 本周: ¥{stats['week_total']:,.2f}")
        print(f"☀️ 今日: ¥{stats['today_total']:,.2f}")
        
        print(f"\n🎯 周目标进度: {stats['progress']}% (目标: ¥{stats['target']:,})")
        
        # 进度条
        bar_length = 30
        filled = int(stats['progress'] / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"[{bar}] {stats['progress']:.1f}%")
        
        print(f"\n📈 收入来源分布:")
        for source, amount in stats['by_source'].items():
            percentage = (amount / stats['total_cny'] * 100) if stats['total_cny'] > 0 else 0
            print(f"  • {source}: ¥{amount:,.2f} ({percentage:.1f}%)")
        
        print(f"\n📝 记录数: {stats['record_count']} 条")
        
        print("\n" + "=" * 60)
        print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def get_quick_actions(self) -> List[Dict]:
        """获取快速行动建议"""
        stats = self.get_stats()
        actions = []
        
        # 检查本周进度
        if stats['progress'] < 50:
            actions.append({
                "priority": "high",
                "action": "紧急获取新客户",
                "suggestion": "发布服务广告，触达10个潜在客户"
            })
        
        # 检查收入来源平衡
        by_source = stats.get('by_source', {})
        for source, weight in self.SOURCE_WEIGHTS.items():
            current_weight = by_source.get(source, 0) / stats['total_cny'] if stats['total_cny'] > 0 else 0
            if current_weight < weight * 0.5:
                actions.append({
                    "priority": "medium",
                    "action": f"增加{source}收入",
                    "suggestion": f"当前占比 {current_weight*100:.1f}%，目标 {weight*100:.0f}%"
                })
        
        if not actions:
            actions.append({
                "priority": "low",
                "action": "保持当前节奏",
                "suggestion": "收入健康，继续执行计划"
            })
        
        return actions


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="收入追踪系统")
    parser.add_argument("--add", action="store_true", help="添加收入记录")
    parser.add_argument("--source", type=str, help="收入来源")
    parser.add_argument("--amount", type=float, help="金额(CNY)")
    parser.add_argument("--desc", type=str, help="描述")
    parser.add_argument("--client", type=str, default="", help="客户")
    parser.add_argument("--demo", action="store_true", help="添加演示数据")
    
    args = parser.parse_args()
    
    tracker = IncomeTracker()
    
    if args.add:
        if args.source and args.amount:
            tracker.add_income(
                source=args.source,
                description=args.desc or "收入",
                amount_cny=args.amount,
                client=args.client
            )
        else:
            print("❌ 请提供 --source 和 --amount")
    
    elif args.demo:
        # 添加演示数据
        tracker.add_income("consulting", "企业AI咨询", 3000, "客户A")
        tracker.add_income("templates", "数据处理器模板", 500, "客户B")
        tracker.add_income("evomap", "赏金任务完成", 800, "EvoMap")
        print("✅ 演示数据已添加")
    
    else:
        # 显示仪表盘
        tracker.print_dashboard()
        
        # 显示建议
        print("\n💡 快速行动建议:")
        for action in tracker.get_quick_actions():
            emoji = "🔴" if action['priority'] == 'high' else "🟡" if action['priority'] == 'medium' else "🟢"
            print(f"  {emoji} {action['action']}: {action['suggestion']}")


if __name__ == "__main__":
    main()
