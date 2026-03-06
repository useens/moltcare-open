"""
神经中枢 2.0 - SQLite数据库
任务持久化和状态存储
"""
import sqlite3
import json
from typing import Optional, List, Dict
from datetime import datetime
from contextlib import contextmanager

class TaskDatabase:
    """任务数据库管理"""
    
    def __init__(self, db_path: str = "/root/.openclaw/workspace/data/neural_hub/tasks.db"):
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def _get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库"""
        with self._get_conn() as conn:
            conn.executescript('''
                -- 任务表
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    priority INTEGER DEFAULT 3,
                    status TEXT DEFAULT 'pending',
                    assigned_to TEXT,
                    created_at REAL,
                    started_at REAL,
                    completed_at REAL,
                    payload TEXT,
                    result TEXT,
                    retry_count INTEGER DEFAULT 0,
                    error TEXT
                );
                
                -- nanobot状态表
                CREATE TABLE IF NOT EXISTS bot_status (
                    bot_id TEXT PRIMARY KEY,
                    name TEXT,
                    role TEXT,
                    state TEXT DEFAULT 'offline',
                    capabilities TEXT,
                    current_task TEXT,
                    last_heartbeat REAL,
                    success_rate REAL DEFAULT 1.0,
                    total_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0
                );
                
                -- 事件日志
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    level TEXT,
                    source TEXT,
                    event_type TEXT,
                    message TEXT,
                    metadata TEXT
                );
                
                -- 消息历史
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    msg_type TEXT,
                    from_bot TEXT,
                    to_bot TEXT,
                    content TEXT,
                    timestamp REAL,
                    delivered BOOLEAN DEFAULT 0
                );
                
                -- 创建索引
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to);
                CREATE INDEX IF NOT EXISTS idx_bot_status_state ON bot_status(state);
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
            ''')
    
    # ========== 任务管理 ==========
    
    def create_task(self, task_id: str, task_type: str, priority: int = 3, 
                    payload: dict = None) -> bool:
        """创建任务"""
        with self._get_conn() as conn:
            conn.execute('''
                INSERT INTO tasks (id, type, priority, status, created_at, payload)
                VALUES (?, ?, ?, 'pending', ?, ?)
            ''', (task_id, task_type, priority, datetime.now().timestamp(),
                  json.dumps(payload) if payload else None))
        return True
    
    def assign_task(self, task_id: str, bot_id: str) -> bool:
        """分配任务"""
        with self._get_conn() as conn:
            conn.execute('''
                UPDATE tasks 
                SET assigned_to = ?, status = 'assigned', started_at = ?
                WHERE id = ?
            ''', (bot_id, datetime.now().timestamp(), task_id))
            
            conn.execute('''
                UPDATE bot_status SET current_task = ? WHERE bot_id = ?
            ''', (task_id, bot_id))
        return True
    
    def complete_task(self, task_id: str, result: dict = None) -> bool:
        """完成任务"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                'SELECT assigned_to FROM tasks WHERE id = ?', (task_id,)
            )
            row = cursor.fetchone()
            bot_id = row['assigned_to'] if row else None
            
            conn.execute('''
                UPDATE tasks 
                SET status = 'completed', completed_at = ?, result = ?
                WHERE id = ?
            ''', (datetime.now().timestamp(), 
                  json.dumps(result) if result else None, task_id))
            
            if bot_id:
                conn.execute('''
                    UPDATE bot_status 
                    SET current_task = NULL, total_tasks = total_tasks + 1
                    WHERE bot_id = ?
                ''', (bot_id,))
        return True
    
    def fail_task(self, task_id: str, error: str) -> bool:
        """标记任务失败"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                'SELECT assigned_to, retry_count FROM tasks WHERE id = ?', (task_id,)
            )
            row = cursor.fetchone()
            bot_id = row['assigned_to'] if row else None
            retry_count = row['retry_count'] if row else 0
            
            if retry_count < 3:
                # 重试
                conn.execute('''
                    UPDATE tasks 
                    SET status = 'pending', assigned_to = NULL, 
                        retry_count = retry_count + 1, error = ?
                    WHERE id = ?
                ''', (error, task_id))
            else:
                # 最终失败
                conn.execute('''
                    UPDATE tasks 
                    SET status = 'failed', error = ?, completed_at = ?
                    WHERE id = ?
                ''', (error, datetime.now().timestamp(), task_id))
            
            if bot_id:
                conn.execute('''
                    UPDATE bot_status 
                    SET current_task = NULL, failed_tasks = failed_tasks + 1
                    WHERE bot_id = ?
                ''', (bot_id,))
        return True
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务"""
        with self._get_conn() as conn:
            cursor = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def list_pending_tasks(self, limit: int = 100) -> List[Dict]:
        """获取待处理任务"""
        with self._get_conn() as conn:
            cursor = conn.execute('''
                SELECT * FROM tasks 
                WHERE status IN ('pending', 'retry')
                ORDER BY priority ASC, created_at ASC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== Bot状态管理 ==========
    
    def register_bot(self, bot_id: str, name: str, role: str, 
                     capabilities: List[str]) -> bool:
        """注册bot"""
        with self._get_conn() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO bot_status 
                (bot_id, name, role, state, capabilities, last_heartbeat)
                VALUES (?, ?, ?, 'idle', ?, ?)
            ''', (bot_id, name, role, json.dumps(capabilities),
                  datetime.now().timestamp()))
        return True
    
    def update_bot_status(self, bot_id: str, state: str, 
                          current_task: str = None) -> bool:
        """更新bot状态"""
        with self._get_conn() as conn:
            conn.execute('''
                UPDATE bot_status 
                SET state = ?, current_task = ?, last_heartbeat = ?
                WHERE bot_id = ?
            ''', (state, current_task, datetime.now().timestamp(), bot_id))
        return True
    
    def heartbeat(self, bot_id: str) -> bool:
        """更新心跳"""
        with self._get_conn() as conn:
            conn.execute('''
                UPDATE bot_status 
                SET last_heartbeat = ?
                WHERE bot_id = ?
            ''', (datetime.now().timestamp(), bot_id))
        return True
    
    def get_bot_status(self, bot_id: str) -> Optional[Dict]:
        """获取bot状态"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                'SELECT * FROM bot_status WHERE bot_id = ?', (bot_id,)
            )
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['capabilities'] = json.loads(data['capabilities'] or '[]')
                return data
            return None
    
    def list_active_bots(self) -> List[Dict]:
        """获取活跃bot列表"""
        with self._get_conn() as conn:
            # 30秒内有心跳的视为活跃
            threshold = datetime.now().timestamp() - 30
            cursor = conn.execute('''
                SELECT * FROM bot_status 
                WHERE last_heartbeat > ?
                ORDER BY name
            ''', (threshold,))
            bots = []
            for row in cursor.fetchall():
                data = dict(row)
                data['capabilities'] = json.loads(data['capabilities'] or '[]')
                bots.append(data)
            return bots
    
    def list_idle_bots(self) -> List[Dict]:
        """获取空闲bot列表"""
        with self._get_conn() as conn:
            threshold = datetime.now().timestamp() - 30
            cursor = conn.execute('''
                SELECT * FROM bot_status 
                WHERE state = 'idle' AND last_heartbeat > ?
                ORDER BY total_tasks ASC
            ''', (threshold,))
            bots = []
            for row in cursor.fetchall():
                data = dict(row)
                data['capabilities'] = json.loads(data['capabilities'] or '[]')
                bots.append(data)
            return bots
    
    # ========== 事件日志 ==========
    
    def log_event(self, level: str, source: str, event_type: str,
                  message: str, metadata: dict = None) -> bool:
        """记录事件"""
        with self._get_conn() as conn:
            conn.execute('''
                INSERT INTO events (timestamp, level, source, event_type, message, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (datetime.now().timestamp(), level, source, event_type,
                  message, json.dumps(metadata) if metadata else None))
        return True
    
    def get_recent_events(self, limit: int = 100) -> List[Dict]:
        """获取最近事件"""
        with self._get_conn() as conn:
            cursor = conn.execute('''
                SELECT * FROM events 
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== 统计 ==========
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self._get_conn() as conn:
            stats = {}
            
            # 任务统计
            cursor = conn.execute('''
                SELECT status, COUNT(*) as count FROM tasks GROUP BY status
            ''')
            stats['tasks'] = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Bot统计
            cursor = conn.execute('''
                SELECT state, COUNT(*) as count FROM bot_status GROUP BY state
            ''')
            stats['bots'] = {row['state']: row['count'] for row in cursor.fetchall()}
            
            # 总任务数
            cursor = conn.execute('SELECT COUNT(*) as total FROM tasks')
            stats['total_tasks'] = cursor.fetchone()['total']
            
            return stats
