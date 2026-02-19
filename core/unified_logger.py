"""
简化版日志聚合系统
支持SQLite存储和基础查询接口
"""

import sqlite3
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class UnifiedLogger:
    """统一日志系统 - SQLite存储"""
    
    def __init__(self, db_path='data/unified_logs.db'):
        """初始化日志系统
        
        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = db_path
        # 确保data目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_table()
    
    def _init_table(self):
        """初始化日志表"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT,
                timestamp TEXT NOT NULL,
                extra_metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引以加速查询
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_source ON logs(source)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_level ON logs(level)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp)')
        
        self.conn.commit()
    
    def log(self, source: str, level: str, message: str, 
            timestamp: Optional[str] = None, extra: Optional[Dict] = None):
        """写入单条日志
        
        Args:
            source: 日志来源（如 upgrade-daemon, decision-engine）
            level: 日志级别
            message: 日志消息
            timestamp: 可选的时间戳字符串
            extra: 额外的元数据
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        extra_json = json.dumps(extra) if extra else None
        
        self.conn.execute('''
            INSERT INTO logs (source, level, message, timestamp, extra_metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (source, level, message, timestamp, extra_json))
        
        self.conn.commit()
    
    def query(self, source: Optional[str] = None, 
              level: Optional[str] = None,
              limit: int = 100) -> List[Dict]:
        """基础查询接口
        
        Args:
            source: 按来源过滤
            level: 按级别过滤
            limit: 返回记录数
            
        Returns:
            日志记录列表
        """
        query = 'SELECT * FROM logs WHERE 1=1'
        params = []
        
        if source:
            query += ' AND source = ?'
            params.append(source)
        
        if level:
            query += ' AND level = ?'
            params.append(level)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def query_by_time_range(self, start_time: str, end_time: str,
                            source: Optional[str] = None) -> List[Dict]:
        """按时间范围查询
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            source: 可选的来源过滤
            
        Returns:
            日志记录列表
        """
        query = 'SELECT * FROM logs WHERE timestamp >= ? AND timestamp <= ?'
        params = [start_time, end_time]
        
        if source:
            query += ' AND source = ?'
            params.append(source)
        
        query += ' ORDER BY timestamp'
        
        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_stats(self) -> Dict:
        """获取日志统计信息
        
        Returns:
            统计信息字典
        """
        stats = {}
        
        # 总记录数
        cursor = self.conn.execute('SELECT COUNT(*) as total FROM logs')
        stats['total_count'] = cursor.fetchone()['total']
        
        # 按来源统计
        cursor = self.conn.execute('''
            SELECT source, COUNT(*) as count 
            FROM logs 
            GROUP BY source 
            ORDER BY count DESC
        ''')
        stats['by_source'] = {row['source']: row['count'] for row in cursor.fetchall()}
        
        # 按级别统计
        cursor = self.conn.execute('''
            SELECT level, COUNT(*) as count 
            FROM logs 
            GROUP BY level 
            ORDER BY count DESC
        ''')
        stats['by_level'] = {row['level']: row['count'] for row in cursor.fetchall()}
        
        # 时间范围
        cursor = self.conn.execute('''
            SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time 
            FROM logs
        ''')
        row = cursor.fetchone()
        stats['time_range'] = {
            'earliest': row['min_time'],
            'latest': row['max_time']
        }
        
        return stats
    
    def get_sources(self) -> List[str]:
        """获取所有日志来源列表"""
        cursor = self.conn.execute('SELECT DISTINCT source FROM logs ORDER BY source')
        return [row['source'] for row in cursor.fetchall()]
    
    def migrate_from_file(self, log_file: str, source_name: str) -> Tuple[int, int]:
        """从日志文件迁移日志到SQLite
        
        支持多种日志格式：
        1. ISO格式: [2026-02-19T02:00:00.156077] [INFO] message
        2. 标准格式: [2026-02-19 10:46:20,672] INFO: message
        
        Args:
            log_file: 日志文件路径
            source_name: 日志来源名称
            
        Returns:
            (成功迁移数, 跳过数)
        """
        success_count = 0
        skip_count = 0
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parsed = self._parse_log_line(line)
                    if parsed:
                        self.log(
                            source=source_name,
                            level=parsed['level'],
                            message=parsed['message'],
                            timestamp=parsed['timestamp']
                        )
                        success_count += 1
                    else:
                        skip_count += 1
        except Exception as e:
            print(f"迁移文件 {log_file} 时出错: {e}")
        
        return success_count, skip_count
    
    def _parse_log_line(self, line: str) -> Optional[Dict]:
        """解析日志行
        
        Args:
            line: 日志行
            
        Returns:
            包含 timestamp, level, message 的字典，解析失败返回None
        """
        # 格式1: ISO格式 [2026-02-19T02:00:00.156077] [INFO] message
        match1 = re.match(r'\[(.*?)\]\s+\[(\w+)\]\s+(.*)', line)
        if match1:
            return {
                'timestamp': match1.group(1),
                'level': match1.group(2),
                'message': match1.group(3)
            }
        
        # 格式2: 标准格式 [2026-02-19 10:46:20,672] INFO: message
        match2 = re.match(r'\[(.*?)\]\s+(\w+):\s*(.*)', line)
        if match2:
            # 将标准格式转换为ISO格式
            try:
                dt = datetime.strptime(match2.group(1), '%Y-%m-%d %H:%M:%S,%f')
                iso_timestamp = dt.isoformat()
                return {
                    'timestamp': iso_timestamp,
                    'level': match2.group(2),
                    'message': match2.group(3)
                }
            except ValueError:
                pass
        
        return None
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()


def create_unified_logger(db_path: str = 'data/unified_logs.db') -> UnifiedLogger:
    """创建并返回UnifiedLogger实例"""
    return UnifiedLogger(db_path)


if __name__ == '__main__':
    # 测试代码
    logger = UnifiedLogger()
    
    # 写入测试日志
    logger.log('test', 'INFO', '测试日志消息')
    logger.log('test', 'WARN', '测试警告消息')
    logger.log('test', 'ERROR', '测试错误消息')
    
    # 查询日志
    results = logger.query(source='test')
    print(f"查询到 {len(results)} 条日志:")
    for row in results:
        print(f"[{row['timestamp']}] [{row['level']}] {row['message']}")
    
    # 获取统计信息
    stats = logger.get_stats()
    print(f"\n统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    logger.close()
