#!/usr/bin/env python3
"""
决策效果分析器 - 增强反馈闭环
"""
import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"

def analyze_decision_effectiveness():
    """分析决策效果"""
    outcomes_file = DATA_DIR / "decision-outcomes.jsonl"
    
    if not outcomes_file.exists():
        print("⚠️ 无决策效果数据")
        return
    
    lines = outcomes_file.read_text().strip().split('\n')
    print(f"决策效果记录: {len(lines)}条")
    
    # 简单分析
    successful = 0
    failed = 0
    
    for line in lines:
        try:
            data = json.loads(line)
            if data.get('success', False):
                successful += 1
            else:
                failed += 1
        except:
            pass
    
    success_rate = successful / len(lines) * 100 if lines else 0
    
    print(f"  成功: {successful}")
    print(f"  失败: {failed}")
    print(f"  成功率: {success_rate:.1f}%")
    
    # 记录分析结果
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "total_decisions": len(lines),
        "successful": successful,
        "failed": failed,
        "success_rate": success_rate,
        "feedback_loop_status": "active" if len(lines) > 50 else "building"
    }
    
    analysis_file = WORKSPACE / "memory" / "self-upgrade" / "decision-effectiveness-analysis.json"
    analysis_file.parent.mkdir(parents=True, exist_ok=True)
    analysis_file.write_text(json.dumps(analysis, indent=2))
    
    print(f"✅ 决策效果分析已保存: {analysis_file}")
    
    return analysis

if __name__ == "__main__":
    analyze_decision_effectiveness()
