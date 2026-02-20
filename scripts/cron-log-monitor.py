#!/usr/bin/env python3
"""
Cron 日志自动监控器
每小时检查所有 cron 任务日志，发现错误立即报告
"""

import json
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
LOGS_DIR = WORKSPACE / "logs"
REPORTS_DIR = WORKSPACE / "reports"

# 错误关键词
ERROR_PATTERNS = [
    r"permission denied",
    r"permission denied",
    r"error",
    r"fail",
    r"fatal",
    r"traceback",
    r"exception",
    r"not found",
    r"no such file",
    r"command not found",
    r"denied",
]

# 需要监控的 cron 日志文件
CRON_LOGS = [
    "task-hunter-cron.log",
    "monitor-cron.log", 
    "evomap-cron.log",
    "cron-decision.log",
    "cron-learning.log",
    "cron-system.log",
    "night-evolution-cron.log",
    "memory-backup-cron.log",
    "data/moltbook/cron-active-hours.log",
    "data/moltbook/cron-moderate-hours.log",
    "data/moltbook/cron-light-hours.log",
    "data/moltbook/cron-activity.log",
    "data/moltbook/cron-deep-learning.log",
]

def check_log_for_errors(log_file):
    """检查单个日志文件的最近错误"""
    if not log_file.exists():
        return []
    
    errors = []
    try:
        with open(log_file, 'r', errors='ignore') as f:
            lines = f.readlines()
            # 只检查最近100行
            recent_lines = lines[-100:] if len(lines) > 100 else lines
            
            for i, line in enumerate(recent_lines, 1):
                line_lower = line.lower()
                for pattern in ERROR_PATTERNS:
                    if re.search(pattern, line_lower):
                        errors.append({
                            'line_num': len(lines) - len(recent_lines) + i,
                            'content': line.strip()[:200],
                            'pattern': pattern
                        })
                        break
    except Exception as e:
        errors.append({'error': f'无法读取日志: {e}'})
    
    return errors

def main():
    """主函数"""
    print("=" * 60)
    print("🛡️  Cron 日志监控器")
    print("=" * 60)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    all_errors = []
    
    for log_name in CRON_LOGS:
        log_path = LOGS_DIR / log_name
        errors = check_log_for_errors(log_path)
        
        if errors:
            all_errors.append({
                'log': log_name,
                'errors': errors
            })
            print(f"❌ {log_name}: 发现 {len(errors)} 个错误")
        else:
            print(f"✅ {log_name}: 正常")
    
    print()
    
    # 如果有错误，生成报告
    if all_errors:
        print("=" * 60)
        print("🚨 发现错误，需要立即处理！")
        print("=" * 60)
        
        for item in all_errors:
            print(f"\n📄 {item['log']}:")
            for err in item['errors'][:3]:  # 只显示前3个
                print(f"   行 {err.get('line_num', '?')}: {err.get('content', err)}")
        
        # 保存报告
        report_file = REPORTS_DIR / f"cron-errors-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
        REPORTS_DIR.mkdir(exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'errors': all_errors
            }, f, indent=2)
        
        print(f"\n💾 详细报告: {report_file}")
        
        # 返回错误状态
        return 1
    else:
        print("✅ 所有 cron 任务运行正常")
        return 0

if __name__ == "__main__":
    exit(main())
