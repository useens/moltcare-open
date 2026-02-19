#!/usr/bin/env python3
"""
日志迁移工具 - 将分散的日志文件迁移到统一SQLite存储
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import re

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../..')

from core.logging.unified_logger import UnifiedLogger, LogEntry

class LogMigrator:
    """日志迁移器"""
    
    # 定义要迁移的日志文件映射
    LOG_FILES = {
        'diagnosis': {
            'path': 'data/diagnosis_history.jsonl',
            'parser': 'parse_diagnosis'
        },
        'heal': {
            'path': 'data/heal_history.jsonl', 
            'parser': 'parse_heal'
        },
        'notification': {
            'path': 'data/notifications.jsonl',
            'parser': 'parse_notification'
        },
        'decision': {
            'path': '.autonomy/decision_history.jsonl',
            'parser': 'parse_decision'
        },
        'decision_engine': {
            'path': 'data/decision-engine.jsonl',
            'parser': 'parse_jsonl_generic'
        }
    }
    
    # 文本日志文件
    TEXT_LOGS = [
        ('logs/decision-engine.log', 'decision_engine_log'),
        ('logs/unified-monitor.log', 'monitor'),
        ('logs/optimization-execution.log', 'optimization'),
    ]
    
    def __init__(self, logger: UnifiedLogger = None):
        self.logger = logger or UnifiedLogger()
        self.stats = {
            'total_files': 0,
            'total_entries': 0,
            'migrated_entries': 0,
            'failed_entries': 0,
            'by_source': {}
        }
    
    def parse_timestamp(self, ts) -> datetime:
        """解析各种格式的时间戳"""
        if ts is None:
            return datetime.now()
        
        # 处理float类型的时间戳
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts)
        
        # 处理字符串
        ts_str = str(ts)
        ts_str = ts_str.replace('Z', '+00:00').replace('+00:00', '')
        
        try:
            return datetime.fromisoformat(ts_str)
        except ValueError:
            try:
                return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                try:
                    return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return datetime.now()
    
    def parse_diagnosis(self, data: Dict[str, Any]) -> List[LogEntry]:
        """解析诊断日志"""
        entries = []
        timestamp = self.parse_timestamp(data.get('timestamp'))
        
        # 整体状态记录
        entries.append(LogEntry(
            timestamp=timestamp,
            source='diagnosis',
            level='INFO' if data.get('overall_status') == 'healthy' else 'WARNING',
            message=f"诊断完成 - 状态: {data.get('overall_status')}, 分数: {data.get('overall_score', 0):.1f}",
            metadata={
                'overall_status': data.get('overall_status'),
                'overall_score': data.get('overall_score'),
                'recommendations': data.get('recommendations', []),
                'auto_heal_attempted': data.get('auto_heal_attempted')
            }
        ))
        
        # 每个检查项记录
        for check in data.get('checks', []):
            level_map = {
                'healthy': 'INFO',
                'warning': 'WARNING',
                'critical': 'ERROR',
                'unknown': 'DEBUG'
            }
            entries.append(LogEntry(
                timestamp=self.parse_timestamp(check.get('timestamp')),
                source='diagnosis',
                level=level_map.get(check.get('status'), 'INFO'),
                message=check.get('message', ''),
                metadata={
                    'component': check.get('component'),
                    'status': check.get('status'),
                    'score': check.get('score'),
                    'details': check.get('details')
                }
            ))
        
        return entries
    
    def parse_heal(self, data: Dict[str, Any]) -> List[LogEntry]:
        """解析修复日志"""
        entries = []
        timestamp = self.parse_timestamp(data.get('timestamp'))
        
        level_map = {
            'critical': 'CRITICAL',
            'high': 'ERROR',
            'medium': 'WARNING',
            'low': 'INFO'
        }
        
        entries.append(LogEntry(
            timestamp=timestamp,
            source='heal',
            level=level_map.get(data.get('severity'), 'INFO'),
            message=f"自动修复 - 触发原因: {data.get('trigger_reason')}, 成功: {data.get('overall_success')}",
            metadata={
                'trigger_reason': data.get('trigger_reason'),
                'severity': data.get('severity'),
                'overall_success': data.get('overall_success'),
                'needs_human_attention': data.get('needs_human_attention'),
                'actions': data.get('actions', [])
            }
        ))
        
        return entries
    
    def parse_notification(self, data: Dict[str, Any]) -> List[LogEntry]:
        """解析通知日志"""
        entries = []
        timestamp = self.parse_timestamp(data.get('timestamp'))
        
        entries.append(LogEntry(
            timestamp=timestamp,
            source='notification',
            level=data.get('level', 'INFO').upper(),
            message=data.get('message', '')[:500],  # 限制长度
            metadata={'full_message': data.get('message')}
        ))
        
        return entries
    
    def parse_decision(self, data: Dict[str, Any]) -> List[LogEntry]:
        """解析决策日志"""
        entries = []
        timestamp = self.parse_timestamp(data.get('timestamp'))
        
        entries.append(LogEntry(
            timestamp=timestamp,
            source='decision',
            level='INFO',
            message=f"决策记录 - 类型: {data.get('decision_type', 'unknown')}",
            metadata=data
        ))
        
        return entries
    
    def parse_jsonl_generic(self, data: Dict[str, Any]) -> List[LogEntry]:
        """通用JSONL解析"""
        entries = []
        timestamp = self.parse_timestamp(data.get('timestamp'))
        
        # 尝试提取级别
        level = 'INFO'
        if 'level' in data:
            level = str(data['level']).upper()
        elif 'status' in data:
            status = str(data['status']).lower()
            if status in ['error', 'failed', 'critical']:
                level = 'ERROR'
            elif status in ['warning', 'warn']:
                level = 'WARNING'
        
        entries.append(LogEntry(
            timestamp=timestamp,
            source='generic',
            level=level,
            message=json.dumps(data, ensure_ascii=False)[:1000],
            metadata=data
        ))
        
        return entries
    
    def parse_text_log(self, filepath: str, source: str) -> List[LogEntry]:
        """解析文本格式日志"""
        entries = []
        
        # 匹配格式: [2026-02-19 10:46:20,672] INFO: 消息
        pattern = r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}),?(\d{3})?\]\s*(\w+):\s*(.+)'
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    match = re.match(pattern, line)
                    if match:
                        date_str = match.group(1)
                        level = match.group(3).upper()
                        message = match.group(4)
                        
                        try:
                            timestamp = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            timestamp = datetime.now()
                        
                        entries.append(LogEntry(
                            timestamp=timestamp,
                            source=source,
                            level=level if level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] else 'INFO',
                            message=message[:1000],
                            metadata={'raw_line': line[:500]}
                        ))
        except Exception as e:
            print(f"  解析文件失败 {filepath}: {e}")
        
        return entries
    
    def migrate_file(self, filepath: str, source: str, parser_name: str) -> int:
        """迁移单个文件"""
        if not os.path.exists(filepath):
            print(f"  跳过: 文件不存在 {filepath}")
            return 0
        
        print(f"  迁移: {filepath} -> source={source}")
        
        count = 0
        parser = getattr(self, parser_name)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        entries = parser(data)
                        if entries:
                            self.logger.log_batch(entries)
                            count += len(entries)
                    except json.JSONDecodeError:
                        self.stats['failed_entries'] += 1
                    except Exception as e:
                        print(f"    处理行失败: {e}")
                        self.stats['failed_entries'] += 1
        except Exception as e:
            print(f"  读取文件失败: {e}")
        
        return count
    
    def migrate_all(self) -> Dict[str, Any]:
        """执行所有迁移"""
        print("=" * 60)
        print("开始日志迁移")
        print("=" * 60)
        
        # 迁移JSONL文件
        for source, config in self.LOG_FILES.items():
            print(f"\n[JSONL] 处理源: {source}")
            count = self.migrate_file(
                config['path'],
                source,
                config['parser']
            )
            self.stats['by_source'][source] = count
            self.stats['total_entries'] += count
            print(f"  迁移 {count} 条记录")
        
        # 迁移文本日志
        for filepath, source in self.TEXT_LOGS:
            print(f"\n[TEXT] 处理: {filepath}")
            if os.path.exists(filepath):
                entries = self.parse_text_log(filepath, source)
                if entries:
                    self.logger.log_batch(entries)
                    count = len(entries)
                    self.stats['by_source'][source] = self.stats['by_source'].get(source, 0) + count
                    self.stats['total_entries'] += count
                    print(f"  迁移 {count} 条记录")
            else:
                print(f"  跳过: 文件不存在")
        
        self.stats['migrated_entries'] = self.stats['total_entries']
        
        print("\n" + "=" * 60)
        print("迁移完成")
        print("=" * 60)
        
        return self.stats
    
    def get_space_savings(self) -> Dict[str, Any]:
        """计算存储空间优化情况"""
        original_size = 0
        
        # 计算原始日志文件总大小
        for source, config in self.LOG_FILES.items():
            filepath = config['path']
            if os.path.exists(filepath):
                original_size += os.path.getsize(filepath)
        
        for filepath, _ in self.TEXT_LOGS:
            if os.path.exists(filepath):
                original_size += os.path.getsize(filepath)
        
        # 获取新数据库大小
        db_size = os.path.getsize(self.logger.db_path) if os.path.exists(self.logger.db_path) else 0
        
        savings = original_size - db_size if original_size > 0 else 0
        savings_pct = (savings / original_size * 100) if original_size > 0 else 0
        
        return {
            'original_size_bytes': original_size,
            'original_size_mb': round(original_size / (1024 * 1024), 2),
            'new_size_bytes': db_size,
            'new_size_mb': round(db_size / (1024 * 1024), 2),
            'savings_bytes': savings,
            'savings_mb': round(savings / (1024 * 1024), 2),
            'savings_percent': round(savings_pct, 2)
        }


def main():
    """主函数"""
    print("日志迁移工具启动")
    
    migrator = LogMigrator()
    stats = migrator.migrate_all()
    space_stats = migrator.get_space_savings()
    
    print("\n📊 迁移统计:")
    print(f"  总条目数: {stats['total_entries']}")
    print(f"  失败条目: {stats['failed_entries']}")
    for source, count in stats['by_source'].items():
        print(f"    - {source}: {count} 条")
    
    print("\n💾 存储空间对比:")
    print(f"  原始大小: {space_stats['original_size_mb']} MB")
    print(f"  新数据库: {space_stats['new_size_mb']} MB")
    print(f"  节省空间: {space_stats['savings_mb']} MB ({space_stats['savings_percent']}%)")
    
    # 验证查询
    print("\n✅ 验证查询:")
    logger = migrator.logger
    results = logger.query(limit=5)
    for r in results:
        print(f"  [{r['timestamp']}] {r['source']} - {r['level']}")
    
    return stats, space_stats


if __name__ == '__main__':
    main()
