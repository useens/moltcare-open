#!/usr/bin/env python3
"""
超精简汇报模板 v1.0
目标: 最大化节约Token，保持关键信息
"""

from datetime import datetime
from typing import Dict, List

class MinimalReporter:
    """极简汇报器"""
    
    @staticmethod
    def result_table(headers: List[str], rows: List[List]) -> str:
        """表格格式 (最省Token)"""
        lines = ["| " + " | ".join(headers) + " |"]
        lines.append("|" + "|".join(["---" for _ in headers]) + "|")
        for row in rows:
            lines.append("| " + " | ".join([str(c) for c in row]) + " |")
        return "\n".join(lines)
    
    @staticmethod
    def status_line(emoji: str, item: str, status: str) -> str:
        """单行状态 (省Token)"""
        return f"{emoji} {item}: {status}"
    
    @staticmethod
    def summary(title: str, stats: Dict) -> str:
        """极简总结"""
        lines = [f"📊 {title} ({datetime.now().strftime('%m/%d')})"]
        for k, v in stats.items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)
    
    @staticmethod
    def verify_result(component: str, passed: bool, details: str = "") -> str:
        """验证结果 (极简)"""
        status = "✅" if passed else "❌"
        if details:
            return f"{status} {component} ({details})"
        return f"{status} {component}"

# 使用示例
if __name__ == "__main__":
    reporter = MinimalReporter()
    
    # 示例1: 表格
    print("示例1 - 表格:")
    print(reporter.result_table(
        ["组件", "状态", "Token"],
        [
            ["情报收集", "✅", "0"],
            ["任务执行", "✅", "150"],
            ["汇报", "✅", "200"],
        ]
    ))
    print()
    
    # 示例2: 单行状态
    print("示例2 - 状态:")
    print(reporter.status_line("✅", "验证1", "通过"))
    print(reporter.status_line("✅", "验证2", "通过"))
    print(reporter.status_line("✅", "验证3", "通过"))
    print()
    
    # 示例3: 极简总结
    print("示例3 - 总结:")
    print(reporter.summary("测试", {
        "通过": "3/3",
        "耗时": "1.2s",
        "Token": "350",
    }))
    print()
    
    # 示例4: 验证结果
    print("示例4 - 验证:")
    print(reporter.verify_result("功能测试", True, "14行"))
    print(reporter.verify_result("零Token", True, "0调用"))
