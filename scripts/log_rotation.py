#!/usr/bin/env python3
"""
日志轮转脚本 - 自动清理超过30天的日志
可通过cron定期执行
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from core.logging.unified_logger import get_logger

LOG_FILE = "logs/log_rotation.log"

def log_rotation_event(message: str):
    """记录轮转事件"""
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] {message}\n"
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_line)
    
    print(message)


def rotate_unified_logs():
    """执行统一日志轮转"""
    logger = get_logger()
    
    # 获取轮转前统计
    stats_before = logger.get_stats()
    log_rotation_event(f"轮转前: {stats_before['total_records']:,} 条记录, {stats_before['db_size_mb']} MB")
    
    # 执行轮转
    result = logger.rotate()
    
    # 获取轮转后统计
    stats_after = logger.get_stats()
    
    log_rotation_event(f"删除记录: {result['deleted_records']:,}")
    log_rotation_event(f"轮转后: {stats_after['total_records']:,} 条记录, {stats_after['db_size_mb']} MB")
    
    return {
        'deleted': result['deleted_records'],
        'before_count': stats_before['total_records'],
        'after_count': stats_after['total_records'],
        'before_size_mb': stats_before['db_size_mb'],
        'after_size_mb': stats_after['db_size_mb']
    }


def cleanup_old_jsonl_logs():
    """清理旧的JSONL日志文件"""
    old_files = [
        'data/diagnosis_history.jsonl',
        'data/heal_history.jsonl',
        'data/notifications.jsonl',
        'data/decision-engine.jsonl',
        '.autonomy/decision_history.jsonl'
    ]
    
    freed_space = 0
    for filepath in old_files:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            # 备份而不是直接删除
            backup_path = f"{filepath}.backup"
            os.rename(filepath, backup_path)
            freed_space += size
            log_rotation_event(f"已备份: {filepath} -> {backup_path}")
    
    return freed_space


def main():
    """主函数"""
    print("=" * 60)
    print("日志轮转脚本启动")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 60)
    
    log_rotation_event("=== 日志轮转开始 ===")
    
    # 1. 轮转统一日志
    log_rotation_event("\n[步骤1] 轮转统一日志数据库...")
    try:
        rotation_result = rotate_unified_logs()
        log_rotation_event("✅ 统一日志轮转完成")
    except Exception as e:
        log_rotation_event(f"❌ 统一日志轮转失败: {e}")
        rotation_result = None
    
    # 2. 清理旧JSONL文件
    log_rotation_event("\n[步骤2] 备份旧日志文件...")
    try:
        freed = cleanup_old_jsonl_logs()
        log_rotation_event(f"✅ 已备份旧日志文件, 释放: {freed / 1024 / 1024:.2f} MB")
    except Exception as e:
        log_rotation_event(f"❌ 旧日志备份失败: {e}")
        freed = 0
    
    # 汇总
    log_rotation_event("\n=== 轮转完成 ===")
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'rotation': rotation_result,
        'jsonl_freed_bytes': freed,
        'jsonl_freed_mb': round(freed / (1024 * 1024), 2)
    }
    
    print("\n📊 轮转结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


if __name__ == '__main__':
    main()
