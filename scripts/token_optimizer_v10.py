#!/usr/bin/env python3
"""
Token优化监控器 v1.0
功能: 监控Token使用 + 自动优化建议 + 预警机制
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class TokenOptimizer:
    """Token优化器"""
    
    def __init__(self):
        self.log_file = Path("/root/.openclaw/workspace/data/token-usage.log")
        self.thresholds = {
            "daily_limit": 100000,  # 每日Token上限
            "single_limit": 5000,   # 单次Token上限
            "warning": 80000,       # 预警阈值
        }
        
    def log_usage(self, operation: str, tokens_in: int, tokens_out: int):
        """记录Token使用"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "total": tokens_in + tokens_out,
        }
        
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_daily_stats(self) -> Dict:
        """获取每日统计"""
        if not self.log_file.exists():
            return {"total": 0, "count": 0, "avg": 0}
        
        today = datetime.now().strftime("%Y-%m-%d")
        total = 0
        count = 0
        
        with open(self.log_file) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry["timestamp"].startswith(today):
                        total += entry["total"]
                        count += 1
                except:
                    continue
        
        return {
            "total": total,
            "count": count,
            "avg": total // count if count > 0 else 0,
            "limit": self.thresholds["daily_limit"],
            "remaining": self.thresholds["daily_limit"] - total,
        }
    
    def check_optimization(self, text: str) -> List[str]:
        """检查优化建议"""
        suggestions = []
        
        # 检查长度
        lines = text.split("\n")
        if len(lines) > 50:
            suggestions.append(f"输出过长 ({len(lines)}行)，建议精简到30行以内")
        
        # 检查重复
        if text.count("✅") > 10:
            suggestions.append("重复标记过多，建议合并同类项")
        
        # 检查表格使用
        if "|" not in text and len(lines) > 20:
            suggestions.append("长文本建议使用表格格式")
        
        return suggestions
    
    def generate_report(self) -> str:
        """生成Token使用报告"""
        stats = self.get_daily_stats()
        
        lines = [
            f"📊 Token使用报告 ({datetime.now().strftime('%m/%d')})",
            "",
            f"今日使用: {stats['total']:,} / {stats['limit']:,} ({stats['total']/stats['limit']*100:.1f}%)",
            f"操作次数: {stats['count']}",
            f"平均每次: {stats['avg']:,}",
            f"剩余额度: {stats['remaining']:,}",
        ]
        
        if stats['total'] > self.thresholds["warning"]:
            lines.append("⚠️  预警: 今日Token使用已超过80%")
        
        return "\n".join(lines)

# 全局实例
token_optimizer = TokenOptimizer()

def log_token_usage(operation: str, tokens_in: int, tokens_out: int):
    """便捷函数: 记录Token使用"""
    token_optimizer.log_usage(operation, tokens_in, tokens_out)

def get_token_report() -> str:
    """便捷函数: 获取Token报告"""
    return token_optimizer.generate_report()

if __name__ == "__main__":
    # 测试
    optimizer = TokenOptimizer()
    
    # 模拟记录
    optimizer.log_usage("情报收集", 100, 50)
    optimizer.log_usage("任务执行", 200, 100)
    
    # 生成报告
    print(optimizer.generate_report())
