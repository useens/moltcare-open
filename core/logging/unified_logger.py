#!/usr/bin/env python3
"""
Unified Logger - SQLite-based centralized logging system
支持多源日志统一存储、按source/level/time查询、30天自动轮转
"""

import sqlite3
import json
import os
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Lock
import logging

@dataclass
class LogEntry:
    """日志条目数据结构"""
    timestamp: datetime
    source: str
    level: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'level': self.level,
            'message': self.message,
            'metadata': json.dumps(self.metadata) if self.metadata else None
        }

class UnifiedLogger:
    """
    统一日志管理器 - SQLite存储
    """
    
    DEFAULT_DB_PATH = "data/unified_logs.db"
    RETENTION_DAYS = 30
    
    # 日志级别映射
    LEVELS = {
        'DEBUG': 10,
        'INFO': 20,
        'WARNING': 30,
        'WARN': 30,
        'ERROR': 40,
        'CRITICAL': 50,
        'CRIT': 50
    }
    
    def __init__(self, db_path: str = None, retention_days: int = None):
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.retention_days = retention_days or self.RETENTION_DAYS
        self._lock = Lock()
        self._ensure_db()
    
    def _ensure_db(self):
        """确保数据库和表存在，处理schema迁移"""
        with self._get_conn() as conn:
            # 检查表是否存在
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # 创建新表
                conn.execute('''
                    CREATE TABLE logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        source TEXT NOT NULL,
                        level TEXT NOT NULL,
                        level_value INTEGER NOT NULL,
                        message TEXT NOT NULL,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                # 检查是否需要添加列
                cursor = conn.execute("PRAGMA table_info(logs)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'level_value' not in columns:
                    conn.execute('ALTER TABLE logs ADD COLUMN level_value INTEGER DEFAULT 20')
                    for level, value in self.LEVELS.items():
                        conn.execute('UPDATE logs SET level_value = ? WHERE level = ?', (value, level))
                
                if 'metadata' not in columns:
                    conn.execute('ALTER TABLE logs ADD COLUMN metadata TEXT')
            
            # 创建索引
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_source ON logs(source)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_level ON logs(level)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_level_value ON logs(level_value)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_source_time ON logs(source, timestamp)')
            conn.commit()
    
    @contextmanager
    def _get_conn(self):
        """获取数据库连接（线程安全）"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            yield conn
        finally:
            conn.close()
    
    def _get_level_value(self, level: str) -> int:
        """获取日志级别的数值"""
        return self.LEVELS.get(level.upper(), 20)
    
    def log(self, source: str, level: str, message: str, metadata: Dict[str, Any] = None):
        """
        写入单条日志
        
        Args:
            source: 日志来源 (如 'diagnosis', 'heal', 'notification')
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: 日志消息
            metadata: 可选的元数据字典
        """
        entry = LogEntry(
            timestamp=datetime.now(),
            source=source,
            level=level.upper(),
            message=message,
            metadata=metadata
        )
        
        with self._lock:
            with self._get_conn() as conn:
                conn.execute('''
                    INSERT INTO logs (timestamp, source, level, level_value, message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    entry.timestamp.isoformat(),
                    entry.source,
                    entry.level,
                    self._get_level_value(entry.level),
                    entry.message,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
    
    def log_batch(self, entries: List[LogEntry]):
        """批量写入日志"""
        with self._lock:
            with self._get_conn() as conn:
                for entry in entries:
                    conn.execute('''
                        INSERT INTO logs (timestamp, source, level, level_value, message, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        entry.timestamp.isoformat(),
                        entry.source,
                        entry.level,
                        self._get_level_value(entry.level),
                        entry.message,
                        json.dumps(entry.metadata) if entry.metadata else None
                    ))
                conn.commit()
    
    def query(self, 
              source: Optional[str] = None,
              level: Optional[str] = None,
              min_level: Optional[str] = None,
              start_time: Optional[datetime] = None,
              end_time: Optional[datetime] = None,
              keyword: Optional[str] = None,
              limit: int = 100,
              offset: int = 0) -> List[Dict[str, Any]]:
        """
        查询日志
        
        Args:
            source: 按来源过滤
            level: 按确切级别过滤
            min_level: 按最小级别过滤 (包含该级别及以上)
            start_time: 开始时间
            end_time: 结束时间
            keyword: 消息关键词
            limit: 返回数量限制
            offset: 分页偏移
        """
        conditions = []
        params = []
        
        if source:
            conditions.append("source = ?")
            params.append(source)
        
        if level:
            conditions.append("level = ?")
            params.append(level.upper())
        
        if min_level:
            conditions.append("level_value >= ?")
            params.append(self._get_level_value(min_level))
        
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        
        if keyword:
            conditions.append("message LIKE ?")
            params.append(f"%{keyword}%")
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f'''
            SELECT timestamp, source, level, message, metadata
            FROM logs
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        '''
        params.extend([limit, offset])
        
        with self._get_conn() as conn:
            cursor = conn.execute(query, params)
            results = []
            for row in cursor.fetchall():
                results.append({
                    'timestamp': row[0],
                    'source': row[1],
                    'level': row[2],
                    'message': row[3],
                    'metadata': json.loads(row[4]) if row[4] else None
                })
            return results
    
    def count(self,
              source: Optional[str] = None,
              level: Optional[str] = None,
              min_level: Optional[str] = None,
              start_time: Optional[datetime] = None,
              end_time: Optional[datetime] = None,
              keyword: Optional[str] = None) -> int:
        """查询日志数量"""
        conditions = []
        params = []
        
        if source:
            conditions.append("source = ?")
            params.append(source)
        
        if level:
            conditions.append("level = ?")
            params.append(level.upper())
        
        if min_level:
            conditions.append("level_value >= ?")
            params.append(self._get_level_value(min_level))
        
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        
        if keyword:
            conditions.append("message LIKE ?")
            params.append(f"%{keyword}%")
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"SELECT COUNT(*) FROM logs {where_clause}"
        
        with self._get_conn() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        with self._get_conn() as conn:
            # 总记录数
            total = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
            
            # 按来源统计
            cursor = conn.execute('''
                SELECT source, COUNT(*) FROM logs GROUP BY source
            ''')
            by_source = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按级别统计
            cursor = conn.execute('''
                SELECT level, COUNT(*) FROM logs GROUP BY level
            ''')
            by_level = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 时间范围
            cursor = conn.execute('''
                SELECT MIN(timestamp), MAX(timestamp) FROM logs
            ''')
            min_time, max_time = cursor.fetchone()
            
            # 数据库大小
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                'total_records': total,
                'by_source': by_source,
                'by_level': by_level,
                'time_range': {'min': min_time, 'max': max_time},
                'db_size_bytes': db_size,
                'db_size_mb': round(db_size / (1024 * 1024), 2)
            }
    
    def rotate(self, archive_dir: str = "data/log_archives") -> Dict[str, Any]:
        """
        执行日志轮转 - 删除超过保留期的日志
        
        Args:
            archive_dir: 归档目录路径
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        with self._lock:
            with self._get_conn() as conn:
                # 先统计要删除的记录
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM logs WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
                count_to_delete = cursor.fetchone()[0]
                
                # 执行删除
                conn.execute(
                    "DELETE FROM logs WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
                conn.commit()
        
        # VACUUM需要在事务外执行
        with self._get_conn() as conn:
            conn.execute("VACUUM")
            conn.commit()
        
        return {
            'deleted_records': count_to_delete,
            'cutoff_date': cutoff_date.isoformat(),
            'retention_days': self.retention_days
        }
    
    def export_to_jsonl(self, filepath: str, 
                        source: Optional[str] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> int:
        """导出日志到JSONL文件"""
        entries = self.query(
            source=source,
            start_time=start_time,
            end_time=end_time,
            limit=1000000  # 大限制以获取所有记录
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        return len(entries)


class UnifiedLogHandler(logging.Handler):
    """
    Python标准logging的Handler，将日志写入统一存储
    """
    
    def __init__(self, logger: UnifiedLogger, source: str):
        super().__init__()
        self.ulogger = logger
        self.source = source
    
    def emit(self, record: logging.LogRecord):
        """发送日志记录到统一存储"""
        try:
            metadata = {
                'module': record.module,
                'funcName': record.funcName,
                'lineno': record.lineno,
                'threadName': record.threadName
            }
            if record.exc_info:
                metadata['exception'] = self.formatException(record.exc_info)
            
            self.ulogger.log(
                source=self.source,
                level=record.levelname,
                message=self.format(record),
                metadata=metadata
            )
        except Exception:
            self.handleError(record)


# 全局单例
_default_logger = None
_default_lock = Lock()

def get_logger(db_path: str = None) -> UnifiedLogger:
    """获取默认日志管理器实例"""
    global _default_logger
    if _default_logger is None:
        with _default_lock:
            if _default_logger is None:
                _default_logger = UnifiedLogger(db_path)
    return _default_logger


if __name__ == '__main__':
    # 测试代码
    logger = UnifiedLogger()
    
    # 写入测试日志
    logger.log('test', 'INFO', '测试日志消息', {'key': 'value'})
    logger.log('test', 'WARNING', '警告日志')
    logger.log('test', 'ERROR', '错误日志')
    
    # 查询
    print("所有日志:")
    for entry in logger.query(limit=10):
        print(f"  [{entry['timestamp']}] {entry['source']} - {entry['level']}: {entry['message']}")
    
    # 统计
    print("\n统计信息:")
    print(logger.get_stats())
