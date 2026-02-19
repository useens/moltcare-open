#!/usr/bin/env python3
"""
日志系统验证脚本
测试SQLite数据库的读写功能和查询接口
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.unified_logger import UnifiedLogger
import json


def test_write_operations(logger):
    """测试写入操作"""
    print("\n" + "=" * 60)
    print("测试1: 写入操作")
    print("=" * 60)
    
    # 写入测试数据
    logger.log('test-source', 'INFO', '这是一条测试INFO日志')
    logger.log('test-source', 'WARN', '这是一条测试WARN日志')
    logger.log('test-source', 'ERROR', '这是一条测试ERROR日志', extra={'error_code': 500})
    logger.log('test-source', 'INFO', '带自定义时间戳的日志', timestamp='2026-02-19T14:00:00.000000')
    
    print("✅ 成功写入 4 条测试日志")


def test_query_operations(logger):
    """测试查询操作"""
    print("\n" + "=" * 60)
    print("测试2: 查询操作")
    print("=" * 60)
    
    # 查询所有test-source的日志
    results = logger.query(source='test-source')
    print(f"\n📊 查询 test-source 日志 (共 {len(results)} 条):")
    for row in results[:5]:  # 只显示前5条
        extra = json.loads(row['extra_metadata']) if row['extra_metadata'] else None
        extra_str = f" | extra: {extra}" if extra else ""
        print(f"  [{row['timestamp']}] [{row['level']}] {row['message']}{extra_str}")
    
    # 按级别过滤
    print(f"\n📊 查询 ERROR 级别日志:")
    error_logs = logger.query(level='ERROR')
    print(f"  共 {len(error_logs)} 条ERROR日志")
    for row in error_logs:
        print(f"  - {row['source']}: {row['message']}")
    
    # 按来源和级别过滤
    print(f"\n📊 查询 upgrade-daemon 的 WARN 日志:")
    warn_logs = logger.query(source='upgrade-daemon', level='WARN', limit=10)
    print(f"  共 {len(warn_logs)} 条")
    for row in warn_logs:
        print(f"  {row['timestamp']}: {row['message'][:80]}")


def test_query_by_time_range(logger):
    """测试时间范围查询"""
    print("\n" + "=" * 60)
    print("测试3: 时间范围查询")
    print("=" * 60)
    
    # 查询最近的时间范围
    start_time = '2026-02-19 10:00:00'
    end_time = '2026-02-19 14:00:00'
    
    results = logger.query_by_time_range(start_time, end_time)
    print(f"\n📊 时间范围查询 ({start_time} ~ {end_time}):")
    print(f"  共 {len(results)} 条日志")
    
    # 按来源分组统计
    by_source = {}
    for row in results:
        source = row['source']
        by_source[source] = by_source.get(source, 0) + 1
    
    print(f"\n  按来源分布:")
    for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
        print(f"    - {source}: {count} 条")


def test_stats(logger):
    """测试统计信息"""
    print("\n" + "=" * 60)
    print("测试4: 统计信息")
    print("=" * 60)
    
    stats = logger.get_stats()
    
    print(f"\n📊 总体统计:")
    print(f"  总记录数: {stats['total_count']}")
    print(f"  时间范围:")
    print(f"    最早: {stats['time_range']['earliest']}")
    print(f"    最新: {stats['time_range']['latest']}")
    
    print(f"\n📊 按来源统计 (Top 10):")
    sorted_sources = sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True)
    for source, count in sorted_sources[:10]:
        print(f"  - {source}: {count} 条")
    
    print(f"\n📊 按级别统计:")
    sorted_levels = sorted(stats['by_level'].items(), key=lambda x: x[1], reverse=True)
    for level, count in sorted_levels:
        print(f"  - {level}: {count} 条")


def test_sources_list(logger):
    """测试获取来源列表"""
    print("\n" + "=" * 60)
    print("测试5: 获取来源列表")
    print("=" * 60)
    
    sources = logger.get_sources()
    print(f"\n📊 所有日志来源 ({len(sources)} 个):")
    for source in sources:
        print(f"  - {source}")


def main():
    """主测试函数"""
    print("=" * 60)
    print("SQLite日志系统验证")
    print("=" * 60)
    
    # 创建logger实例
    logger = UnifiedLogger(db_path='data/unified_logs.db')
    
    try:
        # 运行所有测试
        test_write_operations(logger)
        test_query_operations(logger)
        test_query_by_time_range(logger)
        test_stats(logger)
        test_sources_list(logger)
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.close()


if __name__ == '__main__':
    main()
