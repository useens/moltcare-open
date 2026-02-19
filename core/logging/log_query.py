#!/usr/bin/env python3
"""
日志查询CLI工具 - 统一日志查询接口
"""

import argparse
import json
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../..')

from core.logging.unified_logger import get_logger

class LogQueryCLI:
    """日志查询命令行接口"""
    
    def __init__(self):
        self.logger = get_logger()
    
    def parse_datetime(self, s: str) -> datetime:
        """解析日期时间字符串"""
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        raise ValueError(f"无法解析日期: {s}")
    
    def cmd_query(self, args):
        """查询日志命令"""
        start_time = None
        end_time = None
        
        if args.since:
            start_time = self.parse_datetime(args.since)
        if args.until:
            end_time = self.parse_datetime(args.until)
        if args.last:
            # 最近N小时/天
            if args.last.endswith('h'):
                hours = int(args.last[:-1])
                start_time = datetime.now() - timedelta(hours=hours)
            elif args.last.endswith('d'):
                days = int(args.last[:-1])
                start_time = datetime.now() - timedelta(days=days)
        
        results = self.logger.query(
            source=args.source,
            level=args.level,
            min_level=args.min_level,
            start_time=start_time,
            end_time=end_time,
            keyword=args.keyword,
            limit=args.limit,
            offset=args.offset
        )
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for entry in results:
                ts = entry['timestamp'][:19]  # 截断到秒
                source = entry['source'][:12].ljust(12)
                level = entry['level'][:8].ljust(8)
                message = entry['message'][:80]
                if len(entry['message']) > 80:
                    message += '...'
                print(f"[{ts}] [{source}] [{level}] {message}")
        
        # 输出统计
        count = self.logger.count(
            source=args.source,
            level=args.level,
            min_level=args.min_level,
            start_time=start_time,
            end_time=end_time,
            keyword=args.keyword
        )
        print(f"\n总计: {count} 条记录 (显示 {len(results)} 条)", file=sys.stderr)
    
    def cmd_stats(self, args):
        """统计命令"""
        stats = self.logger.get_stats()
        
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print("📊 日志统计信息")
            print("=" * 50)
            print(f"总记录数: {stats['total_records']:,}")
            print(f"数据库大小: {stats['db_size_mb']} MB")
            print(f"时间范围: {stats['time_range']['min']} ~ {stats['time_range']['max']}")
            
            print("\n📁 按来源分布:")
            for source, count in sorted(stats['by_source'].items(), key=lambda x: -x[1]):
                pct = count / stats['total_records'] * 100 if stats['total_records'] > 0 else 0
                print(f"  {source:15} {count:8,} ({pct:5.1f}%)")
            
            print("\n📈 按级别分布:")
            for level, count in sorted(stats['by_level'].items(), key=lambda x: -x[1]):
                pct = count / stats['total_records'] * 100 if stats['total_records'] > 0 else 0
                print(f"  {level:8} {count:8,} ({pct:5.1f}%)")
    
    def cmd_sources(self, args):
        """列出所有来源"""
        stats = self.logger.get_stats()
        sources = list(stats['by_source'].keys())
        
        if args.json:
            print(json.dumps(sources, ensure_ascii=False))
        else:
            print("可用日志来源:")
            for source in sorted(sources):
                count = stats['by_source'][source]
                print(f"  - {source} ({count:,} 条)")
    
    def cmd_rotate(self, args):
        """执行日志轮转"""
        result = self.logger.rotate(args.archive_dir)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("🗑️  日志轮转完成")
            print(f"  删除记录: {result['deleted_records']:,}")
            print(f"  截止时间: {result['cutoff_date']}")
            print(f"  保留天数: {result['retention_days']} 天")
    
    def cmd_export(self, args):
        """导出日志"""
        start_time = None
        end_time = None
        
        if args.since:
            start_time = self.parse_datetime(args.since)
        if args.until:
            end_time = self.parse_datetime(args.until)
        
        count = self.logger.export_to_jsonl(
            args.output,
            source=args.source,
            start_time=start_time,
            end_time=end_time
        )
        
        print(f"✅ 导出完成: {count} 条记录到 {args.output}")
    
    def cmd_tail(self, args):
        """实时跟踪日志"""
        import time
        
        last_time = datetime.now() - timedelta(seconds=5)
        
        try:
            while True:
                results = self.logger.query(
                    source=args.source,
                    level=args.level,
                    min_level=args.min_level,
                    start_time=last_time,
                    limit=100
                )
                
                # 倒序输出
                for entry in reversed(results):
                    ts = entry['timestamp'][:19]
                    source = entry['source'][:12].ljust(12)
                    level = entry['level'][:8].ljust(8)
                    print(f"[{ts}] [{source}] [{level}] {entry['message'][:100]}")
                
                if results:
                    last_time = datetime.fromisoformat(results[0]['timestamp'].replace('Z', '+00:00').replace('+00:00', ''))
                
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n跟踪已停止")
    
    def run(self):
        """运行CLI"""
        parser = argparse.ArgumentParser(
            description='统一日志查询工具',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用示例:
  # 查询最近1小时的ERROR级别日志
  %(prog)s query --last 1h --min-level ERROR
  
  # 查询特定来源的日志
  %(prog)s query --source diagnosis --limit 20
  
  # 按关键词搜索
  %(prog)s query --keyword "CPU" --since "2026-02-01"
  
  # 查看统计信息
  %(prog)s stats
  
  # 导出日志到文件
  %(prog)s export --output logs_export.jsonl --since "2026-02-01"
  
  # 实时跟踪日志
  %(prog)s tail --source diagnosis --interval 5
"""
        )
        
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # query 命令
        query_parser = subparsers.add_parser('query', help='查询日志')
        query_parser.add_argument('--source', '-s', help='按来源过滤')
        query_parser.add_argument('--level', '-l', help='按确切级别过滤')
        query_parser.add_argument('--min-level', help='按最小级别过滤')
        query_parser.add_argument('--since', help='开始时间 (如: 2026-02-01)')
        query_parser.add_argument('--until', help='结束时间')
        query_parser.add_argument('--last', help='最近时间 (如: 1h, 1d)')
        query_parser.add_argument('--keyword', '-k', help='关键词搜索')
        query_parser.add_argument('--limit', type=int, default=50, help='返回数量')
        query_parser.add_argument('--offset', type=int, default=0, help='分页偏移')
        query_parser.add_argument('--json', action='store_true', help='JSON输出')
        
        # stats 命令
        stats_parser = subparsers.add_parser('stats', help='查看统计信息')
        stats_parser.add_argument('--json', action='store_true', help='JSON输出')
        
        # sources 命令
        sources_parser = subparsers.add_parser('sources', help='列出所有来源')
        sources_parser.add_argument('--json', action='store_true', help='JSON输出')
        
        # rotate 命令
        rotate_parser = subparsers.add_parser('rotate', help='执行日志轮转')
        rotate_parser.add_argument('--archive-dir', default='data/log_archives', help='归档目录')
        rotate_parser.add_argument('--json', action='store_true', help='JSON输出')
        
        # export 命令
        export_parser = subparsers.add_parser('export', help='导出日志')
        export_parser.add_argument('--output', '-o', required=True, help='输出文件')
        export_parser.add_argument('--source', help='按来源过滤')
        export_parser.add_argument('--since', help='开始时间')
        export_parser.add_argument('--until', help='结束时间')
        
        # tail 命令
        tail_parser = subparsers.add_parser('tail', help='实时跟踪日志')
        tail_parser.add_argument('--source', help='按来源过滤')
        tail_parser.add_argument('--level', help='按级别过滤')
        tail_parser.add_argument('--min-level', help='按最小级别过滤')
        tail_parser.add_argument('--interval', type=int, default=5, help='刷新间隔(秒)')
        
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        # 执行命令
        commands = {
            'query': self.cmd_query,
            'stats': self.cmd_stats,
            'sources': self.cmd_sources,
            'rotate': self.cmd_rotate,
            'export': self.cmd_export,
            'tail': self.cmd_tail
        }
        
        commands[args.command](args)


def main():
    cli = LogQueryCLI()
    cli.run()


if __name__ == '__main__':
    main()
