#!/usr/bin/env python3
"""
日志迁移脚本
将现有的三个主要日志文件迁移到SQLite数据库
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.unified_logger import UnifiedLogger


def migrate_all_logs():
    """迁移所有主要日志文件"""
    
    # 创建日志系统实例
    logger = UnifiedLogger(db_path='data/unified_logs.db')
    
    # 定义要迁移的日志文件
    log_files = [
        ('logs/upgrade-daemon.log', 'upgrade-daemon'),
        ('logs/decision-engine.log', 'decision-engine'),
        ('logs/unified-monitor.log', 'unified-monitor'),
    ]
    
    print("=" * 60)
    print("开始日志迁移")
    print("=" * 60)
    
    total_success = 0
    total_skip = 0
    
    for log_file, source_name in log_files:
        if not os.path.exists(log_file):
            print(f"⚠️  文件不存在: {log_file}")
            continue
        
        print(f"\n📁 迁移文件: {log_file} -> {source_name}")
        print("-" * 60)
        
        success, skip = logger.migrate_from_file(log_file, source_name)
        
        print(f"✅ 成功: {success} 条")
        print(f"⏭️  跳过: {skip} 条")
        
        total_success += success
        total_skip += skip
    
    print("\n" + "=" * 60)
    print("迁移完成")
    print("=" * 60)
    print(f"总计成功: {total_success} 条")
    print(f"总计跳过: {total_skip} 条")
    
    # 获取统计信息
    stats = logger.get_stats()
    print(f"\n数据库统计信息:")
    print(f"  总记录数: {stats['total_count']}")
    print(f"  时间范围: {stats['time_range']['earliest']} 到 {stats['time_range']['latest']}")
    print(f"\n按来源统计:")
    for source, count in stats['by_source'].items():
        print(f"  - {source}: {count} 条")
    
    print(f"\n按级别统计:")
    for level, count in stats['by_level'].items():
        print(f"  - {level}: {count} 条")
    
    # 获取来源列表
    sources = logger.get_sources()
    print(f"\n所有日志来源: {', '.join(sources)}")
    
    logger.close()


if __name__ == '__main__':
    migrate_all_logs()
