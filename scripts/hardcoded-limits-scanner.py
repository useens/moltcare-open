#!/usr/bin/env python3
"""
硬编码限制扫描器 - 识别并记录代码中的限制
"""
import re
import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")

def scan_hardcoded_limits():
    """扫描硬编码限制"""
    limits_found = []
    
    # 扫描模式
    patterns = [
        (r'limit\s*=\s*(\d+)', 'variable_limit'),
        (r'max_\w+\s*=\s*(\d+)', 'max_variable'),
        (r'min_\w+\s*=\s*(\d+)', 'min_variable'),
        (r'range\((\d+)\)', 'range_limit'),
        (r'\[:(\d+)\]', 'slice_limit'),
        (r'timeout\s*=\s*(\d+)', 'timeout_limit'),
        (r'retry\s*=\s*(\d+)', 'retry_limit'),
        (r'count\s*[=:]\s*(\d+)', 'count_limit'),
        (r'size\s*[=:]\s*(\d+)', 'size_limit'),
    ]
    
    scanned = 0
    for py_file in WORKSPACE.rglob("*.py"):
        if scanned > 200:
            break
        if "venv" in str(py_file) or ".git" in str(py_file):
            continue
            
        try:
            content = py_file.read_text()
            scanned += 1
            
            for pattern, limit_type in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    value = match.group(1)
                    
                    limits_found.append({
                        "file": str(py_file.relative_to(WORKSPACE)),
                        "line": line_num,
                        "type": limit_type,
                        "value": value,
                        "context": content.split('\n')[line_num-1].strip()[:80]
                    })
        except:
            pass
    
    # 去重和分类
    critical_limits = [l for l in limits_found if int(l['value']) < 100 and l['type'] in ['timeout_limit', 'retry_limit']]
    high_limits = [l for l in limits_found if 100 <= int(l['value']) < 1000]
    normal_limits = [l for l in limits_found if int(l['value']) >= 1000]
    
    # 保存结果
    limits_report = {
        "timestamp": datetime.now().isoformat(),
        "total_scanned": scanned,
        "limits_found": len(limits_found),
        "critical_limits": critical_limits[:20],  # 只保留前20个
        "high_limits_count": len(high_limits),
        "normal_limits_count": len(normal_limits),
        "recommendations": [
            "Review timeout limits - may be too restrictive",
            "Consider making hardcoded values configurable",
            "Add documentation for limit rationale"
        ]
    }
    
    report_file = WORKSPACE / "memory" / "self-upgrade" / "limits-removed.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(limits_report, indent=2))
    
    print(f"扫描完成:")
    print(f"  扫描文件数: {scanned}")
    print(f"  发现限制: {len(limits_found)}")
    print(f"  关键限制: {len(critical_limits)}")
    print(f"  报告保存: {report_file}")
    
    return limits_report

if __name__ == "__main__":
    scan_hardcoded_limits()
