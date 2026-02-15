#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速扫描模块 - L2级别 (每6小时执行)
功能: Token消耗检测、臃肿识别
"""

import os
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")
LOG_DIR = WORKSPACE / "memory/self-pruning"

def log(msg):
    """输出日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def check_token_usage():
    """检测Token消耗情况"""
    log("📊 检测Token消耗...")
    
    # 分析memory目录下的日志文件
    memory_dir = WORKSPACE / "memory"
    
    total_logs = 0
    large_logs = []
    
    if memory_dir.exists():
        for log_file in memory_dir.rglob("*.md"):
            try:
                size = log_file.stat().st_size
                total_logs += 1
                if size > 102400:  # >100KB
                    large_logs.append((log_file.name, size))
            except:
                pass
    
    log(f"  日志文件总数: {total_logs}")
    log(f"  大日志文件: {len(large_logs)}")
    
    for name, size in sorted(large_logs, key=lambda x: -x[1])[:5]:
        log(f"    - {name}: {size/1024:.1f}KB")
    
    # 返回是否有严重问题
    return len(large_logs) > 10

def check_bloated_files():
    """识别臃肿文件"""
    log("🗂️ 识别臃肿文件...")
    
    bloated = []
    
    # 检查各种临时和缓存文件
    patterns = [
        "*.tmp", "*.temp", "*.cache", "*.log", "*~",
        ".*.swp", ".*.swo", "*.bak", "*.old"
    ]
    
    total_size = 0
    for pattern in patterns:
        for f in WORKSPACE.rglob(pattern):
            try:
                if f.is_file():
                    size = f.stat().st_size
                    total_size += size
                    bloated.append((f.relative_to(WORKSPACE), size))
            except:
                pass
    
    log(f"  臃肿文件数: {len(bloated)}")
    log(f"  总占用: {total_size/1024:.1f}KB")
    
    # 检查空目录
    empty_dirs = []
    for d in WORKSPACE.rglob("*"):
        try:
            if d.is_dir() and not any(d.iterdir()):
                empty_dirs.append(d.relative_to(WORKSPACE))
        except:
            pass
    
    log(f"  空目录数: {len(empty_dirs)}")
    
    return len(bloated) > 50 or len(empty_dirs) > 20

def check_duplicate_patterns():
    """检查重复模式"""
    log("🔄 检查重复模式...")
    
    # 简单的重复文件名检测
    from collections import defaultdict
    
    name_counts = defaultdict(list)
    
    for f in WORKSPACE.rglob("*.py"):
        if f.is_file():
            name_counts[f.name].append(f.relative_to(WORKSPACE))
    
    duplicates = {k: v for k, v in name_counts.items() if len(v) > 1}
    
    if duplicates:
        log(f"  发现 {len(duplicates)} 个重复文件名:")
        for name, paths in list(duplicates.items())[:5]:
            log(f"    - {name}: {len(paths)} 处")
    else:
        log("  未发现重复文件名")
    
    return len(duplicates) > 5

def generate_scan_report(has_critical):
    """生成扫描报告"""
    report_file = LOG_DIR / "last-scan-report.txt"
    
    with open(report_file, 'w') as f:
        f.write(f"快速扫描报告 - {datetime.now()}\n")
        f.write("=" * 50 + "\n")
        
        if has_critical:
            f.write("CRITICAL: 发现需要深度评估的问题\n")
        else:
            f.write("STATUS: 正常\n")
    
    log(f"📄 扫描报告已保存: {report_file}")

def main():
    """快速扫描主流程"""
    log("=" * 50)
    log("🚀 快速扫描启动 (L2/MEDIUM)")
    log("=" * 50)
    
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 执行各项检查
    critical_token = check_token_usage()
    critical_bloat = check_bloated_files()
    critical_dup = check_duplicate_patterns()
    
    # 判断是否有严重问题
    has_critical = critical_token or critical_bloat or critical_dup
    
    if has_critical:
        log("⚠️ 发现需要关注的问题")
        # 创建L3触发标记
        trigger_file = LOG_DIR / ".l3-trigger"
        trigger_file.touch()
        log("🚨 已创建L3深度评估触发标记")
    else:
        log("✅ 系统状态良好")
    
    # 生成报告
    generate_scan_report(has_critical)
    
    log("=" * 50)
    log("✅ 快速扫描完成")
    
    return 0 if not has_critical else 1

if __name__ == "__main__":
    sys.exit(main())
