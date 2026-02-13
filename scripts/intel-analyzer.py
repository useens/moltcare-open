#!/usr/bin/env python3
"""
情报分析工具
分析收集到的情报数据，提取高Signal内容
"""

import json
from datetime import datetime
from pathlib import Path

def analyze_intel(intel_file=None):
    """分析情报数据"""
    if intel_file is None:
        intel_file = Path("/root/.openclaw/workspace/memory/intel/latest.json")
    
    print(f"🔍 分析情报: {intel_file}")
    
    if not Path(intel_file).exists():
        print("⚠️  未找到情报文件")
        return
    
    with open(intel_file) as f:
        data = json.load(f)
    
    # 统计
    total = len(data.get("items", []))
    high_signal = [i for i in data.get("items", []) if i.get("signal", 0) >= 7]
    
    print(f"📊 分析结果:")
    print(f"  总条目: {total}")
    print(f"  高Signal: {len(high_signal)}")
    print(f"  发现率: {len(high_signal)/total*100:.1f}%" if total > 0 else "  发现率: N/A")
    
    # 显示高Signal内容
    if high_signal:
        print(f"\n🌟 高Signal内容:")
        for item in high_signal[:5]:
            print(f"  - {item.get('title', 'N/A')[:50]}... (Signal: {item.get('signal')})")

def main():
    print("="*60)
    print("🧠 情报分析工具")
    print("="*60)
    analyze_intel()
    print("="*60)

if __name__ == "__main__":
    main()
